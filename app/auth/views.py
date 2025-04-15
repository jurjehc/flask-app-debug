from flask import redirect, url_for
from flask_admin.contrib.sqla import ModelView
from flask_admin import AdminIndexView
from flask_login import current_user

class SecureModelView(ModelView):
    def is_accessible(self):
        return current_user.is_authenticated and current_user.is_admin

    def inaccessible_callback(self, name, **kwargs):
        return redirect(url_for('auth.login'))

class MyAdminIndexView(AdminIndexView):
    def is_accessible(self):
        return current_user.is_authenticated and current_user.is_admin

    def inaccessible_callback(self, name, **kwargs):
        return redirect(url_for('auth.login'))

class RaceModelView(SecureModelView):
    column_list = ['name', 'date', 'location', 'status', 'admin']
    column_searchable_list = ['name', 'location']
    column_filters = ['status', 'date', 'admin']
    form_excluded_columns = ['results', 'created_at', 'updated_at']
    
    def on_model_change(self, form, model, is_created):
        if is_created and not model.admin_id:
            model.admin_id = current_user.id

class RunnerModelView(SecureModelView):
    column_list = ['first_name', 'last_name', 'email', 'gender', 'club']
    column_searchable_list = ['first_name', 'last_name', 'email', 'club']
    column_filters = ['gender', 'club']
    form_excluded_columns = ['results', 'created_at']

class UserModelView(SecureModelView):
    column_list = ['username', 'email', 'is_admin', 'is_super_admin']
    column_searchable_list = ['username', 'email']
    column_filters = ['is_admin', 'is_super_admin']
    form_excluded_columns = ['password_hash']
    
    def is_accessible(self):
        return current_user.is_authenticated and current_user.is_super_admin