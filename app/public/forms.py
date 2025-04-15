from flask_wtf import FlaskForm
from wtforms import StringField, SelectField, DateField, TextAreaField
from wtforms.validators import DataRequired, Email, Optional
from datetime import date

class RaceRegistrationForm(FlaskForm):
    first_name = StringField('First Name', validators=[DataRequired()])
    last_name = StringField('Last Name', validators=[DataRequired()])
    email = StringField('Email', validators=[DataRequired(), Email()])
    gender = SelectField('Gender', choices=[('M', 'Male'), ('F', 'Female')], validators=[DataRequired()])
    birth_date = DateField('Date of Birth', validators=[Optional()], default=date(2000, 1, 1))
    club = StringField('Club Name', validators=[Optional()])
    address = StringField('Address', validators=[Optional()])
    phone = StringField('Phone Number', validators=[Optional()])
    emergency_contact = StringField('Emergency Contact', validators=[Optional()])
    event = SelectField('Event', coerce=str, validators=[DataRequired()]) 
    
    def __init__(self, *args, **kwargs):
        super(RaceRegistrationForm, self).__init__(*args, **kwargs)
        # The event choices will be set in the route based on the race events