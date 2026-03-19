from flask import Flask, render_template, redirect, url_for, request, flash, jsonify, session
from flask_sqlalchemy import SQLAlchemy
from flask_migrate import Migrate
from flask_login import LoginManager, UserMixin, login_user, login_required, logout_user, current_user
from werkzeug.security import generate_password_hash, check_password_hash
from datetime import datetime, date, timedelta
from functools import wraps
import os
import uuid
from sqlalchemy import ForeignKey, event, func, text
from sqlalchemy.orm import relationship, Session


def generate_book_code():
    """Generate a short unique book code."""
    # Use UUID4-based string and check for collisions
    for _ in range(5):
        code = f"BK{uuid.uuid4().hex[:8].upper()}"
        if not db.session.query(Book).filter_by(book_code=code).first():
            return code
    return f"BK{uuid.uuid4().hex[:8].upper()}"

# Initialize Flask app
app = Flask(__name__)
app.config.from_object('config.DevelopmentConfig')

# Initialize extensions
db = SQLAlchemy(app)
migrate = Migrate(app, db)
login_manager = LoginManager()
login_manager.init_app(app)
login_manager.login_view = 'login'

# ==================== DATABASE MODELS ====================

class User(UserMixin, db.Model):
    """User model for authentication with proper relationships."""
    __tablename__ = 'users'
    
    employee_id = db.Column(db.String(20), primary_key=True)
    password = db.Column(db.String(200), nullable=False)
    role = db.Column(db.String(50), nullable=False)
    name = db.Column(db.String(100), nullable=False)
    email = db.Column(db.String(100), unique=True, nullable=False)
    phone = db.Column(db.String(20))
    department = db.Column(db.String(100))
    designation = db.Column(db.String(100))
    assigned_course = db.Column(db.String(50))
    assigned_semester = db.Column(db.Integer)
    is_active = db.Column(db.Boolean, default=True)
    must_change_password = db.Column(db.Boolean, default=False)
    created_at = db.Column(db.DateTime, default=datetime.utcnow)
    
    # Relationships
    leaves_applied = relationship('Leave', foreign_keys='Leave.employee_id', 
                                 backref='applicant', cascade='all, delete-orphan')
    leaves_forwarded = relationship('Leave', foreign_keys='Leave.forwarded_by',
                                   backref='forwarded_by_user')
    leaves_approved = relationship('Leave', foreign_keys='Leave.approved_by',
                                  backref='approved_by_user')
    attendance_records = relationship('Attendance', foreign_keys='Attendance.employee_id',
                                     backref='employee', cascade='all, delete-orphan')
    attendance_marked = relationship('Attendance', foreign_keys='Attendance.marked_by',
                                    backref='marked_by_user')
    book_transactions = relationship('BookTransaction', backref='employee', cascade='all, delete-orphan')
    salaries = relationship('Salary', backref='employee', cascade='all, delete-orphan')
    expenses_submitted = relationship('Expense', foreign_keys='Expense.submitted_by',
                                     backref='submitted_by_user')
    expenses_approved = relationship('Expense', foreign_keys='Expense.approved_by',
                                    backref='approved_by_user')
    grades_marked = relationship('Grade', backref='marked_by_user')
    student_attendance_marked = relationship('StudentAttendance', backref='marked_by_user')
    linked_student = relationship('Student', uselist=False, backref='user_account')
    notifications = relationship('Notification', backref='user', cascade='all, delete-orphan')
    
    def __repr__(self):
        return f'<User {self.employee_id} - {self.name} ({self.role})>'
    
    def get_id(self):
        return str(self.employee_id)


class Leave(db.Model):
    """Leave management model with proper relationships."""
    __tablename__ = 'leaves'
    
    id = db.Column(db.Integer, primary_key=True)
    employee_id = db.Column(db.String(20), ForeignKey('users.employee_id', ondelete='CASCADE'), nullable=False)
    leave_type = db.Column(db.String(50), nullable=False)
    start_date = db.Column(db.Date, nullable=False)
    end_date = db.Column(db.Date, nullable=False)
    reason = db.Column(db.Text)
    department = db.Column(db.String(100))
    status = db.Column(db.String(20), default='Pending')
    forwarded_by = db.Column(db.String(20), ForeignKey('users.employee_id', ondelete='SET NULL'))
    approved_by = db.Column(db.String(20), ForeignKey('users.employee_id', ondelete='SET NULL'))
    created_at = db.Column(db.DateTime, default=datetime.utcnow)
    
    def __repr__(self):
        return f'<Leave {self.id} - {self.employee_id} ({self.status})>'


class Attendance(db.Model):
    """Attendance tracking model with proper relationships."""
    __tablename__ = 'attendance'
    
    id = db.Column(db.Integer, primary_key=True)
    employee_id = db.Column(db.String(20), ForeignKey('users.employee_id', ondelete='CASCADE'), nullable=False)
    date = db.Column(db.Date, nullable=False)
    status = db.Column(db.String(20), nullable=False)
    marked_by = db.Column(db.String(20), ForeignKey('users.employee_id', ondelete='SET NULL'))
    remarks = db.Column(db.Text)
    created_at = db.Column(db.DateTime, default=datetime.utcnow)
    
    def __repr__(self):
        return f'<Attendance {self.id} - {self.employee_id} ({self.date})>'


class Book(db.Model):
    """Library books model with relationship to transactions."""
    __tablename__ = 'books'
    
    book_id = db.Column(db.Integer, primary_key=True)
    book_code = db.Column(db.String(20), unique=True, nullable=False)
    title = db.Column(db.String(200), nullable=False)
    author = db.Column(db.String(100))
    edition = db.Column(db.String(50))
    isbn = db.Column(db.String(20), unique=True)
    category = db.Column(db.String(50))
    quantity = db.Column(db.Integer, default=1)
    available_quantity = db.Column(db.Integer, default=1)
    shelf_location = db.Column(db.String(50))
    created_at = db.Column(db.DateTime, default=datetime.utcnow)
    
    # Relationships
    transactions = relationship('BookTransaction', backref='book', cascade='all, delete-orphan')
    
    def __repr__(self):
        return f'<Book {self.book_id} - {self.title}>'


class BookTransaction(db.Model):
    """Library book issue/return transactions with proper relationships."""
    __tablename__ = 'book_transactions'
    
    id = db.Column(db.Integer, primary_key=True)
    book_id = db.Column(db.Integer, ForeignKey('books.book_id', ondelete='CASCADE'), nullable=False)
    employee_id = db.Column(db.String(20), ForeignKey('users.employee_id', ondelete='CASCADE'), nullable=False)
    issue_date = db.Column(db.Date, nullable=False)
    due_date = db.Column(db.Date, nullable=False)
    return_date = db.Column(db.Date)
    status = db.Column(db.String(20), default='Issued')
    
    def __repr__(self):
        return f'<BookTransaction {self.id} - Book {self.book_id} to {self.employee_id}>'


class Salary(db.Model):
    """Salary management model with relationship to User."""
    __tablename__ = 'salaries'
    
    id = db.Column(db.Integer, primary_key=True)
    employee_id = db.Column(db.String(20), ForeignKey('users.employee_id', ondelete='CASCADE'), nullable=False)
    month = db.Column(db.Integer, nullable=False)
    year = db.Column(db.Integer, nullable=False)
    basic_salary = db.Column(db.Float, default=0)
    hra = db.Column(db.Float, default=0)
    da = db.Column(db.Float, default=0)
    allowances = db.Column(db.Float, default=0)
    deductions = db.Column(db.Float, default=0)
    net_salary = db.Column(db.Float, default=0)
    payment_status = db.Column(db.String(20), default='Pending')
    payment_date = db.Column(db.Date)
    created_at = db.Column(db.DateTime, default=datetime.utcnow)
    
    def __repr__(self):
        return f'<Salary {self.id} - {self.employee_id} ({self.month}/{self.year})>'


class Expense(db.Model):
    """Expense tracking model with proper relationships."""
    __tablename__ = 'expenses'
    
    id = db.Column(db.Integer, primary_key=True)
    category = db.Column(db.String(50), nullable=False)
    description = db.Column(db.Text)
    amount = db.Column(db.Float, nullable=False)
    date = db.Column(db.Date, nullable=False)
    submitted_by = db.Column(db.String(20), ForeignKey('users.employee_id', ondelete='SET NULL'))
    approved_by = db.Column(db.String(20), ForeignKey('users.employee_id', ondelete='SET NULL'))
    status = db.Column(db.String(20), default='Pending')
    created_at = db.Column(db.DateTime, default=datetime.utcnow)
    
    def __repr__(self):
        return f'<Expense {self.id} - {self.category} (₹{self.amount})>'


class Student(db.Model):
    """Student model with proper relationships."""
    __tablename__ = 'students'
    
    id = db.Column(db.Integer, primary_key=True)
    roll_number = db.Column(db.String(20), unique=True, nullable=False)
    name = db.Column(db.String(100), nullable=False)
    first_name = db.Column(db.String(50))
    last_name = db.Column(db.String(50))
    father_name = db.Column(db.String(100))
    email = db.Column(db.String(100))
    phone = db.Column(db.String(20))
    course = db.Column(db.String(50))
    semester = db.Column(db.Integer)
    department = db.Column(db.String(100))
    user_id = db.Column(db.String(20), ForeignKey('users.employee_id', ondelete='SET NULL'), unique=True)
    created_at = db.Column(db.DateTime, default=datetime.utcnow)
    
    # Relationships
    attendance_records = relationship('StudentAttendance', backref='student', cascade='all, delete-orphan')
    grades = relationship('Grade', backref='student', cascade='all, delete-orphan')
    
    def __repr__(self):
        return f'<Student {self.roll_number} - {self.name}>'


class StudentAttendance(db.Model):
    """Student attendance model with proper relationships."""
    __tablename__ = 'student_attendance'
    
    id = db.Column(db.Integer, primary_key=True)
    student_id = db.Column(db.Integer, ForeignKey('students.id', ondelete='CASCADE'), nullable=False)
    date = db.Column(db.Date, nullable=False)
    status = db.Column(db.String(20), nullable=False)
    marked_by = db.Column(db.String(20), ForeignKey('users.employee_id', ondelete='SET NULL'))
    subject = db.Column(db.String(50))
    created_at = db.Column(db.DateTime, default=datetime.utcnow)
    
    def __repr__(self):
        return f'<StudentAttendance {self.id} - Student {self.student_id} ({self.date})>'


class Grade(db.Model):
    """Student grades model with proper relationships."""
    __tablename__ = 'grades'
    
    id = db.Column(db.Integer, primary_key=True)
    student_id = db.Column(db.Integer, ForeignKey('students.id', ondelete='CASCADE'), nullable=False)
    subject = db.Column(db.String(50), nullable=False)
    marks = db.Column(db.Float, nullable=False)
    max_marks = db.Column(db.Float, default=100)
    grade = db.Column(db.String(5))
    semester = db.Column(db.Integer)
    exam_type = db.Column(db.String(50))
    remarks = db.Column(db.Text)
    marked_by = db.Column(db.String(20), ForeignKey('users.employee_id', ondelete='SET NULL'))
    created_at = db.Column(db.DateTime, default=datetime.utcnow)
    
    def __repr__(self):
        return f'<Grade {self.id} - Student {self.student_id} ({self.subject}): {self.marks}/{self.max_marks}>'


class Subject(db.Model):
    """Subject model for course management."""
    __tablename__ = 'subjects'
    
    id = db.Column(db.Integer, primary_key=True)
    code = db.Column(db.String(20), unique=True, nullable=False)
    name = db.Column(db.String(100), nullable=False)
    department = db.Column(db.String(100), ForeignKey('users.department'), nullable=False)
    semester = db.Column(db.Integer, nullable=False)
    session_year = db.Column(db.String(20))  # academic session / year (e.g. 2025-26)
    credits = db.Column(db.Integer, default=3)
    faculty_id = db.Column(db.String(20), ForeignKey('users.employee_id', ondelete='SET NULL'))
    max_marks = db.Column(db.Float, default=100)
    created_at = db.Column(db.DateTime, default=datetime.utcnow)
    
    # Relationships
    enrollments = relationship('SubjectEnrollment', backref='subject', cascade='all, delete-orphan')
    exams = relationship('Exam', backref='subject', cascade='all, delete-orphan')
    attendance_records = relationship('SubjectAttendance', backref='subject', cascade='all, delete-orphan')
    faculty = relationship('User', foreign_keys=[faculty_id], backref='taught_subjects')
    
    def __repr__(self):
        return f'<Subject {self.code} - {self.name}>'


class SubjectEnrollment(db.Model):
    """Student enrollment in subjects."""
    __tablename__ = 'subject_enrollments'
    
    id = db.Column(db.Integer, primary_key=True)
    student_id = db.Column(db.Integer, ForeignKey('students.id', ondelete='CASCADE'), nullable=False)
    subject_id = db.Column(db.Integer, ForeignKey('subjects.id', ondelete='CASCADE'), nullable=False)
    enrolled_date = db.Column(db.DateTime, default=datetime.utcnow)
    
    # Relationships
    student = relationship('Student', backref='subject_enrollments')
    
    def __repr__(self):
        return f'<SubjectEnrollment {self.id} - Student {self.student_id} in Subject {self.subject_id}>'


class Exam(db.Model):
    """Exam model for tracking various assessments."""
    __tablename__ = 'exams'
    
    id = db.Column(db.Integer, primary_key=True)
    subject_id = db.Column(db.Integer, ForeignKey('subjects.id', ondelete='CASCADE'), nullable=False)
    exam_type = db.Column(db.String(50), nullable=False)  # Unit Test, Mid Term, Final, etc.
    exam_date = db.Column(db.Date, nullable=False)
    total_marks = db.Column(db.Float, default=100)
    created_by = db.Column(db.String(20), ForeignKey('users.employee_id', ondelete='SET NULL'))
    created_at = db.Column(db.DateTime, default=datetime.utcnow)
    
    # Relationships
    marks = relationship('Mark', backref='exam', cascade='all, delete-orphan')
    
    def __repr__(self):
        return f'<Exam {self.id} - {self.exam_type} for Subject {self.subject_id}>'


