from flask_wtf import FlaskForm
from wtforms import StringField, SubmitField, TextAreaField
from wtforms.validators import DataRequired

# Quick Firmware Build Firefox
class QuickFirmwareBuildFirefoxForm(FlaskForm):
    client_name = StringField('Name', validators=[DataRequired()])
    description = TextAreaField('Description', validators=[DataRequired()])
    submit = SubmitField('Build')

# Quick Firmware Build Chrome
class QuickFirmwareBuildChromeForm(FlaskForm):
    client_name = StringField('Name', validators=[DataRequired()])
    description = TextAreaField('Description', validators=[DataRequired()])
    submit = SubmitField('Build')

# Quick Firmware Build VMware Horizon Client
class QuickFirmwareBuildVmwareHorizonForm(FlaskForm):
    client_name = StringField('Name', validators=[DataRequired()])
    source_url = StringField('Source URL', validators=[DataRequired()])
    description = TextAreaField('Description', validators=[DataRequired()])
    submit = SubmitField('Build')