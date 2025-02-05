# `reconcile`

A powerful tool for reconciling names across multiple data sources using AI-powered fuzzy matching and Google Sheets integration.

## Overview 📖

This tool helps you match and reconcile names across different datasets using advanced AI models. It's particularly useful when dealing with:

-   Multiple variations of the same name
-   Misspellings and typos
-   Different formatting conventions
-   Large datasets requiring automated matching

## Features ✨

-   AI-powered fuzzy name matching
-   Integration with Google Sheets for input and output
-   Configurable matching parameters
-   Support for multiple reference lists
-   Confidence scoring for matches
-   Batch processing capabilities
-   Caching system for improved performance

## Requirements 🛠️

-   Python ^3.12
-   Google Sheets API access
-   Valid Google API credentials
-   Required Python packages:
    -   googleapiutils2
    -   pandas
    -   litellm
    -   loguru

## Quick Start 🚀

1. Create a `config.toml` file with your settings:

```toml
google_credentials = "path/to/credentials.json"
model_name = "your-ai-model"
system_prompt = "Your matching context here"

[input_sheet]
url = "your-sheet-url"
range_name = "Sheet1!A:B"
column_name = "Name"

[[reference_sheets]]
url = "reference-sheet-url"
range_name = "Sheet1!A:B"
column_name = "Reference_Name"

[output_sheet]
url = "output-sheet-url"
range_name = "Sheet1!A:E"
column_name = "Matched_Name"
```

2. Run the reconciliation:

```python
from pathlib import Path
from main import main

main(config_path=Path("./config.toml"))
```

## Configuration 🔧

The tool is configured using a TOML file with the following sections:

### Core Settings

-   `google_credentials`: Path to Google API credentials file
-   `model_name`: AI model to use for matching
-   `system_prompt`: Context provided to the AI for matching
-   `batch_size`: Optional batch size for processing
-   `include_references`: Include reference data in output
-   `include_input`: Include input data in output

### Sheet Configurations

Each sheet configuration requires:

-   `url`: Google Sheet URL
-   `range_name`: Sheet range in A1 notation
-   `column_name`: Column to use for matching

## How It Works 🔍

1. **Loading Data**:

    - Reads input names from specified Google Sheet
    - Loads reference lists from configured sheets

2. **Matching Process**:

    - Attempts exact matches first
    - Uses AI model for fuzzy matching
    - Calculates confidence scores using sequence matching
    - Caches results for 24 hours

3. **Output Generation**:
    - Writes matches to specified output sheet
    - Includes confidence scores and match metadata
    - Optional inclusion of reference and input data

## Output Format 📊

The tool generates an output with the following columns:

-   Name: Original input name
-   Matched Name: Best match found
-   Match Index: Index in reference data
-   Confidence: Match confidence score (0-1)
-   Additional columns based on configuration

## Best Practices 💡

1. **Reference Data Quality**:

    - Keep reference lists well-maintained and standardized
    - Remove duplicates and inconsistencies
    - Include common variations where possible

2. **Performance Optimization**:

    - Use batch processing for large datasets
    - Leverage caching for repeated matches
    - Monitor and adjust batch sizes as needed

3. **Match Validation**:
    - Review matches with low confidence scores
    - Maintain a list of known exceptions
    - Regularly update reference data based on findings

## Match Quality Issues 🔧

    - Adjust system prompt for better context
    - Review and clean reference data
    - Consider lowering batch size for more accurate matching
