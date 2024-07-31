from flask import Blueprint, render_template, request, redirect, url_for, flash
from flask_login import login_required, current_user, logout_user
from app import db, bcrypt
from app.users.forms import ChangePasswordForm
from app.models import User

# Blueprint for the users routes
users_route = Blueprint('users', __name__, template_folder="templates")

# Home
@users_route.route('/users')
def users_home():
    return render_template('users/home.html', title="User")

# Change Password
@users_route.route('/change_password', methods=['GET', 'POST'])
@login_required
def change_password():
    form = ChangePasswordForm()
    if form.validate_on_submit():
        user = User.query.filter_by(id=current_user.id).first()
        hashed_password = bcrypt.generate_password_hash(form.password.data).decode('utf-8')
        user.password = hashed_password
        db.session.commit()
        flash('Your password has been updated!', 'success')
        return redirect(url_for('users.logout'))
    return render_template('users/change_password.html', title="Change Password", form=form)

@users_route.route('/logout')
@login_required
def logout():
    logout_user()
    return redirect(url_for('login.user_login'))