class Mark(db.Model):
    """Student marks in exams."""
    __tablename__ = 'marks'
    
    id = db.Column(db.Integer, primary_key=True)
    exam_id = db.Column(db.Integer, ForeignKey('exams.id', ondelete='CASCADE'), nullable=False)
    student_id = db.Column(db.Integer, ForeignKey('students.id', ondelete='CASCADE'), nullable=False)
    marks_obtained = db.Column(db.Float, nullable=False)
    uploaded_by = db.Column(db.String(20), ForeignKey('users.employee_id', ondelete='SET NULL'))
    created_at = db.Column(db.DateTime, default=datetime.utcnow)
    
    # Relationships
    student = relationship('Student', backref='exam_marks')
    
    def __repr__(self):
        return f'<Mark {self.id} - Student {self.student_id}: {self.marks_obtained}>'


class SubjectAttendance(db.Model):
    """Subject-wise attendance tracking."""
    __tablename__ = 'subject_attendance'
    
    id = db.Column(db.Integer, primary_key=True)
    student_id = db.Column(db.Integer, ForeignKey('students.id', ondelete='CASCADE'), nullable=False)
    subject_id = db.Column(db.Integer, ForeignKey('subjects.id', ondelete='CASCADE'), nullable=False)
    date = db.Column(db.Date, nullable=False)
    status = db.Column(db.String(20), nullable=False)  # Present, Absent, Leave
    marked_by = db.Column(db.String(20), ForeignKey('users.employee_id', ondelete='SET NULL'))
    created_at = db.Column(db.DateTime, default=datetime.utcnow)
    
    # Relationships
    student_rel = relationship('Student', backref='subject_attendance')
    
    def __repr__(self):
        return f'<SubjectAttendance {self.id} - Student {self.student_id} in Subject {self.subject_id}>'


# ==================== NOTIFICATIONS ====================


class Notification(db.Model):
    """In-app notifications for users."""
    __tablename__ = 'notifications'

    id = db.Column(db.Integer, primary_key=True)
    user_id = db.Column(db.String(20), ForeignKey('users.employee_id', ondelete='CASCADE'), nullable=False)
    title = db.Column(db.String(200))
    message = db.Column(db.Text)
    is_read = db.Column(db.Boolean, default=False)
    created_at = db.Column(db.DateTime, default=datetime.utcnow)

    def __repr__(self):
        return f'<Notification {self.id} to {self.user_id} - {self.title}>'


# ==================== HELPER FUNCTIONS ====================

@login_manager.user_loader
def load_user(employee_id):
    """Load user by employee ID."""
    return db.session.get(User, employee_id)


def is_hod(user=None):
    """Return True if the given user (or current_user) is an HOD.
    We allow either a dedicated role of 'HOD' or a designation containing
    'Head of Department' or similar, since some records use 'Teaching'
    for HOD-level users.
    """
    u = user or current_user
    if not u or not hasattr(u, 'role'):
        return False
    if u.role == 'HOD':
        return True
    # designation check if available
    if hasattr(u, 'designation') and u.designation:
        if 'Head of Department' in u.designation or 'HOD' in u.designation:
            return True
    return False


def role_required(*roles):
    """Decorator to check user role (and designation for HOD)."""
    def decorator(f):
        @wraps(f)
        def decorated_function(*args, **kwargs):
            if not current_user.is_authenticated:
                return redirect(url_for('login'))
            # treat HOD designation as role 'HOD'
            if 'HOD' in roles and is_hod():
                return f(*args, **kwargs)
            if current_user.role not in roles:
                flash('You do not have permission to access this page.', 'danger')
                return redirect(url_for('dashboard'))
            return f(*args, **kwargs)
        return decorated_function
    return decorator


def get_dashboard_stats():
    """Get statistics for dashboard."""
    try:
        stats = {
            'total_employees': db.session.query(User).filter(User.role != 'Student').count(),
            'total_students': db.session.query(Student).count(),
            'total_books': db.session.query(Book).count(),
            'available_books': db.session.query(Book).filter(Book.available_quantity > 0).count(),
            'pending_leaves': db.session.query(Leave).filter_by(status='Pending').count(),
            'pending_expenses': db.session.query(Expense).filter_by(status='Pending').count(),
            'books_issued': db.session.query(BookTransaction).filter_by(status='Issued').count(),
        }
    except Exception as e:
        app.logger.error(f"Error getting dashboard stats: {e}")
        stats = {
            'total_employees': 0, 'total_students': 0, 'total_books': 0,
            'available_books': 0, 'pending_leaves': 0, 'pending_expenses': 0,
            'books_issued': 0
        }
    return stats


def get_department_stats(department):
    """Get department-specific statistics for HOD dashboard."""
    try:
        # Employees in the department
        dept_employees = db.session.query(User).filter(
            User.role != 'Student',
            User.department == department
        ).count()
        
        # Students in the department
        dept_students = db.session.query(Student).filter(
            Student.department == department
        ).count()
        
        # Pending leaves for department employees
        dept_pending_leaves = db.session.query(Leave).join(User, Leave.employee_id == User.employee_id).filter(
            User.department == department,
            Leave.status == 'Pending'
        ).count()
        
        # Other stats can be department-specific if applicable
        stats = {
            'total_employees': dept_employees,
            'total_students': dept_students,
            'total_books': db.session.query(Book).count(),  # Global for now
            'available_books': db.session.query(Book).filter(Book.available_quantity > 0).count(),
            'pending_leaves': dept_pending_leaves,
            'pending_expenses': db.session.query(Expense).filter_by(status='Pending').count(),  # Global
            'books_issued': db.session.query(BookTransaction).filter_by(status='Issued').count(),  # Global
        }
    except Exception as e:
        app.logger.error(f"Error getting department stats: {e}")
        stats = {
            'total_employees': 0, 'total_students': 0, 'total_books': 0,
            'available_books': 0, 'pending_leaves': 0, 'pending_expenses': 0,
            'books_issued': 0
        }
    return stats


def generate_employee_id(department: str, designation: str) -> str:
    """Generate unique employee ID based on department and designation."""
    code_map = {
        ('Human Resources', 'HR Manager'): 'HRM',
        ('Management', 'Director'): 'DIR',
        ('Management', 'Dean'): 'DEN',
        ('Administration', 'Registrar'): 'REG',
        ('Accounts', 'Finance Officer'): 'FFO',
        ('Library', 'Library Head'): 'LBH',
    }
    
    teaching_codes = {
        'Head of Department': 'HOD',
        'Professor': 'PRO',
        'Lecturer': 'LEA',
        'Faculty': 'FCL',
    }
    
    if designation in teaching_codes:
        dept_short = (department[:3] if department else 'UNK').upper()
        desig_code = teaching_codes[designation]
        prefix = f"{dept_short}{desig_code}"
    elif (department, designation) in code_map:
        prefix = code_map[(department, designation)]
    else:
        prefix = (department[:3] if department else 'UNK').upper()
    
    try:
        last = db.session.query(User).filter(User.employee_id.startswith(prefix))\
                         .order_by(User.employee_id.desc()).first()
        
        if last:
            try:
                last_seq = int(last.employee_id[-3:])
                seq = last_seq + 1
            except (ValueError, IndexError):
                seq = 1
        else:
            seq = 1
    except Exception:
        seq = 1
    
    return f"{prefix}{seq:03d}"


# ==================== AUTH ROUTES ====================

@app.route('/')
def index():
    """Home page - redirect to login or dashboard."""
    if current_user.is_authenticated:
        return redirect(url_for('dashboard'))
    return redirect(url_for('login'))


@app.route('/login', methods=['GET', 'POST'])
def login():
    """Enhanced login page with role-based authentication."""
    if current_user.is_authenticated:
        return redirect(url_for('dashboard'))
    
    if request.method == 'POST':
        employee_id = request.form.get('employee_id', '').strip()
        password = request.form.get('password')
        user_role = request.form.get('role', 'Student')  # Default to Student

        try:
            # Validate input
            if not employee_id or not password:
                flash('Please enter both ID and password.', 'warning')
                return render_template('login.html')

            # Try direct primary-key lookup first
            user = db.session.get(User, employee_id) if employee_id else None

            # If not found, try a case-insensitive lookup
            if not user and employee_id:
                user = db.session.query(User).filter(
                    func.lower(User.employee_id) == employee_id.lower()
                ).first()

            # Authenticate user
            if user and check_password_hash(user.password, password):
                # Check if account is active
                if not user.is_active:
                    app.logger.warning(f"Login attempt on inactive account: {employee_id}")
                    flash('Your account has been deactivated. Contact administrator.', 'danger')
                    return render_template('login.html')

                # For students: additional validation
                if user.role == 'Student':
                    student = db.session.query(Student).filter_by(user_id=user.employee_id).first()
                    if not student:
                        app.logger.error(f"Student record not found for user: {employee_id}")
                        flash('Student record not found. Contact administrator.', 'danger')
                        return render_template('login.html')
                    
                    # Check student enrollment status
                    if not student.semester or not student.course:
                        flash('Your enrollment details are incomplete. Contact administrator.', 'warning')
                        app.logger.warning(f"Incomplete student enrollment: {employee_id}")

                # Login successful
                login_user(user, remember=False)
                app.logger.info(f"Successful login: {employee_id} ({user.role})")
                
                # Enforce password change if required
                if getattr(user, 'must_change_password', False):
                    flash('You must change your password before continuing.', 'warning')
                    return redirect(url_for('change_password'))
                
                # Redirect to next page or dashboard
                flash(f'Welcome back, {user.name}!', 'success')
                next_page = request.args.get('next')
                if next_page and next_page.startswith('/'):
                    return redirect(next_page)
                return redirect(url_for('dashboard'))
            else:
                # Log failed attempt
                app.logger.warning(f"Failed login attempt: {employee_id}")
                flash('Invalid ID or password. Please try again.', 'danger')
                
        except Exception as e:
            app.logger.error(f"Login error for {employee_id}: {str(e)}", exc_info=True)
            flash('An unexpected error occurred. Please try again later.', 'danger')
    
    return render_template('login.html')


@app.route('/student_login', methods=['GET', 'POST'])
def student_login():
    """Dedicated student login with student-specific features."""
    if current_user.is_authenticated:
        return redirect(url_for('dashboard'))
    
    if request.method == 'POST':
        roll_number = request.form.get('roll_number', '').strip().upper()
        password = request.form.get('password', '')
        
        try:
            # Validate input
            if not roll_number or not password:
                flash('Please enter your Roll Number and password.', 'danger')
                return render_template('student_login.html')
            
            # Find student by roll number
            student = db.session.query(Student).filter_by(roll_number=roll_number).first()
            
            if not student:
                app.logger.warning(f"Student login attempt - invalid roll number: {roll_number}")
                flash('Roll number not found. Please check and try again.', 'danger')
                return render_template('student_login.html')
            
            if not student.user_id:
                app.logger.error(f"Student {roll_number} has no linked user account")
                flash('Your account is not properly set up. Contact administrator.', 'danger')
                return render_template('student_login.html')
            
            # Get associated user
            user = db.session.get(User, student.user_id)
            
            if not user:
                app.logger.error(f"User account not found for student: {roll_number}")
                flash('User account not found. Contact administrator.', 'danger')
                return render_template('student_login.html')
            
            # Verify password
            if not check_password_hash(user.password, password):
                app.logger.warning(f"Failed student login: {roll_number}")
                flash('Invalid password. Please try again.', 'danger')
                return render_template('student_login.html')
            
            # Check account status
            if not user.is_active:
                app.logger.warning(f"Login attempt on inactive student account: {roll_number}")
                flash('Your account is deactivated. Contact your administrator.', 'danger')
                return render_template('student_login.html')
            
            # Verify student is enrolled
            if not student.semester or not student.course:
                flash('Your enrollment is incomplete. Please contact the registrar.', 'warning')
            
            # Successful login
            login_user(user, remember=False)
            session['student_id'] = student.id
            session['roll_number'] = student.roll_number
            
            app.logger.info(f"Student login successful: {roll_number} (User: {user.employee_id})")
            
            # Check if password change is required
            if getattr(user, 'must_change_password', False):
                flash('Please update your password before continuing.', 'info')
                return redirect(url_for('change_password'))
            
            flash(f'Welcome back, {student.name}!', 'success')
            return redirect(url_for('student_dashboard'))
            
        except Exception as e:
            app.logger.error(f"Student login error: {str(e)}", exc_info=True)
            flash('An error occurred during login. Please try again.', 'danger')
    
    return render_template('student_login.html')


@app.route('/logout')
@login_required
def logout():
    """Logout user."""
    logout_user()
    flash('You have been logged out successfully.', 'info')
    return redirect(url_for('login'))


# ==================== DASHBOARD ====================

@app.route('/dashboard')
@login_required
def dashboard():
    """Dashboard page with role-specific content."""
    try:
        # Determine statistics depending on HOD status or standard role
        if is_hod():
            # use department, default to empty string if not set
            stats = get_department_stats(getattr(current_user, 'department', None))
        else:
            stats = get_dashboard_stats()
        
        # Recent leaves
        recent_leaves = db.session.query(Leave).order_by(Leave.created_at.desc()).limit(5).all()
        
        # Recent expenses
        recent_expenses = db.session.query(Expense).order_by(Expense.created_at.desc()).limit(5).all()
        
        # Recent book transactions
        recent_transactions = db.session.query(BookTransaction).order_by(BookTransaction.issue_date.desc()).limit(5).all()
        
        # Student-specific dashboard: render a focused view
        if current_user.role == 'Student':
            student = db.session.query(Student).filter_by(user_id=current_user.employee_id).first()
            grade_data = []
            attendance_records = []
            if student:
                grade_data = db.session.query(Grade).filter_by(student_id=student.id).order_by(Grade.created_at.desc()).all()
                attendance_records = db.session.query(StudentAttendance).filter_by(student_id=student.id).order_by(StudentAttendance.date.desc()).all()

            return render_template('student_dashboard.html',
                                   stats=stats,
                                   student=student,
                                   grade_data=grade_data,
                                   attendance_records=attendance_records)

        # Default (non-student) dashboard
        grade_data = []
        if current_user.role == 'Student':
            student = db.session.query(Student).filter_by(user_id=current_user.employee_id).first()
            if student:
                grade_data = db.session.query(Grade).filter_by(student_id=student.id).all()

        return render_template('dashboard.html',
                             stats=stats,
                             recent_leaves=recent_leaves,
                             recent_expenses=recent_expenses,
                             recent_transactions=recent_transactions,
                             grade_data=grade_data)
    except Exception as e:
        app.logger.error(f"Dashboard error: {e}")
        flash('Error loading dashboard.', 'danger')
        return redirect(url_for('login'))


