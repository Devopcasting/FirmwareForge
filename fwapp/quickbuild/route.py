from flask import Blueprint, render_template, request, redirect, flash, url_for, abort
from fwapp import db, app
from flask_login import current_user, login_required
from fwapp.models import User, QuickBuildFirmware
from werkzeug.utils import secure_filename
from fwapp.quickbuild.form import QuickFirmwareBuildFirefoxForm, QuickFirmwareBuildChromeForm, QuickFirmwareBuildVmwareHorizonForm, QuickFirmwareBuildCitrixWorkspaceAppForm
import os
import random
import subprocess
import shutil
from werkzeug.utils import secure_filename

# Blueprint Object
quickbuild_route = Blueprint('quickbuild', __name__, template_folder='templates')

# Firefox patch build path
FIREFOX_BUILD_PATH = os.path.abspath(os.path.join(os.path.join("fwapp", "static", "firefox_build")))
# Firefox Failed build path
FIREFOX_FAILED_BUILD_PATH = os.path.abspath(os.path.join(os.path.join("fwapp", "static", "firefox_build", "failed_build")))
# Firefox patch build script
FIREFOX_BUILD_SCRIPT = os.path.abspath(os.path.join(os.path.join("fwapp", "static", "firefox_build", "firefox_build.sh")))

# Chrome Patch Build path
CHROME_BUILD_PATH = os.path.abspath(os.path.join(os.path.join("fwapp", "static", "chrome_build")))
# Chrome Failed build path
CHROME_FAILED_BUILD_PATH = os.path.abspath(os.path.join(os.path.join("fwapp", "static", "chrome_build", "failed_build")))
# Chrome Patch Build Script
CHROME_BUILD_SCRIPT = os.path.abspath(os.path.join(os.path.join("fwapp", "static", "chrome_build", "chrome_build.sh")))

# Vmware Patch Build path
VMWARE_BUILD_PATH = os.path.abspath(os.path.join(os.path.join("fwapp", "static", "vmware_build")))
# Vmware Failed build path
VMWARE_FAILED_BUILD_PATH = os.path.abspath(os.path.join(os.path.join("fwapp", "static", "vmware_build", "failed_build")))
# Vmware Patch Build Script
VMWARE_BUILD_SCRIPT = os.path.abspath(os.path.join(os.path.join("fwapp", "static", "vmware_build", "vmware_build.sh")))

# Citrix Workspace App Patch Build path
CITRIX_BUILD_PATH = os.path.abspath(os.path.join(os.path.join("fwapp", "static", "citrix_build")))
# Citrix Workspace App Failed build path
CITRIX_FAILED_BUILD_PATH = os.path.abspath(os.path.join(os.path.join("fwapp", "static", "citrix_build", "failed_build")))
# Citrix Workspace App Patch Build Script
CITRIX_BUILD_SCRIPT = os.path.abspath(os.path.join(os.path.join("fwapp", "static", "citrix_build", "citrix_build.sh")))
app.config['UPLOAD_FOLDER'] = CITRIX_BUILD_PATH


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
        try:
            status = subprocess.run(['bash', f"{FIREFOX_BUILD_SCRIPT}", str(FIREFOX_BUILD_PATH), str(build_id), str(build_log_path)], capture_output=True)
        except subprocess.CalledProcessError as e:
            flash('Error: Build script execution failed', 'danger')
            return redirect(url_for('quickbuild.home'))
        
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
            client_name = form.client_name.data.capitalize()
            # Get the size of the patch
            patch_size = get_file_size(f"{FIREFOX_BUILD_PATH}/{build_id}/{patch_name}.tar.bz2")
            # Save the QuickBuildFirmware object to the database
            quickbuild_firmware = QuickBuildFirmware(firmware_client_name=client_name,firmware_name=patch_name, firmware_version=build_id, firmware_description=form.description.data, firmware_size=patch_size, firmware_log=log_content, firmware_download_link=f"http://{CURRENT_SYSTEM_IP_ADDRESS}/{build_id}/{patch_name}.tar.bz2",user=current_user)
            db.session.add(quickbuild_firmware)
            db.session.commit()
            flash('Build Successful', 'success')
            return redirect(url_for('quickbuild.home'))
        else:
            # Move the build.log file to the failed_build folder
            os.rename(log_file_path, f"{FIREFOX_FAILED_BUILD_PATH}/{build_id}.log")
            # Delete the build id folder
            shutil.rmtree(os.path.join(FIREFOX_BUILD_PATH, str(build_id)))
            # View build error log
            flash(f"Build Failed", 'danger')
            return redirect (url_for('quickbuild.error', id=build_id))
    return render_template('quickbuild/firefox.html', title="User | Firefox Quick Firmware Build", form=form)

