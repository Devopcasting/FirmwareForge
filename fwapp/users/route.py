from flask import Blueprint, render_template, redirect, url_for
from flask_login import logout_user, current_user, login_required
from fwapp import db
from fwapp.models import User
import qrcode
import io
import string
import random

# Set Static path for QR code images
QRCODE_PATH='static/qrcodes/'

# Blueprint object
users_route = Blueprint('users', __name__, template_folder='templates')

# Users Home
@users_route.route('/user', methods=['GET', 'POST'])
def home():
    return render_template('users/home.html', title='Home')

# User Two-Factor Authentication
@users_route.route('/user/2fa', methods=['GET', 'POST'])
def two_factor():
    # Get the status of two factor authentication
    user = User.query.filter_by(id=current_user.id).first()
    two_factor_status = user.two_factor_enabled
    return render_template('users/2fa.html', title='User | 2FA', two_factor_status=two_factor_status)

# Enable Two-Factor Authentication
@users_route.route('/user/2fa/enable', methods=['GET', 'POST'])
def enable_2fa():
    generate_qr_code()
    return render_template('users/set_2fa.html', title='User | 2FA')

# Generate QR code
def generate_qr_code():
    data = current_user.username
    qr = qrcode.QRCode(
        version=1,
        error_correction=qrcode.constants.ERROR_CORRECT_L,
        box_size=10,
        border=4,
    )
    qr.add_data(data)
    qr.make(fit=True)
    img = qr.make_image(fill_color="black", back_color="white")
    img = img.convert("RGB")
    img = img.resize((200, 200))
    # Save the QR code image
    img.save(f"{QRCODE_PATH}{current_user.username}.png")

# Logout User
@users_route.route('/logout')
@login_required
def logout():
    logout_user()
    return redirect(url_for('login.user_login'))