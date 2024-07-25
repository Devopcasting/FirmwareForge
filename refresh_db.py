from app import app, db, bcrypt
from app.models import User

db.drop_all()
db.create_all()

"""Create Admin User"""
hash_password = bcrypt.generate_password_hash('admin@123').decode('utf-8')
admin = User(username='admin', password=hash_password, email='admin@sundynetech.com', role='admin', active=True)
db.session.add(admin)
db.session.commit()