from flask import Blueprint, render_template, request, redirect, flash
from fwapp import db, login_manager
from flask_login import current_user, login_required
from fwapp.models import User, QuickBuildFirmware
from fwapp.quickbuild.form import QuickFirmwareBuildFirefoxForm
import os
import random
import subprocess
from flask import url_for

# Blueprint Object
quickbuild_route = Blueprint('quickbuild', __name__, template_folder='templates')

# Firefox Patch Build path
FIREFOX_BUILD_PATH = os.path.abspath(os.path.join(os.path.join("fwapp", "static", "firefox_build")))
# Firefox Patch Build Script
FIREFOX_BUILD_SCRIPT = os.path.abspath(os.path.join(os.path.join("fwapp", "static", "firefox_build", "firefox_build.sh")))


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

CURRENT_SYSTEM_IP_ADDRESS = get_ip_address()

# Create Random folder in the given path
def create_random_folder(path) -> int:
    random_folder_name = random.randint(1000, 9999)
    random_folder_path = os.path.join(path, str(random_folder_name))
    os.mkdir(random_folder_path)
    return random_folder_name


@quickbuild_route.route('/quickbuild')
@login_required
def home():
    page = request.args.get('page', 1, type=int)
    # Get the total number of QuickBuildFirmware created by current user
    total_quickbuild_firmware = QuickBuildFirmware.query.filter_by(user_id=current_user.id).count()
    # Get the list of all the QuickBuildFirmware created by current user
    quickbuild_firmware_list = QuickBuildFirmware.query.filter_by(user_id=current_user.id).order_by(QuickBuildFirmware.id.desc()).paginate(page=page, per_page=5)
    return render_template('quickbuild/home.html', title="User | Quick Firmware Build", quickbuild_firmware_list=quickbuild_firmware_list, total_quickbuild_firmware=total_quickbuild_firmware)

# Build Firefox
@quickbuild_route.route('/quickbuild/firefox', methods=['GET', 'POST'])
@login_required
def firefox():
    log_content = None
    form = QuickFirmwareBuildFirefoxForm()

    if form.validate_on_submit():
        # Create random folder in firefox_build path
        build_id = create_random_folder(FIREFOX_BUILD_PATH)
        # Build Log Path
        build_log_path = os.path.join(FIREFOX_BUILD_PATH, str(build_id), 'build.log')
        # Run the firefox_build.sh script
        status = subprocess.run(['bash', f"{FIREFOX_BUILD_SCRIPT}", str(FIREFOX_BUILD_PATH), str(build_id), str(build_log_path)], capture_output=True)
        # Read the log
        # Read the file content if it exists. Maintin the new line
        log_file_path = f"{FIREFOX_BUILD_PATH}/{build_id}/build.log"
        if os.path.exists(log_file_path):
            with open(log_file_path, 'r') as file:
                log_content = file.read()

        # Check if the script ran successfully
        if status.returncode == 0:
            # Get the Patch name
            patch_name = None
            for item in os.listdir(os.path.join(FIREFOX_BUILD_PATH, str(build_id))):
                if "QFW" in item:
                    patch_name = item.replace('.tar.bz2','')
                    break
            # Get client name
            client_name = form.client_name.data[0].capitalize()
            # Get the size of the patch
            patch_size = get_file_size(f"{FIREFOX_BUILD_PATH}/{build_id}/{patch_name}.tar.bz2")
            # Save the QuickBuildFirmware object to the database
            quickbuild_firmware = QuickBuildFirmware(firmware_client_name=client_name,firmware_name=patch_name, firmware_version=build_id, firmware_description=form.description.data, firmware_size=patch_size, firmware_log=log_content, firmware_download_link=f"http://{CURRENT_SYSTEM_IP_ADDRESS}/{build_id}/{patch_name}.tar.bz2",user=current_user)
            db.session.add(quickbuild_firmware)
            db.session.commit()
            flash('Build Successful', 'success')
            return redirect(url_for('quickbuild.home'))
        else:
            flash('Error: Build Failed', 'danger')
            return redirect(url_for('quickbuild.home'))
    return render_template('quickbuild/firefox.html', title="User | Firefox Build", form=form)