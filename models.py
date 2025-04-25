from app import db
from flask_login import UserMixin
from datetime import datetime
from sqlalchemy import text
from werkzeug.security import generate_password_hash, check_password_hash
import enum
import json

class Role(db.Model):
    """User roles in the system"""
    id = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.String(50), unique=True, nullable=False)
    description = db.Column(db.String(255))
    
    users = db.relationship('User', backref='role', lazy='dynamic')

class Organization(db.Model):
    """Organizations in the system (Vinatex and its subsidiaries)"""
    id = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.String(255), nullable=False)
    name_en = db.Column(db.String(255))  # English name
    code = db.Column(db.String(20), unique=True, nullable=False)
    description = db.Column(db.Text)
    parent_id = db.Column(db.Integer, db.ForeignKey('organization.id'))
    is_active = db.Column(db.Boolean, default=True)
    created_at = db.Column(db.DateTime, default=datetime.utcnow)
    
    # Self-referential relationship
    children = db.relationship('Organization', backref=db.backref('parent', remote_side=[id]))
    users = db.relationship('User', backref='organization', lazy='dynamic')
    report_assignments = db.relationship('ReportAssignment', backref='organization', lazy='dynamic')

class User(UserMixin, db.Model):
    """Users of the system"""
    id = db.Column(db.Integer, primary_key=True)
    username = db.Column(db.String(64), unique=True, nullable=False)
    email = db.Column(db.String(120), unique=True, nullable=False)
    password_hash = db.Column(db.String(256), nullable=False)
    fullname = db.Column(db.String(255))
    role_id = db.Column(db.Integer, db.ForeignKey('role.id'), nullable=False)
    organization_id = db.Column(db.Integer, db.ForeignKey('organization.id'), nullable=False)
    language = db.Column(db.String(5), default='vi')  # Default language
    is_active = db.Column(db.Boolean, default=True)
    last_login = db.Column(db.DateTime)
    created_at = db.Column(db.DateTime, default=datetime.utcnow)
    
    report_templates = db.relationship('ReportTemplate', backref='created_by_user', lazy='dynamic')
    report_submissions = db.relationship('ReportSubmission', backref='submitted_by_user', lazy='dynamic')
    
    def set_password(self, password):
        self.password_hash = generate_password_hash(password)
    
    def check_password(self, password):
        return check_password_hash(self.password_hash, password)
    
    def is_admin(self):
        return self.role.name == 'admin'
    
    def is_department(self):
        return self.role.name == 'department'
    
    def is_unit(self):
        return self.role.name == 'unit'

class ReportTemplate(db.Model):
    """Report templates that can be assigned to organizations"""
    id = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.String(255), nullable=False)
    name_en = db.Column(db.String(255))  # English name
    description = db.Column(db.Text)
    created_by = db.Column(db.Integer, db.ForeignKey('user.id'), nullable=False)
    is_active = db.Column(db.Boolean, default=True)
    created_at = db.Column(db.DateTime, default=datetime.utcnow)
    updated_at = db.Column(db.DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)
    
    # JSON field to store template structure
    structure = db.Column(db.Text, nullable=False)
    
    report_assignments = db.relationship('ReportAssignment', backref='report_template', lazy='dynamic')
    
    def get_structure(self):
        return json.loads(self.structure)
    
    def set_structure(self, structure_dict):
        self.structure = json.dumps(structure_dict)

class ReportStatus(enum.Enum):
    """Status of a report assignment"""
    PENDING = 'pending'
    SUBMITTED = 'submitted'
    REJECTED = 'rejected'
    APPROVED = 'approved'
    OVERDUE = 'overdue'

class ReportFrequency(enum.Enum):
    """Frequency of report submissions"""
    DAILY = 'daily'
    WEEKLY = 'weekly'
    MONTHLY = 'monthly'
    QUARTERLY = 'quarterly'
    SEMI_ANNUALLY = 'semi_annually'
    ANNUALLY = 'annually'
    ONE_TIME = 'one_time'

class ReportAssignment(db.Model):
    """Assignment of report templates to organizations"""
    id = db.Column(db.Integer, primary_key=True)
    report_template_id = db.Column(db.Integer, db.ForeignKey('report_template.id'), nullable=False)
    organization_id = db.Column(db.Integer, db.ForeignKey('organization.id'), nullable=False)
    due_date = db.Column(db.DateTime, nullable=False)
    frequency = db.Column(db.Enum(ReportFrequency), default=ReportFrequency.MONTHLY)
    status = db.Column(db.Enum(ReportStatus), default=ReportStatus.PENDING)
    created_at = db.Column(db.DateTime, default=datetime.utcnow)
    
    report_submissions = db.relationship('ReportSubmission', backref='report_assignment', lazy='dynamic')

class ReportSubmission(db.Model):
    """Submissions for report assignments"""
    id = db.Column(db.Integer, primary_key=True)
    report_assignment_id = db.Column(db.Integer, db.ForeignKey('report_assignment.id'), nullable=False)
    submitted_by = db.Column(db.Integer, db.ForeignKey('user.id'), nullable=False)
    submitted_at = db.Column(db.DateTime, default=datetime.utcnow)
    sharepoint_path = db.Column(db.String(512))
    filename = db.Column(db.String(255))
    notes = db.Column(db.Text)
    
    # JSON field to store form data
    form_data = db.Column(db.Text)

class Settings(db.Model):
    """System settings"""
    id = db.Column(db.Integer, primary_key=True)
    key = db.Column(db.String(255), unique=True, nullable=False)
    value = db.Column(db.Text)
    description = db.Column(db.Text)
    updated_at = db.Column(db.DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)

class EmailLog(db.Model):
    """Log of emails sent by the system"""
    id = db.Column(db.Integer, primary_key=True)
    to_address = db.Column(db.String(255), nullable=False)
    subject = db.Column(db.String(255), nullable=False)
    body = db.Column(db.Text)
    sent_at = db.Column(db.DateTime, default=datetime.utcnow)
    status = db.Column(db.String(50))  # success, failed
    error_message = db.Column(db.Text)

class AuditLog(db.Model):
    """Log of actions performed in the system"""
    id = db.Column(db.Integer, primary_key=True)
    user_id = db.Column(db.Integer, db.ForeignKey('user.id'))
    action = db.Column(db.String(255), nullable=False)
    details = db.Column(db.Text)
    ip_address = db.Column(db.String(45))
    timestamp = db.Column(db.DateTime, default=datetime.utcnow)
    
    user = db.relationship('User', backref='audit_logs')
