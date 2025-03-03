from __future__ import annotations

import datetime
import difflib
import pprint
from dataclasses import dataclass, field
from typing import Any, Callable, Generator, Hashable

import pandas as pd
from googleapiutils2 import cache_with_stale_interval
from litellm import completion
from loguru import logger

from src.utils import (
    Model,
    handle_response,
)


@dataclass
class Confidence:
    """Confidence score for a match"""

    difflib: float = 0.0
    model: float = 0.0

    @property
    def percent(self) -> float:
        """Calculate average confidence"""
        return (self.difflib * 0.8 + self.model * 1.2) / 2


@dataclass
class MatchResult:
    """Container for individual match results"""

    index: int  # Match index
    name: str  # Matched name
    confidence: Confidence  # Match confidence


@dataclass
class ReconcileResult:
    """Result of name reconciliation with match details"""

    input_name: str  # Original input name

    matched_name: str  # Successfully matched name

    match_ix: int  # Index in reference data

    match_list_ix: int  # Index of matching list

    model: Model  # AI model used for matching

    confidence: Confidence  # Match confidence

    metadata: dict[str, Any] = field(default_factory=dict)  # Additional match metadata


# Type definitions for matching functions
MatchFunction = Callable[
    [str, list[str], str | None],
    MatchResult | None,
]

ModelMatchFunction = Callable[
    [str, list[str], Model, str | None],
    MatchResult | None,
]


@cache_with_stale_interval(datetime.timedelta(days=1))
def find_match(
    input_name: str,
    match_list: list[str],
    model: Model,
    context: str | None = None,
) -> MatchResult | None:

    # Try exact match first
    try:
        match_ix = match_list.index(input_name)

        logger.info(f"Exact match found: '{input_name}'")

        return MatchResult(
            index=match_ix, name=input_name, confidence=Confidence(model=1.0)
        )
    except ValueError:
        pass

    # Prepare input for AI model
    match_list_str = "\n".join(match_list)
    context = context or ""

    # Define system message for AI
    system_msg = f"""Take the following input-name and match-list and fuzzy-find the input-name within the match-list.

    Use your reason to find the best match, and return the best match as a JSON object with the following properties:
    
    - best_match (list[str]): The best match, a list of the best match, or matches, from the **MATCH LIST VERBATIM, NOT FROM THE INPUT NAME**. 
                  If a **REASONABLE** match is not found, return an empty list. Don't overthink it, just use your intuition.
    - confidence (float): An approximate confidence of the match, a number between 0 and 1.

    You **MUST** only include values from the match-list in the best_match list.


    {context}
"""

    # Format content for AI
    content = f"""Input-name: {input_name}
    Match-list:
    {match_list_str}
    """

    # Get AI completion
    response = completion(
        model=model,
        messages=[
            {"role": "system", "content": system_msg},
            {"role": "user", "content": content},
        ],
        response_format={"type": "json_object"},
        drop_params=True,
    )

    # Process response
    data = handle_response(response)
    if data is None or not isinstance(data, dict):
        return None

    # Extract match details
    try:
        match_names = data["best_match"]

        if not match_names:
            logger.warning(f"No match found for '{input_name}'")
            return None

        match_name = match_names[0]

        match_ix = match_list.index(match_name)

        confidence: float = data.get("confidence", 0.0)

        logger.info(f"Match found: '{input_name}' -> '{match_name}'")

        return MatchResult(
            index=match_ix,
            name=match_name,
            confidence=Confidence(model=confidence),
        )

    except Exception as e:
        logger.error(f"Error processing match: {e}")
        return None


class ModelNameReconciler:
    """Name reconciliation engine using AI models"""

    def __init__(
        self,
        models: Model | list[Model],
        context: str | None = None,
        api_keys: dict[Model, str] | None = None,
    ):
        """Initialize reconciler with models and optional context"""
        self.api_keys = api_keys
        self.models = [models] if isinstance(models, str) else models
        self.context = context

    def _reconcile_single_match(
        self,
        name: str,
        match_list_names: list[str],
        match_list_indices: list[int],
        model: Model,
        match_func: ModelMatchFunction,
    ) -> MatchResult | None:
        """Process single match attempt with one model"""
        match: MatchResult | None = match_func(  # type: ignore
            name,
            match_list_names,
            model=model,
            context=self.context,
        )  # type: ignore

        if match is None:
            logger.warning("No match found.")
            return None

        match.index = match_list_indices[match.index]

        # Calculate match confidence with difflib
        difflib_confidence = difflib.SequenceMatcher(None, name, match.name).ratio()

        match.confidence.difflib = difflib_confidence

        return match

    def _reconcile_models_matches(
        self,
        name: str,
        match_lists_names: list[tuple[list[int], list[str]]],
        match_func: ModelMatchFunction,
    ) -> ReconcileResult | None:
        """Try matching across all models and match lists"""
        if pd.isna(name):
            return None

        results: list[ReconcileResult] = []

        # Iterate through match lists and models
        for match_list_ix, (names_indices, names_values) in enumerate(
            match_lists_names
        ):
            for model in self.models:
                match_result = self._reconcile_single_match(
                    name=name,
                    match_list_names=names_values,
                    match_list_indices=names_indices,
                    model=model,
                    match_func=match_func,
                )
                if match_result is None:
                    continue

                # Return successful match result
                result = ReconcileResult(
                    input_name=name,
                    matched_name=match_result.name,
                    match_ix=match_result.index,
                    match_list_ix=match_list_ix,
                    model=model,
                    confidence=match_result.confidence,
                )

                results.append(result)

        if not results:
            return None

        results.sort(key=lambda r: r.confidence.percent, reverse=True)

        best_result = results[0]

        # log the sorted list of results with their confidence:
        for result in results:
            logger.info(
                f"Matched '{result.input_name}' -> '{result.matched_name}' with confidence {result.confidence.percent}"
            )

        logger.success(
            f"Best match for '{name}': '{best_result.matched_name}' with confidence {best_result.confidence.percent}"
        )

        return best_result

    def reconcile(
        self,
        input_list: pd.Series,
        match_lists: list[pd.Series] | pd.Series,
        match_func: ModelMatchFunction | None = None,
    ) -> Generator[tuple[Hashable, ReconcileResult | None], None, None]:

        # Normalize inputs
        if not isinstance(match_lists, list):
            match_lists = [match_lists]

        if match_func is None:
            match_func = find_match

        # Prepare match lists
        match_lists_names_dfs: list[pd.Series] = [
            (match_list.dropna().sort_values()) for match_list in match_lists
        ]

        match_lists_names: list[tuple[list[int], list[str]]] = [
            (df.index.to_list(), df.to_list()) for df in match_lists_names_dfs
        ]

        # Process each input name
        for ix, name in input_list.items():
            logger.info(f"Processing row {ix}: '{name}'")

            result = self._reconcile_models_matches(
                name=name,
                match_lists_names=match_lists_names,
                match_func=match_func,
            )
            yield ix, result
