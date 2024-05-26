from flask import Blueprint, render_template, redirect, url_for, request
from flask_login import logout_user, current_user, login_required
from fwapp import db, bcrypt
from fwapp.models import User, QuickBuildFirmware
from fwapp.admin.form import AddUserForm, EditUserForm
from functools import wraps
from flask import flash


# Blueprint object
admin_route = Blueprint('admin', __name__, template_folder='templates')

# Admin required decorator
def admin_required(f):
    @wraps(f)
    def decorated_function(*args, **kwargs):
        if current_user.role != 'admin':
            return redirect(url_for('main.home'))
        return f(*args, **kwargs)
    return decorated_function

# Admin Home
@admin_route.route('/admin', methods=['GET', 'POST'])
@login_required
@admin_required
def home():
    page = request.args.get('page', 1, type=int)
    # Get the list of all users except admin user
    list_of_users = User.query.filter(User.role != 'admin').paginate(page=page, per_page=5)
    # Get the list of all the QuickBuildFirmware
    list_of_quickbuild_firmware = QuickBuildFirmware.query.order_by(QuickBuildFirmware.id.desc()).paginate(page=page, per_page=5)
    # Get the total number of users except admin user
    total_number_of_users = User.query.count() - 1
    return render_template('admin/home.html', title='Admin | Home', list_of_users=list_of_users, list_of_quickbuild_firmware=list_of_quickbuild_firmware, total_number_of_users=total_number_of_users)

# Add new user
@admin_route.route('/add_new_user', methods=['GET', 'POST'])
@login_required
@admin_required
def add_new_user():
    form = AddUserForm()
    if form.validate_on_submit():
        hashed_password = bcrypt.generate_password_hash(form.password.data).decode('utf-8')
        user = User(username=form.username.data, email=form.email.data, password=hashed_password, role='user')
        db.session.add(user)
        db.session.commit()
        flash('User added successfully!', 'success')
        return redirect(url_for('admin.home'))
    return render_template('admin/add_new_user.html', title='Admin | Add User', form=form)

# Delete User
@admin_route.route('/delete_user/<int:user_id>', methods=['GET', 'POST'])
@login_required
@admin_required
def delete_user(user_id):
    user = User.query.get_or_404(user_id)
    # Delete the user from the database
    db.session.delete(user)
    db.session.commit()
    flash('User deleted successfully!', 'success')
    return redirect(url_for('admin.home'))

# Edit User
@admin_route.route('/edit_user/<int:user_id>', methods=['GET', 'POST'])
@login_required
@admin_required
def edit_user(user_id):
    user = User.query.get_or_404(user_id)
    form = EditUserForm()
    if form.validate_on_submit():
        user.username = form.username.data
        # If password is empty don't update the password
        if form.password.data:
            user.password = bcrypt.generate_password_hash(form.password.data).decode('utf-8')
        user.set_is_active(form.is_active.data)
        # Update the user in the database
        db.session.commit()
        flash('User updated successfully!', 'success')
        return redirect(url_for('admin.home'))
    elif request.method == 'GET':
        form.username.data = user.username
        form.email.data = user.email
        form.password.data = user.password
        form.is_active.data = user.active
    return render_template('admin/edit_user.html', title='Admin | Edit User', form=form, user_info=user)

# Logout Admin
@admin_route.route('/logout')
@login_required
def logout():
    logout_user()
    return redirect(url_for('login.user_login'))