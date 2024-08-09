from flask import Blueprint, render_template, request, redirect, url_for, flash, jsonify
from flask_login import login_required, current_user
from app.models import FirmwareBuild
from app import db
import subprocess
import os
import multiprocessing
import random
import hashlib
from app.firmware.forms import NewFirmwareForm

# Blueprint for the firmware build
firmware_build = Blueprint('firmware', __name__, template_folder="templates")

# Firmware Build Path
FIRMWARE_BUILD_PATH = os.path.join(os.path.dirname(os.path.abspath(__file__)), 'builds')

# Build Firmware Home
@firmware_build.route('/build', methods=['GET', 'POST'])
@login_required
def build_firmware():
    page = request.args.get('page', 1, type=int)
    # Get the total number of Firmware created by current user
    total = FirmwareBuild.query.filter_by(user_id=current_user.id).count()
    # Get the Firmware created by current user with pagination
    firmware = FirmwareBuild.query.filter_by(user_id=current_user.id).order_by(FirmwareBuild.id.desc()).paginate(page=page, per_page=10)
    # Get the count of failed builds
    failed_builds = FirmwareBuild.query.filter_by(user_id=current_user.id, status='failed').count()
    # Render the firmware build template
    return render_template('firmware/firmware.html', title='Build Firmware', firmware=firmware, total=total, failed_builds=failed_builds)

# New Firmware Build
@firmware_build.route('/build/new', methods=['GET', 'POST'])
@login_required
def new_firmware_build():
    form = NewFirmwareForm()
    if form.validate_on_submit():
        # Create random folder name in firmware builds folder
        build_path, build_id = create_random_folder()
        
        # Log path
        log_path = os.path.join(build_path, 'build.log')
        
        # Create root and tmp folder inside build id folder
        os.makedirs(os.path.join(build_path, 'root'), exist_ok=True)
        os.makedirs(os.path.join(build_path, 'tmp'), exist_ok=True)

        # Save uploaded files into the build folder tmp
        # Get list of files from the form
        files = request.files.getlist(form.files.name)
        for file in files:
            if file:
                file_path = os.path.join(build_path, 'tmp', file.filename)
                file.save(file_path)
        
        # Get the data from form
        client_name = form.client_name.data[0].upper() + form.client_name.data[1:].lower()
        description = form.description.data
        install_script = form.install_script.data
        restore_factory = "no"

        # Check if menu entry checkbox is checked
        if form.menu.data:
                # Check if all the fields are filled
                if form.executable.data and form.program_name.data and form.icon.data and form.executable_user.data:
                    menu_executable = form.executable.data
                    menu_icon = form.icon.data
                    menu_user = form.executable_user.data
                    menu_program_name = form.program_name.data
                    menu_dict = {"executable": menu_executable, "icon": menu_icon, "user": menu_user, "program_name": menu_program_name}
                else:
                    print("All fields are required")
                    menu_dict = {}
        else:
            menu_dict = {}
        
        # Check if restore factory checkbox is checked. If yes then set restore_factory to "yes" else "no"
        if form.restore.data:
            restore_factory = "yes"

        # Create new build entry
        new_build = FirmwareBuild(client_name=client_name,firmware_name="NA",firmware_build_id=build_id, firmware_description=description, firmware_size="NA",firmware_log="NA", download_link="NA", md5sum="NA", user_id=current_user.id)
        db.session.add(new_build)
        db.session.commit()

        # Start the build process in the background
        build_process = multiprocessing.Process(target=start_build, args=(log_path, new_build.id, build_id, install_script,
                                                                          menu_dict, restore_factory, form.patch_name.data))
        build_process.start()
        flash('Build started successfully!', 'success')
        return redirect(url_for('firmware.build_firmware'))
    # Render the new firmware build template
    return render_template('firmware/new_firmware_build.html', title='New Firmware Build', form=form)

# Create random folder name in firefox build path
def create_random_folder():
    build_id = str(random.randint(1000, 9999))
    build_path = os.path.join(FIRMWARE_BUILD_PATH, build_id)
    os.makedirs(build_path, exist_ok=True)
    return build_path, build_id

# Get the size of patch
def get_file_size(file_path) -> str:
    # Get the file size in bytes
    size_bytes = os.path.getsize(file_path)
    # Determine the appropriate unit (KB or MB) based on file size
    if size_bytes < 1024:
        file_size = f'{size_bytes} bytes'
    elif size_bytes < 1024 * 1024:
        file_size = f'{size_bytes / 1024:.2f} KB'
    else:
        file_size = f'{size_bytes / (1024 * 1024):.2f} MB'
    return file_size

# Find ethernet IP address of the system
def get_ip_address():
    ip_address = subprocess.check_output(['hostname', '-I'])
    ip_address = ip_address.decode('utf-8').strip()
    return ip_address

# Calculate the MD5SUM of the firmware
def calculate_md5sum(file_path) -> str:
    hash_md5 = hashlib.md5()
    with open(file_path, "rb") as f:
        for chunk in iter(lambda: f.read(4096), b""):
            hash_md5.update(chunk)
    # Return only last 4 characters of md5sum
    return hash_md5.hexdigest()[-4:].upper()

