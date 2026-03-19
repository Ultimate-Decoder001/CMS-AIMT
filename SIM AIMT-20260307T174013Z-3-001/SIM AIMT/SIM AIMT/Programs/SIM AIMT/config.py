import os
from datetime import timedelta

class Config:
    """Base configuration class."""
    SECRET_KEY = os.environ.get('SECRET_KEY') or 'aimt-college-secret-key-2024'
    SQLALCHEMY_DATABASE_URI = 'sqlite:///aimt_college.db'
    SQLALCHEMY_TRACK_MODIFICATIONS = False
    SESSION_COOKIE_SECURE = False
    SESSION_COOKIE_HTTPONLY = True
    SESSION_PERMANENT = False
    PERMANENT_SESSION_LIFETIME = timedelta(hours=24)
    UPLOAD_FOLDER = 'static/uploads'
    MAX_CONTENT_LENGTH = 16 * 1024 * 1024  # 16MB max file size

class DevelopmentConfig(Config):
    """Development configuration."""
    DEBUG = True
    SQLALCHEMY_ECHO = True

class ProductionConfig(Config):
    """Production configuration."""
    DEBUG = False
    SQLALCHEMY_ECHO = False

class TestingConfig(Config):
    """Testing configuration."""
    TESTING = True
    SQLALCHEMY_DATABASE_URI = 'sqlite:///:memory:'

# Configuration dictionary
config = {
    'development': DevelopmentConfig,
    'production': ProductionConfig,
    'testing': TestingConfig,
    'default': DevelopmentConfig
}

# Application roles
# Expanded to match Registrar / Director / Dean / HOD / Faculty / Student / Accountant etc.
ROLES = [
    'Registrar',        # super‑user control
    'Director',         # academic overview and approvals
    'Dean',             # faculty dean, academic management
    'HOD',              # department head
    'Faculty',          # teaching staff
    'Student',          # student users
    'Accountant',       # financial staff
    'HR',
    'Library',
    'Management',       # legacy / combined management role
    'Non-Teaching'      # other staff
]

# Leave types
LEAVE_TYPES = [
    'Casual Leave',
    'Sick Leave',
    'Earned Leave',
    'Maternity Leave',
    'Paternity Leave',
    'Unpaid Leave'
]

# Attendance status
ATTENDANCE_STATUS = [
    'Present',
    'Absent',
    'Late',
    'Half Day'
]

# Payment status
PAYMENT_STATUS = [
    'Pending',
    'Processed',
    'Failed',
    'Cancelled'
]

# Optional SMTP settings (fill for email notifications)
MAIL_SERVER = None
MAIL_PORT = None
MAIL_USERNAME = None
MAIL_PASSWORD = None
MAIL_USE_TLS = False
