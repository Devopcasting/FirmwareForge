from flask import Blueprint, render_template, request, redirect, url_for, flash
from flask_login import login_required, current_user, logout_user

# Blueprint for the users routes
users_route = Blueprint('users', __name__, template_folder="templates")

# Home
@users_route.route('/users')
def users_home():
    return render_template('users/home.html', title="User")

@users_route.route('/logout')
@login_required
def logout():
    logout_user()
    return redirect(url_for('login.user_login'))