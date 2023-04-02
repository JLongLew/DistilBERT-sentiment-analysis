from flask_wtf import FlaskForm
from wtforms import StringField, SubmitField, PasswordField, BooleanField, ValidationError, TextAreaField, SelectField
from wtforms.fields.html5 import EmailField, DateField 
from wtforms.validators import DataRequired, EqualTo, Length, Regexp
from wtforms.widgets import TextArea


# Registration Form
class RegistrationForm(FlaskForm):
	username = StringField('Username', validators=[DataRequired()])
	firstName = StringField('First Name', validators=[DataRequired()])
	lastName = StringField('Last Name', validators=[DataRequired()])
	gender = SelectField('Gender', choices = [('N', 'Not prefer to say'),('M', 'Male'),('F', 'Female')])
	dob = DateField('Date of Birth', format='%Y-%m-%d' , validators=[DataRequired()])
	email = EmailField('Email', validators=[DataRequired()])
	password = PasswordField('Password', validators=[DataRequired(), 
													 EqualTo('password2', message='Passwords Must Match!')])
	password2 = PasswordField('Confirm Password', validators=[DataRequired(message='Password Confirmation is required!')])
	contact = StringField('Contact Number: ', validators=[DataRequired(), 
						  								  Regexp('[0-9]', message='Only numbers are accepted!'), 
						  								  Length(min=10, max=12, message='Field must be between 10 and 12 numbers long.')])
	address = StringField('Address: ', validators=[DataRequired()])
	city = StringField('City: ', validators=[DataRequired()])
	country = StringField('Country: ', validators=[DataRequired()])
	submit = SubmitField('Register new account')
