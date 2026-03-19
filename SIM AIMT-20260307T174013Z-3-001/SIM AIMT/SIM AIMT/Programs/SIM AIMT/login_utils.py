"""
Student Login Utilities Module
Provides helper functions for authentication and student validation
"""

from flask import app, current_app
from werkzeug.security import check_password_hash, generate_password_hash
from models import User, Student, db
from sqlalchemy import func
import logging

logger = logging.getLogger(__name__)


def validate_student_credentials(roll_number, password):
    """
    Validate student login credentials using roll number.
    
    Args:
        roll_number (str): Student roll number
        password (str): Student password
    
    Returns:
        dict: {
            'success': bool,
            'user': User object or None,
            'student': Student object or None,
            'message': str,
            'error_code': str
        }
    """
    try:
        # Normalize input
        roll_number = roll_number.strip().upper() if roll_number else ''
        
        # Validate input
        if not roll_number:
            return {
                'success': False,
                'user': None,
                'student': None,
                'message': 'Roll number is required.',
                'error_code': 'MISSING_ROLL_NUMBER'
            }
        
        if not password:
            return {
                'success': False,
                'user': None,
                'student': None,
                'message': 'Password is required.',
                'error_code': 'MISSING_PASSWORD'
            }
        
        # Find student by roll number
        student = db.session.query(Student).filter_by(
            roll_number=roll_number
        ).first()
        
        if not student:
            logger.warning(f"Student login attempt - roll number not found: {roll_number}")
            return {
                'success': False,
                'user': None,
                'student': None,
                'message': f'Student with roll number {roll_number} not found.',
                'error_code': 'INVALID_ROLL_NUMBER'
            }
        
        # Check if student has linked user account
        if not student.user_id:
            logger.error(f"Student {student_id} has no linked user account")
            return {
                'success': False,
                'user': None,
                'student': student,
                'message': 'Your account is not properly set up.',
                'error_code': 'NO_USER_ACCOUNT'
            }
        
        # Get linked user
        user = db.session.get(User, student.user_id)
        
        if not user:
            logger.error(f"User account not found for student id: {student_id}")
            return {
                'success': False,
                'user': None,
                'student': student,
                'message': 'User account not found.',
                'error_code': 'USER_NOT_FOUND'
            }
        
        # Verify password
        if not check_password_hash(user.password, password):
            logger.warning(f"Failed student login attempt: {student_id}")
            return {
                'success': False,
                'user': user,
                'student': student,
                'message': 'Invalid password.',
                'error_code': 'INVALID_PASSWORD'
            }
        
        # Check if account is active
        if not user.is_active:
            logger.warning(f"Login attempt on inactive student account: {student_id}")
            return {
                'success': False,
                'user': user,
                'student': student,
                'message': 'Your account has been deactivated.',
                'error_code': 'ACCOUNT_INACTIVE'
            }
        
        # Check enrollment status
        warnings = []
        if not student.semester or not student.course:
            warnings.append('Your enrollment details are incomplete.')
        
        # Success
        logger.info(f"Student authentication successful: {student.roll_number}")
        return {
            'success': True,
            'user': user,
            'student': student,
            'message': f'Welcome, {student.name}!',
            'error_code': None,
            'warnings': warnings
        }
    
    except Exception as e:
        logger.error(f"Error validating student credentials: {str(e)}", exc_info=True)
        return {
            'success': False,
            'user': None,
            'student': None,
            'message': 'An error occurred during authentication.',
            'error_code': 'INTERNAL_ERROR'
        }


