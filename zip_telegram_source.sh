#!/bin/bash

# Configuration based on your previous setup
FUNCTION_DIR="backend"
ZIP_OUTPUT_PATH="terraform/telegram_source.zip"
GITIGNORE_FILE=".gitignore"

# --- Zipping Logic ---

echo "Starting deployment zip process..."

# 1. Clean up any previous zip file
if [ -f "$ZIP_OUTPUT_PATH" ]; then
    rm "$ZIP_OUTPUT_PATH"
    echo "Removed old artifact: $ZIP_OUTPUT_PATH"
fi

# 2. Use the 'git ls-files' command to get a list of tracked files
# This is the safest method as it ensures you only package files
# that are actually committed to your repository (excluding local secrets).
git ls-files -z "$FUNCTION_DIR" | \
xargs -0 zip -r9 "$ZIP_OUTPUT_PATH"

echo "Successfully created deployment archive at: $ZIP_OUTPUT_PATH"