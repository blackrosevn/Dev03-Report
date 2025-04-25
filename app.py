import os
import logging
from datetime import datetime
from flask import Flask, request, session, g
from flask_sqlalchemy import SQLAlchemy
from sqlalchemy.orm import DeclarativeBase
from flask_login import LoginManager
from flask_babel import Babel
from werkzeug.middleware.proxy_fix import ProxyFix

logging.basicConfig(level=logging.DEBUG)

class Base(DeclarativeBase):
    pass

db = SQLAlchemy(model_class=Base)

# Create the Flask application
app = Flask(__name__)
app.secret_key = os.environ.get("SESSION_SECRET", "vinatex-report-portal-secret")
app.wsgi_app = ProxyFix(app.wsgi_app, x_proto=1, x_host=1)

# Configure the database
app.config["SQLALCHEMY_DATABASE_URI"] = os.environ.get("DATABASE_URL", "sqlite:///vinatex.db")
app.config["SQLALCHEMY_ENGINE_OPTIONS"] = {
    "pool_recycle": 300,
    "pool_pre_ping": True,
}
app.config["SQLALCHEMY_TRACK_MODIFICATIONS"] = False

# Initialize the database
db.init_app(app)

# Configure login manager
login_manager = LoginManager()
login_manager.init_app(app)
login_manager.login_view = 'login'
login_manager.login_message = 'Please log in to access this page.'

# Configure babel for internationalization
babel = Babel(app)

# Define locale selector function
def get_locale():
    # If a user is logged in, use their preferred language
    if 'language' in session:
        return session['language']
    # Otherwise try to detect the language from the request
    return request.accept_languages.best_match(['en', 'vi'])

# Register the locale selector with Babel
babel.locale_selector_func = get_locale

# Import models here to avoid circular imports
with app.app_context():
    import models
    db.create_all()

    # Add first admin user if no users exist
    from models import User, Role, Organization
    if not User.query.first():
        # Create roles if they don't exist
        admin_role = Role.query.filter_by(name="admin").first()
        if not admin_role:
            admin_role = Role(name="admin", description="Administrator")
            db.session.add(admin_role)

        department_role = Role.query.filter_by(name="department").first()
        if not department_role:
            department_role = Role(name="department", description="Ban chức năng")
            db.session.add(department_role)

        unit_role = Role.query.filter_by(name="unit").first()
        if not unit_role:
            unit_role = Role(name="unit", description="Đơn vị thành viên")
            db.session.add(unit_role)
        
        # Create Vinatex organization if it doesn't exist
        vinatex = Organization.query.filter_by(code="VINATEX").first()
        if not vinatex:
            vinatex = Organization(
                name="Tập đoàn Dệt May Việt Nam",
                name_en="Vietnam National Textile and Garment Group",
                code="VINATEX",
                description="Tập đoàn Dệt May Việt Nam",
                is_active=True,
                parent_id=None
            )
            db.session.add(vinatex)
            
        db.session.commit()
        
        # Create default admin user
        from utils import create_user
        create_user(
            username="admin",
            email="admin@vinatex.com.vn",
            password="admin",
            fullname="Administrator",
            role_id=admin_role.id,
            organization_id=vinatex.id
        )
        
        # Create sample departments and units
        from config import SAMPLE_ORGANIZATIONS
        for org in SAMPLE_ORGANIZATIONS:
            parent_id = vinatex.id if org['parent'] == 'VINATEX' else None
            new_org = Organization(
                name=org['name'],
                name_en=org.get('name_en', ''),
                code=org['code'],
                description=org.get('description', ''),
                is_active=True,
                parent_id=parent_id
            )
            db.session.add(new_org)
        db.session.commit()
        
        # Create sample users
        from config import SAMPLE_USERS
        for user in SAMPLE_USERS:
            role_name = user['role']
            role = Role.query.filter_by(name=role_name).first()
            org = Organization.query.filter_by(code=user['organization']).first()
            
            if role and org:
                create_user(
                    username=user['username'],
                    email=user['email'],
                    password=user['password'],
                    fullname=user['fullname'],
                    role_id=role.id,
                    organization_id=org.id
                )
        
        # Write account info to file
        with open('accounts.txt', 'w') as f:
            f.write("Vinatex Report Portal - Account Information\n")
            f.write("===========================================\n\n")
            for user in User.query.all():
                role = Role.query.get(user.role_id)
                org = Organization.query.get(user.organization_id)
                f.write(f"Username: {user.username}\n")
                f.write(f"Password: {user.username}  # Same as username for initial setup\n")
                f.write(f"Email: {user.email}\n")
                f.write(f"Role: {role.name}\n")
                f.write(f"Organization: {org.name}\n")
                f.write("-------------------------------------------\n")
                
        # Write organization info to file
        with open('Organizations.txt', 'w') as f:
            f.write("Vinatex Report Portal - Organizations\n")
            f.write("====================================\n\n")
            for org in Organization.query.all():
                parent = Organization.query.get(org.parent_id) if org.parent_id else None
                f.write(f"Name: {org.name}\n")
                f.write(f"English Name: {org.name_en}\n")
                f.write(f"Code: {org.code}\n")
                f.write(f"Parent: {parent.name if parent else 'None'}\n")
                f.write(f"Description: {org.description}\n")
                f.write("-------------------------------------------\n")

@login_manager.user_loader
def load_user(user_id):
    from models import User
    return User.query.get(int(user_id))

@app.before_request
def before_request():
    g.current_time = datetime.now()
