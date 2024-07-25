from flask_wtf import FlaskForm
from wtforms import StringField, SubmitField, PasswordField, EmailField, BooleanField
from wtforms.validators import DataRequired, Email, ValidationError
from app.models import User

# Add new user form
class AddUserForm(FlaskForm):
    username = StringField("Username", validators=[DataRequired()])
    email = EmailField("Email", validators=[DataRequired(), Email()])
    password = PasswordField("Password", validators=[DataRequired()])
    submit = SubmitField("Add new user")

    # Validate email
    def validate_email(self, email):
        user = User.query.filter_by(email=email.data).first()
        if user:
            raise ValidationError("Email already exists")
        # Check if email is valid for sundynetech.com
        if not email.data.endswith("@sundynetech.com"):
            raise ValidationError("Email must be a SundyneTech email")
        
    # Validate username
    def validate_username(self, username):
        user = User.query.filter_by(username=username.data).first()
        if user:
            raise ValidationError("Username already exists")

# Edit user form
class EditUserForm(FlaskForm):
    username = StringField("Username")
    email = EmailField("Email")
    password = PasswordField("Password")
    is_active = BooleanField("Is Active")
    submit = SubmitField("Update user")    