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
ICACLIENT_URL="$4"
CTXUSB_URL="$5"
REFERENCE_PATH="$6"
UPDATE_INI_SCRIPT="$7"

# Ensure log file exits
[ ! -f "$LOG_FILE" ] && touch "$LOG_FILE"

log_message "Starting citrix workspace app build"
log_message "-----------------------------------"

# Create a locked name file in the build path
touch "$CITRIX_BUILD_PATH/$BUILD_ID/locked"

# Download icaclient deb package
log_message "Downloading icaclient deb package"
ICACLIENT="$CITRIX_BUILD_PATH/$BUILD_ID/icaclient.deb"
wget -O "$ICACLIENT" "$ICACLIENT_URL" --no-check-certificate
check_command "Downloading icaclient deb package"

# Get the version of icaclient from the deb package
ICACLIENT_VERSION=$(dpkg-deb -f "$ICACLIENT" Version)
log_message "ICAClient Version: $ICACLIENT_VERSION"

# Download ctxusb deb package
log_message "Downloading ctxusb deb package"
CTXUSB="$CITRIX_BUILD_PATH/$BUILD_ID/ctxusb.deb"
wget -O "$CTXUSB" "$CTXUSB_URL" --no-check-certificate
check_command "Downloading ctxusb deb package"

# Extract the icaclient,ctxusb deb package
log_message "Extracting icaclient deb package"
mkdir -p "$CITRIX_BUILD_PATH/$BUILD_ID/002-Citrix-Workspace-$ICACLIENT_VERSION"
dpkg-deb -x "$ICACLIENT" "$CITRIX_BUILD_PATH/$BUILD_ID/002-Citrix-Workspace-$ICACLIENT_VERSION"
dpkg-deb -x "$CTXUSB" "$CITRIX_BUILD_PATH/$BUILD_ID/002-Citrix-Workspace-$ICACLIENT_VERSION"
check_command "Extracting icaclient, ctxusb deb package"

# Refactor the package contents
log_message "Refactoring package contents"
cd "$CITRIX_BUILD_PATH/$BUILD_ID/002-Citrix-Workspace-$ICACLIENT_VERSION"
cd opt/Citrix/ICAClient
ln -s /usr/verixo-bin/vdimp.dll
ln -s ./nls/en.UTF-8/eula.txt .

cd "$CITRIX_BUILD_PATH/$BUILD_ID/002-Citrix-Workspace-$ICACLIENT_VERSION"
cd opt/Citrix/ICAClient/lib
mv UIDialogLibWebKit3.so UIDialogLibWebKit3.so-orig
cp  $REFERENCE_PATH/UIDialogLibWebKit3.so .
mv UIDialogLib.so UIDialogLib.so-orig
ln -s UIDialogLibWebKit3.so UIDialogLib.so
cd UIDialogLibWebKit3_ext
mv UIDialogLibWebKit3_ext.so UIDialogLibWebKit3_ext.so-orig
cp  $REFERENCE_PATH/UIDialogLibWebKit3_ext.so .

cd "$CITRIX_BUILD_PATH/$BUILD_ID/002-Citrix-Workspace-$ICACLIENT_VERSION"
cd opt/Citrix/ICAClient/util
rm -rf AppProtection-service.tar.gz
ln -s /opt/Citrix/ICAClient/util/gst_play1.0 gst_play
ln -s /opt/Citrix/ICAClient/util/gst_read1.0 gst_read
ln -s libgstflatstm1.0.so libgstflatstm.so
mv storebrowse storebrowse.bin
ln -s /usr/verixo-bin/storebrowse storebrowse

cd "$CITRIX_BUILD_PATH/$BUILD_ID/002-Citrix-Workspace-$ICACLIENT_VERSION"
cd opt/Citrix/ICAClient/config
ln -s ../nls/en/appsrv.template appsrv.template
ln -s /etc/icaclient/nls/en/module.ini module.ini
ln -s ../nls/en/wfclient.template wfclient.template

