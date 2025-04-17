from datetime import datetime
from werkzeug.security import generate_password_hash, check_password_hash
from flask_login import UserMixin
from sqlalchemy.ext.mutable import MutableList
from sqlalchemy.dialects.sqlite import JSON
from app import db, login


class User(UserMixin, db.Model):
    id = db.Column(db.Integer, primary_key=True)
    username = db.Column(db.String(64), unique=True, nullable=False)
    email = db.Column(db.String(120), unique=True, nullable=False)
    password_hash = db.Column(db.String(128))
    is_admin = db.Column(db.Boolean, default=False)
    is_super_admin = db.Column(db.Boolean, default=False)
    races = db.relationship("Race", backref="admin", lazy="dynamic")

    def set_password(self, password):
        self.password_hash = generate_password_hash(password)

    def check_password(self, password):
        return check_password_hash(self.password_hash, password)


@login.user_loader
def load_user(id):
    return User.query.get(int(id))


# Association table for many-to-many relationship between Race and Runner
race_runners = db.Table(
    "race_runners",
    db.Column("race_id", db.Integer, db.ForeignKey("race.id")),
    db.Column("runner_id", db.Integer, db.ForeignKey("runner.id")),
)


class Race(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.String(128), nullable=False)
    date = db.Column(db.DateTime, nullable=False)
    location = db.Column(db.String(128))
    description = db.Column(db.Text)
    status = db.Column(db.String(20), default="open")
    laps = db.Column(db.Integer, nullable=False, default=1)
    admin_id = db.Column(db.Integer, db.ForeignKey("user.id"))
    events = db.relationship(
        "Event", backref="race", lazy="dynamic", cascade="all, delete-orphan"
    )
    runners = db.relationship("Runner", secondary=race_runners, backref="races")
    results = db.relationship("RaceResult", backref="race", lazy="dynamic")
    registration_fields = db.Column(db.JSON)
    registration_end = db.Column(db.DateTime)  # Add this line
    created_at = db.Column(db.DateTime, default=datetime.utcnow)
    updated_at = db.Column(
        db.DateTime, default=datetime.utcnow, onupdate=datetime.utcnow
    )
    age_groups = db.Column(db.Text, nullable=True)


class Event(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.String(64), nullable=False)
    distance = db.Column(db.Float)  # in kilometers
    race_id = db.Column(db.Integer, db.ForeignKey("race.id"))
    has_checkpoints = db.Column(db.Boolean, default=False)
    number_of_laps = db.Column(db.Integer, default=1)
    start_time = db.Column(db.DateTime)
    results = db.relationship("RaceResult", backref="event", lazy="dynamic")


class Runner(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    first_name = db.Column(db.String(64), nullable=False)
    last_name = db.Column(db.String(64), nullable=False)
    email = db.Column(db.String(120), nullable=False)
    gender = db.Column(db.String(1))  # 'M' or 'F'
    birth_date = db.Column(db.Date)
    club = db.Column(db.String(64))
    address = db.Column(db.String(128))
    phone = db.Column(db.String(20))
    emergency_contact = db.Column(db.String(128))
    results = db.relationship("RaceResult", backref="runner", lazy="dynamic")
    created_at = db.Column(db.DateTime, default=datetime.utcnow)
    
    @property
    def name(self):
        return f"{self.first_name} {self.last_name}"

class RaceResult(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    race_id = db.Column(db.Integer, db.ForeignKey("race.id"))
    event_id = db.Column(db.Integer, db.ForeignKey("event.id"))
    runner_id = db.Column(db.Integer, db.ForeignKey("runner.id"))
    bib_number = db.Column(db.Integer)
    start_time = db.Column(db.DateTime)
    finish_time = db.Column(db.DateTime)
    checkpoint_times = db.Column(db.JSON)  # Store checkpoint times as JSON
    custom_fields = db.Column(MutableList.as_mutable(JSON), default=dict)
    status = db.Column(db.String(20))  # DNS, DNF, finished
    created_at = db.Column(db.DateTime, default=datetime.utcnow)
    lap_times = db.Column(MutableList.as_mutable(JSON), default=list)
    updated_at = db.Column(
        db.DateTime, default=datetime.utcnow, onupdate=datetime.utcnow
    )

    @property
    def finish_duration(self):
        if self.start_time and self.finish_time:
            return self.finish_time - self.start_time
        return None
