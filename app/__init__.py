# app/__init__.py

from flask import Flask
from flask_sqlalchemy import SQLAlchemy
from flask_login import LoginManager
from flask_bcrypt import Bcrypt

# Initialize Flask extensions
app = Flask(__name__)
app.config['SECRET_KEY'] = '878436c0a462c4145fa59eec2c43a66a'
app.config['SQLALCHEMY_DATABASE_URI'] = 'sqlite:///user.db'
app.config['SQLALCHMEY_BINDS'] = {"user": 'sqlite:///user.db', "firmware": 'sqlite:///quick_firmware.db'}
app.app_context().push()

# Initialize SQLAlchemy
db = SQLAlchemy(app)

# Initialize Bcrypt for password hashing
bcrypt = Bcrypt(app)

# Initialize Flask-Login
login_manager = LoginManager(app)
login_manager.login_view = 'login.user_login'
login_manager.login_message_category = 'info'
login_manager.session_protection = "strong"

# Register blueprints
from app.login.routes import login_route
app.register_blueprint(login_route)
from app.admin.routes import admin_route
app.register_blueprint(admin_route)
from app.users.routes import users_route
app.register_blueprint(users_route)
from app.quickfirmware.routes import quickfirmware_route
app.register_blueprint(quickfirmware_route)
from app.quickbuild_firefox.routes import quickbuild_firefox_route
app.register_blueprint(quickbuild_firefox_route)
from app.quickbuild_chrome.routes import quickbuild_chrome_route
app.register_blueprint(quickbuild_chrome_route)
from app.quickbuild_vmware_horizon.routes import quickbuild_vmware_horizon_route
app.register_blueprint(quickbuild_vmware_horizon_route)
from app.quickbuild_citrix_workspace.routes import quickbuild_citrix_workspace_route
app.register_blueprint(quickbuild_citrix_workspace_route)
from app.firmware.routes import firmware_build
app.register_blueprint(firmware_build)