cd "$CITRIX_BUILD_PATH/$BUILD_ID/002-Citrix-Workspace-$ICACLIENT_VERSION"
cd opt/Citrix/ICAClient
cp  $REFERENCE_PATH/usb.conf .

check_command "Refactoring package contents"

# Update the INI files
# MODULE.INI
log_message "Updating MODULE.INI"
cd "$CITRIX_BUILD_PATH/$BUILD_ID/002-Citrix-Workspace-$ICACLIENT_VERSION"
cd etc/icaclient/nls/en
python3 $UPDATE_INI_SCRIPT module.ini
check_command "Updating MODULE.INI"

# Create patch directory
log_message "Creating patch directory"
mkdir -p "$CITRIX_BUILD_PATH/$BUILD_ID/root"
mkdir -p "$CITRIX_BUILD_PATH/$BUILD_ID/tmp"

# Create PKGS file
log_message "Creating PKGS file"
cd "$CITRIX_BUILD_PATH/$BUILD_ID/002-Citrix-Workspace-$ICACLIENT_VERSION"
mkdir pkgs
find . > pkgs/"002-Citrix-Workspace-$ICACLIENT_VERSION"
sed -i 's/^.//g' pkgs/"002-Citrix-Workspace-$ICACLIENT_VERSION"
cd "$CITRIX_BUILD_PATH/$BUILD_ID"
check_command "Creating PKGS file"

# Create SquashFS file
log_message "Creating SquashFS file"
cd "$CITRIX_BUILD_PATH/$BUILD_ID"
mksquashfs "002-Citrix-Workspace-$ICACLIENT_VERSION" "002-Citrix-Workspace-$ICACLIENT_VERSION.sq" -b 1048576 -comp xz -Xdict-size 100% &>> "$LOG_FILE"
mv "002-Citrix-Workspace-$ICACLIENT_VERSION.sq" "$CITRIX_BUILD_PATH/$BUILD_ID/tmp"
rm -rf "002-Citrix-Workspace-$ICACLIENT_VERSION"
check_command "Creating SquashFS file"

# Create Install script
log_message "Creating Install script"
cat <<EOF > "$CITRIX_BUILD_PATH/$BUILD_ID/root/install.sh"
#!/bin/bash
pids=\$(pgrep -f ctxusb)
for pid in \$pids; do
    kill \$pid
done

mount -o remount,rw /sda1

dir=\$(find /data/apps-mount/ -type d -name 002* -print | awk 'NR==1')
[ -n "\$dir" ] && { mount -t aufs -o remount,del="\$dir" /; umount "\$dir"; rm -rf "\$dir"; }

rm -f /sda1/data/apps/002-* 2>/dev/null
cp /tmp/002-* /sda1/data/apps/
chmod 755 /sda1/data/apps/002-*
mount -o remount,ro /sda1
EOF
chmod +x "$CITRIX_BUILD_PATH/$BUILD_ID/root/install.sh"
check_command "Creating install script"

# Create final tarball
log_message "Creating final tarball"
build_date=$(date +%d%m%y)
final_tarball="$CITRIX_BUILD_PATH/$BUILD_ID/citrix_$ICACLIENT_VERSION-QFW$BUILD_ID-$build_date.tar.bz2"
cd "$CITRIX_BUILD_PATH/$BUILD_ID"
tar -cjf "$final_tarball" root tmp
check_command "Creating final tarball"

# Corrupt the final tarball
log_message "Corrupting the final tarball"
cd "$CITRIX_BUILD_PATH/$BUILD_ID"
damage corrupt $final_tarball 1
check_command "Corrupting the final tarball"

# Move the final tarball to the web directory
log_message "Moving the final tarball to the web directory"
web_dir="/var/www/html/$BUILD_ID"
mkdir -p "$web_dir"
chmod -R 755 "$web_dir"
cp "$final_tarball" "$web_dir"
chmod -R 755 "$web_dir"

# Remove the locked name file
rm -f "$CITRIX_BUILD_PATH/$BUILD_ID/locked"