# Start the build process
def start_build(log_path, user_id, build_id, install_script, menu, restore_factory, patchname):
    build = FirmwareBuild.query.get(user_id)
    log_content = ""
    try:
        # Write the content of install_script in root/install.sh
        with open(os.path.join(FIRMWARE_BUILD_PATH, build_id, 'root', 'install.sh'), 'w') as f:
            f.write(install_script)

        # Check if menu is not empty
        if menu:
            MENU_FILE = "/sda1/data/menu.orig"
            PROGRAM_NAME = menu["program_name"]
            ICON_PATH = menu["icon"]
            EXECUTABLE_PATH = menu["executable"]
            USERNAME=menu["user"]

            MENU_TEMPLATE='''
# Check if the username is not root, then prepare the command accordingly
if [ "{USERNAME}" != "root" ]; then
    MENU_ENTRY="prog \"{PROGRAM_NAME}\" \"{ICON_PATH}\" su {USERNAME} -c \"{EXECUTABLE_PATH}\""
else
    MENU_ENTRY="prog \"{PROGRAM_NAME}\" \"{ICON_PATH}\" {EXECUTABLE_PATH}"
fi

TARGET_LINE="prog \"AnyConnect""

# Check if the program name is present in the menu file
if grep -q "{PROGRAM_NAME}" {MENU_FILE}; then
    # Remove existing entry for the program
    sed -i "/{PROGRAM_NAME}/d" {MENU_FILE}
fi

# Insert the program entry after the target line
sed -i "/$TARGET_LINE.*/a $MENU_ENTRY" "{MENU_FILE}"

# Copy the modified menu file to the target location
cp {MENU_FILE} /data/menu.orig
cp {MENU_FILE} /data/menu
cp {MENU_FILE} /sda1/data/menu
'''
            SHELL_SCRIPT = MENU_TEMPLATE.format(
                MENU_FILE=MENU_FILE,
                PROGRAM_NAME=PROGRAM_NAME, 
                ICON_PATH=ICON_PATH, 
                EXECUTABLE_PATH=EXECUTABLE_PATH, 
                USERNAME=USERNAME
                )
            with open(os.path.join(FIRMWARE_BUILD_PATH, build_id, 'root', 'install.sh'), 'a') as f:
                f.write('\n')
                f.write(SHELL_SCRIPT)
 
        # If restore_factory is "yes" then append echo 0 > /data/.rfd in install.sh
        if restore_factory == "yes":
            with open(os.path.join(FIRMWARE_BUILD_PATH, build_id, 'root', 'install.sh'), 'a') as f:
                f.write('\necho 0 > /data/.rfd')
        
        # Write the content of install_script in root/install.sh
        with open(os.path.join(FIRMWARE_BUILD_PATH, build_id, 'root', 'install.sh'), 'a') as f:
            f.write('\nmount -o remount,rw /sda1')
        
        # Create tarball of root and tmp folder in the name of patchname and build id
        tarball_name = f'{patchname}_{build_id}.tar.bz2'
        tarball_path = os.path.join(FIRMWARE_BUILD_PATH,build_id, tarball_name)
        TAR_COMMAND = f'tar -cjpf {tarball_path} root tmp'
        subprocess.run(TAR_COMMAND, shell=True, check=True,cwd=os.path.join(FIRMWARE_BUILD_PATH, build_id))

        # Damage the tarball
        DAMAGE_COMMAND = f'damage corrupt {tarball_path} 1'
        subprocess.run(DAMAGE_COMMAND, shell=True, check=True, cwd=os.path.join(FIRMWARE_BUILD_PATH, build_id))

        # Get the size of the tarball
        file_size = get_file_size(tarball_path)
        build.firmware_size = file_size

        # Get the IP address
        ip_address = get_ip_address()

        # Get the Md5sum of the tarball
        md5sum = calculate_md5sum(tarball_path)
        build.md5sum = md5sum
        
        # Create the build_id named folder in /var/www/html/repo
        os.makedirs(os.path.join('/var/www/html/repo', build_id), exist_ok=True)
        os.chmod(os.path.join('/var/www/html/repo', build_id), 0o755)

        # Copy the patch to the /var/www/html/repo/build_id
        subprocess.run(['cp', tarball_path, os.path.join('/var/www/html/repo', build_id, tarball_name)], check=True)
        os.chmod(os.path.join('/var/www/html/repo', build_id, tarball_name), 0o755)

        # Get the download link
        download_link_url = f'http://{ip_address}/repo/{build_id}/{tarball_name}'
        build.download_link = download_link_url
        
        # Get the build id
        build.firmware_build_id = build_id
        
        # Save Patch name
        build.firmware_name = patchname
        build.status = 'success'
    except Exception as e:
        build.status = 'failed'
        build.firmware_log = log_content
    finally:
        db.session.commit()