# ==================== EMPLOYEE MANAGEMENT ====================

@app.route('/manage_employees')
@login_required
@role_required('Registrar', 'Director', 'Dean', 'HR', 'Management', 'HOD')
def manage_employees():
    """Manage employees."""
    try:
        if current_user.role in ['Registrar', 'Director', 'Dean', 'HR', 'Management']:
            employees = db.session.query(User).filter(User.role != 'Student').all()
        elif current_user.role == 'HOD':
            # HOD can only see faculty in their department
            employees = db.session.query(User).filter(
                User.department == current_user.department,
                User.role.in_(['Faculty', 'HOD'])
            ).all()
        else:
            employees = []
        
        return render_template('manage_employees.html', employees=employees)
    except Exception as e:
        app.logger.error(f"Manage employees error: {e}")
        flash('Error loading employees.', 'danger')
        return redirect(url_for('dashboard'))


@app.route('/add_employee', methods=['GET', 'POST'])
@login_required
@role_required('Registrar', 'Director', 'Dean', 'HR', 'Management', 'HOD')
def add_employee():
    """Add new employee."""
    if request.method == 'POST':
        try:
            name = request.form.get('name')
            email = request.form.get('email')
            phone = request.form.get('phone')
            role = request.form.get('role')
            department = request.form.get('department')
            designation = request.form.get('designation')
            password = request.form.get('password')
            
            # Validate required fields
            if not all([name, email, role, department, designation, password]):
                flash('All fields are required.', 'danger')
                return redirect(url_for('add_employee'))
            
            # HOD can only add faculty to their own department
            if current_user.role == 'HOD':
                if department != current_user.department:
                    flash('HOD can only add faculty to their own department.', 'warning')
                    return redirect(url_for('add_employee'))
                if role not in ['Faculty', 'Teaching']:
                    flash('HOD can only add Faculty or Teaching staff.', 'warning')
                    return redirect(url_for('add_employee'))
            
            employee_id = generate_employee_id(department, designation)
            
            new_user = User(
                employee_id=employee_id,
                name=name,
                email=email,
                phone=phone,
                role=role,
                department=department,
                designation=designation,
                password=generate_password_hash(password)
            )
            
            db.session.add(new_user)
            db.session.commit()
            
            flash(f'Employee {name} added successfully with ID {employee_id} and role {role}!', 'success')
            return redirect(url_for('manage_employees'))
        except Exception as e:
            db.session.rollback()
            app.logger.error(f"Add employee error: {e}")
            flash(f'Error adding employee: {str(e)}', 'danger')
    
    from config import ROLES
    
    # If HOD, only show their department
    if current_user.role == 'HOD':
        departments = [current_user.department]
        roles = ['Faculty', 'Teaching']
    else:
        departments = None  # Show all departments in template
        roles = ROLES
    
    return render_template('add_employee.html', roles=roles, departments=departments)


@app.route('/edit_employee/<employee_id>', methods=['GET', 'POST'])
@login_required
@role_required('Registrar', 'Director', 'Dean', 'HR', 'Management', 'HOD')
def edit_employee(employee_id):
    """Edit employee details."""
    employee = db.session.get(User, employee_id)
    if not employee:
        flash('Employee not found.', 'danger')
        return redirect(url_for('manage_employees'))
    
    # HOD can only edit faculty in their department
    if current_user.role == 'HOD' and employee.department != current_user.department:
        flash('You can only edit faculty in your department.', 'warning')
        return redirect(url_for('manage_employees'))
    
    if request.method == 'POST':
        try:
            employee.name = request.form.get('name', employee.name)
            employee.email = request.form.get('email', employee.email)
            employee.phone = request.form.get('phone', employee.phone)
            
            # HOD cannot change department
            if current_user.role != 'HOD':
                employee.department = request.form.get('department', employee.department)
            
            employee.designated = request.form.get('designation', employee.designation)
            
            db.session.commit()
            flash('Employee updated successfully!', 'success')
            return redirect(url_for('manage_employees'))
        except Exception as e:
            db.session.rollback()
            app.logger.error(f"Edit employee error: {e}")
            flash(f'Error updating employee: {str(e)}', 'danger')
    
    return render_template('edit_employee.html', employee=employee)


@app.route('/delete_employee/<employee_id>', methods=['GET', 'POST'])
@login_required
@role_required('Registrar', 'Director', 'Dean', 'HR', 'HOD')
def delete_employee(employee_id):
    """Delete employee."""
    try:
        employee = db.session.get(User, employee_id)
        if not employee:
            flash('Employee not found.', 'danger')
            return redirect(url_for('manage_employees'))
        
        # HOD can only delete faculty in their department
        if current_user.role == 'HOD' and employee.department != current_user.department:
            flash('You can only delete faculty in your department.', 'warning')
            return redirect(url_for('manage_employees'))
        
        db.session.delete(employee)
        db.session.commit()
        flash('Employee deleted successfully!', 'success')
    except Exception as e:
        db.session.rollback()
        app.logger.error(f"Delete employee error: {e}")
        flash(f'Error deleting employee: {str(e)}', 'danger')
    
    return redirect(url_for('manage_employees'))


# ==================== LEAVE MANAGEMENT ====================

@app.route('/apply_leave', methods=['GET', 'POST'])
@login_required
def apply_leave():
    """Apply for leave."""
    if request.method == 'POST':
        try:
            leave_type = request.form.get('leave_type')
            start_date = datetime.strptime(request.form.get('start_date'), '%Y-%m-%d').date()
            end_date = datetime.strptime(request.form.get('end_date'), '%Y-%m-%d').date()
            reason = request.form.get('reason')
            
            new_leave = Leave(
                employee_id=current_user.employee_id,
                leave_type=leave_type,
                start_date=start_date,
                end_date=end_date,
                reason=reason,
                department=current_user.department,
                status='Pending'
            )
            
            db.session.add(new_leave)
            db.session.commit()
            
            flash('Leave application submitted successfully!', 'success')
            # Redirect students to their own leave list, others to leave management
            if current_user.role == 'Student':
                return redirect(url_for('my_leaves'))
            return redirect(url_for('leave_management'))
        except Exception as e:
            db.session.rollback()
            app.logger.error(f"Apply leave error: {e}")
            flash(f'Error submitting leave: {str(e)}', 'danger')
    
    # Provide leave options: students get only Sick and Personal leaves
    if current_user.role == 'Student':
        leave_options = ['Sick Leave', 'Personal Leave']
    else:
        leave_options = ['Casual Leave', 'Sick Leave', 'Earned Leave', 'Maternity Leave', 'Paternity Leave', 'Unpaid Leave']

    return render_template('apply_leave.html', leave_options=leave_options)


@app.route('/leave_management')
@login_required
@role_required('Registrar', 'Director', 'HOD', 'HR', 'Management', 'Faculty')
def leave_management():
    """Manage leave requests with designation-based filtering."""
    try:
        if current_user.role in ['Registrar', 'Director', 'Management']:
            leaves = db.session.query(Leave).all()
        elif is_hod():
            leaves = db.session.query(Leave).filter_by(department=current_user.department).all()
        else:
            leaves = db.session.query(Leave).filter_by(employee_id=current_user.employee_id).all()
        
        # Build employee info dictionary for template
        employee_info = {}
        for leave in leaves:
            emp = db.session.get(User, leave.employee_id)
            if emp:
                employee_info[leave.id] = emp
        
        return render_template('leave_management.html', leaves=leaves, employee_info=employee_info)
    except Exception as e:
        app.logger.error(f"Leave management error: {e}")
        flash('Error loading leave requests.', 'danger')
        return redirect(url_for('dashboard'))


@app.route('/my_leaves')
@login_required
def my_leaves():
    """Show current user's leave applications (students and staff)."""
    try:
        leaves = db.session.query(Leave).filter_by(employee_id=current_user.employee_id).order_by(Leave.created_at.desc()).all()
        return render_template('my_leaves.html', leaves=leaves)
    except Exception as e:
        app.logger.error(f"My leaves error: {e}")
        flash('Error loading your leave requests.', 'danger')
        return redirect(url_for('dashboard'))


@app.route('/approve_leave/<int:leave_id>', methods=['POST'])
@login_required
@role_required('Registrar', 'Director', 'HOD', 'Management')
def approve_leave(leave_id):
    """Approve leave request."""
    try:
        leave = db.session.get(Leave, leave_id)
        if not leave:
            flash('Leave request not found.', 'danger')
            return redirect(url_for('leave_management'))
        # Load applicant user to make role/department based decisions
        applicant = db.session.get(User, leave.employee_id)

        # HOD: can approve student leaves of their department, forward faculty leaves of their department
        if current_user.role == 'HOD':
            if not applicant or applicant.department != current_user.department:
                flash('You are not authorized to manage leaves for this department.', 'danger')
                return redirect(url_for('leave_management'))

            if applicant.role == 'Student':
                leave.approved_by = current_user.employee_id
                leave.status = 'Approved'
                msg = 'Student leave approved.'
            elif applicant.role == 'Faculty':
                leave.forwarded_by = current_user.employee_id
                leave.status = 'Forwarded'
                msg = 'Faculty leave forwarded to higher authority.'
            else:
                flash('HOD may only approve student leaves or forward faculty leaves in their department.', 'danger')
                return redirect(url_for('leave_management'))

        else:
            # Registrar / Director / Management approve directly
            leave.approved_by = current_user.employee_id
            leave.status = 'Approved'
            msg = 'Leave request approved.'

        db.session.commit()
        flash(msg, 'success')

        # If HOD forwarded a faculty leave, notify approvers
        try:
            if current_user.role == 'HOD' and applicant and applicant.role == 'Faculty' and leave.status == 'Forwarded':
                notify_on_forward(leave)
        except Exception:
            app.logger.exception('Error sending forward notification')
    except Exception as e:
        db.session.rollback()
        app.logger.error(f"Approve leave error: {e}")
        flash(f'Error approving leave: {str(e)}', 'danger')
    
    return redirect(url_for('leave_management'))


@app.route('/reject_leave/<int:leave_id>', methods=['POST'])
@login_required
@role_required('Registrar', 'Director', 'HOD', 'Management')
def reject_leave(leave_id):
    """Reject leave request."""
    try:
        leave = db.session.get(Leave, leave_id)
        if not leave:
            flash('Leave request not found.', 'danger')
            return redirect(url_for('leave_management'))
        # Load applicant user to make role/department based decisions
        applicant = db.session.get(User, leave.employee_id)

        # HOD: can reject student leaves of their department
        if current_user.role == 'HOD':
            if not applicant or applicant.department != current_user.department:
                flash('You are not authorized to manage leaves for this department.', 'danger')
                return redirect(url_for('leave_management'))

        # Registrar / Director / Management / HOD can reject
        leave.approved_by = current_user.employee_id
        leave.status = 'Rejected'
        msg = 'Leave request rejected.'

        db.session.commit()
        flash(msg, 'success')
    except Exception as e:
        db.session.rollback()
        app.logger.error(f"Reject leave error: {e}")
        flash(f'Error rejecting leave: {str(e)}', 'danger')
    
    return redirect(url_for('leave_management'))


# ==================== ATTENDANCE ====================

@app.route('/manage_attendance')
@login_required
@role_required('Registrar', 'Director', 'HR', 'HOD', 'Management')
def manage_attendance():
    """Manage employee attendance."""
    try:
        if current_user.role in ['Registrar', 'Director', 'HR', 'Management']:
            attendance = db.session.query(Attendance).order_by(Attendance.date.desc()).limit(100).all()
        else:
            attendance = db.session.query(Attendance).filter_by(employee_id=current_user.employee_id).all()
        
        return render_template('attendance.html', attendance=attendance)
    except Exception as e:
        app.logger.error(f"Manage attendance error: {e}")
        flash('Error loading attendance.', 'danger')
        return redirect(url_for('dashboard'))


def notify_on_forward(leave):
    """Notify responsible users when a leave is forwarded by HOD.

    Attempts to send email if SMTP config exists; otherwise logs the notification.
    """
    try:
        approvers = db.session.query(User).filter(User.role.in_(['Director', 'Registrar', 'Management'])).all()
        recipients = [u.email for u in approvers if u.email]
        subject = f"Leave Forwarded: ID {leave.id} by {leave.employee_id}"
        body = f"Leave request {leave.id} ({leave.leave_type}) from {leave.employee_id} was forwarded by HOD {current_user.employee_id}.\nPlease review it in the Leave Management panel."

        if recipients:
            import smtplib
            from email.message import EmailMessage
            mail_server = app.config.get('MAIL_SERVER')
            mail_port = app.config.get('MAIL_PORT')
            mail_user = app.config.get('MAIL_USERNAME')
            mail_pass = app.config.get('MAIL_PASSWORD')
            use_tls = app.config.get('MAIL_USE_TLS')
            if mail_server and mail_port:
                msg = EmailMessage()
                msg['Subject'] = subject
                msg['From'] = mail_user or 'no-reply@aimt.local'
                msg['To'] = ', '.join(recipients)
                msg.set_content(body)
                try:
                    with smtplib.SMTP(mail_server, int(mail_port), timeout=10) as s:
                        if use_tls:
                            s.starttls()
                        if mail_user and mail_pass:
                            s.login(mail_user, mail_pass)
                        s.send_message(msg)
                    app.logger.info(f"Forward notification sent to: {recipients}")
                except Exception as e:
                    app.logger.error(f"SMTP send failed: {e}")

        # Create in-app notifications for approvers
        try:
            for approver in approvers:
                if approver and approver.employee_id:
                    n = Notification(user_id=approver.employee_id, title=subject, message=body)
                    db.session.add(n)
            db.session.commit()
            app.logger.info(f"Created in-app notifications for approvers: {[u.employee_id for u in approvers]}")
        except Exception as e:
            app.logger.error(f"Failed to create in-app notifications: {e}")
        app.logger.info(f"Leave {leave.id} forwarded; notify users: {recipients}")
    except Exception as e:
        app.logger.error(f"notify_on_forward error: {e}")
    return False


