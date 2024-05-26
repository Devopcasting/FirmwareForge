from datetime import datetime
from fwapp import db, login_manager, bcrypt
from flask_login import UserMixin

@login_manager.user_loader
def load_user(user_id):
    return User.query.get(int(user_id))

class User(db.Model, UserMixin):
    id = db.Column(db.Integer, primary_key=True)
    username = db.Column(db.String(20), unique=True, nullable=False)
    email = db.Column(db.String(120), unique=True, nullable=False)
    password = db.Column(db.String(60), nullable=False)
    image_file = db.Column(db.String(20), nullable=False, default='default.png')
    role = db.Column(db.String(20), nullable=False, default='user')
    active = db.Column(db.Boolean(), default=True)
    # Create one to many relationship with Firmware
    firmware = db.relationship('QuickBuildFirmware', backref='user', lazy=True)
    
    def is_admin(self):
        return self.role == 'admin'
    
    def is_active(self):
        return self.active
    
    def set_is_active(self, active):
        self.active = active

class QuickBuildFirmware(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    firmware_name = db.Column(db.String(20), unique=True, nullable=False)
    firmware_version = db.Column(db.String(20), nullable=False)
    firmware_description = db.Column(db.String(100), nullable=False)
    firmware_date = db.Column(db.DateTime, nullable=False, default=datetime.now)
    firmware_size = db.Column(db.String(20), nullable=False, default='default.bin')
    firmware_log = db.Column(db.String(200), nullable=False)
    user_id = db.Column(db.Integer, db.ForeignKey('user.id'), nullable=False)