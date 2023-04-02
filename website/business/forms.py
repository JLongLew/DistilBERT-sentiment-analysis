from flask_wtf import FlaskForm
from wtforms import StringField, SubmitField, PasswordField, BooleanField, ValidationError, TextAreaField, SelectField
from wtforms.fields.html5 import EmailField 
from wtforms.validators import DataRequired, EqualTo, Length, Regexp
from wtforms.widgets import TextArea
# from flask_ckeditor import CKEditorField
from flask_wtf.file import FileField

# Login Form
class LoginForm(FlaskForm):
	email = EmailField("Email", validators=[DataRequired()])
	password = PasswordField("Password", validators=[DataRequired()])
	role = SelectField('Your Role', choices = [('none', 'Choice ...'), ('bus', 'Business'),('cus', 'Customer')])
	submit = SubmitField("Log in to your account")
	

# Registration Form
class RegistrationForm(FlaskForm):
	name = StringField("Business Name", validators=[DataRequired(), Length(min=4, max=25)])
	email = EmailField("Email", validators=[DataRequired()])
	password = PasswordField('Password', validators=[DataRequired(), EqualTo('password2', message='Passwords Must Match!')])
	password2 = PasswordField('Confirm Password', validators=[DataRequired()])
	contact = StringField('Contact Number: ', validators=[DataRequired(), Regexp('[0-9]', message='Only numbers are accepted!'), Length(min=10, max=12)])
	address = StringField('Address: ', validators=[DataRequired()])
	city = StringField('City: ', validators=[DataRequired()])
	country = StringField('Country: ', validators=[DataRequired()])
	submit = SubmitField("Register new account")
