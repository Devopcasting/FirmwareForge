from flask import Blueprint, render_template, request, redirect, url_for, flash
from flask_login import login_required, current_user
from werkzeug.utils import secure_filename
from app import db
from app.models import User, QuickFirmwareBuild
from app.quickbuild_firefox.forms import QuickFirmwareBuildFirefoxForm
import os
import subprocess
import random
import multiprocessing

# Blueprint for the quickbuild_firefox routes
quickbuild_firefox_route = Blueprint('quickbuild_firefox', __name__, template_folder="templates")

# Firefox patch build path
FIREFOX_BUILD_PATH = os.path.abspath(os.path.join(os.path.join("app","quickbuild_firefox", "builds")))
# Firefox build script path
FIREFOX_BUILD_SCRIPT_PATH = os.path.abspath(os.path.join("app", "quickbuild_firefox", "build.sh"))
# Firefox build reference path
FIREFOX_BUILD_REFERENCE_PATH = os.path.abspath(os.path.join("app", "quickbuild_firefox", "references"))

# QuickBuild Firefox
@quickbuild_firefox_route.route('/quickbuild_firefox', methods=['GET', 'POST'])
@login_required
def quickbuild_firefox():
    form = QuickFirmwareBuildFirefoxForm()
    if form.validate_on_submit():
        # Create random folder name in firefox build path
        build_path, build_id = create_random_folder()
        # Log path
        log_path = os.path.join(FIREFOX_BUILD_PATH, build_id, "build.log")
        # Get data from form
        client_name = form.client_name.data[0].upper() + form.client_name.data[1:].lower()
        description = form.description.data
        # Create new build entry
        new_build = QuickFirmwareBuild(client_name=client_name,firmware_name="NA",firmware_build_id=build_id, firmware_description=description, firmware_size="NA",firmware_log="NA", download_link="NA", user_id=current_user.id)
        db.session.add(new_build)
        db.session.commit()
        # Start the build process in the background
        build_process = multiprocessing.Process(target=start_build, args=(log_path, new_build.id, build_id))
        build_process.start()
        flash('Build started successfully!', 'success')
        return redirect(url_for('quickfirmware.quickfirmware'))
    return render_template('quickbuild_firefox/build.html', title="Quick Build Firefox", form=form)

# Create random folder name in firefox build path
def create_random_folder():
    build_id = str(random.randint(1000, 9999))
    build_path = os.path.join(FIREFOX_BUILD_PATH, build_id)
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

# Start the build process
def start_build(log_path, user_id, build_id):
    build = QuickFirmwareBuild.query.get(user_id)
    log_content = ""
    patch_name = ""
    try:
        start_build = subprocess.run(
            ['bash', f"{FIREFOX_BUILD_SCRIPT_PATH}", str(FIREFOX_BUILD_PATH), str(build_id), str(log_path), f"{FIREFOX_BUILD_REFERENCE_PATH}"], 
            capture_output=True
            )
        
        # Write the log contents
        if os.path.exists(log_path):
            with open(log_path, 'r') as f:
                log_content = f.read()

        # Check the status of the build
        if start_build.returncode == 0:
            # Get the Path name
            for item in os.listdir(os.path.join(FIREFOX_BUILD_PATH, str(build_id))):
                if "QFW" in item:
                    patch_name = item.replace(".tar.bz2", "")
                    break
            
            # Get the Patch size
            patch_size = get_file_size(os.path.join(FIREFOX_BUILD_PATH, str(build_id), patch_name + ".tar.bz2"))
            
            # Get the IP address
            ip_address = get_ip_address()

            # Save the patch info in db
            build.firmware_name = patch_name
            build.firmware_size = patch_size
            build.firmware_log = log_content
            build.download_link = f"http://{ip_address}/{build_id}/{patch_name}.tar.bz2"
            build.status = 'success'
        else:
            build.status = 'failed' 
    except Exception as e:
        build.status = 'failed'
    finally:
        db.session.commit()

