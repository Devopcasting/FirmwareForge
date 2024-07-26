from flask import Blueprint, render_template, request, redirect, url_for, flash, jsonify
from flask_login import login_required, current_user
from app.models import QuickFirmwareBuild
from app import db
from app.quickbuild_firefox.routes import FIREFOX_BUILD_PATH
from app.quickbuild_chrome.routes import CHROME_BUILD_PATH
from app.quickbuild_vmware_horizon.routes import VMWARE_HORIZON_BUILD_PATH
from app.quickbuild_citrix_workspace.routes import CITRIX_WORKSPACE_BUILD_PATH
import subprocess
import os

# Blueprint for the quickfirmware routes
quickfirmware_route = Blueprint('quickfirmware', __name__, template_folder="templates")

# Download Folder path
PATCH_DOWNLOAD_FOLDER = "/var/www/html/"

# QuickFirmware dashboard
@quickfirmware_route.route('/quickfirmware')
@login_required
def quickfirmware():
    page = request.args.get('page', 1, type=int)
    # Get the total number of QuickBuildFirmware created by current user
    total = QuickFirmwareBuild.query.filter_by(user_id=current_user.id).count()
    # Get the QuickBuildFirmware created by current user with pagination
    quickfirmware = QuickFirmwareBuild.query.filter_by(user_id=current_user.id).order_by(QuickFirmwareBuild.id.desc()).paginate(page=page, per_page=10)
    # Get the count of failed builds
    failed_builds = QuickFirmwareBuild.query.filter_by(user_id=current_user.id, status='failed').count()
    return render_template('quickfirmware/quickfirmware.html', title="Quick Firmware", quickfirmware=quickfirmware, total=total, failed_builds=failed_builds)

# QuickBuild Info
@quickfirmware_route.route('/quickfirmware/info/<int:id>')
@login_required
def quickfirmware_info(id):
    quickfirmware = QuickFirmwareBuild.query.get_or_404(id)
    return render_template('quickfirmware/quickfirmware_info.html', title="Build Info", quickfirmware=quickfirmware)

# Delete Build
@quickfirmware_route.route('/quickfirmware/delete/<int:id>')
@login_required
def quickfirmware_delete(id):
    quickfirmware = QuickFirmwareBuild.query.get_or_404(id)
    try:
        # Delete the build folder
        build_folder = os.path.join(FIREFOX_BUILD_PATH, str(quickfirmware.firmware_build_id))
        subprocess.run(['rm', '-rf', build_folder], check=True)
        # Delete the patch from download folder path
        download_path = os.path.join(PATCH_DOWNLOAD_FOLDER, str(quickfirmware.firmware_build_id))
        subprocess.run(['rm', '-rf', download_path], check=True)
        db.session.delete(quickfirmware)
        db.session.commit()
        flash('Build deleted successfully', 'success')
        return redirect(url_for('quickfirmware.quickfirmware'))
    except Exception as e:
        flash('Error deleting build: ' + str(e), 'danger')
        return redirect(url_for('quickfirmware.quickfirmware'))

