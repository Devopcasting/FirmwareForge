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
FIREFOX_BUILD_PATH="$1"
BUILD_ID="$2"
LOG_FILE="$3"
FIREFOX_REFRENCE_PATH="$4"
TARBALL="$FIREFOX_BUILD_PATH/$BUILD_ID/firefox.tar.bz2"
FIREFOX_SRC_FOLDER="$FIREFOX_BUILD_PATH/$BUILD_ID/firefox"


# Ensure log file exits
[ ! -f "$LOG_FILE" ] && touch "$LOG_FILE"

log_message "Starting firefox build"
log_message "----------------------"

# Create a locked name file in the build path
touch "$FIREFOX_BUILD_PATH/$BUILD_ID/locked"

# Download the latest firefox source code
latest_firefox_url=$(curl -s 'https://download.mozilla.org/?product=firefox-latest&os=linux64&lang=en-US'| grep -oP 'https://[^"]+\.tar\.bz2')
log_message "Downloading firefox source code"

curl -k "$latest_firefox_url" -o "$TARBALL" &>> "$LOG_FILE"
check_command "Download firefox source code"

# Get the version number of the downloaded Firefox
version_no=$(curl -sI 'https://download.mozilla.org/?product=firefox-latest&os=linux64&lang=en-US'| grep -o 'firefox-[0-9.]\+[0-9]' | cut -d'-' -f2)
firefox_pkg_name="005-firefox-$version_no"
log_message "Firefox version: $version_no"

# Validate the tarball
log_message "Validating tarball"
tar -tf "$TARBALL" &>> "$LOG_FILE"
check_command "Validate tarball"

# Extract the tarball
log_message "Extracting tarball"
tar -xjf "$TARBALL" -C "$FIREFOX_BUILD_PATH/$BUILD_ID" &>> "$LOG_FILE"
check_command "Extract tarball"

# Verify extraction
if [ -d "$FIREFOX_SRC_FOLDER" ] && [ "$(ls -A "$FIREFOX_SRC_FOLDER")" ]; then
    log_message "Firefox folder is extracted and not empty"
else
    log_message "Error: Firefox folder is not extracted or empty"
    exit 1
fi

# Create Patch directory structure
log_message "Creating Patch directory structure"
mkdir -p "$FIREFOX_BUILD_PATH/$BUILD_ID/root"
mkdir -p "$FIREFOX_BUILD_PATH/$BUILD_ID/tmp"
check_command "Create Patch directory structure"

# Create SquashFS Package
log_message "Creating SquashFS Package"
mkdir -p "$FIREFOX_BUILD_PATH/$BUILD_ID/tmp/$firefox_pkg_name"
mkdir -p "$FIREFOX_BUILD_PATH/$BUILD_ID/tmp/$firefox_pkg_name/opt"
mkdir -p "$FIREFOX_BUILD_PATH/$BUILD_ID/tmp/$firefox_pkg_name/usr"
mkdir -p "$FIREFOX_BUILD_PATH/$BUILD_ID/tmp/$firefox_pkg_name/pkgs"
chmod -R 755 "$FIREFOX_BUILD_PATH/$BUILD_ID/tmp/$firefox_pkg_name"
mv "$FIREFOX_SRC_FOLDER" "$FIREFOX_BUILD_PATH/$BUILD_ID/tmp/$firefox_pkg_name/opt"
mkdir -p "$FIREFOX_BUILD_PATH/$BUILD_ID/tmp/$firefox_pkg_name/opt/firefox/distribution"
chmod 755 "$FIREFOX_BUILD_PATH/$BUILD_ID/tmp/$firefox_pkg_name/opt/firefox/distribution"
cp -pa $FIREFOX_REFRENCE_PATH/distribution/* "$FIREFOX_BUILD_PATH/$BUILD_ID/tmp/$firefox_pkg_name/opt/firefox/distribution/"
cp -pa $FIREFOX_REFRENCE_PATH/defaults/* "$FIREFOX_BUILD_PATH/$BUILD_ID/tmp/$firefox_pkg_name/opt/firefox/defaults/"
cp -pa $FIREFOX_REFRENCE_PATH/usr/* "$FIREFOX_BUILD_PATH/$BUILD_ID/tmp/$firefox_pkg_name/usr/"
cd "$FIREFOX_BUILD_PATH/$BUILD_ID/tmp/$firefox_pkg_name"
find . > pkgs/"$firefox_pkg_name"
sed -i 's/^.//g' pkgs/"$firefox_pkg_name"
cd "$FIREFOX_BUILD_PATH/$BUILD_ID/tmp"
mksquashfs "$firefox_pkg_name" "$firefox_pkg_name.sq" -b 1048576 -comp xz -Xdict-size 100% &>> "$LOG_FILE"
check_command "Create SquashFS Package"

# Create install script
log_message "Creating install script"
cat <<EOF > "$FIREFOX_BUILD_PATH/$BUILD_ID/root/install.sh"
#!/bin/bash
pids=\$(pgrep -f firefox)
for pid in \$pids; do
    kill \$pid
done

mount -o remount,rw /sda1

dir=\$(find /data/apps-mount/ -type d -name 005* -print | awk 'NR==1')
[ -n "\$dir" ] && { mount -t aufs -o remount,del="\$dir" /; umount "\$dir"; rm -rf "\$dir"; }

rm -f /sda1/data/apps/005-firefox-* 2>/dev/null
cp /tmp/005-firefox-* /sda1/data/apps/
chmod 755 /sda1/data/apps/005-firefox-*
mount -o remount,ro /sda1
EOF
chmod +x "$FIREFOX_BUILD_PATH/$BUILD_ID/root/install.sh"
check_command "Creating install script"

# Clean up
log_message "Cleaning up"
rm -rf "$FIREFOX_BUILD_PATH/$BUILD_ID/tmp/$firefox_pkg_name"
check_command "Cleaning up"

# Create final tarball
build_date=$(date +%d%m%y)
final_tarball="$FIREFOX_BUILD_PATH/$BUILD_ID/firefox_$version_no-QFW$BUILD_ID-$build_date.tar.bz2"
log_message "Creating final tarball: $final_tarball"
cd "$FIREFOX_BUILD_PATH/$BUILD_ID"
tar -cjf "$final_tarball" root tmp
check_command "Creating final tarball"

# Corrupt tarball
log_message "Corrupting tarball"
damage corrupt $final_tarball 1
check_command "Corrupting tarball"

# Move tarball to web directory
log_message "Moving tarball to web directory"
web_dir="/var/www/html/repo/$BUILD_ID"
sudo mkdir -p "$web_dir"
sudo chmod 755 "$web_dir"
sudo cp "$final_tarball" "$web_dir"
sudo chmod 755 "$web_dir/firefox_$version_no-QFW$BUILD_ID-$build_date.tar.bz2"
check_command "Moving tarball to web directory"
log_message "Build process completed successfully"
# Remove the locked name file
rm "$FIREFOX_BUILD_PATH/$BUILD_ID/locked"