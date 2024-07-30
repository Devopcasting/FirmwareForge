#!/bin/bash
#set -e
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
VMWARE_BUILD_PATH="$1"
BUILD_ID="$2"
VMWARE_SOURCE_URL="$3"
LOG_PATH="$4"
VMWARE_REFERENCE_PATH="$5"
VMWARE_FOLDER="$VMWARE_BUILD_PATH/$BUILD_ID/vmware"

# Ensure log file exists
[ ! -f "$LOG_PATH" ] && touch "$LOG_PATH"

log_message "Starting VWware Horizon Client build"
log_message "-------------------------------------"

# Create a locked name file in the build path
touch "$VMWARE_BUILD_PATH/$BUILD_ID/locked"

# Get the vmware bundle name
vmware_bundle_name=$(basename "$VMWARE_SOURCE_URL")

# Get the vmware bundle version
vmware_bundle_version=$(echo "$vmware_bundle_name" | grep -oP '\d+\.\d+-\d+\.\d+\.\d+-\d+')
# Convert '-' to '_' in vmware bundle version
vmware_bundle_version=$(echo "$vmware_bundle_version" | sed 's/-/_/g')

# Download the latest Vmware view Horizon release
latest_vmware_url="$VMWARE_SOURCE_URL"
log_message "Downloading latest Vmware view Horizon release from $latest_vmware_url"
curl -o "$VMWARE_BUILD_PATH/$BUILD_ID/$vmware_bundle_name" "$latest_vmware_url" &>> "$LOG_PATH"
chmod +x "$VMWARE_BUILD_PATH/$BUILD_ID/$vmware_bundle_name"
check_command "Download latest Vmware view Horizon release"

# Extract the vmware bundle
log_message "Extracting $vmware_bundle_name"
cd "$VMWARE_BUILD_PATH/$BUILD_ID"
sudo ./$vmware_bundle_name -I -x bundle &>> "$LOG_PATH"
check_command "Extract $vmware_bundle_name"

# Create Package structure
log_message "Creating package structure"
mkdir "007-vmware-view-horizon-$vmware_bundle_version"
mkdir -p "007-vmware-view-horizon-$vmware_bundle_version/usr"
mkdir -p "007-vmware-view-horizon-$vmware_bundle_version/etc"
check_command "Create Package structure"

