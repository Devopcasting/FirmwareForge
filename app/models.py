from datetime import datetime, time
from app import db, login_manager
from flask_login import UserMixin

@login_manager.user_loader
def load_user(user_id):
    return User.query.get(int(user_id))

class User(db.Model, UserMixin):
    id = db.Column(db.Integer, primary_key=True)
    username = db.Column(db.String(20), unique=True, nullable=False)
    email = db.Column(db.String(120), unique=True, nullable=False)
    password = db.Column(db.String(60), nullable=False)
    profile_image = db.Column(db.String(20), nullable=False, default='default.png')
    role = db.Column(db.String(20), nullable=False, default='user')
    active = db.Column(db.Boolean(), default=True)
    # Create one to many relationship with QuickFirmwareBuild
    quick_firmware_builds = db.relationship('QuickFirmwareBuild', backref='user', lazy=True)

    def is_admin(self):
        return self.role == 'admin'
    
    def is_active(self):
        return self.active
    
    def set_is_active(self, active):
        self.active = active

class FirmwareBuild(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    client_name = db.Column(db.String(100), nullable=False)
    firmware_name = db.Column(db.String(100), nullable=False)
    firmware_build_id = db.Column(db.Integer, nullable=False)
    firmware_description = db.Column(db.Text, nullable=False)
    firmware_size = db.Column(db.String(20), nullable=False)
    firmware_log = db.Column(db.Text, nullable=False)
    download_link = db.Column(db.String(200), nullable=False)
    build_date = db.Column(db.DateTime, nullable=False, default=datetime.now)
    status = db.Column(db.String(20), nullable=False, default='started')
    md5sum = db.Column(db.String(32), nullable=False)
    user_id = db.Column(db.Integer, db.ForeignKey('user.id'), nullable=False)
    
class QuickFirmwareBuild(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    client_name = db.Column(db.String(100), nullable=False)
    firmware_name = db.Column(db.String(100), nullable=False)
    firmware_build_id = db.Column(db.Integer, nullable=False)
    firmware_description = db.Column(db.Text, nullable=False)
    firmware_size = db.Column(db.String(20), nullable=False)
    firmware_log = db.Column(db.Text, nullable=False)
    download_link = db.Column(db.String(200), nullable=False)
    build_date = db.Column(db.DateTime, nullable=False, default=datetime.now)
    status = db.Column(db.String(20), nullable=False, default='started')
    md5sum = db.Column(db.String(32), nullable=False)
    user_id = db.Column(db.Integer, db.ForeignKey('user.id'), nullable=False)
    