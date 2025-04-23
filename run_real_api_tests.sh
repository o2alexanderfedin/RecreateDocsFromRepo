#!/bin/bash

# Script to run the real API integration tests
# You can provide your Mistral API key as an argument:
# ./run_real_api_tests.sh YOUR_API_KEY
# Or it will use the MISTRAL_API_KEY from .env file if available

# Check if .env file exists and source it
if [ -f .env ]; then
    echo "Loading API key from .env file..."
    export $(grep -v '^#' .env | xargs)
fi

# If argument is provided, it overrides the .env file
if [ $# -ge 1 ]; then
    export MISTRAL_API_KEY=$1
fi

# Check if we have an API key
if [ -z "$MISTRAL_API_KEY" ]; then
    echo "No API key provided. Please either:"
    echo "1. Add MISTRAL_API_KEY to .env file"
    echo "2. Provide API key as argument: $0 <MISTRAL_API_KEY>"
    exit 1
fi

echo "Using Mistral API key: ${MISTRAL_API_KEY:0:5}***************"

# Run the real API tests with verbose output
python3 -m pytest src/file_analyzer/tests/test_real_api.py -v

# Status code from pytest
exit_code=$?

# Done
echo ""
echo "Tests completed with exit code: $exit_code"
exit $exit_code