from flask import Blueprint, render_template, request, redirect, url_for, flash
from flask_login import login_required, current_user, logout_user
from app import db, bcrypt
from app.admin.forms import AddUserForm, EditUserForm
from app.models import User,QuickFirmwareBuild
from functools import wraps
import subprocess
import os
from app.quickbuild_firefox.routes import FIREFOX_BUILD_PATH
from app.quickbuild_chrome.routes import CHROME_BUILD_PATH
from app.quickbuild_vmware_horizon.routes import VMWARE_HORIZON_BUILD_PATH
from app.quickbuild_citrix_workspace.routes import CITRIX_WORKSPACE_BUILD_PATH
from reportlab.pdfgen import canvas
from reportlab.lib.pagesizes import A4
from reportlab.lib.units import inch
from reportlab.lib.colors import black
from reportlab.platypus import Table, TableStyle
from reportlab.lib.enums import TA_LEFT, TA_CENTER
from datetime import date

# Blueprint for the admin routes
admin_route = Blueprint('admin', __name__, template_folder="templates")

# Download Folder path
PATCH_DOWNLOAD_FOLDER = "/var/www/html/"

# Admin role decorator
def admin_role_required(func):
    @wraps(func)
    def wrapper(*args, **kwargs):
        if current_user.role != 'admin':
            flash('You do not have permission to access this page.', 'danger')
            return redirect(url_for('admin.logout'))
        return func(*args, **kwargs)
    return wrapper

# Admin Home
@admin_route.route('/admin', methods=['GET', 'POST'])
@login_required
@admin_role_required
def admin_home():
    page = request.args.get('page', 1, type=int)
    # Get the list of all users except admin user
    list_of_users = User.query.filter(User.role != 'admin').paginate(page=page, per_page=5)
    # Get the list of all the QuickBuildFirmware
    list_of_quickbuild_firmware = QuickFirmwareBuild.query.order_by(QuickFirmwareBuild.id.desc()).paginate(page=page, per_page=5)
    # Get the total number of users except admin user
    total_number_of_users = User.query.count() - 1
    return render_template('admin/home.html', title="Admin", list_of_users=list_of_users, list_of_quickbuild_firmware=list_of_quickbuild_firmware, total_number_of_users=total_number_of_users)

# Add new user
@admin_route.route('/admin/add-user', methods=['GET', 'POST'])
@login_required
@admin_role_required
def add_user():
    form = AddUserForm()
    if form.validate_on_submit():
        hashed_password = bcrypt.generate_password_hash(form.password.data).decode('utf-8')
        user = User(username=form.username.data, email=form.email.data, password=hashed_password, role='user', is_active=True)
        db.session.add(user)
        db.session.commit()
        flash('User added successfully', 'success')
        return redirect(url_for('admin.admin_home'))
    return render_template('admin/add_user.html', title="Add User", form=form)

# Delete User
@admin_route.route('/admin/delete-user/<int:user_id>', methods=['GET', 'POST'])
@login_required
@admin_role_required
def delete_user(user_id):
    user = User.query.get_or_404(user_id)
    db.session.delete(user)
    db.session.commit()
    flash('User deleted successfully', 'success')
    return redirect(url_for('admin.admin_home'))

# Edit User
@admin_route.route('/admin/edit-user/<int:user_id>', methods=['GET', 'POST'])
@login_required
@admin_role_required
def edit_user(user_id):
    user = User.query.get_or_404(user_id)
    form = EditUserForm()
    if request.method == 'POST' and form.validate_on_submit():
        user.username = form.username.data
        if form.password.data:
            hashed_password = bcrypt.generate_password_hash(form.password.data).decode('utf-8')
            user.password = hashed_password
        user.set_is_active(form.is_active.data)
        db.session.commit()
        flash('User updated successfully', 'success')
        return redirect(url_for('admin.admin_home'))
    else:
        form.username.data = user.username
        form.email.data = user.email
        form.is_active.data = user.active
    return render_template('admin/edit_user.html', title="Edit User", form=form)

# Information Patch created by user
@admin_route.route('/admin/patch-info/<int:user_id>', methods=['GET', 'POST'])
@login_required
@admin_role_required
def patch_info(user_id):
    page = request.args.get('page', 1, type=int)
    # Count total quick patch
    total_quick_patch = QuickFirmwareBuild.query.filter_by(user_id=user_id, status='success').count()
    quick_patch = QuickFirmwareBuild.query.filter_by(user_id=user_id, status='success').paginate(page=page, per_page=5)
    return render_template('admin/patch_info.html', title="Patch Info", quickpatch=quick_patch, total_quick_patch=total_quick_patch)

