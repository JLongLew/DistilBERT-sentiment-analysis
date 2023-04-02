from flask_wtf import FlaskForm
from wtforms import StringField, SubmitField, TextAreaField, SelectField, SelectMultipleField, widgets
from wtforms.fields.html5 import EmailField, DateField
from wtforms.validators import DataRequired, EqualTo, Length, Regexp
from wtforms.widgets import TextArea
from datetime import datetime

class MultiCheckboxField(SelectMultipleField):
    widget = widgets.ListWidget(prefix_label=False)
    option_widget = widgets.CheckboxInput()
    
# Product Form
class ProductForm(FlaskForm):
    name = StringField('Product Name', validators=[DataRequired()])
    description = TextAreaField('Description', validators=[DataRequired()])
    submit = SubmitField('Add Product')


# Product Review Form
class ReviewForm(FlaskForm):
    title = StringField('Give Your Feedback a Title', validators=[DataRequired()])
    tag_1 = SelectField('First Tag')
    tag_2 = SelectField('Second Tag')
    tag_3 = SelectField('Third Tag')
    feedback = TextAreaField('Your Feedback', validators=[DataRequired()])
    date = DateField('Date of Experience', format='%Y-%m-%d', validators=[DataRequired()])
