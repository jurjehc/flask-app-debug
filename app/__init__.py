from flask import Flask
from flask_sqlalchemy import SQLAlchemy
from flask_migrate import Migrate
from flask_login import LoginManager
from flask_mail import Mail
from flask_admin import Admin
from config import Config
from app.utils.helpers import get_race_status_class  # Add this line
from datetime import datetime



db = SQLAlchemy()
migrate = Migrate()
login = LoginManager()
login.login_view = 'auth.login'
login.login_message = 'Please log in to access this page.'
mail = Mail()
flask_admin = Admin(name='Trkaljka Admin', template_mode='bootstrap4')



def create_app(config_class=Config):
    app = Flask(__name__)
    app.config.from_object(config_class)

    # Initialize Flask extensions
    db.init_app(app)
    migrate.init_app(app, db)
    login.init_app(app)
    mail.init_app(app)
    flask_admin.init_app(app)

    app.jinja_env.filters['format_time'] = format_time

    # Register context processors
    @app.context_processor
    def utility_processor():
        return {
            'get_race_status_class': get_race_status_class
        }

    # Register blueprints
    from app.auth import bp as auth_bp
    app.register_blueprint(auth_bp, url_prefix='/auth')

    from app.admin import bp as admin_bp
    app.register_blueprint(admin_bp, url_prefix='/admin_panel')

    from app.public import bp as public_bp
    app.register_blueprint(public_bp)

    def format_duration(start_time, finish_time):
        if not start_time or not finish_time:
            return "--:--"
        
        # Calculate duration in seconds
        delta = (finish_time - start_time).total_seconds()
        
        # Format as MM:SS or HH:MM:SS
        if delta < 3600:  # Less than an hour
            minutes = int(delta // 60)
            seconds = int(delta % 60)
            return f"{minutes:02d}:{seconds:02d}"
        else:
            hours = int(delta // 3600)
            minutes = int((delta % 3600) // 60)
            seconds = int(delta % 60)
            return f"{hours:02d}:{minutes:02d}:{seconds:02d}"
    

    app.jinja_env.globals['format_duration'] = format_duration
    return app

    

from app import models

def format_time(value, format='%H:%M:%S'):
        """Format datetime or time string"""
        if value is None:
            return ""
        if isinstance(value, str):
            try:
                value = datetime.fromisoformat(value)
            except ValueError:
                return value
        return value.strftime(format)


