from app import db
from werkzeug.security import generate_password_hash
from models import User, AuditLog, EmailLog
import smtplib
from email.mime.text import MIMEText
from email.mime.multipart import MIMEMultipart
import json
import pandas as pd
import os
from datetime import datetime

def create_user(username, email, password, fullname, role_id, organization_id):
    """Create a new user and add to database"""
    user = User(
        username=username,
        email=email,
        fullname=fullname,
        role_id=role_id,
        organization_id=organization_id,
        is_active=True
    )
    user.set_password(password)
    db.session.add(user)
    db.session.commit()
    return user

def log_action(user_id, action, details, ip_address=None):
    """Log an action in the audit log"""
    log = AuditLog(
        user_id=user_id,
        action=action,
        details=details,
        ip_address=ip_address
    )
    db.session.add(log)
    db.session.commit()
    return log

def send_email(to_address, subject, body):
    """Send an email"""
    from app import app
    from models import Settings
    
    # Get email settings
    with app.app_context():
        smtp_server = Settings.query.filter_by(key='smtp_server').first()
        smtp_port = Settings.query.filter_by(key='smtp_port').first()
        smtp_username = Settings.query.filter_by(key='smtp_username').first()
        smtp_password = Settings.query.filter_by(key='smtp_password').first()
    
    # Use settings or defaults
    smtp_server = smtp_server.value if smtp_server else 'smtp.office365.com'
    smtp_port = int(smtp_port.value) if smtp_port else 587
    smtp_username = smtp_username.value if smtp_username else 'reports@vinatex.com.vn'
    smtp_password = smtp_password.value if smtp_password else ''
    
    # Create message
    msg = MIMEMultipart()
    msg['From'] = smtp_username
    msg['To'] = to_address
    msg['Subject'] = subject
    
    msg.attach(MIMEText(body, 'plain'))
    
    # Log the attempt
    email_log = EmailLog(
        to_address=to_address,
        subject=subject,
        body=body,
        status='pending'
    )
    db.session.add(email_log)
    db.session.commit()
    
    try:
        # Connect to the server
        server = smtplib.SMTP(smtp_server, smtp_port)
        server.starttls()
        
        # Login if credentials are provided
        if smtp_username and smtp_password:
            server.login(smtp_username, smtp_password)
        
        # Send email
        server.send_message(msg)
        server.quit()
        
        # Update log
        email_log.status = 'success'
        db.session.commit()
        return True
    except Exception as e:
        # Log error
        email_log.status = 'failed'
        email_log.error_message = str(e)
        db.session.commit()
        return False

def save_excel_file(file, directory):
    """Save an uploaded Excel file"""
    if not os.path.exists(directory):
        os.makedirs(directory, exist_ok=True)
    
    filename = f"{datetime.now().strftime('%Y%m%d%H%M%S')}.xlsx"
    filepath = os.path.join(directory, filename)
    file.save(filepath)
    return filepath, filename

def generate_excel(form_data, template_structure, filepath):
    """Generate an Excel file from form data based on the template structure"""
    # Create a new Excel writer
    writer = pd.ExcelWriter(filepath, engine='openpyxl')
    
    # Process each sheet in the template
    for sheet in template_structure['sheets']:
        sheet_name = sheet['name']
        
        # Create DataFrame with columns from the sheet's fields
        columns = [field['name'] for field in sheet['fields']]
        labels = [field['label'] for field in sheet['fields']]
        
        # Create data for this sheet from form_data
        data = {}
        for field in sheet['fields']:
            field_name = field['name']
            if field_name in form_data:
                data[field_name] = [form_data[field_name]]
            else:
                data[field_name] = ['']
        
        # Create DataFrame
        df = pd.DataFrame(data)
        
        # Rename columns to use labels
        column_mapping = {field['name']: field['label'] for field in sheet['fields']}
        df = df.rename(columns=column_mapping)
        
        # Write to Excel
        df.to_excel(writer, sheet_name=sheet_name, index=False)
    
    # Save the Excel file
    writer.save()
    return filepath
