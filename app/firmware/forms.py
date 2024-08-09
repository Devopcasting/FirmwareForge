from flask_wtf import FlaskForm
from flask_wtf.file import FileField, FileAllowed
from wtforms import StringField, SubmitField, TextAreaField, BooleanField
from wtforms.validators import DataRequired

# Build new firmware
class NewFirmwareForm(FlaskForm):
    patch_name = StringField('Patch Name', validators=[DataRequired()])
    client_name = StringField('Client Name', validators=[DataRequired()])
    description = TextAreaField('Description', validators=[DataRequired()])
    install_script = TextAreaField('Install Script',default="#!/bin/bash\n\nmount -o remount,rw /sda1", validators=[DataRequired()])
    files = FileField('Upload Files', validators=[DataRequired()], render_kw={"multiple": True})
    menu = BooleanField('Menu')
    restore = BooleanField('Restore')
    executable = StringField('Executable')
    program_name = StringField('Program Name')
    icon = StringField('Icon')
    executable_user = StringField('User', default="root")
    submit = SubmitField('Build')
