#!/bin/bash
set -e

# Function to log messages
log_message() {
    echo -e "$1\n" >> "$LOG_FILE"
}

# Function to check command success and log accordingly
check_command() {
    if [ $? -eq 0 ]; then
        log_message "$1 succeeded"
    else
        log_message "$1 failed"
        exit 1
    fi
}

# Initialization
CITRIX_BUILD_PATH="$1"
BUILD_ID="$2"
LOG_FILE="$3"
ICACLIENT="$4"
CTXUSB="$5"
ICACLIENT_SRC_FOLDER="$CITRIX_BUILD_PATH/$BUILD_ID/icaclient"
CTXUSB_SRC_FOLDER="$CITRIX_BUILD_PATH/$BUILD_ID/ctxusb"

# Ensure log file exits
[ ! -f "$LOG_FILE" ] && touch "$LOG_FILE"

log_message "Starting citrix workspace app build"
log_message "-----------------------------------"

# Move icaclient and ctxusb deb package to ICACLIENT_SRC_FOLDER
mkdir -p "$ICACLIENT_SRC_FOLDER"
mkdir -p "$CTXUSB_SRC_FOLDER"
log_message "Moving icaclient and ctxusb deb package to ICACLIENT_SRC_FOLDER and CTXUSB_SRC_FOLDER respectively"
mv "$ICACLIENT" "$ICACLIENT_SRC_FOLDER"
mv "$CTXUSB" "$CTXUSB_SRC_FOLDER"
check_command "Moving icaclient and ctxusb deb package to ICACLIENT_SRC_FOLDER and CTXUSB_SRC_FOLDER respectively"

# Get the version of icaclient from the deb package
icaclient_deb_pkg=$(ls "$ICACLIENT_SRC_FOLDER")
ICACLIENT_VERSION=$(dpkg-deb -f "$ICACLIENT_SRC_FOLDER/$icaclient_deb_pkg" Version)
log_message "ICAClient Version: $ICACLIENT_VERSION"
# Get the version of ctxusb from the deb package
ctxusb_deb_pkg=$(ls "$CTXUSB_SRC_FOLDER")
CTXUSB_VERSION=$(dpkg-deb -f "$CTXUSB_SRC_FOLDER/$ctxusb_deb_pkg" Version)
log_message "CTXUSB Version: $CTXUSB_VERSION"

# Extract the icaclient deb package
log_message "Extracting icaclient deb package"
mkdir -p "$ICACLIENT_SRC_FOLDER/002-Citrix-Workspace-$ICACLIENT_VERSION"
dpkg-deb -x "$ICACLIENT_SRC_FOLDER/$icaclient_deb_pkg" "$ICACLIENT_SRC_FOLDER/002-Citrix-Workspace-$ICACLIENT_VERSION"
check_command "Extracting icaclient deb package"

# Extract the ctxusb deb package
log_message "Extracting ctxusb deb package"
mkdir -p "$CTXUSB_SRC_FOLDER/002-Citrix-Workspace-USB-$CTXUSB_VERSION"
dpkg-deb -x "$CTXUSB_SRC_FOLDER/$ctxusb_deb_pkg" "$CTXUSB_SRC_FOLDER/002-Citrix-Workspace-USB-$CTXUSB_VERSION"
check_command "Extracting ctxusb deb package"