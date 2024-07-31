from flask_wtf import FlaskForm
from flask_wtf.file import FileField, FileAllowed
from wtforms import StringField, SubmitField, TextAreaField
from wtforms.validators import DataRequired

# Quick Firmware Build VMware Horizon Client
class QuickFirmwareBuildVmwareHorizonForm(FlaskForm):
    client_name = StringField('Name', validators=[DataRequired()])
    source_url = StringField('Source URL', validators=[DataRequired()])
    description = TextAreaField('Description', validators=[DataRequired()])
    submit = SubmitField('Build')