# ==================== HOD DEPARTMENT MANAGEMENT ====================

@app.route('/hod_department')
@login_required
@role_required('HOD')
def hod_department():
    """HOD view of department - students and faculty."""
    try:
        department = current_user.department
        
        # Get filter parameters
        student_year = request.args.get('student_year', type=int)
        student_sem = request.args.get('student_sem', type=int)
        faculty_dept = request.args.get('faculty_dept', department)
        
        # Query students
        student_query = db.session.query(Student).filter_by(department=department)
        if student_year:
            student_query = student_query.filter_by(course=str(student_year))
        if student_sem:
            student_query = student_query.filter_by(semester=student_sem)
        
        students = student_query.all()
        
        # Query faculty (teaching employees in department)
        faculty = db.session.query(User).filter(
            User.department == department,
            User.role.in_(['Faculty', 'Teaching', 'HOD'])
        ).all()
        
        # Get available years and semesters
        available_years = db.session.query(Student.course).filter_by(department=department).distinct().all()
        available_sems = db.session.query(Student.semester).filter_by(department=department).distinct().all()
        
        return render_template('hod_department.html',
                             students=students,
                             faculty=faculty,
                             department=department,
                             student_year=student_year,
                             student_sem=student_sem,
                             available_years=[y[0] for y in available_years if y[0]],
                             available_sems=[s[0] for s in available_sems if s[0]])
    except Exception as e:
        app.logger.error(f"HOD department view error: {e}")
        flash('Error loading department data.', 'danger')
        return redirect(url_for('dashboard'))


@app.route('/assign_subject', methods=['GET', 'POST'])
@login_required
@role_required('HOD')
def assign_subject():
    """HOD assigns subjects to faculty."""
    try:
        department = current_user.department
        
        if request.method == 'POST':
            faculty_id = request.form.get('faculty_id')
            subject_id = request.form.get('subject_id')
            
            subject = db.session.get(Subject, subject_id)
            if not subject:
                flash('Subject not found.', 'danger')
                return redirect(url_for('assign_subject'))
            
            if subject.department != department:
                flash('You can only assign subjects in your department.', 'danger')
                return redirect(url_for('assign_subject'))
            
            faculty = db.session.get(User, faculty_id)
            if not faculty or faculty.department != department:
                flash('Faculty not found or not in your department.', 'danger')
                return redirect(url_for('assign_subject'))
            
            # Update subject with faculty
            subject.faculty_id = faculty_id
            db.session.commit()
            
            flash(f'Subject "{subject.name}" assigned to {faculty.name} successfully!', 'success')
            return redirect(url_for('assign_subject'))
        
        # GET: Show available subjects and faculty
        faculty = db.session.query(User).filter(
            User.department == department,
            User.role.in_(['Faculty', 'Teaching', 'HOD'])
        ).all()
        
        subjects = db.session.query(Subject).filter_by(department=department).all()
        
        return render_template('assign_subject.html', subjects=subjects, faculty=faculty)
    except Exception as e:
        app.logger.error(f"Assign subject error: {e}")
        flash('Error assigning subject.', 'danger')
        return redirect(url_for('dashboard'))


# ==================== SUBJECTS (For HOD) ====================

@app.route('/manage_subjects')
@login_required
@role_required('HOD', 'Registrar', 'Director', 'Dean', 'Management')
def manage_subjects():
    """Manage subjects - HOD can see their department subjects."""
    try:
        if current_user.role in ['Registrar', 'Director', 'Dean', 'Management']:
            subjects = db.session.query(Subject).all()
        elif is_hod():
            subjects = db.session.query(Subject).filter_by(department=current_user.department).all()
        else:
            subjects = []
        
        return render_template('manage_subjects.html', subjects=subjects)
    except Exception as e:
        app.logger.error(f"Manage subjects error: {e}")
        flash('Error loading subjects.', 'danger')
        return redirect(url_for('dashboard'))


@app.route('/notifications')
@login_required
def notifications():
    """List notifications for current user."""
    try:
        notes = db.session.query(Notification).filter_by(user_id=current_user.employee_id).order_by(Notification.created_at.desc()).all()
        return render_template('notifications.html', notifications=notes)
    except Exception as e:
        app.logger.error(f"Notifications load error: {e}")
        flash('Error loading notifications.', 'danger')
        return redirect(url_for('dashboard'))


@app.route('/notifications/mark_read/<int:notification_id>', methods=['POST'])
@login_required
def mark_notification_read(notification_id):
    try:
        n = db.session.get(Notification, notification_id)
        if not n or n.user_id != current_user.employee_id:
            flash('Notification not found.', 'danger')
            return redirect(url_for('notifications'))
        n.is_read = True
        db.session.commit()
        flash('Notification marked as read.', 'success')
    except Exception as e:
        db.session.rollback()
        app.logger.error(f"Mark notification read error: {e}")
        flash('Error updating notification.', 'danger')
    return redirect(url_for('notifications'))


@app.route('/add_subject', methods=['GET', 'POST'])
@login_required
@role_required('HOD', 'Registrar', 'Director', 'Dean', 'Management')
def add_subject():
    """Add new subject for a department."""
    if request.method == 'POST':
        try:
            code = request.form.get('code')
            name = request.form.get('name')
            department = request.form.get('department')
            semester = request.form.get('semester', type=int)
            session_year = request.form.get('session_year')
            credits = request.form.get('credits', type=int, default=3)
            faculty_id = request.form.get('faculty_id')
            max_marks = request.form.get('max_marks', type=float, default=100)
            
            new_subject = Subject(
                code=code,
                name=name,
                department=department,
                semester=semester,
                session_year=session_year,
                credits=credits,
                faculty_id=faculty_id if faculty_id else None,
                max_marks=max_marks
            )
            
            db.session.add(new_subject)
            db.session.commit()
            
            flash(f'Subject "{name}" added successfully!', 'success')
            return redirect(url_for('manage_subjects'))
        except Exception as e:
            db.session.rollback()
            app.logger.error(f"Add subject error: {e}")
            flash(f'Error adding subject: {str(e)}', 'danger')
    
    # Get all faculty members (multiple roles: Faculty, Teaching, HOD, or designation containing 'Faculty'/'Teaching')
    faculty = db.session.query(User).filter(
        (User.role.in_(['Faculty', 'Teaching', 'HOD'])) | 
        ((User.designation != None) & (User.designation.ilike('%Faculty%'))) |
        ((User.designation != None) & (User.designation.ilike('%Teaching%')))
    ).all()
    
    return render_template('add_subject.html', faculty=faculty)


@app.route('/edit_subject/<int:subject_id>', methods=['GET', 'POST'])
@login_required
@role_required('HOD', 'Registrar', 'Director', 'Dean', 'Management')
def edit_subject(subject_id):
    """Edit subject details."""
    subject = db.session.get(Subject, subject_id)
    if not subject:
        flash('Subject not found.', 'danger')
        return redirect(url_for('manage_subjects'))
    
    if request.method == 'POST':
        try:
            subject.name = request.form.get('name', subject.name)
            subject.semester = request.form.get('semester', type=int, default=subject.semester)
            subject.session_year = request.form.get('session_year', subject.session_year)
            subject.credits = request.form.get('credits', type=int, default=subject.credits)
            subject.faculty_id = request.form.get('faculty_id') or None
            subject.max_marks = request.form.get('max_marks', type=float, default=subject.max_marks)
            
            db.session.commit()
            flash('Subject updated successfully!', 'success')
            return redirect(url_for('manage_subjects'))
        except Exception as e:
            db.session.rollback()
            app.logger.error(f"Edit subject error: {e}")
            flash(f'Error updating subject: {str(e)}', 'danger')
    
    faculty = db.session.query(User).filter_by(role='Faculty').all()
    return render_template('edit_subject.html', subject=subject, faculty=faculty)


@app.route('/delete_subject/<int:subject_id>', methods=['POST'])
@login_required
@role_required('HOD', 'Registrar', 'Director', 'Dean', 'Management')
def delete_subject(subject_id):
    """Delete a subject."""
    try:
        subject = db.session.get(Subject, subject_id)
        if subject:
            db.session.delete(subject)
            db.session.commit()
            flash('Subject deleted successfully!', 'success')
        else:
            flash('Subject not found.', 'danger')
    except Exception as e:
        db.session.rollback()
        app.logger.error(f"Delete subject error: {e}")
        flash(f'Error deleting subject: {str(e)}', 'danger')
    
    return redirect(url_for('manage_subjects'))


@app.route('/subject_enrollments/<int:subject_id>')
@login_required
@role_required('HOD', 'Registrar', 'Director', 'Dean', 'Faculty', 'Management')
def subject_enrollments(subject_id):
    """View and manage student enrollments for a subject."""
    try:
        subject = db.session.get(Subject, subject_id)
        if not subject:
            flash('Subject not found.', 'danger')
            return redirect(url_for('manage_subjects'))
        
        # Get enrolled students
        enrollments = db.session.query(SubjectEnrollment).filter_by(subject_id=subject_id).all()
        enrolled_student_ids = [e.student_id for e in enrollments]
        
        # Get available students for this department and semester
        if current_user.role == 'HOD':
            available_students = db.session.query(Student).filter_by(
                department=current_user.department,
                semester=subject.semester
            ).all()
        else:
            available_students = db.session.query(Student).filter_by(
                semester=subject.semester
            ).all()
        
        return render_template('subject_enrollments.html', 
                             subject=subject, 
                             enrollments=enrollments,
                             available_students=available_students,
                             enrolled_student_ids=enrolled_student_ids)
    except Exception as e:
        app.logger.error(f"Subject enrollments error: {e}")
        flash('Error loading enrollments.', 'danger')
        return redirect(url_for('manage_subjects'))


@app.route('/enroll_student', methods=['POST'])
@login_required
@role_required('HOD', 'Registrar', 'Director', 'Dean', 'Faculty', 'Management')
def enroll_student():
    """Enroll a student in a subject."""
    try:
        subject_id = request.form.get('subject_id', type=int)
        student_id = request.form.get('student_id', type=int)
        
        # Check if already enrolled
        existing = db.session.query(SubjectEnrollment).filter_by(
            subject_id=subject_id,
            student_id=student_id
        ).first()
        
        if existing:
            flash('Student already enrolled in this subject.', 'warning')
        else:
            enrollment = SubjectEnrollment(
                subject_id=subject_id,
                student_id=student_id
            )
            db.session.add(enrollment)
            db.session.commit()
            flash('Student enrolled successfully!', 'success')
    except Exception as e:
        db.session.rollback()
        app.logger.error(f"Enroll student error: {e}")
        flash(f'Error enrolling student: {str(e)}', 'danger')
    
    return redirect(url_for('subject_enrollments', subject_id=request.form.get('subject_id')))


@app.route('/unenroll_student/<int:enrollment_id>', methods=['POST'])
@login_required
@role_required('HOD', 'Registrar', 'Director', 'Dean', 'Faculty', 'Management')
def unenroll_student(enrollment_id):
    """Unenroll a student from a subject."""
    try:
        enrollment = db.session.get(SubjectEnrollment, enrollment_id)
        if enrollment:
            subject_id = enrollment.subject_id
            db.session.delete(enrollment)
            db.session.commit()
            flash('Student unenrolled successfully!', 'success')
            return redirect(url_for('subject_enrollments', subject_id=subject_id))
        else:
            flash('Enrollment not found.', 'danger')
    except Exception as e:
        db.session.rollback()
        app.logger.error(f"Unenroll student error: {e}")
        flash(f'Error unenrolling student: {str(e)}', 'danger')
    
    return redirect(url_for('manage_subjects'))


# ==================== EXAMS (For HOD) ====================

@app.route('/manage_exams')
@login_required
@role_required('HOD', 'Registrar', 'Director', 'Dean', 'Faculty', 'Management')
def manage_exams():
    """Manage exams."""
    try:
        if current_user.role in ['Registrar', 'Director', 'Dean', 'Management']:
            exams = db.session.query(Exam).all()
        elif current_user.role == 'HOD':
            # Get subjects in HOD's department
            subjects = db.session.query(Subject).filter_by(department=current_user.department).all()
            subject_ids = [s.id for s in subjects]
            exams = db.session.query(Exam).filter(Exam.subject_id.in_(subject_ids)).all()
        elif current_user.role == 'Faculty':
            exams = db.session.query(Exam).filter_by(created_by=current_user.employee_id).all()
        else:
            exams = []
        
        # Get subject details for each exam
        exam_data = []
        for exam in exams:
            subject = db.session.get(Subject, exam.subject_id)
            exam_data.append({'exam': exam, 'subject': subject})
        
        return render_template('manage_exams.html', exam_data=exam_data)
    except Exception as e:
        app.logger.error(f"Manage exams error: {e}")
        flash('Error loading exams.', 'danger')
        return redirect(url_for('dashboard'))


@app.route('/add_exam', methods=['GET', 'POST'])
@login_required
@role_required('HOD', 'Registrar', 'Director', 'Dean', 'Faculty', 'Management')
def add_exam():
    """Add new exam for a subject."""
    if request.method == 'POST':
        try:
            subject_id = request.form.get('subject_id', type=int)
            exam_type = request.form.get('exam_type')
            exam_date = datetime.strptime(request.form.get('exam_date'), '%Y-%m-%d').date()
            total_marks = request.form.get('total_marks', type=float, default=100)
            
            new_exam = Exam(
                subject_id=subject_id,
                exam_type=exam_type,
                exam_date=exam_date,
                total_marks=total_marks,
                created_by=current_user.employee_id
            )
            
            db.session.add(new_exam)
            db.session.commit()
            
            flash('Exam added successfully!', 'success')
            return redirect(url_for('manage_exams'))
        except Exception as e:
            db.session.rollback()
            app.logger.error(f"Add exam error: {e}")
            flash(f'Error adding exam: {str(e)}', 'danger')
    
    # Get subjects
    if current_user.role == 'HOD':
        subjects = db.session.query(Subject).filter_by(department=current_user.department).all()
    else:
        subjects = db.session.query(Subject).all()
    
    return render_template('add_exam.html', subjects=subjects)


