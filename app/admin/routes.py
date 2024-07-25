from flask import Blueprint, render_template, request, redirect, url_for, flash
from flask_login import login_required, current_user, logout_user
from app import db, bcrypt
from app.admin.forms import AddUserForm, EditUserForm
from app.models import User,QuickFirmwareBuild
from functools import wraps

# Blueprint for the admin routes
admin_route = Blueprint('admin', __name__, template_folder="templates")

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

@admin_route.route('/logout')
@login_required
def logout():
    logout_user()
    return redirect(url_for('login.user_login'))