# Build Google Chrome
@quickbuild_route.route('/quickbuild/chrome', methods=['GET', 'POST'])
@login_required
def chrome():
    log_content = None
    form = QuickFirmwareBuildChromeForm()

    if form.validate_on_submit():
        # Create random folder in chrome_build path
        build_id = create_random_folder(CHROME_BUILD_PATH)
        
        # Build Log Path
        build_log_path = os.path.join(CHROME_BUILD_PATH, str(build_id), 'build.log')
        
        # Run the chrome_build.sh script
        try:
            status = subprocess.run(['bash', f"{CHROME_BUILD_SCRIPT}", str(CHROME_BUILD_PATH), str(build_id), str(build_log_path)], capture_output=True)
        except subprocess.CalledProcessError as e:
            flash('Error: Build script execution failed', 'danger')
            return redirect(url_for('quickbuild.home'))
        
        # Read the log
        # Read the file content if it exists. Maintin the new line
        log_file_path = f"{CHROME_BUILD_PATH}/{build_id}/build.log"
        if os.path.exists(log_file_path):
            with open(log_file_path, 'r') as file:
                log_content = file.read()

        # Check if the script ran successfully
        if status.returncode == 0:
            # Get the Patch name
            patch_name = None
            for item in os.listdir(os.path.join(CHROME_BUILD_PATH, str(build_id))):
                if "QFW" in item:
                    patch_name = item.replace('.tar.bz2','')
                    break
            # Get client name
            client_name = form.client_name.data.capitalize()
            # Get the size of the patch
            patch_size = get_file_size(f"{CHROME_BUILD_PATH}/{build_id}/{patch_name}.tar.bz2")
            # Save the QuickBuildFirmware object to the database
            quickbuild_firmware = QuickBuildFirmware(firmware_client_name=client_name,firmware_name=patch_name, firmware_version=build_id, firmware_description=form.description.data, firmware_size=patch_size, firmware_log=log_content, firmware_download_link=f"http://{CURRENT_SYSTEM_IP_ADDRESS}/{build_id}/{patch_name}.tar.bz2",user=current_user)
            db.session.add(quickbuild_firmware)
            db.session.commit()
            flash('Build Successful', 'success')
            return redirect(url_for('quickbuild.home'))
        else:
            # Move the build.log file to the failed_build folder
            os.rename(log_file_path, f"{CHROME_FAILED_BUILD_PATH}/{build_id}.log")
            # Delete the build id folder
            shutil.rmtree(os.path.join(CHROME_BUILD_PATH, str(build_id)))
            # View build error log
            flash(f"Build Failed", 'danger')
            return redirect (url_for('quickbuild.error', id=build_id))
    return render_template('quickbuild/google_chrome.html', title="User | Google Chrome Quick Firmware Build", form=form)

# Build VMware Horizon Client
@quickbuild_route.route('/quickbuild/vmware_horizon', methods=['GET', 'POST'])
@login_required
def vmware_horizon():
    log_content = None
    form = QuickFirmwareBuildVmwareHorizonForm()
    if form.validate_on_submit():
        # Create random folder in vmware_build path
        build_id = create_random_folder(VMWARE_BUILD_PATH)
        
        # Build Log Path
        build_log_path = os.path.join(VMWARE_BUILD_PATH, str(build_id), 'build.log')
        
        # Run the vmware_build.sh script
        try:
            status = subprocess.run(['bash', f"{VMWARE_BUILD_SCRIPT}", str(VMWARE_BUILD_PATH), str(build_id),str(form.source_url.data), str(build_log_path)], capture_output=True)
        except subprocess.CalledProcessError as e:
            flash('Error: Build script execution failed', 'danger')
            return redirect(url_for('quickbuild.home'))
        
        # Read the log
        # Read the file content if it exists. Maintin the new line
        log_file_path = f"{VMWARE_BUILD_PATH}/{build_id}/build.log"
        if os.path.exists(log_file_path):
            with open(log_file_path, 'r') as file:
                log_content = file.read()

        # Check if the script ran successfully
        if status.returncode == 0:
            # Get the Patch name
            patch_name = None
            for item in os.listdir(os.path.join(VMWARE_BUILD_PATH, str(build_id))):
                if "QFW" in item:
                    patch_name = item.replace('.tar.bz2','')
                    break
            # Get client name
            client_name = form.client_name.data.capitalize()
            # Get the size of the patch
            patch_size = get_file_size(f"{VMWARE_BUILD_PATH}/{build_id}/{patch_name}.tar.bz2")
            # Save the QuickBuildFirmware object to the database
            quickbuild_firmware = QuickBuildFirmware(firmware_client_name=client_name,firmware_name=patch_name, firmware_version=build_id, firmware_description=form.description.data, firmware_size=patch_size, firmware_log=log_content, firmware_download_link=f"http://{CURRENT_SYSTEM_IP_ADDRESS}/{build_id}/{patch_name}.tar.bz2",user=current_user)
            db.session.add(quickbuild_firmware)
            db.session.commit()
            flash('Build Successful', 'success')
            return redirect(url_for('quickbuild.home'))
        else:
            # Move the build.log file to the failed_build folder
            os.rename(log_file_path, f"{VMWARE_FAILED_BUILD_PATH}/{build_id}.log")
            # Delete the build id folder
            shutil.rmtree(os.path.join(VMWARE_BUILD_PATH, str(build_id)))
            # View build error log
            flash(f"Build Failed", 'danger')
            return redirect (url_for('quickbuild.error', id=build_id))
    return render_template('quickbuild/vmware_horizon.html', title="User | VMware Horizon Quick Firmware Build", form=form)

