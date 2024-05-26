from flask import Blueprint, render_template, redirect, url_for
from flask_login import logout_user, current_user, login_required
from fwapp import db
from fwapp.models import User


# Blueprint object
users_route = Blueprint('users', __name__, template_folder='templates')

# Users Home
@users_route.route('/user', methods=['GET', 'POST'])
def home():
    return render_template('users/home.html', title='Home')

# Logout User
@users_route.route('/logout')
@login_required
def logout():
    logout_user()
    return redirect(url_for('login.user_login'))