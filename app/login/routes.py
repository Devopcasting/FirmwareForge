from flask import Blueprint, render_template, redirect, request, flash, url_for
from flask_login import login_user
from app import db, bcrypt
from app.models import User
from app.login.forms import LoginForm

# Blueprint for login routes
login_route = Blueprint('login', __name__, template_folder='templates')

@login_route.route('/', methods=['GET', 'POST'])
def user_login():
    form = LoginForm()
    if form.validate_on_submit():
        user = User.query.filter_by(email=form.email.data).first()
        if user and bcrypt.check_password_hash(user.password, form.password.data):
            # Check if the user is active
            if user.active == 1:
                login_user(user)
                next_page = request.args.get('next')
                # Check the role
                if user.is_admin():
                    return redirect(next_page) if next_page else redirect(url_for('admin.admin_home'))
                else:
                    return redirect(next_page) if next_page else redirect(url_for('users.users_home'))
            else:
                flash('Your account is not active. Please contact the administrator.', 'danger')
                return redirect(url_for('login.user_login'))
        else:
            flash('Login Unsuccessful. Please check email and password', 'danger')
            return redirect(url_for('login.user_login'))
    return render_template('login/login.html', title='Login', form=form)
    