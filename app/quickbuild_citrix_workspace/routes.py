from flask import Blueprint, render_template, request, redirect, url_for, flash
from flask_login import login_required, current_user
from werkzeug.utils import secure_filename
from app import db
from app.models import User, QuickFirmwareBuild
from app.quickbuild_citrix_workspace.forms import QuickFirmwareBuildCitrixWorkspaceAppForm
import os
import subprocess
import random
import multiprocessing

# Blueprint for the quickbuild_citrix_workspace routes
quickbuild_citrix_workspace_route = Blueprint('quickbuild_citrix_workspace', __name__, template_folder="templates")

# Citrix Workspace build path
CITRIX_WORKSPACE_BUILD_PATH = os.path.abspath(os.path.join(os.path.join("app","quickbuild_citrix_workspace", "builds")))
# Citrix Workspace build script path
CITRIX_WORKSPACE_BUILD_SCRIPT_PATH = os.path.abspath(os.path.join("app", "quickbuild_citrix_workspace", "build.sh"))
# Citrix Workspace build reference path
CITRIX_WORKSPACE_BUILD_REFERENCE_PATH = os.path.abspath(os.path.join("app", "quickbuild_citrix_workspace", "references"))

# QuickBuild CitrixWorkspace
@quickbuild_citrix_workspace_route.route('/quickbuild_citrix_workspace', methods=['GET', 'POST'])
@login_required
def quickbuild_citrix_workspace():
    form = QuickFirmwareBuildCitrixWorkspaceAppForm()
    return render_template('quickbuild_citrix_workspace/build.html', form=form)