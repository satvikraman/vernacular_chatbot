#!/bin/bash

# Configuration
# ----------------------------------------------------------------------
# CHANGE 1: The root directory of the source code to be zipped
SOURCE_ROOT_DIR="./" 
ZIP_OUTPUT_PATH="../infra/telegram_source.zip"

# CHANGE 2: The .zipignore file is now relative to the source root
ZIP_IGNORE_FILE="$SOURCE_ROOT_DIR/.zipignore" 
TEMP_FILE="files_to_zip.txt"

# --- Zipping Logic ---

echo "Starting deployment zip process..."

# 1. Clean up previous artifacts
if [ -f "$ZIP_OUTPUT_PATH" ]; then
    rm "$ZIP_OUTPUT_PATH"
    echo "Removed old artifact: $ZIP_OUTPUT_PATH"
fi

# 2. Get all tracked files within the SOURCE_ROOT_DIR (backend/)
# This lists files using the full relative path, e.g., 'backend/functions/telegram_main.py'
git ls-files "$SOURCE_ROOT_DIR" > "$TEMP_FILE"

# 3. Filter the list using .zipignore (Assuming patterns use the full path)
if [ -f "$ZIP_IGNORE_FILE" ]; then
    echo "Applying exclusions from $ZIP_IGNORE_FILE..."
    grep -v -E -f "$ZIP_IGNORE_FILE" "$TEMP_FILE" > "${TEMP_FILE}.filtered"
    mv "${TEMP_FILE}.filtered" "$TEMP_FILE"
fi

# 4. Create the ZIP archive using the final filtered file list
# IMPORTANT: Use the -n option to not strip paths. We pipe the list of files
# and tell zip to store them using their full path relative to the repo root.
# Then, use a shell trick to temporarily change directory for the zip command.
cat "$TEMP_FILE" | zip -@ "$ZIP_OUTPUT_PATH"

# 5. Clean up temporary file
rm "$TEMP_FILE"

echo "Successfully created deployment archive at: $ZIP_OUTPUT_PATH"