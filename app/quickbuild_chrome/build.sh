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
CHROME_BUILD_PATH="$1"
BUILD_ID="$2"
LOG_PATH="$3"
STATIC_PATH="$4"
CHROME_FOLDER="$CHROME_BUILD_PATH/$BUILD_ID/chrome"

# Ensure log file exists
[ ! -f "$LOG_PATH" ] && touch "$LOG_PATH"

log_message "Starting Google Chrome build"
log_message "----------------------------"

# Create a locked name file in the build path
touch "$CHROME_BUILD_PATH/$BUILD_ID/locked"

# Download the latest Google Chrome debian and save the file in CHROME BUILD PATH
latest_chrome_url="https://dl.google.com/linux/direct/google-chrome-stable_current_amd64.deb"
log_message "Downloading Google Chrome from: $latest_chrome_url"
curl -o "$CHROME_BUILD_PATH/$BUILD_ID/google-chrome-stable_current_amd64.deb" "$latest_chrome_url" &>> "$LOG_PATH"
check_command "Downloading Google Chrome"

# Extract the Google Chrome debian
log_message "Extracting Google Chrome"
dpkg -x "$CHROME_BUILD_PATH/$BUILD_ID/google-chrome-stable_current_amd64.deb" "$CHROME_FOLDER" &>> "$LOG_PATH"
check_command "Extracting Google Chrome"

# Remove the Google Chrome debian
log_message "Removing Google Chrome debian"
rm "$CHROME_BUILD_PATH/$BUILD_ID/google-chrome-stable_current_amd64.deb" &>> "$LOG_PATH"
check_command "Removing Google Chrome debian"

# Get the version of Google Chrome
log_message "Getting Google Chrome version"
repo_url="http://dl.google.com/linux/chrome/deb/dists/stable/main/binary-amd64/Packages"
version_no=$(curl -s "$repo_url" | grep -m1 -A 10 '^Package: google-chrome-stable$' | grep -oP 'Version: \K\S+')
version_no=${version_no//-*/}
log_message "Google Chrome version: $version_no"

# Create the version folder
log_message "Creating Google Chrome version folder"
mkdir -p "$CHROME_FOLDER/025-Google-Chrome-$version_no" &>> "$LOG_PATH"

# Move the Google Chrome files to the version folder
log_message "Moving Google Chrome files to version folder"
cd "$CHROME_FOLDER"
rm -rf etc
rm -rf usr/share/man
mkdir pkgs
mv opt pkgs usr "025-Google-Chrome-$version_no" &>> "$LOG_PATH"

# Generate the package content list
log_message "Generating package content list"
cd "025-Google-Chrome-$version_no"
find . > pkgs/"025-Google-Chrome-$version_no"
sed -i 's/^.//g' pkgs/"025-Google-Chrome-$version_no"
cd ..
check_command "Generating package content list"

# Create SquashFS file
log_message "Creating SquashFS file"
mksquashfs "025-Google-Chrome-$version_no" "025-Google-Chrome-$version_no.sq" -b 1048576 -comp xz -Xdict-size 100% &>> "$LOG_PATH"
chmod +x "025-Google-Chrome-$version_no.sq"
rm -rf "025-Google-Chrome-$version_no"
cd "$CHROME_BUILD_PATH/$BUILD_ID"
check_command "Creating SquashFS file"

# Create Patch structure
log_message "Creating Patch structure"
mkdir root tmp
mv "$CHROME_FOLDER/025-Google-Chrome-$version_no.sq" tmp
check_command  "Creating Patch structure"

# Create install script in root folder
log_message "Creating install script in root folder"
cat <<EOF > root/install.sh
#!/bin/bash

pids=$(pgrep -f google)
for pid in $pids; do
    kill $pid
done

dir=$(find /data/apps-mount/ -type d -name 025* -print | awk 'NR==1')
[ -n "$dir" ] && { mount -t aufs -o remount,del="$dir" /; umount "$dir"; rm -rf "$dir"; }

mount -o remount,rw /sda1
rm -rf /sda1/data/apps/025* 2>/dev/null
cp /tmp/025-Google-* /sda1/data/apps/
chmod 755 /sda1/data/apps/025-Google-*
chown -R  root:root /sda1/data/apps/025-Google-*
mount -o remount,ro /sda1
EOF
chmod +x root/install.sh
check_command "Creating install script in root folder"

# Creating final tarball
build_date=$(date +%d%m%y)
final_tarball="google-chrome_$version_no-QFW$BUILD_ID-$build_date.tar.bz2"
log_message "Creating final tarball"
tar -jcf "$final_tarball" root tmp &>> "$LOG_PATH"
check_command "Creating final tarball"

# Corrupt the final tarball
log_message "Corrupting final tarball"
damage corrupt "$final_tarball" 1 &>> "$LOG_PATH"
check_command "Corrupting final tarball"

# Move tarbal to web directory
log_message "Moving tarball to web directory"
web_dir="/var/www/html/repo/$BUILD_ID"
sudo mkdir -p "$web_dir"
sudo chmod 755 "$web_dir"
sudo cp "$final_tarball" "$web_dir"
check_command "Moving tarball to web directory"
log_message "Build process completed successfully"
# Remove the locked name file
rm "$CHROME_BUILD_PATH/$BUILD_ID/locked"