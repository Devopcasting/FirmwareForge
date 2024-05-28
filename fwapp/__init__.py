from flask import Flask
from flask_sqlalchemy import SQLAlchemy
from flask_login import LoginManager
from flask_bcrypt import Bcrypt
from flask_migrate import Migrate
from flask_wtf.csrf import CSRFProtect

# App Configuration
app = Flask(__name__)
app.config['SECRET_KEY'] = '878436c0a462c4145fa59eec2c43a66a'
app.config['SQLALCHEMY_DATABASE_URI'] = 'sqlite:///user.db'
app.config['SQLALCHEMY_BINDS'] = {"user": 'sqlite:///user.db', "firmware": 'sqlite:///firmware.db'}
db = SQLAlchemy(app)
app.app_context().push()
bcrypt = Bcrypt(app)

# Login Manager Configuration
login_manager = LoginManager(app)
login_manager.login_view = 'login.user_login'
login_manager.login_message_category = 'info'
login_manager.session_protection = 'strong'

# Database Migrations
migrate = Migrate(app, db)

# CSRF Protection
csrf = CSRFProtect(app)

# Register Blueprint
from fwapp.login.route import login_route
app.register_blueprint(login_route)
from fwapp.admin.route import admin_route
app.register_blueprint(admin_route)
from fwapp.users.route import users_route
app.register_blueprint(users_route)
from fwapp.quickbuild.route import quickbuild_route
app.register_blueprint(quickbuild_route)