# Build Citrix Workspace App
@quickbuild_route.route('/quickbuild/citrix_workspace_app', methods=['GET', 'POST'])
@login_required
def citrix_workspace_app():
    log_content = None
    form = QuickFirmwareBuildCitrixWorkspaceAppForm()
    if form.validate_on_submit():
        # Get the icaclient file
        icaclient_file = request.files['icaclient']
        # Get the icaclient file name
        icaclient_file_name = secure_filename(icaclient_file.filename)
        # ICAClient file path
        icaclient_file_path = os.path.join(app.config['UPLOAD_FOLDER'], icaclient_file_name)

        # Get the ctxusb file
        ctxusb_file = request.files['ctxusb']
        # Get the ctxusb file name
        ctxusb_file_name = secure_filename(ctxusb_file.filename)
        # Ctxusb file path
        ctxusb_file_path = os.path.join(app.config['UPLOAD_FOLDER'], ctxusb_file_name)

        # Save the icaclient and ctxusb file to the upload folder
        if icaclient_file and ctxusb_file:
            # Save the icaclient and ctxusb file to the upload folder
            icaclient_file.save(icaclient_file_path)
            ctxusb_file.save(ctxusb_file_path)
        
        # Create random folder in path
        build_id = create_random_folder(CITRIX_BUILD_PATH)
        
        # Build Log Path
        build_log_path = os.path.join(CITRIX_BUILD_PATH, str(build_id), 'build.log')

        # Run the citrix_build.sh script
        try:
            status = subprocess.run(['bash', f"{CITRIX_BUILD_SCRIPT}", str(CITRIX_BUILD_PATH), str(build_id), str(build_log_path), str(icaclient_file_path), str(ctxusb_file_path)], capture_output=True)
        except subprocess.CalledProcessError as e:
            flash('Error: Build script execution failed', 'danger')
            return redirect(url_for('quickbuild.home'))

    return render_template('quickbuild/citrix_workspace_app.html', title="User | Citrix Workspace App Quick Firmware Build", form=form)

# Build Information
@quickbuild_route.route('/quickbuild/info/<int:id>')
@login_required
def info(id):
    # Get the QuickBuildFirmware object by id
    quickbuild_firmware = QuickBuildFirmware.query.get_or_404(id)
    return render_template('quickbuild/buildinfo.html', title="User | Information Quick Firmware Build", quickbuild_firmware=quickbuild_firmware)

# View Error log
@quickbuild_route.route('/quickbuild/error/<int:id>')
@login_required
def error(id):
    build_id = id
    error_log_path = os.path.join(FIREFOX_FAILED_BUILD_PATH, f"{build_id}.log")
    error_content = None
    # Read the content of build_id.log
    with open(error_log_path, 'r') as file:
        error_content = file.read()

    return render_template('quickbuild/errorlog.html', title="User | Error Quick Firmware Build",buildid = build_id, error_content = error_content )

# Delete Firmware. Only Current user can delete
@quickbuild_route.route('/quickbuild/delete/<int:firmware_id>')
@login_required
def firmware_delete(firmware_id, methods=['GET', 'POST']):
    firmware_to_delete = QuickBuildFirmware.query.get_or_404(firmware_id)
    if firmware_to_delete.user != current_user:
        abort(403)
    db.session.delete(firmware_to_delete)
    db.session.commit()
    # Delete the folder recursevly with the build_id. Use subprocess
    subprocess.run(['sudo','rm', '-rf', f"{FIREFOX_BUILD_PATH}/{firmware_to_delete.firmware_version}"])
    # Delete patch from /var/www/html/
    subprocess.run(['sudo', 'rm', '-rf', f"/var/www/html/{firmware_to_delete.firmware_version}"])

    flash('Firmware has been deleted', 'success')
    return redirect(url_for('quickbuild.home'))
