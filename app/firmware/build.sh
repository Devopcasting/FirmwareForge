#!/bin/bash
set -e
set -x
# Function to log messages
log_message() {
    echo -e "$1\n" >> "$LOG_PATH"
}

# Function to check command success and log accordingly
check_command() {
    if [ $? -ne 0 ]; then
        log_message "$1 failed"
        exit 1
    else
        log_message "$1 succeeded"
    fi
}

# Initialization
BUILD_PATH="$1"
BUILD_ID="$2"
LOG_PATH="$3"

# Ensure log file exists
[ ! -f "$LOG_PATH" ] && touch "$LOG_PATH"

log_message "Starting Google Chrome build"
log_message "----------------------------"

# Create Patch structure
log_message "Creating Patch structure"
mkdir -p "$BUILD_PATH/patch"