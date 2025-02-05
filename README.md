# `reconcile`

A tool for reconciling names across multiple data sources using AI-powered fuzzy matching and Google Sheets integration.

## Features ✨

-   AI-powered fuzzy name matching
    -   Using GPT-4o, Claude 3, or other models
-   Integration with Google Sheets for input and output
-   Configurable matching parameters
-   Support for multiple reference lists
-   Confidence scoring for matches
-   Model caching system for improved performance

## Quickstart 🚀

This project requires Python `^3.12` to run.

### via [`poetry`](https://python-poetry.org/docs/)

Install poetry, then run

> poetry install

And you're done.

### Usage

1. Create a `config.toml` file with your settings:

```toml
google_credentials = "path/to/credentials.json"
model_credentials = "your-model-api-key" # optional, only needed for some models
model_name = "your-ai-model" # must be supported by litellm
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

Or via running the script directly:

```bash
poetry run python reconcile --config ./config.toml
```

To leverage a given model (ChatGPT, Claude, etc.), you'll need to add your respective API key to the above config. For Google Sheets, you'll need to set up a service account and download the credentials JSON file; see the [`googleapiutils2`](https://github.com/mkbabb/googleapiutils2) repo for more information.

## Configuration 🔧

The tool is configured using a TOML file with the following sections:

### Core Settings

-   `google_credentials`: Path to Google API credentials file
-   `model_credentials`: API key for the AI model
-   `model_name`: AI model to use for matching
-   `system_prompt`: Context provided to the AI for matching
-   `batch_size`: Optional batch size for processing
-   `include_references`: Include reference data rows in output
-   `include_input`: Include input data rows in output

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
-   Confidence: Match confidence score, based on Python's difflib (Levenshtein distance & c) (0-1)
-   Additional columns based on configuration
    -   Reference data: row data from the matched reference
    -   Input data: row data from the input
