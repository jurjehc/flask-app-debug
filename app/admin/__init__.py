from flask import Blueprint

bp = Blueprint('admin_panel', __name__)  # Changed from 'admin' to 'admin_panel'

from app.admin import routes