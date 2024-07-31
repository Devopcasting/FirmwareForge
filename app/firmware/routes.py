from flask import Blueprint, render_template, request, redirect, url_for, flash, jsonify
from flask_login import login_required, current_user
from app.models import QuickFirmwareBuild
from app import db
import subprocess
import os

# Blueprint for the firmware build
firmware_build = Blueprint('firmware', __name__, template_folder="templates")

# Build Firmware
@firmware_build.route('/build', methods=['GET', 'POST'])
@login_required
def build_firmware():
    # Render the firmware build template
    return render_template('firmware/firmware_build.html', title='Build Firmware')