def validate_user_credentials(employee_id, password):
    """
    Validate user login credentials (all roles).
    
    Args:
        employee_id (str): User employee ID
        password (str): User password
    
    Returns:
        dict: Authentication result
    """
    try:
        # Normalize input
        employee_id = employee_id.strip() if employee_id else ''
        
        if not employee_id:
            return {
                'success': False,
                'user': None,
                'message': 'Employee ID is required.',
                'error_code': 'MISSING_EMPLOYEE_ID'
            }
        
        if not password:
            return {
                'success': False,
                'user': None,
                'message': 'Password is required.',
                'error_code': 'MISSING_PASSWORD'
            }
        
        # Try direct lookup first
        user = db.session.get(User, employee_id)
        
        # Try case-insensitive lookup
        if not user:
            user = db.session.query(User).filter(
                func.lower(User.employee_id) == employee_id.lower()
            ).first()
        
        if not user:
            logger.warning(f"Login attempt - employee ID not found: {employee_id}")
            return {
                'success': False,
                'user': None,
                'message': 'Invalid employee ID or password.',
                'error_code': 'INVALID_CREDENTIALS'
            }
        
        # Verify password
        if not check_password_hash(user.password, password):
            logger.warning(f"Failed login attempt: {employee_id}")
            return {
                'success': False,
                'user': user,
                'message': 'Invalid employee ID or password.',
                'error_code': 'INVALID_PASSWORD'
            }
        
        # Check if account is active
        if not user.is_active:
            logger.warning(f"Login attempt on inactive account: {employee_id}")
            return {
                'success': False,
                'user': user,
                'message': 'Your account has been deactivated.',
                'error_code': 'ACCOUNT_INACTIVE'
            }
        
        logger.info(f"Successful login: {employee_id} ({user.role})")
        return {
            'success': True,
            'user': user,
            'message': f'Welcome, {user.name}!',
            'error_code': None
        }
    
    except Exception as e:
        logger.error(f"Error validating user credentials: {str(e)}", exc_info=True)
        return {
            'success': False,
            'user': None,
            'message': 'An error occurred during authentication.',
            'error_code': 'INTERNAL_ERROR'
        }


def check_password_change_required(user):
    """
    Check if user must change password.
    
    Args:
        user (User): User object
    
    Returns:
        bool: True if password change is required
    """
    return getattr(user, 'must_change_password', False)


def reset_student_password(roll_number, new_password):
    """
    Reset student password (for admin use).
    
    Args:
        roll_number (str): Student roll number
        new_password (str): New password
    
    Returns:
        dict: Success status
    """
    try:
        student = db.session.query(Student).filter_by(
            roll_number=roll_number
        ).first()
        
        if not student or not student.user_id:
            return {'success': False, 'message': 'Student not found.'}
        
        user = db.session.get(User, student.user_id)
        if not user:
            return {'success': False, 'message': 'User account not found.'}
        
        # Hash and set new password
        user.password = generate_password_hash(new_password)
        user.must_change_password = True
        
        db.session.commit()
        logger.info(f"Password reset for student: {roll_number}")
        
        return {
            'success': True,
            'message': f'Password reset for {student.name}. They must change it on next login.'
        }
    
    except Exception as e:
        db.session.rollback()
        logger.error(f"Error resetting password for {roll_number}: {str(e)}")
        return {'success': False, 'message': 'Error resetting password.'}


def get_student_login_history(roll_number, limit=10):
    """
    Get recent login history for a student (if tracking is implemented).
    
    Args:
        roll_number (str): Student roll number
        limit (int): Number of records to retrieve
    
    Returns:
        list: Login history records
    """
    # This would require a LoginHistory model
    # Placeholder for future implementation
    return []


def validate_student_enrollment(student_id):
    """
    Validate student has complete enrollment information.
    
    Args:
        student_id (int): Student ID
    
    Returns:
        dict: Validation result with missing fields
    """
    student = db.session.query(Student).get(student_id)
    
    if not student:
        return {'valid': False, 'missing_fields': ['Student record']}
    
    missing_fields = []
    
    if not student.semester:
        missing_fields.append('Semester')
    if not student.course:
        missing_fields.append('Course')
    if not student.department:
        missing_fields.append('Department')
    if not student.email:
        missing_fields.append('Email')
    # phone is no longer required by policy
    
    return {
        'valid': len(missing_fields) == 0,
        'missing_fields': missing_fields,
        'student': student
    }
