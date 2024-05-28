from flask import Blueprint, render_template, redirect, flash, request
from flask_login import login_user
from fwapp import db, bcrypt
from fwapp.models import User
from fwapp.login.form import LoginForm
from flask import url_for

# Blueprint object
login_route = Blueprint('login', __name__, template_folder='templates')

@login_route.route('/', methods=['GET', 'POST'])
def user_login():
    form = LoginForm()
    if form.validate_on_submit():
        user = User.query.filter_by(email=form.email.data).first()
        if user and bcrypt.check_password_hash(user.password, form.password.data):
            # Check if user is active
            if user.is_active():
                login_user(user)
                next_page = request.args.get('next')
                # If user role is admin then redirect to admin page
                if user.is_admin():
                    return redirect(next_page) if next_page else redirect(url_for('admin.home'))
                else:
                    return redirect(next_page) if next_page else redirect(url_for('users.home'))   
            else:
                flash('Your account is not active. Please contact the administrator', 'danger')
                return redirect(url_for('login.user_login'))
        else:
            flash('Login Unsuccessful. Please check email and password', 'danger')
    return render_template('login/login.html', title='Login', form=form)