# Delete all the builds at once
@quickfirmware_route.route('/quickfirmware/delete_all', methods=['POST','GET'])
@login_required
def quickfirmware_delete_all():
    try:
        # Get all the builds created by current user
        builds = QuickFirmwareBuild.query.filter_by(user_id=current_user.id).all()
        for build in builds:
            # Delete the build folder inside firefox
            # Check if locked named file is not available in build_id folder
            if not os.path.exists(os.path.join(FIREFOX_BUILD_PATH, str(build.firmware_build_id), 'locked')):
                build_folder = os.path.join(FIREFOX_BUILD_PATH, str(build.firmware_build_id))
                subprocess.run(['rm', '-rf', build_folder], check=True)
            
            # Delete the build folder inside chrome
            # Check if locked named file is not available in build_id folder
            if not os.path.exists(os.path.join(CHROME_BUILD_PATH, str(build.firmware_build_id), 'locked')):
                build_folder = os.path.join(CHROME_BUILD_PATH, str(build.firmware_build_id))
                subprocess.run(['rm', '-rf', build_folder], check=True)
            
            # Delete the build folder inside vmware
            # Check if locked named file is not available in build_id folder
            if not os.path.exists(os.path.join(VMWARE_HORIZON_BUILD_PATH, str(build.firmware_build_id), 'locked')):
                build_folder = os.path.join(VMWARE_HORIZON_BUILD_PATH, str(build.firmware_build_id))
                subprocess.run(['rm', '-rf', build_folder], check=True)
            
            # Delete the build folder inside citrix
            # Check if locked named file is not available in build_id folder
            if not os.path.exists(os.path.join(CITRIX_WORKSPACE_BUILD_PATH, str(build.firmware_build_id), 'locked')):
                build_folder = os.path.join(CITRIX_WORKSPACE_BUILD_PATH, str(build.firmware_build_id))
                subprocess.run(['rm', '-rf', build_folder], check=True)
                
            # Delete the patch from download folder path
            download_path = os.path.join(PATCH_DOWNLOAD_FOLDER, str(build.firmware_build_id))
            subprocess.run(['rm', '-rf', download_path], check=True)
        
        # Delete all the builds from the database
        QuickFirmwareBuild.query.filter_by(user_id=current_user.id).delete()
        db.session.commit()
        flash('All builds deleted successfully', 'success')
        return redirect(url_for('quickfirmware.quickfirmware'))
    except Exception as e:
        flash('Error deleting builds: ' + str(e), 'danger')
        return redirect(url_for('quickfirmware.quickfirmware'))

# Delete builds which have failed status
@quickfirmware_route.route('/quickfirmware/delete_failed', methods=['POST', 'GET'])
@login_required
def quickfirmware_delete_failed():
    try:
        # Get all the builds with failed status
        builds = QuickFirmwareBuild.query.filter_by(user_id=current_user.id, status='failed').all()
        for build in builds:
            # Delete the build folder inside firefox
            # Check if locked named file is not available in build_id folder
            if not os.path.exists(os.path.join(FIREFOX_BUILD_PATH, str(build.firmware_build_id), 'locked')):
                build_folder = os.path.join(FIREFOX_BUILD_PATH, str(build.firmware_build_id))
                subprocess.run(['rm', '-rf', build_folder], check=True)

            # Delete the build folder inside chrome
            # Check if locked named file is not available in build_id folder
            if not os.path.exists(os.path.join(CHROME_BUILD_PATH, str(build.firmware_build_id), 'locked')):
                build_folder = os.path.join(CHROME_BUILD_PATH, str(build.firmware_build_id))
                subprocess.run(['rm', '-rf', build_folder], check=True)

            # Delete the build folder inside vmware
            # Check if locked named file is not available in build_id folder
            if not os.path.exists(os.path.join(VMWARE_HORIZON_BUILD_PATH, str(build.firmware_build_id), 'locked')):
                build_folder = os.path.join(VMWARE_HORIZON_BUILD_PATH, str(build.firmware_build_id))
                subprocess.run(['rm', '-rf', build_folder], check=True)
            
            # Delete the build folder inside citrix
            # Check if locked named file is not available in build_id folder
            if not os.path.exists(os.path.join(CITRIX_WORKSPACE_BUILD_PATH, str(build.firmware_build_id), 'locked')):
                build_folder = os.path.join(CITRIX_WORKSPACE_BUILD_PATH, str(build.firmware_build_id))
                subprocess.run(['rm', '-rf', build_folder], check=True)
        # Delete all the builds with failed status
        QuickFirmwareBuild.query.filter_by(user_id=current_user.id, status='failed').delete()
        db.session.commit()
        flash('Failed builds deleted successfully', 'success')
        return redirect(url_for('quickfirmware.quickfirmware'))
    except Exception as e:
        flash('Error deleting builds: ' + str(e), 'danger')
        return redirect(url_for('quickfirmware.quickfirmware'))
    
# Check the status of the build
@quickfirmware_route.route('/quickfirmware/check_status', methods=['GET'])
@login_required
def check_status():
    firmware_id = request.args.get('id')
    firmware = QuickFirmwareBuild.query.get(firmware_id)
    if firmware:
        status = firmware.status
        return jsonify({'status': status})
    return jsonify({'status': 'unknown'})