# Loop through all the files in the vmware bundle
cd "$VMWARE_BUILD_PATH/$BUILD_ID/bundle"
for file in *; do
    # Enter into file
    echo "$file" &>> "$LOG_PATH"
    cd "$file"
    # Check if user folder exists
    if [ -d "usr" ]; then
        # Copy usr folder contents to "007-vmware-view-horizon-$vmware_bundle_version/usr". Redirect the verbose to log
        cp -pva usr/* ../../"007-vmware-view-horizon-$vmware_bundle_version/usr" &>> "$LOG_PATH"
    fi
    # Check if etc folder exists
    if [ -d "etc" ]; then
        # Copy etc folder contents to "007-vmware-view-horizon-$vmware_bundle_version/etc"
        cp -pva etc/* ../../"007-vmware-view-horizon-$vmware_bundle_version/etc" &>> "$LOG_PATH"
    fi
    cd ..
done
# Setup Vmware USB
log_message "Setting up Vmware USB"
cd "$VMWARE_BUILD_PATH/$BUILD_ID/007-vmware-view-horizon-$vmware_bundle_version/etc"
mkdir rc.d
rm -rf init.d/ftscan*
rm -rf init.d/ftsprhv*
mv init.d rc.d/
cd rc.d
mkdir rc5.d
cd rc5.d
ln -s /etc/rc.d/init.d/vmware-USBArbitrator K08vmware-USBArbitrator
ln -s /etc/rc.d/init.d/vmware-USBArbitrator S50vmware-USBArbitrator
cd "$VMWARE_BUILD_PATH/$BUILD_ID/007-vmware-view-horizon-$vmware_bundle_version/etc"
chmod -R 755 *
check_command "Setup Vmware USB"

# Finalize the package
log_message "Finalizing package"
cd "$VMWARE_BUILD_PATH/$BUILD_ID"
cp -pa $VMWARE_REFERENCE_PATH/etc/* "007-vmware-view-horizon-$vmware_bundle_version/etc"
cd "$VMWARE_BUILD_PATH/$BUILD_ID/007-vmware-view-horizon-$vmware_bundle_version/usr/lib/vmware"
ln -s /lib64/libudev.so.1 libudev.so.0
cd "$VMWARE_BUILD_PATH/$BUILD_ID/007-vmware-view-horizon-$vmware_bundle_version/usr/bin"
ln -s /usr/lib/vmware/view/usb/vmware-usbarbitrator vmware-usbarbitrator
mkdir -p "$VMWARE_BUILD_PATH/$BUILD_ID/007-vmware-view-horizon-$vmware_bundle_version/usr/lib/cupsPPD"
if [ -f "$VMWARE_BUILD_PATH/$BUILD_ID/007-vmware-view-horizon-$vmware_bundle_version/usr/lib/vmware/view/integratedPrinting/prlinuxcupsppd" ];then
    cp -pva "$VMWARE_BUILD_PATH/$BUILD_ID/007-vmware-view-horizon-$vmware_bundle_version/usr/lib/vmware/view/integratedPrinting/prlinuxcupsppd" "$VMWARE_BUILD_PATH/$BUILD_ID/007-vmware-view-horizon-$vmware_bundle_version/usr/lib/cupsPPD"
fi
cd "$VMWARE_BUILD_PATH/$BUILD_ID/007-vmware-view-horizon-$vmware_bundle_version"
mkdir pkgs
find . > pkgs/"007-vmware-view-horizon-$vmware_bundle_version"
sed -i 's/^.//g' pkgs/"007-vmware-view-horizon-$vmware_bundle_version"
chmod -R 755 *
chmod 4755 ./usr/lib/cupsPPD/*
check_command "Finalize package"

# Create squashfs
log_message "Creating squashfs"
cd "$VMWARE_BUILD_PATH/$BUILD_ID"
mksquashfs "007-vmware-view-horizon-$vmware_bundle_version" "007-vmware-view-horizon-$vmware_bundle_version.sq" -b 1048576 -comp xz -Xdict-size 100% &>> "$LOG_PATH"
chmod +x "007-vmware-view-horizon-$vmware_bundle_version.sq"
rm -rf "007-vmware-view-horizon-$vmware_bundle_version"
check_command "Create squashfs"

# Create patch structure
log_message "Creating patch structure"
cd "$VMWARE_BUILD_PATH/$BUILD_ID"
mkdir tmp root
mv "007-vmware-view-horizon-$vmware_bundle_version.sq" tmp

# Create install script in root folder
cat <<EOF > root/install.sh
#!/bin/bash

pids=$(pgrep -f vmware)
for pid in $pids; do
    kill $pid
done

dir=\$(find /data/apps-mount/ -type d -name 007* -print | awk 'NR==1')
[ -n "\$dir" ] && { mount -t aufs -o remount,del="\$dir" /; umount "\$dir"; rm -rf "\$dir"; }

mount -o remount,rw /sda1
rm -rf /sda1/data/apps/007* 2>/dev/null
cp /tmp/007-* /sda1/data/apps/
chmod 755 /sda1/data/apps/007-*
mount -o remount,ro /sda1

EOF
chmod +x root/install.sh
check_command "Create install script"

# Create final tarball
log_message "Creating final tarball"
cd "$VMWARE_BUILD_PATH/$BUILD_ID"
build_date=$(date +%d%m%y)
final_tarball="vmwareview-horizon_$vmware_bundle_version-QFW$BUILD_ID-$build_date.tar.bz2"
tar -jcf "$final_tarball" root tmp &>> "$LOG_PATH"
check_command "Creating final tarball"

# Corrupt the final tarball
log_message "Corrupting final tarball"
damage corrupt "$final_tarball" 1 &>> "$LOG_PATH"
check_command "Corrupting final tarball"

# Move tarbal to web directory
log_message "Moving tarball to web directory"
web_dir="/var/www/html/$BUILD_ID"
sudo mkdir -p "$web_dir"
sudo chmod 755 "$web_dir"
sudo cp "$final_tarball" "$web_dir"
check_command "Moving tarball to web directory"
log_message "Build process completed successfully"
# Remove the locked name file
rm "$VMWARE_BUILD_PATH/$BUILD_ID/locked"