@app.route('/upload_marks/<int:exam_id>', methods=['GET', 'POST'])
@login_required
@role_required('HOD', 'Registrar', 'Director', 'Dean', 'Faculty', 'Management')
def upload_marks(exam_id):
    """Upload marks for an exam."""
    exam = db.session.get(Exam, exam_id)
    if not exam:
        flash('Exam not found.', 'danger')
        return redirect(url_for('manage_exams'))
    
    if request.method == 'POST':
        try:
            student_id = request.form.get('student_id', type=int)
            marks_obtained = request.form.get('marks_obtained', type=float)
            
            # Check if marks already exist
            existing = db.session.query(Mark).filter_by(
                exam_id=exam_id,
                student_id=student_id
            ).first()
            
            if existing:
                existing.marks_obtained = marks_obtained
                flash('Marks updated successfully!', 'success')
            else:
                new_mark = Mark(
                    exam_id=exam_id,
                    student_id=student_id,
                    marks_obtained=marks_obtained,
                    uploaded_by=current_user.employee_id
                )
                db.session.add(new_mark)
                flash('Marks uploaded successfully!', 'success')
            
            db.session.commit()
            return redirect(url_for('upload_marks', exam_id=exam_id))
        except Exception as e:
            db.session.rollback()
            app.logger.error(f"Upload marks error: {e}")
            flash(f'Error uploading marks: {str(e)}', 'danger')
    
    # Get enrolled students for this subject
    enrollments = db.session.query(SubjectEnrollment).filter_by(subject_id=exam.subject_id).all()
    student_ids = [e.student_id for e in enrollments]
    students = db.session.query(Student).filter(Student.id.in_(student_ids)).all()
    
    # Get existing marks
    existing_marks = db.session.query(Mark).filter_by(exam_id=exam_id).all()
    marks_dict = {m.student_id: m.marks_obtained for m in existing_marks}
    
    subject = db.session.get(Subject, exam.subject_id)
    return render_template('upload_marks.html', 
                         exam=exam, 
                         subject=subject,
                         students=students,
                         marks_dict=marks_dict)


# ==================== SUBJECT ATTENDANCE (For HOD) ====================

@app.route('/subject_attendance', methods=['GET', 'POST'])
@login_required
@role_required('HOD', 'Director', 'Dean', 'Registrar', 'Faculty', 'Management')
def subject_attendance():
    """Mark and view subject-wise attendance."""
    try:
        if request.method == 'POST':
            student_id = request.form.get('student_id', type=int)
            subject_id = request.form.get('subject_id', type=int)
            status = request.form.get('status')
            
            attendance = SubjectAttendance(
                student_id=student_id,
                subject_id=subject_id,
                date=date.today(),
                status=status,
                marked_by=current_user.employee_id
            )
            
            db.session.add(attendance)
            db.session.commit()
            
            flash('Attendance marked successfully!', 'success')
            return redirect(url_for('subject_attendance'))
        
        # Get subjects for dropdown
        if current_user.role == 'HOD':
            subjects = db.session.query(Subject).filter_by(department=current_user.department).all()
        else:
            subjects = db.session.query(Subject).all()
        
        # Get students filtered by subject
        selected_subject_id = request.args.get('subject_id', type=int)
        students = []
        enrolled_students = []
        
        if selected_subject_id:
            enrollments = db.session.query(SubjectEnrollment).filter_by(subject_id=selected_subject_id).all()
            student_ids = [e.student_id for e in enrollments]
            students = db.session.query(Student).filter(Student.id.in_(student_ids)).all()
        
        return render_template('subject_attendance.html', 
                             subjects=subjects,
                             students=students,
                             selected_subject_id=selected_subject_id)
    except Exception as e:
        db.session.rollback()
        app.logger.error(f"Subject attendance error: {e}")
        flash(f'Error managing attendance: {str(e)}', 'danger')
        return redirect(url_for('dashboard'))


@app.route('/view_subject_attendance')
@login_required
@role_required('HOD', 'Registrar', 'Director', 'Dean', 'Faculty', 'Management')
def view_subject_attendance():
    """View subject-wise attendance reports."""
    try:
        subject_id = request.args.get('subject_id', type=int)
        
        if subject_id:
            attendance_records = db.session.query(SubjectAttendance).filter_by(subject_id=subject_id).all()
            subject = db.session.get(Subject, subject_id)
        else:
            attendance_records = []
            subject = None
        
        # Get all subjects for filter
        if current_user.role == 'HOD':
            subjects = db.session.query(Subject).filter_by(department=current_user.department).all()
        else:
            subjects = db.session.query(Subject).all()
        
        return render_template('view_subject_attendance.html',
                             attendance_records=attendance_records,
                             subjects=subjects,
                             selected_subject=subject)
    except Exception as e:
        app.logger.error(f"View attendance error: {e}")
        flash('Error loading attendance.', 'danger')
        return redirect(url_for('dashboard'))


# ==================== STUDENTS ====================

@app.route('/manage_students')
@login_required
@role_required('Registrar', 'Director', 'Dean', 'HOD', 'Faculty', 'Management')
def manage_students():
    """Manage students."""
    try:
        if current_user.role in ['Registrar', 'Director', 'Dean', 'Management']:
            students = db.session.query(Student).order_by(Student.roll_number).all()
        elif is_hod():
            # HOD can see students in their department
            department = current_user.department
            students = db.session.query(Student).filter_by(department=department).order_by(Student.roll_number).all()
        elif current_user.role == 'Faculty':
            # Faculty can see students in their department
            department = current_user.department
            students = db.session.query(Student).filter_by(department=department).order_by(Student.roll_number).all()
        else:
            students = []
        
        return render_template('manage_students.html', students=students)
    except Exception as e:
        app.logger.error(f"Manage students error: {e}")
        flash('Error loading students.', 'danger')
        return redirect(url_for('dashboard'))


@app.route('/add_student', methods=['GET', 'POST'])
@login_required
@role_required('Registrar', 'HOD')
def add_student():
    """Add new student."""
    if request.method == 'POST':
        try:
            first_name = request.form.get('first_name', '').strip()
            last_name = request.form.get('last_name', '').strip()
            father_name = request.form.get('father_name', '').strip()
            name = request.form.get('name', '').strip()
            email = request.form.get('email', '').strip()
            department = request.form.get('department', '').strip()
            semester = request.form.get('semester', type=int)
            admission_year = request.form.get('admission_year', type=int)
            college_code = request.form.get('college_code', '225').strip()
            permanent_address = request.form.get('Permanent_address', '').strip()
            current_address = request.form.get('current_address', '').strip()
            manual_roll_number = request.form.get('manual_roll_number', '').strip()
            initial_password = request.form.get('initial_password', '').strip()
            
            # Validate required fields (only roll number and password plus basic info)
            if not all([first_name, last_name, father_name, department, semester, admission_year, manual_roll_number, initial_password]):
                flash('Please fill all required fields (*).', 'danger')
                return redirect(url_for('add_student'))
            
            # Validate roll number format
            if len(manual_roll_number) < 3:
                flash('Roll Number must be at least 3 characters long.', 'danger')
                return redirect(url_for('add_student'))
            
            # Use provided roll number
            roll_number = manual_roll_number
            
            # Check if roll number already exists
            existing = db.session.query(Student).filter_by(roll_number=roll_number).first()
            if existing:
                flash(f'Roll Number "{roll_number}" already exists. Please use a different roll number.', 'danger')
                return redirect(url_for('add_student'))
            
            # Student and user ID are the same now
            student_id = roll_number
            
            # Create User account using provided password
            new_user = User(
                employee_id=student_id,
                name=name if name else f"{first_name} {last_name}",
                email=email if email else f"{student_id.lower()}@aimt.edu",
                phone=None,
                role='Student',
                department=department,
                designation='Student',
                password=generate_password_hash(initial_password),
                must_change_password=True,
                is_active=True
            )
            
            # Create Student record
            new_student = Student(
                roll_number=roll_number,
                name=name if name else f"{first_name} {last_name}",
                first_name=first_name,
                last_name=last_name,
                father_name=father_name,
                email=email if email else f"{student_id.lower()}@aimt.edu",
                phone=None,
                semester=semester,
                department=department,
                course=department,
                user_id=student_id  # Link to User account
            )            
            db.session.add(new_user)
            db.session.add(new_student)
            db.session.commit()
            
            # Show credentials to admin
            flash(f'Student {first_name} {last_name} added successfully!<br>'
                f'<strong>Roll Number:</strong> {roll_number}<br>'
                f'<strong>Initial Password:</strong> {initial_password}<br>'
                f'<em>Student must change password on first login.</em>', 'success')
            return redirect(url_for('manage_students'))
        except Exception as e:
            db.session.rollback()
            app.logger.error(f"Add student error: {e}")
            flash(f'Error adding student: {str(e)}', 'danger')
            return redirect(url_for('add_student'))
    
    from datetime import datetime
    now = datetime.now()
    return render_template('add_student.html', now=now)


@app.route('/edit_student/<int:student_id>', methods=['GET', 'POST'])
@login_required
@role_required('Registrar')
def edit_student(student_id):
    """Edit student details."""
    try:
        student = db.session.get(Student, student_id)
        if not student:
            flash('Student not found.', 'danger')
            return redirect(url_for('manage_students'))
        
        if request.method == 'POST':
            try:
                student.first_name = request.form.get('first_name', '').strip()
                student.last_name = request.form.get('last_name', '').strip()
                student.father_name = request.form.get('father_name', '').strip()
                student.name = request.form.get('name', '').strip()
                student.email = request.form.get('email', '').strip() or None
                student.phone = request.form.get('phone', '').strip() or None
                # If phone provided, enforce 10-digit numeric format
                if student.phone:
                    if not student.phone.isdigit() or len(student.phone) != 10:
                        flash('Mobile number must be exactly 10 digits (numbers only).', 'danger')
                        return redirect(url_for('edit_student', student_id=student_id))
                student.department = request.form.get('department', '').strip()
                student.semester = request.form.get('semester', type=int)
                
                # Validate required fields
                if not all([student.first_name, student.last_name, student.father_name, student.department, student.semester]):
                    flash('Please fill all required fields (*).', 'danger')
                    return redirect(url_for('edit_student', student_id=student_id))
                
                db.session.commit()
                flash(f'Student {student.first_name} {student.last_name} updated successfully!', 'success')
                return redirect(url_for('manage_students'))
            except Exception as e:
                db.session.rollback()
                app.logger.error(f"Edit student error: {e}")
                flash(f'Error updating student: {str(e)}', 'danger')
                return redirect(url_for('edit_student', student_id=student_id))
        
        from datetime import datetime
        now = datetime.now()
        return render_template('edit_student.html', student=student, now=now)
    except Exception as e:
        app.logger.error(f"Edit student page error: {e}")
        flash('Error loading student details.', 'danger')
        return redirect(url_for('manage_students'))


@app.route('/delete_student/<int:student_id>')
@login_required
@role_required('Registrar')
def delete_student(student_id):
    """Delete a student."""
    try:
        student = db.session.get(Student, student_id)
        if not student:
            flash('Student not found.', 'danger')
            return redirect(url_for('manage_students'))
        
        student_name = f"{student.first_name} {student.last_name}"
        db.session.delete(student)
        db.session.commit()
        flash(f'Student {student_name} deleted successfully!', 'success')
        return redirect(url_for('manage_students'))
    except Exception as e:
        db.session.rollback()
        app.logger.error(f"Delete student error: {e}")
        flash(f'Error deleting student: {str(e)}', 'danger')
        return redirect(url_for('manage_students'))


@app.route('/student_login_credentials/<int:student_id>')
@login_required
@role_required('Registrar')
def student_login_credentials(student_id):
    """View student login credentials."""
    try:
        student = db.session.get(Student, student_id)
        if not student:
            flash('Student not found.', 'danger')
            return redirect(url_for('manage_students'))
        
        user = None
        if student.user_id:
            user = db.session.get(User, student.user_id)
        
        return render_template('student_credentials.html', student=student, user=user)
    except Exception as e:
        app.logger.error(f"View credentials error: {e}")
        flash('Error loading credentials.', 'danger')
        return redirect(url_for('manage_students'))


@app.route('/reset_student_password/<int:student_id>', methods=['GET', 'POST'])
@login_required
@role_required('Registrar')
def reset_student_password(student_id):
    """Reset student password to a temporary password."""
    try:
        student = db.session.get(Student, student_id)
        if not student:
            flash('Student not found.', 'danger')
            return redirect(url_for('manage_students'))
        
        user = None
        if student.user_id:
            user = db.session.get(User, student.user_id)
        
        if request.method == 'POST':
            # Generate temporary password
            import random
            import string
            new_password = ''.join(random.choices(string.ascii_uppercase + string.digits, k=8))
            
            # Update user password
            if user:
                user.password = generate_password_hash(new_password)
                # Force student to change password on next login
                try:
                    user.must_change_password = True
                except Exception:
                    pass
                db.session.commit()
                flash(f'Password reset successfully! New temporary password: <strong>{new_password}</strong><br>'
                      f'Please provide this password to the student.', 'success')
            else:
                flash('Student user account not found.', 'danger')
            
            return redirect(url_for('manage_students'))
        
        return render_template('reset_student_password.html', student=student, user=user)
    except Exception as e:
        db.session.rollback()
        app.logger.error(f"Reset password error: {e}")
        flash(f'Error resetting password: {str(e)}', 'danger')
        return redirect(url_for('manage_students'))