# Delete Build
@admin_route.route('/admin/delete/<int:id>')
@login_required
@admin_role_required
def quickfirmware_delete(id):
    quickfirmware = QuickFirmwareBuild.query.get_or_404(id)
    try:
        # Check if build id is available in FIREFOX_BUILD_PATH
        build_folder = os.path.join(FIREFOX_BUILD_PATH, str(quickfirmware.firmware_build_id))
        if os.path.exists(build_folder):
            subprocess.run(['rm', '-rf', build_folder], check=True)
            
        # Check if build id is available in CHROME_BUILD_PATH
        build_folder = os.path.join(CHROME_BUILD_PATH, str(quickfirmware.firmware_build_id))
        if os.path.exists(build_folder):
            subprocess.run(['rm', '-rf', build_folder], check=True)
        # Check if build id is available in VMWARE_HORIZON_BUILD_PATH
        build_folder = os.path.join(VMWARE_HORIZON_BUILD_PATH, str(quickfirmware.firmware_build_id))
        if os.path.exists(build_folder):
            subprocess.run(['rm', '-rf', build_folder], check=True)
        # Check if build id is available in CITRIX_WORKSPACE_BUILD_PATH
        build_folder = os.path.join(CITRIX_WORKSPACE_BUILD_PATH, str(quickfirmware.firmware_build_id))
        if os.path.exists(build_folder):
            subprocess.run(['rm', '-rf', build_folder], check=True)
        
        # Delete patch from /var/www/html
        subprocess.run(['rm', '-rf', os.path.join(PATCH_DOWNLOAD_FOLDER, str(quickfirmware.firmware_build_id))], check=True)

        # Update the Database
        db.session.delete(quickfirmware)
        db.session.commit()
        flash('Build deleted successfully', 'success')
        return redirect(url_for('admin.admin_home'))

    except Exception as e:
        flash('Error deleting build: ' + str(e), 'danger')
        return redirect(url_for('admin.admin_home'))

# Get the current system IP address
def get_ip_address():
    try:
        ip = subprocess.check_output(['hostname', '-i']).decode().strip()
        return ip
    except Exception as e:
        return "Unknown"
    
# Generate User firmware updates build report
@admin_route.route('/admin/user-report/<int:user_id>')
@login_required
@admin_role_required
def user_report(user_id):
    user = User.query.get_or_404(user_id)
    quick_patch = QuickFirmwareBuild.query.filter_by(user_id=user_id, status='success').all()

    # Check for total number of quick firmware updates
    total_quick_patch = len(quick_patch)
    if len(quick_patch) == 0:
        flash('No firmware updates found for this user', 'warning')
        return redirect(url_for('admin.admin_home'))
    # Create a PDF report
    pdf_file = os.path.join(PATCH_DOWNLOAD_FOLDER, f"{user.username}_report.pdf")
    c = canvas.Canvas(pdf_file, pagesize=A4)
    
    # Set font and font size
    c.setFont("Helvetica", 12)
    
    # Add title
    title = "Firmware Update Report"
    title_x = (8.5*inch - c.stringWidth(title, "Helvetica", 15)) / 2
    c.setFont("Helvetica", 15)
    c.drawString(title_x, 10.5*inch, title)
    c.line(1*inch, 10*inch, 8*inch, 10*inch)

    # Add current date
    current_date = date.today().strftime("%Y-%m-%d")
    c.setFont("Helvetica", 10)
    c.drawString(1*inch, 9.5*inch, "Generated on: " + current_date)

    # Add user information
    c.drawString(1*inch, 9*inch, f"Username: {user.username}")
    c.drawString(1*inch, 8.5*inch, f"Email: {user.email}")

    # Add firmware update statistics
    c.drawString(1*inch, 8*inch, "Total number of Firmware updates: " + str("NA"))
    c.drawString(1*inch, 7.5*inch, "Total number of Quick Firmware updates: " + str("NA"))


    # Create a table for firmware updates
    data = [["Build Id", "Md5sum", "Patchname", "Patch size", "Build Date"]]
    for firmware in quick_patch:
        data.append([str(firmware.firmware_build_id), firmware.md5sum, firmware.firmware_name, str(firmware.firmware_size), str(firmware.build_date.strftime('%d-%m-%Y'))])
    
    # Add heading for the table    
    c.setFont("Helvetica", 12)
    c.drawString(1*inch, 7.2*inch, "Quick Firmware Update")
    table = Table(data, colWidths=[1.2*inch, 1.2*inch, 2*inch, 1.2*inch, 0.8*inch])

    table.setStyle(TableStyle([
    ('FONTNAME', (0,0), (-1,-1), 'Helvetica'),
    ('FONTSIZE', (0,0), (-1,-1), 8),
    ('ALIGN', (0,0), (-1,-1), 'LEFT'),
    ('VALIGN', (0,0), (-1,-1), 'MIDDLE'),
    ('INNERGRID', (0,0), (-1,-1), 0.25, black),
    ('BOX', (0,0), (-1,-1), 0.25, black),
    ('WRAP', (0,0),(-1,-1),True),]))
    
    # Split the table across multiple pages
    table_height = table.wrapOn(c, 7*inch, 5*inch)[1]
    if table_height > 5*inch:
        # Split the table into multiple tables
        num_pages = int(table_height / 5*inch) + 1
        for i in range(num_pages):
            table_page = table.split(num_pages, i)
            table_page.drawOn(c, 0.5*inch, 6*inch - i*5*inch)
            if i < num_pages - 1:
                c.showPage()
    else:
        table.drawOn(c, 0.5*inch, 6*inch)

    # Save PDF and Display the download URL
    c.save()
    report_download_link = f"http://{get_ip_address()}/{user.username}_report.pdf"
    flash(f'Report generated successfully. {report_download_link}', 'success')
    return redirect(url_for('admin.admin_home'))

@admin_route.route('/logout')
@login_required
def logout():
    logout_user()
    return redirect(url_for('login.user_login'))