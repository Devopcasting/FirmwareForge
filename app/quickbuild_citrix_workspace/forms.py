from flask_wtf import FlaskForm
from flask_wtf.file import FileField, FileAllowed
from wtforms import StringField, SubmitField, TextAreaField
from wtforms.validators import DataRequired

# Quick Firmware Build Citrix Workspace App
class QuickFirmwareBuildCitrixWorkspaceAppForm(FlaskForm):
    client_name = StringField('Name', validators=[DataRequired()])
    # icaclient = FileField(label="ICAClient", validators=[DataRequired()])
    # ctxusb = FileField(label='CTXUSB', validators=[DataRequired()])
    description = TextAreaField('Description', validators=[DataRequired()])
    submit = SubmitField('Build')