@app.route('/student_attendance', methods=['GET', 'POST'])
@login_required
@role_required('Registrar', 'Director', 'Dean', 'HOD', 'Faculty', 'Management')
def student_attendance():
    """Mark student attendance."""
    try:
        if request.method == 'POST':
            student_id = request.form.get('student_id', type=int)
            status = request.form.get('status')
            subject = request.form.get('subject')
            
            attendance = StudentAttendance(
                student_id=student_id,
                date=date.today(),
                status=status,
                marked_by=current_user.employee_id,
                subject=subject
            )
            
            db.session.add(attendance)
            db.session.commit()
            
            flash('Attendance recorded!', 'success')
            return redirect(url_for('student_attendance'))
        
        students = db.session.query(Student).all()
        return render_template('student_attendance.html', students=students)
    except Exception as e:
        db.session.rollback()
        app.logger.error(f"Student attendance error: {e}")
        flash(f'Error recording attendance: {str(e)}', 'danger')
        return redirect(url_for('dashboard'))


@app.route('/my_attendance')
@login_required
@role_required('Student')
def my_attendance():
    """View logged-in student's attendance records."""
    try:
        student = db.session.query(Student).filter_by(user_id=current_user.employee_id).first()
        if not student:
            flash('Student record not found.', 'danger')
            return redirect(url_for('dashboard'))

        attendances = db.session.query(StudentAttendance).filter_by(student_id=student.id).order_by(StudentAttendance.date.desc()).all()
        return render_template('my_attendance.html', student=student, attendance_records=attendances)
    except Exception as e:
        app.logger.error(f"My attendance error: {e}")
        flash('Error loading attendance.', 'danger')
        return redirect(url_for('dashboard'))


@app.route('/change_password', methods=['GET', 'POST'])
@login_required
def change_password():
    """Allow user to change their password. If they were forced, unset the flag."""
    if request.method == 'POST':
        current_pwd = request.form.get('current_password', '')
        new_pwd = request.form.get('new_password', '').strip()
        confirm_pwd = request.form.get('confirm_password', '').strip()

        if not new_pwd or len(new_pwd) < 6:
            flash('New password must be at least 6 characters long.', 'danger')
            return redirect(url_for('change_password'))
        if new_pwd != confirm_pwd:
            flash('New password and confirmation do not match.', 'danger')
            return redirect(url_for('change_password'))

        try:
            user = db.session.get(User, current_user.employee_id)
            # If current password provided, verify it (optional)
            if current_pwd:
                if not check_password_hash(user.password, current_pwd):
                    flash('Current password is incorrect.', 'danger')
                    return redirect(url_for('change_password'))

            user.password = generate_password_hash(new_pwd)
            try:
                user.must_change_password = False
            except Exception:
                pass
            db.session.commit()
            flash('Password changed successfully.', 'success')
            return redirect(url_for('dashboard'))
        except Exception as e:
            db.session.rollback()
            app.logger.error(f"Change password error: {e}")
            flash('Error changing password.', 'danger')
            return redirect(url_for('change_password'))

    return render_template('change_password.html')


