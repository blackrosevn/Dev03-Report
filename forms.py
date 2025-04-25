from flask_wtf import FlaskForm
from wtforms import StringField, PasswordField, BooleanField, SelectField, TextAreaField, FileField, DateField, HiddenField, SubmitField
from wtforms.validators import DataRequired, Email, EqualTo, Length, ValidationError
from models import User, Organization

class LoginForm(FlaskForm):
    username = StringField('Username', validators=[DataRequired()])
    password = PasswordField('Password', validators=[DataRequired()])
    remember_me = BooleanField('Remember Me')
    submit = SubmitField('Sign In')

class RegisterForm(FlaskForm):
    username = StringField('Username', validators=[DataRequired(), Length(min=4, max=25)])
    email = StringField('Email', validators=[DataRequired(), Email()])
    password = PasswordField('Password', validators=[DataRequired(), Length(min=6)])
    confirm_password = PasswordField('Confirm Password', validators=[DataRequired(), EqualTo('password')])
    fullname = StringField('Full Name', validators=[DataRequired()])
    role = SelectField('Role', coerce=int, validators=[DataRequired()])
    organization = SelectField('Organization', coerce=int, validators=[DataRequired()])
    submit = SubmitField('Register')
    
    def validate_username(self, username):
        user = User.query.filter_by(username=username.data).first()
        if user:
            raise ValidationError('That username is already taken. Please choose a different one.')
    
    def validate_email(self, email):
        user = User.query.filter_by(email=email.data).first()
        if user:
            raise ValidationError('That email is already registered. Please use a different one.')

class UserForm(FlaskForm):
    username = StringField('Username', validators=[DataRequired(), Length(min=4, max=25)])
    email = StringField('Email', validators=[DataRequired(), Email()])
    fullname = StringField('Full Name', validators=[DataRequired()])
    role = SelectField('Role', coerce=int, validators=[DataRequired()])
    organization = SelectField('Organization', coerce=int, validators=[DataRequired()])
    is_active = BooleanField('Active')
    password = PasswordField('Password', validators=[Length(min=6)])
    confirm_password = PasswordField('Confirm Password', validators=[EqualTo('password')])
    submit = SubmitField('Save User')

class OrganizationForm(FlaskForm):
    name = StringField('Name (Vietnamese)', validators=[DataRequired()])
    name_en = StringField('Name (English)')
    code = StringField('Code', validators=[DataRequired(), Length(min=2, max=20)])
    description = TextAreaField('Description')
    parent = SelectField('Parent Organization', coerce=int, validators=[])
    is_active = BooleanField('Active')
    id = HiddenField('ID')  # Hidden field to store the ID for validation during edits
    submit = SubmitField('Save Organization')
    
    def validate_code(self, code):
        org = Organization.query.filter_by(code=code.data).first()
        # Get current org id from the hidden field if it exists
        current_org_id = int(self.id.data) if self.id.data else None
        if org and org.id != current_org_id:
            raise ValidationError('That code is already in use. Please choose a different one.')

class ReportTemplateForm(FlaskForm):
    name = StringField('Name (Vietnamese)', validators=[DataRequired()])
    name_en = StringField('Name (English)')
    description = TextAreaField('Description')
    structure = HiddenField('Structure', validators=[DataRequired()])
    is_active = BooleanField('Active')
    submit = SubmitField('Save Template')

class ReportAssignmentForm(FlaskForm):
    report_template = SelectField('Report Template', coerce=int, validators=[DataRequired()])
    organization = SelectField('Organization', coerce=int, validators=[DataRequired()])
    due_date = DateField('Due Date', validators=[DataRequired()])
    frequency = SelectField('Frequency', validators=[DataRequired()], choices=[
        ('daily', 'Daily'),
        ('weekly', 'Weekly'),
        ('monthly', 'Monthly'),
        ('quarterly', 'Quarterly'),
        ('semi_annually', 'Semi-Annually'),
        ('annually', 'Annually'),
        ('one_time', 'One-Time')
    ])
    submit = SubmitField('Assign Report')

class ReportSubmissionForm(FlaskForm):
    notes = TextAreaField('Notes')
    file = FileField('Excel File')
    form_data = HiddenField('Form Data')
    submit = SubmitField('Submit Report')

class SettingsForm(FlaskForm):
    sharepoint_url = StringField('Sharepoint URL', validators=[DataRequired()])
    email_notifications = BooleanField('Email Notifications')
    email_reminder_days = StringField('Email Reminder Days (comma-separated)')
    smtp_server = StringField('SMTP Server')
    smtp_port = StringField('SMTP Port')
    smtp_username = StringField('SMTP Username')
    smtp_password = PasswordField('SMTP Password')
    submit = SubmitField('Save Settings')

class ChangeLanguageForm(FlaskForm):
    language = SelectField('Language', choices=[('en', 'English'), ('vi', 'Tiếng Việt')])
    submit = SubmitField('Change Language')

class ChangePasswordForm(FlaskForm):
    current_password = PasswordField('Current Password', validators=[DataRequired()])
    new_password = PasswordField('New Password', validators=[DataRequired(), Length(min=6)])
    confirm_password = PasswordField('Confirm New Password', validators=[DataRequired(), EqualTo('new_password')])
    submit = SubmitField('Change Password')
