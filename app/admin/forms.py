from flask_wtf import FlaskForm
from wtforms import (
    StringField,
    TextAreaField,
    DateTimeField,
    FloatField,
    IntegerField,
    SelectField,
)
from wtforms import BooleanField, SubmitField, SelectMultipleField
from wtforms.validators import DataRequired, Email, Optional, NumberRange


class RaceForm(FlaskForm):
    name = StringField("Race Name", validators=[DataRequired()])
    date = DateTimeField(
        "Race Date", format="%Y-%m-%dT%H:%M", validators=[DataRequired()]
    )  # Changed format
    location = StringField("Location", validators=[DataRequired()])
    description = TextAreaField("Description")
    registration_fields = SelectMultipleField(
        "Registration Fields",
        choices=[
            ("birth_date", "Date of Birth"),
            ("club", "Club Name"),
            ("address", "Address"),
            ("phone", "Phone Number"),
            ("emergency_contact", "Emergency Contact"),
            ("shirt_size", "T-Shirt Size"),
        ],
        default=[],
    )
    age_groups = TextAreaField(
        "Age Groups (JSON format)",
        default='[{"min": 0, "max": 17, "label": "Under 18"}, {"min": 18, "max": 29, "label": "18-29"}]',
    )
    submit = SubmitField("Save Race")


class EventForm(FlaskForm):
    name = StringField("Event Name", validators=[DataRequired()])
    distance = FloatField(
        "Distance (km)", validators=[DataRequired(), NumberRange(min=0)]
    )
    has_checkpoints = BooleanField("Has Checkpoints")
    number_of_laps = IntegerField(
        "Number of Laps", validators=[Optional(), NumberRange(min=1)]
    )
    submit = SubmitField("Save Event")


class RunnerForm(FlaskForm):
    first_name = StringField("First Name", validators=[DataRequired()])
    last_name = StringField("Last Name", validators=[DataRequired()])
    email = StringField("Email", validators=[DataRequired(), Email()])
    gender = SelectField("Gender", choices=[("M", "Male"), ("F", "Female")])
    birth_date = DateTimeField("Birth Date", format="%Y-%m-%d", validators=[Optional()])
    club = StringField("Club")
    address = StringField("Address")
    phone = StringField("Phone")
    emergency_contact = StringField("Emergency Contact")
    submit = SubmitField("Save Runner")


class RunnerResultForm(FlaskForm):
    bib_number = IntegerField("Bib Number", validators=[Optional()])
    event = SelectField("Event", coerce=int, validators=[DataRequired()])
    status = SelectField(
        "Status",
        choices=[
            ("registered", "Registered"),
            ("DNS", "Did Not Start"),
            ("DNF", "Did Not Finish"),
            ("finished", "Finished"),
        ],
    )
    submit = SubmitField("Save Changes")
