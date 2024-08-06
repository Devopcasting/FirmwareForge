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
    # Render the firmware build template
    return render_template('firmware/firmware.html', title='Build Firmware')

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
        display_name = ""
        menu_executable = ""
        menu_icon = ""
        restore_factory = "no"
        # Check if menu entry checkbox is checked. If yes then check if executable and icon form data is not empty.
        if form.menu.data:
            if form.executable.data and form.icon.data and form.menu_display_name.data:
                display_name = form.menu_display_name.data
                menu_executable = form.executable.data
                menu_icon = form.icon.data
        # Check if restore factory checkbox is checked. If yes then set restore_factory to "yes" else "no"
        if form.restore.data:
            restore_factory = "yes"

        # Create new build entry
        new_build = FirmwareBuild(client_name=client_name,firmware_name="NA",firmware_build_id=build_id, firmware_description=description, firmware_size="NA",firmware_log="NA", download_link="NA", md5sum="NA", user_id=current_user.id)
        db.session.add(new_build)
        db.session.commit()

        # Start the build process in the background
        build_process = multiprocessing.Process(target=start_build, args=(log_path, new_build.id, build_id, install_script,
                                                                          menu_executable, menu_icon, restore_factory, display_name))
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
def start_build(log_path, user_id, build_id, install_script, menu_executable, menu_icon, restore_factory, display_name):
    build = FirmwareBuild.query.get(user_id)
    log_content = ""
    patch_name = ""
    try:
        # Write the content of install_script in root/install.sh
        with open(os.path.join(FIRMWARE_BUILD_PATH, build_id, 'root', 'install.sh'), 'w') as f:
            f.write(install_script)

        # If restore_factory is "yes" then append echo 0 > /data/.rfd in install.sh
        if restore_factory == "yes":
            with open(os.path.join(FIRMWARE_BUILD_PATH, build_id, 'root', 'install.sh'), 'a') as f:
                f.write('\necho 0 > /data/.rfd')
    except Exception as e:
        build.status = 'failed'
        build.firmware_log = log_content
    finally:
        db.session.commit()

