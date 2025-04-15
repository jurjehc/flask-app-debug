from flask_sqlalchemy import SQLAlchemy
from flask_migrate import Migrate
from flask_login import LoginManager
from flask_mail import Mail
from flask_admin import Admin

db = SQLAlchemy()
migrate = Migrate()
login = LoginManager()
mail = Mail()
admin = Admin(template_mode='bootstrap4')

# Configure login
login.login_view = 'auth.login'
login.login_message = 'Please log in to access this page.'
login.login_message_category = 'info'