@app.route('/manage_grades', methods=['GET'])
@login_required
@role_required('Registrar', 'Director', 'Dean', 'HOD', 'Faculty', 'Management')
def manage_grades():
    """View student grades with department, year, and subject filters."""
    try:
        # Get filter parameters
        department_filter = request.args.get('department', '')
        year_filter = request.args.get('year', type=int)
        subject_filter = request.args.get('subject', '')
        
        # Get grades with filters
        grades_query = db.session.query(Grade)
        
        # Build student query with filters
        students_query = db.session.query(Student)
        
        if department_filter:
            students_query = students_query.filter_by(department=department_filter)
        
        if year_filter:
            # Convert year to semester range (year 1 = sems 1-2, year 2 = sems 3-4, etc)
            sem_start = (year_filter - 1) * 2 + 1
            sem_end = year_filter * 2
            students_query = students_query.filter(Student.semester.in_([sem_start, sem_end]))
        
        students = students_query.order_by(Student.roll_number).all()
        
        # Filter grades by selected students
        if students:
            student_ids = [s.id for s in students]
            grades_query = grades_query.filter(Grade.student_id.in_(student_ids))
        
        # Further filter by subject if specified
        if subject_filter:
            grades_query = grades_query.filter(Grade.subject == subject_filter)
        
        grades = grades_query.all()
        
        # Get unique departments for filter dropdown
        departments = db.session.query(Student.department).filter(Student.department != None).distinct().all()
        departments = [d[0] for d in departments if d[0]]
        
        # Get unique years from semester data
        semesters = db.session.query(Student.semester).filter(Student.semester != None).distinct().all()
        years = sorted(set((s[0] - 1) // 2 + 1 for s in semesters if s[0]))
        
        # Get unique subjects from grades
        subjects = db.session.query(Grade.subject).filter(Grade.subject != None).distinct().all()
        subjects = sorted([s[0] for s in subjects if s[0]])
        
        return render_template('manage_grades.html', 
                             students=students, 
                             grades=grades, 
                             departments=departments,
                             years=years,
                             subjects=subjects,
                             selected_department=department_filter,
                             selected_year=year_filter,
                             selected_subject=subject_filter)
    except Exception as e:
        db.session.rollback()
        app.logger.error(f"Manage grades error: {e}")
        flash(f'Error managing grades: {str(e)}', 'danger')
        return redirect(url_for('dashboard'))


@app.route('/bulk_grades', methods=['GET', 'POST'])
@login_required
def bulk_grades():
    """Bulk grade entry for multiple students in table format. Faculty can only grade their assigned subjects."""
    try:
        if request.method == 'POST':
            # Handle bulk grade submission - expect JSON from frontend
            try:
                data = request.get_json()
                if not data:
                    return jsonify({'error': 'No data provided'}), 400
                
                grades_data = data.get('grades_data')
                subject_id = data.get('subject_id')
                exam_type = data.get('exam_type')
                max_marks_val = data.get('max_marks', 100)
                
                if not grades_data or not isinstance(grades_data, list):
                    return jsonify({'error': 'Invalid grades data format'}), 400
                if not subject_id:
                    return jsonify({'error': 'Subject ID is required'}), 400
                if not exam_type:
                    return jsonify({'error': 'Exam type is required'}), 400
                
                subject = db.session.query(Subject).get(subject_id)
                if not subject:
                    return jsonify({'error': 'Subject not found'}), 404
                
                # If user is Faculty, verify they teach this subject
                if current_user.role == 'Faculty':
                    if subject.faculty_id != current_user.employee_id:
                        return jsonify({'error': 'You can only add grades for your assigned subjects'}), 403
                
                saved_count = 0
                try:
                    for grade_entry in grades_data:
                        if not isinstance(grade_entry, dict):
                            continue
                            
                        student_id = grade_entry.get('student_id')
                        marks = grade_entry.get('marks')
                        remarks = grade_entry.get('remarks', '')
                        
                        if marks is None or marks == '':
                            continue
                        
                        try:
                            marks = float(marks)
                        except (ValueError, TypeError):
                            continue
                        
                        max_marks = float(max_marks_val) if max_marks_val else 100.0
                        
                        # Calculate grade
                        percentage = (marks / max_marks * 100) if max_marks > 0 else 0
                        if percentage >= 90:
                            grade = 'A+'
                        elif percentage >= 80:
                            grade = 'A'
                        elif percentage >= 70:
                            grade = 'B'
                        elif percentage >= 60:
                            grade = 'C'
                        else:
                            grade = 'F'
                        
                        # Check if grade already exists
                        existing_grade = db.session.query(Grade).filter_by(
                            student_id=student_id,
                            subject=subject.name,
                            exam_type=exam_type,
                            semester=subject.semester
                        ).first()
                        
                        if existing_grade:
                            # Update existing
                            existing_grade.marks = marks
                            existing_grade.max_marks = max_marks
                            existing_grade.grade = grade
                            existing_grade.remarks = remarks if remarks else None
                            existing_grade.marked_by = current_user.employee_id
                        else:
                            # Create new
                            new_grade = Grade(
                                student_id=student_id,
                                subject=subject.name,
                                marks=marks,
                                max_marks=max_marks,
                                grade=grade,
                                semester=subject.semester,
                                exam_type=exam_type,
                                remarks=remarks if remarks else None,
                                marked_by=current_user.employee_id
                            )
                            db.session.add(new_grade)
                        
                        saved_count += 1
                    
                    db.session.commit()
                    return jsonify({'success': True, 'message': f'{saved_count} grades saved successfully'}), 200
                
                except Exception as e:
                    db.session.rollback()
                    app.logger.error(f"Error saving grades: {e}")
                    return jsonify({'error': f'Error saving grades: {str(e)}'}), 400
            
            except Exception as e:
                app.logger.error(f"Bulk grades POST error: {e}")
                return jsonify({'error': str(e)}), 400
        
        # GET request - show bulk entry form
        # Get academic years (semesters converted to years)
        semester_rows = db.session.query(Student.semester).filter(Student.semester != None).distinct().all()
        semesters = sorted(set(s[0] for s in semester_rows if s[0]))
        years = [{'value': (s-1)//2 + 1, 'label': f'Year {(s-1)//2 + 1}'} for s in semesters]
        # Remove duplicates
        years = {y['value']: y for y in years}.values()
        years = sorted(years, key=lambda x: x['value'])
        
        # Get departments - if Faculty, only show their assigned subjects' departments
        if current_user.role == 'Faculty':
            # Get departments from their assigned subjects
            faculty_subjects = db.session.query(Subject).filter_by(faculty_id=current_user.employee_id).all()
            departments = list(set(s.department for s in faculty_subjects))
            departments = sorted(departments) if departments else []
        else:
            # Show all departments for non-faculty users
            departments = db.session.query(Student.department).filter(Student.department != None).distinct().all()
            departments = sorted([d[0] for d in departments if d[0]])
        
        return render_template('bulk_grades.html', years=years, departments=departments)
    
    except Exception as e:
        db.session.rollback()
        app.logger.error(f"Bulk grades error: {e}")
        flash(f'Error: {str(e)}', 'danger')
        return redirect(url_for('dashboard'))


@app.route('/faculty_grades', methods=['GET', 'POST'])
@login_required
@role_required('Faculty')
def faculty_grades():
    """Faculty add grades for their assigned subjects."""
    try:
        current_faculty_id = current_user.employee_id
        
        if request.method == 'POST':
            # Handle grade submission
            try:
                data = request.get_json()
                if not data:
                    return jsonify({'error': 'No data provided'}), 400
                
                grades_data = data.get('grades_data')
                subject_id = data.get('subject_id')
                exam_type = data.get('exam_type')
                max_marks_val = data.get('max_marks', 100)
                
                if not grades_data or not isinstance(grades_data, list):
                    return jsonify({'error': 'Invalid grades data format'}), 400
                if not subject_id:
                    return jsonify({'error': 'Subject ID is required'}), 400
                if not exam_type:
                    return jsonify({'error': 'Exam type is required'}), 400
                
                subject = db.session.query(Subject).get(subject_id)
                if not subject:
                    return jsonify({'error': 'Subject not found'}), 404
                
                # Verify this subject belongs to the faculty member
                if subject.faculty_id != current_faculty_id:
                    return jsonify({'error': 'You can only add grades for your assigned subjects'}), 403
                
                saved_count = 0
                try:
                    for grade_entry in grades_data:
                        if not isinstance(grade_entry, dict):
                            continue
                            
                        student_id = grade_entry.get('student_id')
                        marks = grade_entry.get('marks')
                        remarks = grade_entry.get('remarks', '')
                        
                        if marks is None or marks == '':
                            continue
                        
                        try:
                            marks = float(marks)
                        except (ValueError, TypeError):
                            continue
                        
                        max_marks = float(max_marks_val) if max_marks_val else 100.0
                        
                        # Calculate grade
                        percentage = (marks / max_marks * 100) if max_marks > 0 else 0
                        if percentage >= 90:
                            grade = 'A+'
                        elif percentage >= 80:
                            grade = 'A'
                        elif percentage >= 70:
                            grade = 'B'
                        elif percentage >= 60:
                            grade = 'C'
                        else:
                            grade = 'F'
                        
                        # Check if grade already exists
                        existing_grade = db.session.query(Grade).filter_by(
                            student_id=student_id,
                            subject=subject.name,
                            exam_type=exam_type,
                            semester=subject.semester
                        ).first()
                        
                        if existing_grade:
                            # Update existing
                            existing_grade.marks = marks
                            existing_grade.max_marks = max_marks
                            existing_grade.grade = grade
                            existing_grade.remarks = remarks if remarks else None
                            existing_grade.marked_by = current_user.employee_id
                        else:
                            # Create new
                            new_grade = Grade(
                                student_id=student_id,
                                subject=subject.name,
                                marks=marks,
                                max_marks=max_marks,
                                grade=grade,
                                semester=subject.semester,
                                exam_type=exam_type,
                                remarks=remarks if remarks else None,
                                marked_by=current_user.employee_id
                            )
                            db.session.add(new_grade)
                        
                        saved_count += 1
                    
                    db.session.commit()
                    return jsonify({'success': True, 'message': f'{saved_count} grades saved successfully'}), 200
                
                except Exception as e:
                    db.session.rollback()
                    app.logger.error(f"Error saving faculty grades: {e}")
                    return jsonify({'error': f'Error saving grades: {str(e)}'}), 400
            
            except Exception as e:
                app.logger.error(f"Faculty grades POST error: {e}")
                return jsonify({'error': str(e)}), 400
        
        # GET request - show subjects assigned to this faculty
        faculty_subjects = db.session.query(Subject).filter_by(faculty_id=current_faculty_id).all()
        
        if not faculty_subjects:
            flash('No subjects assigned to you yet.', 'info')
            return render_template('faculty_grades.html', subjects=[], students=[], grades=[])
        
        # Get all students enrolled in these subjects
        subject_ids = [s.id for s in faculty_subjects]
        enrollments = db.session.query(SubjectEnrollment).filter(SubjectEnrollment.subject_id.in_(subject_ids)).all()
        student_ids = [e.student_id for e in enrollments]
        
        # If no SubjectEnrollments, get students from same department and semester as subjects
        if not student_ids:
            # Get all students in the departments of these subjects
            departments = list(set(s.department for s in faculty_subjects))
            semesters_for_subjects = list(set(s.semester for s in faculty_subjects))
            students = db.session.query(Student).filter(
                Student.department.in_(departments),
                Student.semester.in_(semesters_for_subjects)
            ).order_by(Student.roll_number).all()
            student_ids = [s.id for s in students]
        else:
            students = db.session.query(Student).filter(Student.id.in_(student_ids)).all()
        
        grades = db.session.query(Grade).filter(Grade.student_id.in_(student_ids)).all() if student_ids else []
        
        return render_template('faculty_grades.html', 
                             subjects=faculty_subjects,
                             students=students,
                             grades=grades)
    
    except Exception as e:
        db.session.rollback()
        app.logger.error(f"Faculty grades error: {e}")
        flash(f'Error: {str(e)}', 'danger')
        return redirect(url_for('dashboard'))


@app.route('/api/subjects', methods=['GET'])
@login_required
def get_subjects():
    """Get subjects for a given department and semester. Faculty can only see their assigned subjects."""
    department = request.args.get('department', '')
    year = request.args.get('year', type=int)
    
    if not department or not year:
        return jsonify([]), 400
    
    # Calculate semester range from year
    sem_start = (year - 1) * 2 + 1
    sem_end = year * 2
    
    # Build base query
    query = db.session.query(Subject).filter(
        Subject.department == department,
        Subject.semester.in_([sem_start, sem_end])
    )
    
    # If Faculty, only show their assigned subjects
    if current_user.role == 'Faculty':
        query = query.filter(Subject.faculty_id == current_user.employee_id)
    
    subjects = query.all()
    
    return jsonify([{
        'id': s.id,
        'name': s.name,
        'code': s.code,
        'semester': s.semester,
        'faculty_id': s.faculty_id,
        'faculty_name': s.faculty.name if s.faculty else 'Unassigned',
        'max_marks': s.max_marks
    } for s in subjects])


@app.route('/api/students', methods=['GET'])
@login_required
def get_students_for_subject():
    """Get students for a given department, year, and subject. Faculty can only see students for their subjects."""
    department = request.args.get('department', '')
    year = request.args.get('year', type=int)
    subject_id = request.args.get('subject_id', type=int)
    
    if not department or not year or not subject_id:
        return jsonify([]), 400
    
    # If Faculty, verify they teach this subject
    if current_user.role == 'Faculty':
        subject = db.session.query(Subject).get(subject_id)
        if not subject or subject.faculty_id != current_user.employee_id:
            return jsonify({'error': 'Unauthorized'}), 403
    
    # Calculate semester range from year
    sem_start = (year - 1) * 2 + 1
    sem_end = year * 2
    
    # Get students from the department in the specified year
    students = db.session.query(Student).filter(
        Student.department == department,
        Student.semester.in_([sem_start, sem_end])
    ).order_by(Student.roll_number).all()
    
    return jsonify([{
        'id': s.id,
        'roll_number': s.roll_number,
        'name': s.name,
        'semester': s.semester
    } for s in students])


@app.route('/api/faculty_students', methods=['GET'])
@login_required
@role_required('Faculty')
def get_faculty_students():
    """Get students enrolled in a subject taught by this faculty member."""
    subject_id = request.args.get('subject_id', type=int)
    
    if not subject_id:
        return jsonify([]), 400
    
    # Verify the subject belongs to the current faculty
    subject = db.session.query(Subject).get(subject_id)
    if not subject or subject.faculty_id != current_user.employee_id:
        return jsonify({'error': 'Unauthorized'}), 403
    
    # Get students enrolled in this subject through SubjectEnrollment
    enrollments = db.session.query(SubjectEnrollment).filter_by(subject_id=subject_id).all()
    student_ids = [e.student_id for e in enrollments]
    
    # If no enrollments, get all students in the same semester and department
    if not student_ids:
        students = db.session.query(Student).filter(
            Student.department == subject.department,
            Student.semester.in_([subject.semester, subject.semester - 1])
        ).order_by(Student.roll_number).all()
    else:
        students = db.session.query(Student).filter(Student.id.in_(student_ids)).order_by(Student.roll_number).all()
    
    return jsonify([{
        'id': s.id,
        'roll_number': s.roll_number,
        'name': s.name,
        'semester': s.semester
    } for s in students])


# ==================== LIBRARY ====================

@app.route('/manage_books')
@login_required
@role_required('Registrar', 'Director', 'Dean', 'Library', 'Library Head', 'Management')
def manage_books():
    """Manage library books."""
    try:
        books = db.session.query(Book).all()
        return render_template('library_books.html', books=books)
    except Exception as e:
        app.logger.error(f"Manage books error: {e}")
        flash('Error loading books.', 'danger')
        return redirect(url_for('dashboard'))


@app.route('/add_book', methods=['GET', 'POST'])
@login_required
@role_required('Registrar', 'Director', 'Dean', 'Library', 'Library Head', 'Management')
def add_book():
    """Add new book."""
    if request.method == 'POST':
        try:
            title = request.form.get('title')
            author = request.form.get('author')
            edition = request.form.get('edition')
            if edition:
                edition = edition.strip() or None
            isbn = request.form.get('isbn')
            category = request.form.get('category')
            quantity = request.form.get('quantity', type=int, default=1)
            shelf_location = request.form.get('shelf_location')

            # Validate uniqueness
            # 1) ISBN must be unique if provided.
            if isbn:
                existing = db.session.query(Book).filter_by(isbn=isbn).first()
                if existing:
                    flash('A book with the same ISBN already exists.', 'danger')
                    return redirect(url_for('add_book'))

            # 2) If edition is provided, enforce uniqueness for title+author+edition.
            #    Otherwise, enforce uniqueness for title+author with empty/missing edition.
            if title and author:
                query = db.session.query(Book).filter_by(title=title, author=author)
                if edition:
                    query = query.filter_by(edition=edition)
                else:
                    query = query.filter((Book.edition == None) | (Book.edition == ''))
                existing = query.first()
                if existing:
                    flash('A book with the same title, author and edition already exists.', 'danger')
                    return redirect(url_for('add_book'))

            # Generate a unique book code for tracking
            book_code = generate_book_code()

            new_book = Book(
                book_code=book_code,
                title=title,
                author=author,
                edition=edition,
                isbn=isbn,
                category=category,
                quantity=quantity,
                available_quantity=quantity,
                shelf_location=shelf_location
            )

            db.session.add(new_book)
            db.session.commit()

            flash(f'Book "{title}" added successfully!', 'success')
            return redirect(url_for('manage_books'))
        except Exception as e:
            db.session.rollback()
            app.logger.error(f"Add book error: {e}")
            flash(f'Error adding book: {str(e)}', 'danger')
    
    return render_template('add_book.html')



@app.route('/edit_book/<int:book_id>', methods=['GET', 'POST'])
@login_required
@role_required('Registrar', 'Director', 'Dean', 'Library', 'Library Head', 'Management')
def edit_book(book_id):
    """Edit book."""
    try:
        book = db.session.get(Book, book_id)
        if not book:
            flash('Book not found.', 'danger')
            return redirect(url_for('manage_books'))

        if request.method == 'POST':
            new_title = request.form.get('title')
            new_author = request.form.get('author')
            new_edition = request.form.get('edition')
            if new_edition:
                new_edition = new_edition.strip() or None
            new_isbn = request.form.get('isbn')

            # Prevent ISBN duplicates when editing an existing book
            if new_isbn and new_isbn != book.isbn:
                existing = db.session.query(Book).filter_by(isbn=new_isbn).first()
                if existing:
                    flash('A book with the same ISBN already exists.', 'danger')
                    return redirect(url_for('edit_book', book_id=book_id))

            # Prevent duplicate title+author+edition when editing
            if new_title and new_author:
                query = db.session.query(Book).filter_by(title=new_title, author=new_author)
                if new_edition:
                    query = query.filter_by(edition=new_edition)
                else:
                    query = query.filter((Book.edition == None) | (Book.edition == ''))
                existing = query.first()
                if existing and existing.book_id != book.book_id:
                    flash('A book with the same title, author and edition already exists.', 'danger')
                    return redirect(url_for('edit_book', book_id=book_id))

            book.title = new_title
            book.author = new_author
            book.edition = new_edition
            book.isbn = new_isbn
            book.category = request.form.get('category')
            book.quantity = request.form.get('quantity', type=int)
            book.shelf_location = request.form.get('shelf_location')

            # Ensure available_quantity is not negative
            if book.available_quantity is None:
                book.available_quantity = book.quantity
            else:
                book.available_quantity = max(0, min(book.available_quantity, book.quantity))

            db.session.commit()
            flash('Book updated successfully!', 'success')
            return redirect(url_for('manage_books'))

        return render_template('edit_book.html', book=book)
    except Exception as e:
        db.session.rollback()
        app.logger.error(f"Edit book error: {e}")
        flash('Error updating book.', 'danger')
        return redirect(url_for('manage_books'))


@app.route('/delete_book/<int:book_id>')
@login_required
@role_required('Registrar', 'Director', 'Dean', 'Library', 'Library Head', 'Management')
def delete_book(book_id):
    """Delete book."""
    try:
        book = db.session.get(Book, book_id)
        if not book:
            flash('Book not found.', 'danger')
            return redirect(url_for('manage_books'))

        db.session.delete(book)
        db.session.commit()
        flash('Book deleted successfully!', 'success')
        return redirect(url_for('manage_books'))
    except Exception as e:
        db.session.rollback()
        app.logger.error(f"Delete book error: {e}")
        flash('Error deleting book.', 'danger')
        return redirect(url_for('manage_books'))


@app.route('/issue_book', methods=['GET', 'POST'])
@login_required
@role_required('Registrar', 'Director', 'Dean', 'Library', 'Library Head', 'Management')
def issue_book():
    """Issue book to employee."""
    if request.method == 'POST':
        try:
            book_id = request.form.get('book_id', type=int)
            employee_id = request.form.get('employee_id')
            due_date_str = request.form.get('due_date')
            # If due_date not provided by form, default to 14 days from today
            if not due_date_str:
                due_date = date.today() + timedelta(days=14)
            else:
                due_date = datetime.strptime(due_date_str, '%Y-%m-%d').date()
            
            book = db.session.get(Book, book_id)
            if not book or book.available_quantity <= 0:
                flash('Book not available!', 'danger')
                return redirect(url_for('issue_book'))
            
            transaction = BookTransaction(
                book_id=book_id,
                employee_id=employee_id,
                issue_date=date.today(),
                due_date=due_date,
                status='Issued'
            )
            
            book.available_quantity -= 1
            db.session.add(transaction)
            db.session.commit()
            
            flash('Book issued successfully!', 'success')
            return redirect(url_for('issue_book'))
        except Exception as e:
            db.session.rollback()
            app.logger.error(f"Issue book error: {e}")
            flash(f'Error issuing book: {str(e)}', 'danger')
    
    books = db.session.query(Book).all()
    employees = db.session.query(User).all()
    return render_template('issue_book.html', books=books, employees=employees)


@app.route('/library_transactions')
@login_required
@role_required('Registrar', 'Director', 'Dean', 'Library', 'Library Head', 'Management')
def library_transactions():
    """View library transactions."""
    try:
        transactions = db.session.query(BookTransaction).order_by(BookTransaction.issue_date.desc()).all()
        return render_template('library_transactions.html', transactions=transactions)
    except Exception as e:
        app.logger.error(f"Library transactions error: {e}")
        flash('Error loading transactions.', 'danger')
        return redirect(url_for('dashboard'))


@app.route('/return_book/<int:transaction_id>', methods=['POST'])
@login_required
@role_required('Registrar', 'Director', 'Dean', 'Library', 'Library Head', 'Management')
def return_book(transaction_id):
    """Mark an issued book as returned."""
    try:
        transaction = db.session.get(BookTransaction, transaction_id)
        if not transaction:
            flash('Transaction not found.', 'danger')
            return redirect(url_for('library_transactions'))

        if transaction.status != 'Issued':
            flash('Book has already been returned.', 'info')
            return redirect(url_for('library_transactions'))

        transaction.status = 'Returned'
        transaction.return_date = date.today()

        if transaction.book:
            transaction.book.available_quantity = min(
                transaction.book.quantity,
                (transaction.book.available_quantity or 0) + 1
            )

        db.session.commit()
        flash('Book returned successfully!', 'success')
    except Exception as e:
        db.session.rollback()
        app.logger.error(f"Return book error: {e}")
        flash('Error returning book.', 'danger')

    return redirect(url_for('library_transactions'))


@app.route('/library_dashboard')
@login_required
@role_required('Registrar', 'Director', 'Dean', 'Library', 'Library Head', 'Management')
def library_dashboard():
    """Combined library dashboard with books and transactions."""
    try:
        # Search / sort for books
        search = request.args.get('q', '').strip()
        sort_by = request.args.get('sort_by', 'title')
        order = request.args.get('order', 'asc')

        book_query = db.session.query(Book)

        if search:
            search_term = f"%{search}%"
            book_query = book_query.filter(
                Book.title.ilike(search_term) |
                Book.author.ilike(search_term) |
                Book.isbn.ilike(search_term) |
                Book.book_code.ilike(search_term) |
                Book.edition.ilike(search_term)
            )

        # Sorting
        sort_column = {
            'title': Book.title,
            'author': Book.author,
            'edition': Book.edition,
            'available': Book.available_quantity,
            'code': Book.book_code,
        }.get(sort_by, Book.title)

        if order == 'desc':
            sort_column = sort_column.desc()

        books = book_query.order_by(sort_column).all()

        stats = {
            'total_books': db.session.query(Book).count(),
            'available_books': db.session.query(Book).filter(Book.available_quantity > 0).count(),
            'books_issued': db.session.query(BookTransaction).filter_by(status='Issued').count(),
        }
        transactions = db.session.query(BookTransaction).order_by(BookTransaction.issue_date.desc()).limit(200).all()
        return render_template(
            'library_dashboard.html',
            stats=stats,
            books=books,
            transactions=transactions,
            search=search,
            sort_by=sort_by,
            order=order
        )
    except Exception as e:
        app.logger.error(f"Library dashboard error: {e}")
        flash('Error loading library dashboard.', 'danger')
        return redirect(url_for('dashboard'))


# ==================== FINANCE ====================

@app.route('/manage_salaries')
@login_required
@role_required('Registrar', 'Director', 'Dean', 'Accountant', 'HR', 'Management')
def manage_salaries():
    """Manage employee salaries."""
    try:
        salaries = db.session.query(Salary).all()
        return render_template('manage_salaries.html', salaries=salaries)
    except Exception as e:
        app.logger.error(f"Manage salaries error: {e}")
        flash('Error loading salaries.', 'danger')
        return redirect(url_for('dashboard'))


@app.route('/add_salary', methods=['GET', 'POST'])
@login_required
@role_required('Registrar', 'Director', 'Dean', 'Accountant', 'Management')
def add_salary():
    """Add salary entry."""
    if request.method == 'POST':
        try:
            employee_id = request.form.get('employee_id')
            month = request.form.get('month', type=int)
            year = request.form.get('year', type=int)
            basic_salary = request.form.get('basic_salary', type=float)
            hra = request.form.get('hra', type=float, default=0)
            da = request.form.get('da', type=float, default=0)
            allowances = request.form.get('allowances', type=float, default=0)
            deductions = request.form.get('deductions', type=float, default=0)
            
            net_salary = basic_salary + hra + da + allowances - deductions
            
            salary = Salary(
                employee_id=employee_id,
                month=month,
                year=year,
                basic_salary=basic_salary,
                hra=hra,
                da=da,
                allowances=allowances,
                deductions=deductions,
                net_salary=net_salary,
                payment_status='Pending'
            )
            
            db.session.add(salary)
            db.session.commit()
            
            flash('Salary entry added successfully!', 'success')
            return redirect(url_for('manage_salaries'))
        except Exception as e:
            db.session.rollback()
            app.logger.error(f"Add salary error: {e}")
            flash(f'Error adding salary: {str(e)}', 'danger')
    
    employees = db.session.query(User).all()
    return render_template('add_salary.html', employees=employees)


@app.route('/manage_expenses')
@login_required
@role_required('Registrar', 'Director', 'Dean', 'Accountant', 'Management')
def manage_expenses():
    """Manage expenses."""
    try:
        expenses = db.session.query(Expense).all()
        return render_template('manage_expenses.html', expenses=expenses)
    except Exception as e:
        app.logger.error(f"Manage expenses error: {e}")
        flash('Error loading expenses.', 'danger')
        return redirect(url_for('dashboard'))


@app.route('/add_expense', methods=['GET', 'POST'])
@login_required
def add_expense():
    """Add expense entry."""
    if request.method == 'POST':
        try:
            category = request.form.get('category')
            description = request.form.get('description')
            amount = request.form.get('amount', type=float)
            expense_date = datetime.strptime(request.form.get('date'), '%Y-%m-%d').date()
            
            expense = Expense(
                category=category,
                description=description,
                amount=amount,
                date=expense_date,
                submitted_by=current_user.employee_id,
                status='Pending'
            )
            
            db.session.add(expense)
            db.session.commit()
            
            flash('Expense submitted successfully!', 'success')
            return redirect(url_for('manage_expenses'))
        except Exception as e:
            db.session.rollback()
            app.logger.error(f"Add expense error: {e}")
            flash(f'Error adding expense: {str(e)}', 'danger')
    
    return render_template('manage_expenses.html')


# ==================== USER PROFILE ====================

@app.route('/profile')
@login_required
def profile():
    """User profile page."""
    return render_template('profile.html', user=current_user)


@app.route('/edit_profile', methods=['GET', 'POST'])
@login_required
def edit_profile():
    """Edit user profile."""
    if request.method == 'POST':
        try:
            current_user.name = request.form.get('name', current_user.name)
            current_user.email = request.form.get('email', current_user.email)
            current_user.phone = request.form.get('phone', current_user.phone)
            
            db.session.commit()
            flash('Profile updated successfully!', 'success')
            return redirect(url_for('profile'))
        except Exception as e:
            db.session.rollback()
            app.logger.error(f"Edit profile error: {e}")
            flash(f'Error updating profile: {str(e)}', 'danger')
    
    return render_template('edit_profile.html', user=current_user)


# ==================== REPORTS ====================

@app.route('/reports')
@login_required
@role_required('Registrar', 'Director', 'Dean', 'HOD', 'Accountant', 'HR', 'Management')
def reports():
    """Reports page."""
    return render_template('reports.html')


@app.route('/employee_report')
@login_required
@role_required('Registrar', 'Director', 'Dean', 'HR', 'Management')
def employee_report():
    """Employee report."""
    try:
        employees = db.session.query(User).all()
        return render_template('employee_report.html', employees=employees)
    except Exception as e:
        app.logger.error(f"Employee report error: {e}")
        flash('Error loading employee report.', 'danger')
        return redirect(url_for('reports'))


@app.route('/attendance_report')
@login_required
@role_required('Registrar', 'Director', 'Dean', 'HR', 'HOD', 'Management')
def attendance_report():
    """Attendance report."""
    try:
        attendance = db.session.query(Attendance).all()
        return render_template('attendance_report.html', attendance=attendance)
    except Exception as e:
        app.logger.error(f"Attendance report error: {e}")
        flash('Error loading attendance report.', 'danger')
        return redirect(url_for('reports'))


@app.route('/finance_report')
@login_required
@role_required('Registrar', 'Director', 'Dean', 'Accountant', 'Management')
def finance_report():
    """Finance report."""
    try:
        salaries = db.session.query(Salary).all()
        expenses = db.session.query(Expense).all()
        return render_template('finance_report.html', salaries=salaries, expenses=expenses)
    except Exception as e:
        app.logger.error(f"Finance report error: {e}")
        flash('Error loading finance report.', 'danger')
        return redirect(url_for('reports'))


@app.route('/library_report')
@login_required
@role_required('Registrar', 'Director', 'Dean', 'Library', 'Library Head', 'Librarian', 'Management')
def library_report():
    """Library report / dashboard with key metrics."""
    try:
        books = db.session.query(Book).all()

        # filters from querystring
        start_date = request.args.get('start_date')
        end_date = request.args.get('end_date')
        status = request.args.get('status')

        tx_query = db.session.query(BookTransaction)
        # apply status filter
        if status and status.lower() != 'all':
            tx_query = tx_query.filter(BookTransaction.status == status)
        # apply date range (issue_date)
        try:
            if start_date:
                sd = datetime.strptime(start_date, '%Y-%m-%d').date()
                tx_query = tx_query.filter(BookTransaction.issue_date >= sd)
            if end_date:
                ed = datetime.strptime(end_date, '%Y-%m-%d').date()
                tx_query = tx_query.filter(BookTransaction.issue_date <= ed)
        except Exception as e:
            app.logger.debug(f"Invalid date filter: {e}")

        transactions = tx_query.order_by(BookTransaction.issue_date.desc()).all()

        # compute summary numbers for the dashboard cards
        total_books = len(books)
        available_books = db.session.query(Book).filter(Book.available_quantity > 0).count()
        books_issued = db.session.query(BookTransaction).filter_by(status='Issued').count()

        # top-issued books (title, count)
        top_books = (
            db.session.query(
                Book.title,
                db.func.count(BookTransaction.id).label('issue_count')
            )
            .join(BookTransaction, Book.id == BookTransaction.book_id)
            .group_by(Book.id)
            .order_by(db.desc('issue_count'))
            .limit(5)
            .all()
        )

        return render_template(
            'library_report.html',
            books=books,
            transactions=transactions,
            total_books=total_books,
            available_books=available_books,
            books_issued=books_issued,
            top_books=top_books,
            filter_start=start_date,
            filter_end=end_date,
            filter_status=status or 'all'
        )
    except Exception as e:
        app.logger.error(f"Library report error: {e}")
        flash('Error loading library report.', 'danger')
        return redirect(url_for('reports'))


# ==================== ERROR HANDLERS ====================

@app.errorhandler(404)
def not_found(error):
    """Handle 404 errors."""
    return render_template('error.html', error='Page not found (404)'), 404


@app.errorhandler(403)
def forbidden(error):
    """Handle 403 errors."""
    return render_template('error.html', error='Access forbidden (403)'), 403


@app.errorhandler(500)
def internal_error(error):
    """Handle 500 errors."""
    db.session.rollback()
    app.logger.error(f"Internal server error: {error}")
    return render_template('error.html', error='Internal server error (500)'), 500


# ==================== DATABASE INITIALIZATION ====================

def init_db():
    """Initialize database with sample data."""
    with app.app_context():
        try:
            db.create_all()

            # Ensure the new edition and book_code columns exist for existing databases
            try:
                result = db.session.execute(text("PRAGMA table_info(books)"))
                columns = [row['name'] for row in result.mappings().all()]
                if 'edition' not in columns:
                    db.session.execute(text("ALTER TABLE books ADD COLUMN edition TEXT"))
                    db.session.commit()
                    app.logger.info('Added edition column to books table')
                if 'book_code' not in columns:
                    db.session.execute(text("ALTER TABLE books ADD COLUMN book_code TEXT"))
                    db.session.commit()
                    app.logger.info('Added book_code column to books table')
                # add session_year to subjects if missing
                result = db.session.execute(text("PRAGMA table_info(subjects)"))
                subs_cols = [row['name'] for row in result.mappings().all()]
                if 'session_year' not in subs_cols:
                    db.session.execute(text("ALTER TABLE subjects ADD COLUMN session_year TEXT"))
                    db.session.commit()
                    app.logger.info('Added session_year column to subjects table')
            except Exception:
                # Some DBs may not support PRAGMA table_info or ALTER TABLE as expected.
                # Continue without failing the entire init.
                pass
            
            # Only seed sample users if database is empty
            if db.session.query(User).count() > 0:
                print("Database already populated. Skipping sample data initialization.")
                return
            
            # Add registrar user if not exists
            if not db.session.get(User, 'REG001'):
                registrar = User(
                    employee_id='REG001',
                    name='Registrar User',
                    email='registrar@aimt.edu',
                    phone='9876543210',
                    role='Registrar',
                    department='Administration',
                    designation='Registrar',
                    password=generate_password_hash('registrar123'),
                    is_active=True
                )
                db.session.add(registrar)
            
            # Add Director
            if not db.session.get(User, 'DIR001'):
                director = User(
                    employee_id='DIR001',
                    name='Director',
                    email='director@aimt.edu',
                    phone='9876543211',
                    role='Director',
                    department='Management',
                    designation='Director',
                    password=generate_password_hash('director123'),
                    is_active=True
                )
                db.session.add(director)
            
            # Add Dean
            if not db.session.get(User, 'DEAN001'):
                dean = User(
                    employee_id='DEAN001',
                    name='Dean',
                    email='dean@aimt.edu',
                    phone='9876543212',
                    role='Dean',
                    department='Management',
                    designation='Dean',
                    password=generate_password_hash('dean123'),
                    is_active=True
                )
                db.session.add(dean)
            
            # Add HOD
            if not db.session.get(User, 'HODCS01'):
                hod = User(
                    employee_id='HODCS01',
                    name='HOD - Computer Science',
                    email='hod@aimt.edu',
                    phone='9876543213',
                    role='HOD',
                    department='Computer Science',
                    designation='Head of Department',
                    assigned_course='CS101',
                    assigned_semester=1,
                    password=generate_password_hash('hod123'),
                    is_active=True
                )
                db.session.add(hod)
            
            # Add Faculty
            if not db.session.get(User, 'FAC001'):
                faculty = User(
                    employee_id='FAC001',
                    name='Faculty Member',
                    email='faculty@aimt.edu',
                    phone='9876543214',
                    role='Faculty',
                    department='Computer Science',
                    designation='Lecturer',
                    assigned_course='CS101',
                    assigned_semester=1,
                    password=generate_password_hash('faculty123'),
                    is_active=True
                )
                db.session.add(faculty)
            
            # Add Student
            if not db.session.get(User, 'STU001'):
                student_user = User(
                    employee_id='STU001',
                    name='Student User',
                    email='student@aimt.edu',
                    phone='9876543215',
                    role='Student',
                    department='Computer Science',
                    designation='Student',
                    password=generate_password_hash('student123'),
                    is_active=True
                )
                db.session.add(student_user)
                db.session.flush()
            
            # Only add student record if it doesn't exist by user_id or roll_number
            existing_student_by_user = db.session.query(Student).filter_by(user_id='STU001').first()
            existing_student_by_roll = db.session.query(Student).filter_by(roll_number='2024AITMCS0001').first()
            if not existing_student_by_user and not existing_student_by_roll:
                student = Student(
                    roll_number='2024AITMCS0001',
                    name='Student User',
                    email='student@aimt.edu',
                    phone='9876543215',
                    course='B.Tech',
                    semester=1,
                    department='Computer Science',
                    user_id='STU001'
                )
                db.session.add(student)
            
            # Add Accountant
            if not db.session.get(User, 'ACC001'):
                accountant = User(
                    employee_id='ACC001',
                    name='Accountant',
                    email='accountant@aimt.edu',
                    phone='9876543216',
                    role='Accountant',
                    department='Accounts',
                    designation='Accountant',
                    password=generate_password_hash('accountant123'),
                    is_active=True
                )
                db.session.add(accountant)
            
            # Add HR
            if not db.session.get(User, 'HR001'):
                hr = User(
                    employee_id='HR001',
                    name='HR Manager',
                    email='hr@aimt.edu',
                    phone='9876543217',
                    role='HR',
                    department='Human Resources',
                    designation='HR Manager',
                    password=generate_password_hash('hr123'),
                    is_active=True
                )
                db.session.add(hr)
            
            # Add Library Staff
            if not db.session.get(User, 'LIB001'):
                library = User(
                    employee_id='LIB001',
                    name='Library Head',
                    email='library@aimt.edu',
                    phone='9876543218',
                    role='Library',
                    department='Library',
                    designation='Library Head',
                    password=generate_password_hash('library123'),
                    is_active=True
                )
                db.session.add(library)
            
            db.session.commit()
            print("Database initialized successfully!")
            
        except Exception as e:
            db.session.rollback()
            app.logger.error(f"Database initialization error: {e}")
            print(f"Error initializing database: {e}")



# Helpers available in templates
@app.context_processor
def inject_helpers():
    """Expose utility functions to Jinja templates."""
    return dict(is_hod=is_hod)

# ==================== MAIN ====================

if __name__ == '__main__':
    init_db()
    app.run(debug=True, host='127.0.0.1', port=5000)
