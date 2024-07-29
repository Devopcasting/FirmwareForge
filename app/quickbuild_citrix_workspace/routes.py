from flask import Blueprint, render_template, request, redirect, url_for, flash
from flask_login import login_required, current_user
from app import app, db
from app.models import User, QuickFirmwareBuild
from app.quickbuild_citrix_workspace.forms import QuickFirmwareBuildCitrixWorkspaceAppForm
import os
import subprocess
import random
import multiprocessing
import hashlib
import requests
from bs4 import BeautifulSoup

# Blueprint for the quickbuild_citrix_workspace routes
quickbuild_citrix_workspace_route = Blueprint('quickbuild_citrix_workspace', __name__, template_folder="templates")

# Citrix Workspace build path
CITRIX_WORKSPACE_BUILD_PATH = os.path.abspath(os.path.join(os.path.join("app","quickbuild_citrix_workspace", "builds")))
# Citrix Workspace build script path
CITRIX_WORKSPACE_BUILD_SCRIPT_PATH = os.path.abspath(os.path.join("app", "quickbuild_citrix_workspace", "build.sh"))
# Update INI script path
UPDATE_INI_SCRIPT_PATH = os.path.abspath(os.path.join("app", "quickbuild_citrix_workspace", "update_ini.py"))

# Citrix Workspace build reference path
CITRIX_WORKSPACE_BUILD_REFERENCE_PATH = os.path.abspath(os.path.join("app", "quickbuild_citrix_workspace", "references"))

# QuickBuild CitrixWorkspace
@quickbuild_citrix_workspace_route.route('/quickbuild_citrix_workspace', methods=['GET', 'POST'])
@login_required
def quickbuild_citrix_workspace():
    form = QuickFirmwareBuildCitrixWorkspaceAppForm()
    if form.validate_on_submit():
        # Create random folder name in google chrome build path
        build_id = create_random_folder()

        # Log path
        log_path = os.path.join(CITRIX_WORKSPACE_BUILD_PATH, str(build_id), "build.log")

        # Get the Citrix package URL
        citrix_url = 'https://www.citrix.com/downloads/workspace-app/linux/workspace-app-for-linux-latest.html'
        deb_link = find_deb_link_with_rel(citrix_url)
        if not deb_link:
            flash('Failed to find the latest citrix package link', 'danger')
            return redirect(url_for('quickfirmware.quickfirmware'))
        
        # Set the citrix package urls
        icaclient_url = f"https:{deb_link[0]}"
        ctxusb_url = f"https:{deb_link[1]}"

        # Get the data from form
        client_name = form.client_name.data
        description = form.description.data

        # Create a new build
        new_build = QuickFirmwareBuild(client_name=client_name,firmware_name="NA", firmware_build_id=build_id, firmware_description=description, firmware_size="NA",firmware_log="NA", download_link="NA", md5sum="NA", user_id=current_user.id)
        db.session.add(new_build)
        db.session.commit()
        
        # Start the build process
        build_process = multiprocessing.Process(target=start_build, args=(log_path, new_build.id, build_id, icaclient_url, ctxusb_url))
        build_process.start()
        
        flash('Build started successfully!', 'success')
        return redirect(url_for('quickfirmware.quickfirmware'))
    return render_template('quickbuild_citrix_workspace/build.html', form=form)


# Create random folder name in google chrome build path
def create_random_folder():
    build_id = str(random.randint(1000, 9999))
    build_path = os.path.join(CITRIX_WORKSPACE_BUILD_PATH, build_id)
    os.makedirs(build_path, exist_ok=True)
    return build_id

# Get the Citrix package URL
def find_deb_link_with_rel(url, keyword='amd64.deb') -> list:
    # Make a request to the webpage
    response = requests.get(url)
    link_list = []  
    # Check if the request was successful
    if response.status_code == 200:
        # Parse the HTML content
        soup = BeautifulSoup(response.content, 'html.parser')

        # Find all 'a' tags with a rel attribute
        links = soup.find_all('a', rel=True)

        # Filter and print links where the rel attribute contains the keyword
        for link in links:
            if keyword in link['rel'][0]:
                link_list.append(link['rel'][0])
        return link_list

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
def start_build(log_path, user_id, build_id, icaclient_url, ctxusb_url):
    build = QuickFirmwareBuild.query.get(user_id)
    log_content = ""
    patch_name = ""
    try:
        start_build = subprocess.run(
            ['bash', f"{CITRIX_WORKSPACE_BUILD_SCRIPT_PATH}", str(CITRIX_WORKSPACE_BUILD_PATH), str(build_id), str(log_path), str(icaclient_url), str(ctxusb_url), f"{CITRIX_WORKSPACE_BUILD_REFERENCE_PATH}", f"{UPDATE_INI_SCRIPT_PATH}"], 
            capture_output=True
            )
        
        # Write the log contents
        if os.path.exists(log_path):
            with open(log_path, 'r') as f:
                log_content = f.read()

        # Check the status of the build
        if start_build.returncode == 0:
            # Get the Path name
            for item in os.listdir(os.path.join(CITRIX_WORKSPACE_BUILD_PATH, str(build_id))):
                if "QFW" in item:
                    patch_name = item.replace(".tar.bz2", "")
                    break
            
            # Get the Patch size
            patch_size = get_file_size(os.path.join(CITRIX_WORKSPACE_BUILD_PATH, str(build_id), patch_name + ".tar.bz2"))
            
            # Get the IP address
            ip_address = get_ip_address()

            # Get the MD5SUM
            md5sum = calculate_md5sum(os.path.join(CITRIX_WORKSPACE_BUILD_PATH, str(build_id), patch_name + ".tar.bz2"))
            
            # Save the patch info in db
            build.firmware_name = patch_name
            build.firmware_size = patch_size
            build.firmware_log = log_content
            build.download_link = f"http://{ip_address}/{build_id}/{patch_name}.tar.bz2"
            build.status = 'success'
            build.md5sum = md5sum
            # Remove all the contents inside the build except patch and log
            for item in os.listdir(os.path.join(CITRIX_WORKSPACE_BUILD_PATH, str(build_id))):
                if item != patch_name + ".tar.bz2" and item != "build.log":
                    subprocess.run(['rm', '-rf', os.path.join(CITRIX_WORKSPACE_BUILD_PATH, str(build_id), item)])
        else:
            build.status = 'failed' 
            build.firmware_log = log_content
    except Exception as e:
        build.firmware_log = log_content
        build.status = 'failed'
    finally:
        db.session.commit()

