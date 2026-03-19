from flask import Flask, render_template, redirect, url_for, request, flash, jsonify, session
from flask_sqlalchemy import SQLAlchemy
from flask_login import LoginManager, UserMixin, login_user, login_required, logout_user, current_user
from werkzeug.security import generate_password_hash, check_password_hash
from datetime import datetime, date, timedelta
from functools import wraps
import os
from sqlalchemy.exc import IntegrityError

# Initialize Flask app
app = Flask(__name__)
app.config.from_object('config.DevelopmentConfig')

# Initialize extensions
db = SQLAlchemy(app)
login_manager = LoginManager()
login_manager.init_app(app)
login_manager.login_view = 'login'

# ==================== DATABASE MODELS ====================

class User(UserMixin, db.Model):
    """User model for authentication."""
    __tablename__ = 'users'
    
    employee_id = db.Column(db.String(20), primary_key=True)
    password = db.Column(db.String(200), nullable=False)
    role = db.Column(db.String(50), nullable=False)
    name = db.Column(db.String(100), nullable=False)
    email = db.Column(db.String(100), unique=True, nullable=False)
    phone = db.Column(db.String(20))
    department = db.Column(db.String(100))
    designation = db.Column(db.String(100))
    # optional fields to support faculty/class assignments
    assigned_course = db.Column(db.String(50))            # for faculty: course they teach
    assigned_semester = db.Column(db.Integer)              # for faculty: semester they teach

    is_active = db.Column(db.Boolean, default=True)
    created_at = db.Column(db.DateTime, default=datetime.utcnow)
    
    def __repr__(self):
        return f'<User {self.employee_id} - {self.name} ({self.role})>'
    
    def get_id(self):
        return str(self.employee_id)


class Leave(db.Model):
    """Leave management model with department-based approval workflow."""
    __tablename__ = 'leaves'
    
    id = db.Column(db.Integer, primary_key=True)
    employee_id = db.Column(db.String(20), db.ForeignKey('users.employee_id'), nullable=False)
    leave_type = db.Column(db.String(50), nullable=False)
    start_date = db.Column(db.Date, nullable=False)
    end_date = db.Column(db.Date, nullable=False)
    reason = db.Column(db.Text)
    department = db.Column(db.String(100))  # Track employee's department for routing
    status = db.Column(db.String(20), default='Pending')  # Pending, Forwarded, Approved, Rejected
    forwarded_by = db.Column(db.String(20), db.ForeignKey('users.employee_id'))  # Department head (Registrar/HOD/Library Head/Finance Officer)
    approved_by = db.Column(db.String(20), db.ForeignKey('users.employee_id'))  # Director who approved
    created_at = db.Column(db.DateTime, default=datetime.utcnow)


class Attendance(db.Model):
    """Attendance tracking model."""
    __tablename__ = 'attendance'
    
    id = db.Column(db.Integer, primary_key=True)
    employee_id = db.Column(db.String(20), db.ForeignKey('users.employee_id'), nullable=False)
    date = db.Column(db.Date, nullable=False)
    status = db.Column(db.String(20), nullable=False)
    marked_by = db.Column(db.String(20), db.ForeignKey('users.employee_id'))
    remarks = db.Column(db.Text)
    created_at = db.Column(db.DateTime, default=datetime.utcnow)


class Book(db.Model):
    """Library books model."""
    __tablename__ = 'books'
    
    book_id = db.Column(db.Integer, primary_key=True)
    title = db.Column(db.String(200), nullable=False)
    author = db.Column(db.String(100))
    isbn = db.Column(db.String(20), unique=True)
    category = db.Column(db.String(50))
    quantity = db.Column(db.Integer, default=1)
    available_quantity = db.Column(db.Integer, default=1)
    shelf_location = db.Column(db.String(50))
    created_at = db.Column(db.DateTime, default=datetime.utcnow)


class BookTransaction(db.Model):
    """Library book issue/return transactions."""
    __tablename__ = 'book_transactions'
    
    id = db.Column(db.Integer, primary_key=True)
    book_id = db.Column(db.Integer, db.ForeignKey('books.book_id'), nullable=False)
    employee_id = db.Column(db.String(20), db.ForeignKey('users.employee_id'), nullable=False)
    issue_date = db.Column(db.Date, nullable=False)
    due_date = db.Column(db.Date, nullable=False)
    return_date = db.Column(db.Date)
    status = db.Column(db.String(20), default='Issued')


class Salary(db.Model):
    """Salary management model."""
    __tablename__ = 'salaries'
    
    id = db.Column(db.Integer, primary_key=True)
    employee_id = db.Column(db.String(20), db.ForeignKey('users.employee_id'), nullable=False)
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


class Expense(db.Model):
    """Expense tracking model."""
    __tablename__ = 'expenses'
    
    id = db.Column(db.Integer, primary_key=True)
    category = db.Column(db.String(50), nullable=False)
    description = db.Column(db.Text)
    amount = db.Column(db.Float, nullable=False)
    date = db.Column(db.Date, nullable=False)
    submitted_by = db.Column(db.String(20), db.ForeignKey('users.employee_id'))
    approved_by = db.Column(db.String(20), db.ForeignKey('users.employee_id'))
    status = db.Column(db.String(20), default='Pending')
    created_at = db.Column(db.DateTime, default=datetime.utcnow)


class Student(db.Model):
    """Student model for teaching staff and parent linkage."""
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
    department = db.Column(db.String(100))  # For HOD filtering
    # optional link back to user account for login
    user_id = db.Column(db.String(20), db.ForeignKey('users.employee_id'), unique=True)

    created_at = db.Column(db.DateTime, default=datetime.utcnow)


class StudentAttendance(db.Model):
    """Student attendance model."""
    __tablename__ = 'student_attendance'
    
    id = db.Column(db.Integer, primary_key=True)
    student_id = db.Column(db.Integer, db.ForeignKey('students.id'), nullable=False)
    date = db.Column(db.Date, nullable=False)
    status = db.Column(db.String(20), nullable=False)
    marked_by = db.Column(db.String(20), db.ForeignKey('users.employee_id'))
    subject = db.Column(db.String(50))
    created_at = db.Column(db.DateTime, default=datetime.utcnow)


class Grade(db.Model):
    """Student grades model."""
    __tablename__ = 'grades'
    
    id = db.Column(db.Integer, primary_key=True)
    student_id = db.Column(db.Integer, db.ForeignKey('students.id'), nullable=False)
    subject = db.Column(db.String(50), nullable=False)
    marks = db.Column(db.Float, nullable=False)
    grade = db.Column(db.String(5))
    semester = db.Column(db.Integer)
    exam_type = db.Column(db.String(50))
    marked_by = db.Column(db.String(20), db.ForeignKey('users.employee_id'))
    created_at = db.Column(db.DateTime, default=datetime.utcnow)


# ==================== HELPER FUNCTIONS ====================

@login_manager.user_loader
def load_user(employee_id):
    """Load user by employee ID."""
    return User.query.get(employee_id)


def role_required(*roles):
    """Decorator to check user role."""
    def decorator(f):
        @wraps(f)
        def decorated_function(*args, **kwargs):
            if not current_user.is_authenticated:
                return redirect(url_for('login'))
            if current_user.role not in roles:
                flash('You do not have permission to access this page.', 'danger')
                return redirect(url_for('dashboard'))
            return f(*args, **kwargs)
        return decorated_function
    return decorator


def get_dashboard_stats():
    """Get statistics for dashboard."""
    stats = {
        'total_employees': User.query.count(),
        'total_students': Student.query.count(),
        'total_books': Book.query.count(),
        'available_books': Book.query.filter(Book.available_quantity > 0).count(),
        'pending_leaves': Leave.query.filter_by(status='Pending').count(),
        'pending_expenses': Expense.query.filter_by(status='Pending').count(),
        'books_issued': BookTransaction.query.filter_by(status='Issued').count()
    }
    return stats


def generate_student_id(year: int, college_code: str, dept_code: str, seq_digits: int = 4):
    """Generate a unique student roll number using format YYYYCOLDEPTXXXX.

    Example: 2024AIMTCS0001
    """
    prefix = f"{year}{college_code.upper()}{dept_code.upper()}"
    # find the max existing sequence for this prefix
    last = Student.query.filter(Student.roll_number.startswith(prefix))\
                       .order_by(Student.roll_number.desc()).first()
    if last and len(last.roll_number) >= len(prefix) + seq_digits:
        try:
            last_seq = int(last.roll_number[-seq_digits:])
        except ValueError:
            last_seq = 0
        seq = last_seq + 1
    else:
        seq = 1
    return f"{prefix}{seq:0{seq_digits}d}"


def generate_employee_id(department: str, designation: str) -> str:
    """Generate a unique employee ID based on department and designation.
    
    Format: DDDNNN where DDD is department-designation code and NNN is sequential number.
    Examples: HRM001, DIR001, REG001, LEF001, PRO001, LBH001, etc.
    """
    # Mapping for department + designation combinations
    code_map = {
        ('Human Resources', 'HR Manager'): 'HRM',
        ('Human Resources', 'HR Assistant'): 'HRA',
        ('Management', 'Director'): 'DIR',
        ('Management', 'Dean'): 'DEN',
        ('Administration', 'Registrar'): 'REG',
        ('Administration', 'Administrative Officer'): 'AAO',
        ('Accounts', 'Finance Officer'): 'FFO',
        ('Accounts', 'Cashier'): 'CAS',
        ('Accounts', 'Accountant'): 'ACC',
        ('Library', 'Library Head'): 'LBH',
        ('Library', 'Librarian'): 'LBN',
    }
    
    # Teaching department codes
    teaching_codes = {
        'Head of Department': 'HOD',
        'Professor': 'PRO',
        'Lecturer': 'LEA'
    }
    
    # Check if it's a teaching department + designtion combination
    if designation in teaching_codes and department in ['MCA', 'BTECH', 'B.PHARMA', 'M.PHARMA', 'BCA', 'BBA', 'MBA']:
        # Use department code + teaching role code
        dept_short = department[:3].upper()  # MCA, BTE, BPH, MPH, BCA, BBA, MBA
        desig_code = teaching_codes[designation]
        prefix = f"{dept_short}{desig_code}"
    elif (department, designation) in code_map:
        prefix = code_map[(department, designation)]
    else:
        # Fallback: use first 3 chars of dept + first 3 chars of designation
        prefix = (department[:3] + designation[:3]).upper()[:6]
    
    # Find the max existing sequence for this prefix
    last = User.query.filter(User.employee_id.startswith(prefix))\
                     .order_by(User.employee_id.desc()).first()
    
    if last:
        try:
            # Extract the numeric part (last 3 digits)
            last_seq = int(last.employee_id[-3:])
            seq = last_seq + 1
        except (ValueError, IndexError):
            seq = 1
    else:
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
    """Login page."""
    if current_user.is_authenticated:
        return redirect(url_for('dashboard'))
    
    if request.method == 'POST':
        employee_id = request.form.get('employee_id')
        password = request.form.get('password')
        
        user = User.query.get(employee_id)
        
        if user and check_password_hash(user.password, password):
            if user.is_active:
                login_user(user)
                flash(f'Welcome back, {user.name}!', 'success')
                next_page = request.args.get('next')
                return redirect(next_page or url_for('dashboard'))
            else:
                flash('Your account has been deactivated.', 'danger')
        else:
            flash('Invalid Employee ID or password.', 'danger')
    
    return render_template('login.html')


@app.route('/logout')
@login_required
def logout():
    """Logout user."""
    logout_user()
    flash('You have been logged out successfully.', 'info')
    return redirect(url_for('login'))


# ==================== API ROUTES ====================

@app.route('/api/employee/<employee_id>')
@login_required
def get_employee_details(employee_id):
    """API endpoint to get employee details by ID (for auto-fill in forms)."""
    # Only HR and Registrar can access this
    if current_user.role not in ['HR', 'Registrar', 'Non-Teaching']:
        return jsonify({'error': 'Unauthorized'}), 403
    
    employee = User.query.get(employee_id)
    if not employee:
        return jsonify({'error': 'Employee not found'}), 404
    
    return jsonify({
        'employee_id': employee.employee_id,
        'name': employee.name,
        'role': employee.role,
        'department': employee.department,
        'designation': employee.designation
    })


# ==================== DASHBOARD ROUTES ====================

@app.route('/dashboard')
@login_required
def dashboard():
    """Main dashboard - role-specific with filtered data."""
    stats = get_dashboard_stats()
    
    # Filter data based on user role
    if current_user.role in ['Registrar', 'Director', 'Dean', 'Management', 'Administrative Officer', 'Non-Teaching']:
        # Registrar/Director/Dean/Management/AO see all data
        recent_leaves = Leave.query.order_by(Leave.created_at.desc()).limit(5).all()
        recent_expenses = Expense.query.order_by(Expense.created_at.desc()).limit(5).all()
        recent_transactions = BookTransaction.query.order_by(BookTransaction.issue_date.desc()).limit(5).all()
        grade_data = Grade.query.order_by(Grade.created_at.desc()).limit(5).all()
    elif current_user.role == 'HOD':
        # HOD sees only their department data
        recent_leaves = (Leave.query
                        .join(User, Leave.employee_id == User.employee_id)
                        .filter(User.department == current_user.department)
                        .order_by(Leave.created_at.desc())
                        .limit(5).all())
        recent_expenses = (Expense.query
                          .join(User, Expense.submitted_by == User.employee_id)
                          .filter(User.department == current_user.department)
                          .order_by(Expense.created_at.desc())
                          .limit(5).all())
        recent_transactions = BookTransaction.query.order_by(BookTransaction.issue_date.desc()).limit(5).all()
        grade_data = (Grade.query
                     .join(Student, Grade.student_id == Student.id)
                     .filter(Student.department == current_user.department)
                     .order_by(Grade.created_at.desc())
                     .limit(5).all())
    elif current_user.role == 'Faculty':
        # Faculty sees only their class data
        recent_leaves = Leave.query.filter_by(employee_id=current_user.employee_id).order_by(Leave.created_at.desc()).limit(5).all()
        recent_expenses = Expense.query.order_by(Expense.created_at.desc()).limit(5).all()
        recent_transactions = BookTransaction.query.order_by(BookTransaction.issue_date.desc()).limit(5).all()
        grade_data = (Grade.query
                     .filter_by(marked_by=current_user.employee_id)
                     .order_by(Grade.created_at.desc())
                     .limit(5).all())
    elif current_user.role == 'Accountant':
        # Accountant sees financial data
        recent_leaves = Leave.query.order_by(Leave.created_at.desc()).limit(5).all()
        recent_expenses = Expense.query.order_by(Expense.created_at.desc()).limit(5).all()
        recent_transactions = BookTransaction.query.order_by(BookTransaction.issue_date.desc()).limit(5).all()
        grade_data = []
    elif current_user.role == 'Student':
        # Student sees only their own data
        student = Student.query.filter_by(user_id=current_user.employee_id).first()
        recent_leaves = Leave.query.filter_by(employee_id=current_user.employee_id).order_by(Leave.created_at.desc()).limit(5).all()
        recent_expenses = []
        recent_transactions = []
        grade_data = Grade.query.filter_by(student_id=student.id).order_by(Grade.created_at.desc()).limit(5).all() if student else []
    else:
        # HR, Library, Non-Teaching
        recent_leaves = Leave.query.order_by(Leave.created_at.desc()).limit(5).all()
        recent_expenses = Expense.query.order_by(Expense.created_at.desc()).limit(5).all()
        recent_transactions = BookTransaction.query.order_by(BookTransaction.issue_date.desc()).limit(5).all()
        grade_data = []
    
    return render_template('dashboard.html', 
                           stats=stats,
                           recent_leaves=recent_leaves,
                           recent_expenses=recent_expenses,
                           recent_transactions=recent_transactions,
                           grade_data=grade_data)


# ==================== HR ROUTES ====================

@app.route('/hr/employees')
@login_required
@role_required('HR', 'Registrar', 'Director', 'Dean', 'HOD', 'Management', 'Administrative Officer')
def manage_employees():
    """Manage employees page (view only for some roles)."""
    # HR and Registrar/Director/Dean/Management/AO can see everyone
    if current_user.role in ['HR', 'Registrar', 'Director', 'Dean', 'Management', 'Administrative Officer']:
        employees = User.query.all()
    elif current_user.role == 'HOD':
        # HOD sees only their department
        employees = User.query.filter_by(department=current_user.department).all()
    else:
        employees = []
    return render_template('manage_employees.html', employees=employees)


@app.route('/hr/employees/add', methods=['GET', 'POST'])
@login_required
@role_required('HR', 'Registrar', 'Director', 'Dean', 'Management', 'Administrative Officer', 'Non-Teaching')
def add_employee():
    """Add new employee (HR/admin only)."""
    if request.method == 'POST':
        department = request.form.get('department')
        designation = request.form.get('designation')
        password = request.form.get('password')
        
        # Auto-generate employee ID based on department and designation
        employee_id = generate_employee_id(department, designation)
        
        # Ensure the generated ID is unique (in case of collision)
        counter = 1
        original_id = employee_id
        while User.query.get(employee_id):
            # If collision, append counter to the base prefix
            prefix = original_id[:-3]
            seq = int(original_id[-3:]) + counter
            employee_id = f"{prefix}{seq:03d}"
            counter += 1
        
        user = User(
            employee_id=employee_id,
            name=request.form.get('name'),
            email=request.form.get('email'),
            phone=request.form.get('phone'),
            role=request.form.get('role'),
            department=department,
            designation=designation,
            password=generate_password_hash(password)
        )
        
        db.session.add(user)
        db.session.commit()
        flash(f'Employee added successfully! Employee ID: {employee_id}', 'success')
        return redirect(url_for('manage_employees'))
    
    return render_template('add_employee.html')


@app.route('/hr/employees/edit/<employee_id>', methods=['GET', 'POST'])
@login_required
@role_required('HR', 'Registrar', 'Director', 'Dean', 'Management', 'Administrative Officer', 'Non-Teaching')
def edit_employee(employee_id):
    """Edit employee (HR/admin only)."""
    employee = User.query.get_or_404(employee_id)
    
    if request.method == 'POST':
        try:
            employee.name = request.form.get('name')
            employee.email = request.form.get('email')
            employee.phone = request.form.get('phone')
            employee.role = request.form.get('role')
            employee.department = request.form.get('department')
            employee.designation = request.form.get('designation')
            # only HR/Admin can activate/deactivate
            if current_user.role in ['HR', 'Registrar', 'Director', 'Dean', 'Non-Teaching']:
                employee.is_active = 'is_active' in request.form
            
            db.session.commit()
            flash('Employee updated successfully!', 'success')
            return redirect(url_for('manage_employees'))
        except Exception as e:
            db.session.rollback()
            flash(f'Error updating employee: {str(e)}', 'danger')
            return render_template('edit_employee.html', employee=employee)
    
    return render_template('edit_employee.html', employee=employee)


@app.route('/hr/employees/delete/<employee_id>')
@login_required
@role_required('HR', 'Registrar', 'Director', 'Dean', 'Management', 'Administrative Officer', 'Non-Teaching')
def delete_employee(employee_id):
    """Delete employee (HR/admin only)."""
    employee = User.query.get_or_404(employee_id)
    
    if employee.employee_id == current_user.employee_id:
        flash('You cannot delete your own account.', 'danger')
        return redirect(url_for('manage_employees'))
    
    db.session.delete(employee)
    db.session.commit()
    flash('Employee deleted successfully!', 'success')
    return redirect(url_for('manage_employees'))


@app.route('/hr/leaves')
@login_required
def leave_management():
    """Leave management page with role based filtering.
    - Admin/Director/Management: see all pending leaves
    - HOD: see leaves from Faculty/Non-Teaching staff in their department
    - Faculty/Non-Teaching/Student: see only their own leaves
    """
    if current_user.role in ['Registrar', 'Director', 'Management', 'Non-Teaching']:
        # full access - see all pending leaves
        leaves = Leave.query.order_by(Leave.created_at.desc()).all()
    elif current_user.role == 'HOD':
        # HOD sees leaves from Faculty and Non-Teaching staff in their department
        leaves = (Leave.query
                  .join(User, Leave.employee_id == User.employee_id)
                  .filter(User.department == current_user.department)
                  .filter(User.role.in_(['Faculty', 'Non-Teaching']))
                  .order_by(Leave.created_at.desc())
                  .all())
    else:
        # faculty and student can only see their own requests
        leaves = Leave.query.filter_by(employee_id=current_user.employee_id).order_by(Leave.created_at.desc()).all()
    
    # Build a small mapping of leave.id -> employee role/designation for template logic
    employee_info = {}
    for lv in leaves:
        emp = User.query.get(lv.employee_id)
        employee_info[lv.id] = {
            'role': emp.role if emp else '',
            'designation': emp.designation if emp else ''
        }

    return render_template('leave_management.html', leaves=leaves, employee_info=employee_info)


@app.route('/hr/leaves/apply', methods=['GET', 'POST'])
@login_required
def apply_leave():
    """Apply for leave - Everyone can apply for their own leave. HR/Registrar can apply for any employee.
    HOD leaves are automatically forwarded to Director."""
    if request.method == 'POST':
        # HR/Registrar can apply leave for any employee, others only for themselves
        if current_user.role in ['HR', 'Registrar', 'Non-Teaching']:
            employee_id = request.form.get('employee_id', current_user.employee_id)
            # Verify the employee exists
            employee = User.query.get(employee_id)
            if not employee:
                flash('Selected employee not found.', 'danger')
                return redirect(url_for('apply_leave'))
        else:
            employee_id = current_user.employee_id
        
        # Get employee details for department tracking
        employee = User.query.get(employee_id)
        
        # HOD leaves are automatically forwarded to Director (skip Pending status)
        # Some employees may have 'Teaching' as role but designation 'Head of Department',
        # so check both the role and the designation.
        if employee.role == 'HOD' or employee.designation == 'Head of Department':
            status = 'Forwarded'
            # If someone else (e.g., Registrar/HR) applies on behalf of the HOD,
            # record the current user as the forwarder; otherwise self-forward.
            forwarded_by = current_user.employee_id if current_user.employee_id != employee_id else employee_id
        else:
            status = 'Pending'
            forwarded_by = None
        
        leave = Leave(
            employee_id=employee_id,
            leave_type=request.form.get('leave_type'),
            start_date=datetime.strptime(request.form.get('start_date'), '%Y-%m-%d').date(),
            end_date=datetime.strptime(request.form.get('end_date'), '%Y-%m-%d').date(),
            reason=request.form.get('reason'),
            department=employee.department,  # Store employee's department for routing
            status=status,  # Forwarded if HOD, else Pending
            forwarded_by=forwarded_by  # HOD forwards their own leave
        )
        
        db.session.add(leave)
        db.session.commit()
        flash('Leave application submitted!', 'success')
        return redirect(url_for('leave_management'))
    
    return render_template('apply_leave.html')


@app.route('/hr/leaves/approve/<int:leave_id>')
@login_required
@role_required('Registrar', 'Director', 'HOD', 'Library Head', 'Finance Officer', 'Management', 'Non-Teaching')
def approve_leave(leave_id):
    """Approve or forward leave based on department and role.
    
    Approval workflow:
    - Admin Dept: Registrar forwards → Director approves
    - Academic Dept: HOD forwards → Director approves
    - Library: Library Head forwards → Director approves
    - Accounts: Finance Officer forwards → Director approves
    """
    leave = Leave.query.get_or_404(leave_id)
    employee = User.query.get(leave.employee_id)
    
    if not employee:
        flash('Employee not found.', 'danger')
        return redirect(url_for('leave_management'))
    
    # Get department head for validation
    department = leave.department or employee.department
    
    # Department heads who can forward leaves
    dept_heads = {
        'Administration': 'Registrar',
        'Computer Science': 'HOD',
        'Information Technology': 'HOD',
        'Mechanical Engineering': 'HOD',
        'Electrical Engineering': 'HOD',
        'Library': 'Library Head',
        'Accounts': 'Finance Officer'
    }
    
    expected_forwarder_role = dept_heads.get(department)
    
    if current_user.role == 'Director':
        # Director can approve any leave that is not already final (Approved/Rejected),
        # including Pending, Forwarded and their own leave.
        if leave.status in ['Pending', 'Forwarded'] or leave.employee_id == current_user.employee_id:
            leave.status = 'Approved'
            leave.approved_by = current_user.employee_id
            # Friendly message for self-approval
            if leave.employee_id == current_user.employee_id:
                flash('Your leave approved!', 'success')
            else:
                flash('Leave approved!', 'success')
        else:
            flash('Leave already processed or cannot be approved.', 'danger')
            db.session.rollback()
            return redirect(url_for('leave_management'))
    
    elif current_user.role == expected_forwarder_role:
        # Department head forwards the leave
        if leave.status != 'Pending':
            flash('Can only forward pending leaves.', 'danger')
            return redirect(url_for('leave_management'))
        
        # Verify employee is in same department
        if employee.department != current_user.department:
            flash('You can only forward leaves from your department.', 'danger')
            return redirect(url_for('leave_management'))
        
        leave.status = 'Forwarded'
        leave.forwarded_by = current_user.employee_id
        flash('Leave forwarded to Director for approval!', 'success')
    
    elif current_user.role == 'Management':
        # Management can approve/forward any leave
        if leave.status == 'Pending':
            leave.status = 'Forwarded'
            leave.forwarded_by = current_user.employee_id
            flash('Leave forwarded!', 'success')
        elif leave.status == 'Forwarded':
            leave.status = 'Approved'
            leave.approved_by = current_user.employee_id
            flash('Leave approved!', 'success')
        else:
            flash('Leave already processed.', 'danger')
            return redirect(url_for('leave_management'))
    
    else:
        flash('You do not have permission to process this leave.', 'danger')
        return redirect(url_for('leave_management'))
    
    db.session.commit()
    return redirect(url_for('leave_management'))


@app.route('/hr/leaves/reject/<int:leave_id>')
@login_required
@role_required('Registrar', 'Director', 'HOD', 'Library Head', 'Finance Officer', 'Management', 'Non-Teaching')
def reject_leave(leave_id):
    """Reject leave based on role and employee designation.
    
    Rejection hierarchy:
    - Faculty/Non-Teaching: HOD rejects Pending, Director/Admin rejects Forwarded
    - Other roles: Director/Admin rejects (can self-reject if Director/Admin)
    """
    leave = Leave.query.get_or_404(leave_id)
    employee = User.query.get(leave.employee_id)
    
    if current_user.role == 'HOD':
        # HOD can only reject faculty/non-teaching pending leaves in their department
        if not employee or employee.role not in ['Faculty', 'Non-Teaching']:
            flash('You can only reject leaves for Faculty and Non-Teaching staff.', 'danger')
            return redirect(url_for('leave_management'))
        if employee.department != current_user.department:
            flash('You can only process leaves for your department.', 'danger')
            return redirect(url_for('leave_management'))
        if leave.status != 'Pending':
            flash('Can only reject pending leaves.', 'danger')
            return redirect(url_for('leave_management'))
        
        # HOD rejects the leave
        leave.status = 'Rejected'
        leave.forwarded_by = current_user.employee_id  # Track who rejected
        flash('Leave rejected!', 'success')
        
    elif current_user.role == 'Director':
        # Director can reject forwarded/pending leaves, or self-reject own leave
        if leave.employee_id == current_user.employee_id:
            # Director self-rejecting own leave
            leave.status = 'Rejected'
            leave.approved_by = current_user.employee_id
            flash('Your leave rejected!', 'success')
        elif leave.status in ['Forwarded', 'Pending']:
            leave.status = 'Rejected'
            leave.approved_by = current_user.employee_id
            flash('Leave rejected!', 'success')
        else:
            flash('Cannot reject already processed leaves.', 'danger')
            return redirect(url_for('leave_management'))
        
    elif current_user.role in ['Admin', 'Management']:
        # Admin and Management can reject any leave
        if leave.status in ['Pending', 'Forwarded', 'Approved']:
            leave.status = 'Rejected'
            leave.approved_by = current_user.employee_id
            flash('Leave rejected!', 'success')
        else:
            flash('Cannot reject already processed leaves.', 'danger')
            return redirect(url_for('leave_management'))
    
    db.session.commit()
    return redirect(url_for('leave_management'))


@app.route('/attendance')
@login_required
def manage_attendance():
    """Attendance overview - permissions vary by role."""
    today = date.today()
    attendance_records = []
    employees = []

    if current_user.role in ['Registrar', 'HR', 'Director', 'Dean', 'Management', 'Non-Teaching']:
        employees = User.query.all()
        attendance_records = Attendance.query.filter_by(date=today).all()
    elif current_user.role == 'HOD':
        employees = User.query.filter_by(department=current_user.department).all()
        attendance_records = (Attendance.query
                              .join(User, Attendance.employee_id == User.employee_id)
                              .filter(User.department == current_user.department,
                                      Attendance.date == today)
                              .all())
    elif current_user.role == 'Faculty':
        # faculty can see their assigned class attendance
        query = Student.query.filter_by(department=current_user.department)
        if current_user.assigned_course:
            query = query.filter_by(course=current_user.assigned_course)
        if current_user.assigned_semester:
            query = query.filter_by(semester=current_user.assigned_semester)
        # convert student list to pseudo employee list for display if necessary
        # for now we show attendance_records empty, faculty uses student_attendance route
        employees = []
    elif current_user.role == 'Student':
        # student can view only own attendance (employee table)
        attendance_records = Attendance.query.filter_by(employee_id=current_user.employee_id).order_by(Attendance.date.desc()).all()
    return render_template('attendance.html', 
                           employees=employees, 
                           attendance_records=attendance_records,
                           today=today)


@app.route('/attendance/mark', methods=['POST'])
@login_required
@role_required('Faculty', 'HOD', 'Admin', 'Director', 'Dean', 'HR', 'Management')
def mark_attendance():
    """Mark attendance. Only faculty/HOD/admin can perform."""
    employee_id = request.form.get('employee_id')
    status = request.form.get('status')
    date_str = request.form.get('date')
    attendance_date = datetime.strptime(date_str, '%Y-%m-%d').date() if date_str else date.today()
    
    existing = Attendance.query.filter_by(
        employee_id=employee_id,
        date=attendance_date
    ).first()
    
    if existing:
        existing.status = status
        existing.marked_by = current_user.employee_id
    else:
        attendance = Attendance(
            employee_id=employee_id,
            date=attendance_date,
            status=status,
            marked_by=current_user.employee_id
        )
        db.session.add(attendance)
    
    db.session.commit()
    flash('Attendance marked successfully!', 'success')
    return redirect(url_for('manage_attendance'))


# ==================== LIBRARY ROUTES ====================

@app.route('/library/books')
@login_required
@role_required('Library Head', 'Management')
def manage_books():
    """Manage books page."""
    books = Book.query.all()
    return render_template('library_books.html', books=books)


@app.route('/library/books/add', methods=['GET', 'POST'])
@login_required
@role_required('Library Head', 'Management')
def add_book():
    """Add new book."""
    if request.method == 'POST':
        book = Book(
            title=request.form.get('title'),
            author=request.form.get('author'),
            isbn=request.form.get('isbn'),
            category=request.form.get('category'),
            quantity=int(request.form.get('quantity', 1)),
            available_quantity=int(request.form.get('quantity', 1)),
            shelf_location=request.form.get('shelf_location')
        )
        
        db.session.add(book)
        db.session.commit()
        flash('Book added successfully!', 'success')
        return redirect(url_for('manage_books'))
    
    return render_template('add_book.html')


@app.route('/library/books/edit/<int:book_id>', methods=['GET', 'POST'])
@login_required
@role_required('Library Head', 'Management')
def edit_book(book_id):
    """Edit book."""
    book = Book.query.get_or_404(book_id)
    
    if request.method == 'POST':
        book.title = request.form.get('title')
        book.author = request.form.get('author')
        book.isbn = request.form.get('isbn')
        book.category = request.form.get('category')
        book.quantity = int(request.form.get('quantity'))
        book.shelf_location = request.form.get('shelf_location')
        
        db.session.commit()
        flash('Book updated successfully!', 'success')
        return redirect(url_for('manage_books'))
    
    return render_template('edit_book.html', book=book)


@app.route('/library/books/delete/<int:book_id>')
@login_required
@role_required('Library Head', 'Management')
def delete_book(book_id):
    """Delete book."""
    book = Book.query.get_or_404(book_id)
    db.session.delete(book)
    db.session.commit()
    flash('Book deleted successfully!', 'success')
    return redirect(url_for('manage_books'))


@app.route('/library/issue', methods=['GET', 'POST'])
@login_required
@role_required('Library Head', 'Management')
def issue_book():
    """Issue book to employee."""
    if request.method == 'POST':
        book_id = request.form.get('book_id')
        employee_id = request.form.get('employee_id')
        
        book = Book.query.get(book_id)
        if book.available_quantity > 0:
            transaction = BookTransaction(
                book_id=book_id,
                employee_id=employee_id,
                issue_date=date.today(),
                due_date=date.today() + timedelta(days=14),
                status='Issued'
            )
            
            book.available_quantity -= 1
            db.session.add(transaction)
            db.session.commit()
            flash('Book issued successfully!', 'success')
        else:
            flash('Book not available!', 'danger')
        
        return redirect(url_for('library_transactions'))
    
    books = Book.query.filter(Book.available_quantity > 0).all()
    employees = User.query.all()
    return render_template('issue_book.html', books=books, employees=employees)


@app.route('/library/return/<int:transaction_id>')
@login_required
@role_required('Library Head', 'Management')
def return_book(transaction_id):
    """Return book."""
    transaction = BookTransaction.query.get_or_404(transaction_id)
    transaction.return_date = date.today()
    transaction.status = 'Returned'
    
    book = Book.query.get(transaction.book_id)
    book.available_quantity += 1
    
    db.session.commit()
    flash('Book returned successfully!', 'success')
    return redirect(url_for('library_transactions'))


@app.route('/library/transactions')
@login_required
@role_required('Library Head', 'Management')
def library_transactions():
    """Library transactions page."""
    transactions = BookTransaction.query.order_by(BookTransaction.issue_date.desc()).all()
    return render_template('library_transactions.html', transactions=transactions)


# ==================== ACCOUNTS ROUTES ====================

@app.route('/accounts/salaries')
@login_required
@role_required('Finance Officer', 'Management')
def manage_salaries():
    """Manage salaries page."""
    salaries = Salary.query.order_by(Salary.year.desc(), Salary.month.desc()).all()
    employees = User.query.all()
    return render_template('manage_salaries.html', salaries=salaries, employees=employees)


@app.route('/accounts/salaries/add', methods=['GET', 'POST'])
@login_required
@role_required('Finance Officer', 'Management')
def add_salary():
    """Add salary record."""
    if request.method == 'POST':
        employee_id = request.form.get('employee_id')
        basic = float(request.form.get('basic_salary', 0))
        hra = float(request.form.get('hra', 0))
        da = float(request.form.get('da', 0))
        allowances = float(request.form.get('allowances', 0))
        deductions = float(request.form.get('deductions', 0))
        
        net_salary = basic + hra + da + allowances - deductions
        
        salary = Salary(
            employee_id=employee_id,
            month=int(request.form.get('month')),
            year=int(request.form.get('year')),
            basic_salary=basic,
            hra=hra,
            da=da,
            allowances=allowances,
            deductions=deductions,
            net_salary=net_salary,
            payment_status='Pending'
        )
        
        db.session.add(salary)
        db.session.commit()
        flash('Salary record added!', 'success')
        return redirect(url_for('manage_salaries'))
    
    employees = User.query.all()
    return render_template('add_salary.html', employees=employees)


@app.route('/accounts/salaries/process/<int:salary_id>')
@login_required
@role_required('Finance Officer', 'Management')
def process_salary(salary_id):
    """Process salary payment."""
    salary = Salary.query.get_or_404(salary_id)
    salary.payment_status = 'Processed'
    salary.payment_date = date.today()
    
    db.session.commit()
    flash('Salary processed successfully!', 'success')
    return redirect(url_for('manage_salaries'))


@app.route('/accounts/expenses')
@login_required
def manage_expenses():
    """Manage expenses page."""
    if current_user.role in ['Accounts', 'Management']:
        expenses = Expense.query.order_by(Expense.date.desc()).all()
    else:
        expenses = Expense.query.filter_by(submitted_by=current_user.employee_id).order_by(Expense.date.desc()).all()
    
    return render_template('manage_expenses.html', expenses=expenses)


@app.route('/accounts/expenses/add', methods=['GET', 'POST'])
@login_required
def add_expense():
    """Add expense."""
    if request.method == 'POST':
        expense = Expense(
            category=request.form.get('category'),
            description=request.form.get('description'),
            amount=float(request.form.get('amount')),
            date=datetime.strptime(request.form.get('date'), '%Y-%m-%d').date(),
            submitted_by=current_user.employee_id,
            status='Pending'
        )
        
        db.session.add(expense)
        db.session.commit()
        flash('Expense submitted!', 'success')
        return redirect(url_for('manage_expenses'))
    
    return render_template('add_expense.html')


@app.route('/accounts/expenses/approve/<int:expense_id>')
@login_required
@role_required('Accounts', 'Management')
def approve_expense(expense_id):
    """Approve expense."""
    expense = Expense.query.get_or_404(expense_id)
    expense.status = 'Approved'
    expense.approved_by = current_user.employee_id
    
    db.session.commit()
    flash('Expense approved!', 'success')
    return redirect(url_for('manage_expenses'))


@app.route('/accounts/expenses/reject/<int:expense_id>')
@login_required
@role_required('Accounts', 'Management')
def reject_expense(expense_id):
    """Reject expense."""
    expense = Expense.query.get_or_404(expense_id)
    expense.status = 'Rejected'
    expense.approved_by = current_user.employee_id
    
    db.session.commit()
    flash('Expense rejected!', 'success')
    return redirect(url_for('manage_expenses'))


# ==================== TEACHING ROUTES ====================

@app.route('/students')
@login_required
@role_required('Registrar', 'Director', 'Dean', 'HOD', 'Faculty', 'Management', 'Non-Teaching')
def manage_students():
    """Manage students page with RBAC filtering.

    - Admin/Director/Dean/Management: see all students
    - HOD: see students in their department
    - Faculty: see students in their assigned course/semester (or department)
    """
    if current_user.role in ['Registrar', 'Director', 'Dean', 'Management', 'Non-Teaching']:
        students = Student.query.all()
    elif current_user.role == 'HOD':
        students = Student.query.filter_by(department=current_user.department).all()
    elif current_user.role == 'Faculty':
        query = Student.query.filter_by(department=current_user.department)
        if current_user.assigned_course:
            query = query.filter_by(course=current_user.assigned_course)
        if current_user.assigned_semester:
            query = query.filter_by(semester=current_user.assigned_semester)
        students = query.all()
    else:
        students = []
    return render_template('manage_students.html', students=students)


@app.route('/students/add', methods=['GET', 'POST'])
@login_required
@role_required('Registrar', 'Administrative Officer', 'Non-Teaching')
def add_student():
    """Add new student."""
    if request.method == 'POST':
        # collect form values
        first_name = request.form.get('first_name') or ''
        last_name = request.form.get('last_name') or ''
        name = request.form.get('name') or f"{first_name} {last_name}".strip()
        father_name = request.form.get('father_name')
        email = request.form.get('email')
        phone = request.form.get('phone')
        course = request.form.get('course')
        semester = int(request.form.get('semester')) if request.form.get('semester') else None
        admission_year = int(request.form.get('admission_year')) if request.form.get('admission_year') else date.today().year
        college_code = request.form.get('college_code') or 'AIMT'
        dept_code = request.form.get('department') or (course or '')[:3]

        # generate roll number using format YYYY+COL+DEPT+SEQ
        roll_number = generate_student_id(admission_year, college_code, dept_code)

        student = Student(
            roll_number=roll_number,
            name=name,
            first_name=first_name or None,
            last_name=last_name or None,
            father_name=father_name,
            email=email,
            phone=phone,
            course=course,
            semester=semester,
            department=dept_code
        )

        try:
            db.session.add(student)
            db.session.commit()
            flash(f'Student {roll_number} added successfully!', 'success')
        except IntegrityError:
            db.session.rollback()
            flash('A student with generated roll number already exists. Please try again.', 'danger')
        return redirect(url_for('manage_students'))
    
    return render_template('add_student.html', now=date.today())


@app.route('/students/attendance', methods=['GET', 'POST'])
@login_required
@role_required('Faculty', 'HOD', 'Registrar', 'Director', 'Dean', 'Non-Teaching')
def student_attendance():
    """Student attendance page with class/department filtering."""
    if request.method == 'POST':
        student_id = request.form.get('student_id')
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
        flash('Attendance marked!', 'success')
    
    # filter students according to role
    if current_user.role == 'HOD':
        students = Student.query.filter_by(department=current_user.department).all()
    elif current_user.role == 'Faculty':
        students = Student.query.filter_by(department=current_user.department)
        if current_user.assigned_course:
            students = students.filter_by(course=current_user.assigned_course)
        if current_user.assigned_semester:
            students = students.filter_by(semester=current_user.assigned_semester)
        students = students.all()
    else:
        students = Student.query.all()

    today = date.today()
    attendance_records = StudentAttendance.query.filter_by(date=today).all()
    
    return render_template('student_attendance.html', 
                           students=students, 
                           attendance_records=attendance_records,
                           today=today)


@app.route('/students/grades', methods=['GET', 'POST'])
@login_required
@role_required('Faculty', 'HOD', 'Admin', 'Director', 'Dean')
def manage_grades():
    """Manage student grades with role-based filtering.

    - Admin/Director/Dean: see all students
    - HOD: see grades for students in their department
    - Faculty: see grades for students in their assigned course/semester
    """
    if request.method == 'POST':
        student_id = request.form.get('student_id')
        marks = float(request.form.get('marks'))
        
        if marks >= 90:
            grade = 'A+'
        elif marks >= 80:
            grade = 'A'
        elif marks >= 70:
            grade = 'B+'
        elif marks >= 60:
            grade = 'B'
        elif marks >= 50:
            grade = 'C'
        else:
            grade = 'F'
        
        grade_record = Grade(
            student_id=student_id,
            subject=request.form.get('subject'),
            marks=marks,
            grade=grade,
            semester=int(request.form.get('semester')),
            exam_type=request.form.get('exam_type'),
            marked_by=current_user.employee_id
        )
        
        db.session.add(grade_record)
        db.session.commit()
        flash('Grade added!', 'success')
    
    # filter students by role
    if current_user.role in ['Registrar', 'Director', 'Dean', 'Non-Teaching']:
        students = Student.query.all()
    elif current_user.role == 'HOD':
        students = Student.query.filter_by(department=current_user.department).all()
    elif current_user.role == 'Faculty':
        query = Student.query.filter_by(department=current_user.department)
        if current_user.assigned_course:
            query = query.filter_by(course=current_user.assigned_course)
        if current_user.assigned_semester:
            query = query.filter_by(semester=current_user.assigned_semester)
        students = query.all()
    else:
        students = []
    
    grades = Grade.query.order_by(Grade.created_at.desc()).all()
    
    return render_template('manage_grades.html', students=students, grades=grades)


# ==================== REPORTS ROUTES ====================

@app.route('/reports')
@login_required
@role_required('Admin', 'Director', 'Dean', 'HOD', 'Accountant', 'HR', 'Management')
def reports():
    """Reports page with role-based access."""
    return render_template('reports.html')


@app.route('/reports/employee')
@login_required
@role_required('Admin', 'Director', 'Dean', 'HR', 'Management')
def employee_report():
    """Employee report. HR/Admin/Director/Dean can see everyone; Others see limited data."""
    if current_user.role in ['Admin', 'Director', 'Dean', 'HR', 'Management']:
        employees = User.query.all()
    else:
        employees = []
    return render_template('employee_report.html', employees=employees)


@app.route('/reports/attendance')
@login_required
@role_required('Admin', 'Director', 'Dean', 'HR', 'HOD', 'Management')
def attendance_report():
    """Attendance report with department filtering for HOD."""
    month = request.args.get('month', date.today().month, type=int)
    year = request.args.get('year', date.today().year, type=int)
    
    start_date = date(year, month, 1)
    if month == 12:
        end_date = date(year + 1, 1, 1) - timedelta(days=1)
    else:
        end_date = date(year, month + 1, 1) - timedelta(days=1)
    
    if current_user.role == 'HOD':
        attendances = (Attendance.query
                       .join(User, Attendance.employee_id == User.employee_id)
                       .filter(User.department == current_user.department,
                               Attendance.date >= start_date,
                               Attendance.date <= end_date)
                       .all())
    else:
        attendances = Attendance.query.filter(
            Attendance.date >= start_date,
            Attendance.date <= end_date
        ).all()
    
    return render_template('attendance_report.html', 
                           attendances=attendances,
                           month=month,
                           year=year)


@app.route('/reports/finance')
@login_required
@role_required('Admin', 'Director', 'Dean', 'Accountant', 'Management')
def finance_report():
    """Finance report - salary & expense overview."""
    salaries = Salary.query.all()
    expenses = Expense.query.all()
    
    total_salary = sum(s.net_salary for s in salaries if s.payment_status == 'Processed')
    total_expenses = sum(e.amount for e in expenses if e.status == 'Approved')
    
    return render_template('finance_report.html',
                           salaries=salaries,
                           expenses=expenses,
                           total_salary=total_salary,
                           total_expenses=total_expenses)


@app.route('/reports/library')
@login_required
@role_required('Admin', 'Director', 'Dean', 'Library', 'Management')
def library_report():
    """Library report."""
    total_books = Book.query.count()
    books_issued = BookTransaction.query.filter_by(status='Issued').count()
    transactions = BookTransaction.query.order_by(BookTransaction.issue_date.desc()).all()
    
    return render_template('library_report.html',
                           total_books=total_books,
                           books_issued=books_issued,
                           transactions=transactions)


# ==================== PROFILE ROUTES ====================

@app.route('/profile')
@login_required
def profile():
    """User profile page."""
    return render_template('profile.html')


@app.route('/my-attendance')
@login_required
def my_attendance():
    """View own attendance page for staff or students.

    - Employees see `Attendance` table.
    - Students see their student attendance records.
    """
    if current_user.role == 'Student':
        student = Student.query.filter_by(user_id=current_user.employee_id).first()
        attendance_records = []
        if student:
            attendance_records = StudentAttendance.query.filter_by(
                student_id=student.id
            ).order_by(StudentAttendance.date.desc()).all()
    else:
        attendance_records = Attendance.query.filter_by(
            employee_id=current_user.employee_id
        ).order_by(Attendance.date.desc()).all()
    
    return render_template('my_attendance.html', 
                           attendance_records=attendance_records)


@app.route('/profile/change-password', methods=['POST'])
@login_required
def change_password():
    """Change password."""
    current_password = request.form.get('current_password')
    new_password = request.form.get('new_password')
    confirm_password = request.form.get('confirm_password')
    
    user = User.query.get(current_user.employee_id)
    
    if not check_password_hash(user.password, current_password):
        flash('Current password is incorrect.', 'danger')
    elif new_password != confirm_password:
        flash('New passwords do not match.', 'danger')
    else:
        user.password = generate_password_hash(new_password)
        db.session.commit()
        flash('Password changed successfully!', 'success')
    
    return redirect(url_for('profile'))


# ==================== ERROR HANDLERS ====================

@app.errorhandler(404)
def not_found_error(error):
    """404 error handler."""
    return render_template('error.html', error='Page not found'), 404


@app.errorhandler(500)
def internal_error(error):
    """500 error handler."""
    db.session.rollback()
    return render_template('error.html', error='Internal server error'), 500


# ==================== DATABASE INITIALIZATION ====================

def init_db():
    """Initialize database with sample data."""
    with app.app_context():
        db.create_all()

        # Only populate sample users when the users table is empty.
        # This prevents recreated default accounts after a user intentionally deletes an account.
        if User.query.count() == 0:
            if not User.query.get('HR001'):
                hr = User(
                    employee_id='HR001',
                    name='HR Manager',
                    email='hr@aimt.edu',
                    phone='1234567891',
                    role='HR',
                    department='Human Resources',
                    designation='HR Manager',
                    password=generate_password_hash('hr123'),
                    is_active=True
                )
                db.session.add(hr)
        
        if not User.query.get('ADMIN001'):
            admin = User(
                employee_id='ADMIN001',
                name='Registrar',
                email='registrar@aimt.edu',
                phone='1234567890',
                role='Non-Teaching',
                department='Administration',
                designation='Registrar',
                password=generate_password_hash('admin123'),
                is_active=True
            )
            db.session.add(admin)
        
        if not User.query.get('AO001'):
            ao = User(
                employee_id='AO001',
                name='Administrative Officer',
                email='ao@aimt.edu',
                phone='1234567900',
                role='Administrative Officer',
                department='Administration',
                designation='Administrative Officer',
                password=generate_password_hash('ao123'),
                is_active=True
            )
            db.session.add(ao)
        
        if not User.query.get('DIR001'):
            director = User(
                employee_id='DIR001',
                name='Director',
                email='director@aimt.edu',
                phone='1234567897',
                role='Director',
                department='Administration',
                designation='Director',
                password=generate_password_hash('director123'),
                is_active=True
            )
            db.session.add(director)
        
        if not User.query.get('DEAN001'):
            dean = User(
                employee_id='DEAN001',
                name='Dean',
                email='dean@aimt.edu',
                phone='1234567898',
                role='Dean',
                department='Administration',
                designation='Dean',
                password=generate_password_hash('dean123'),
                is_active=True
            )
            db.session.add(dean)
        
        if not User.query.get('HODCS01'):
            hod = User(
                employee_id='HODCS01',
                name='HOD Computer Science',
                email='hodcs@aimt.edu',
                phone='1234567898',
                role='HOD',
                department='Computer Science',
                designation='Head of Department',
                password=generate_password_hash('hod123'),
                is_active=True
            )
            db.session.add(hod)
        
        # update existing sample roles to align with new naming
        if not User.query.get('ACC001'):
            accounts = User(
                employee_id='ACC001',
                name='Finance Officer',
                email='finance@aimt.edu',
                phone='1234567892',
                role='Finance Officer',
                department='Accounts',
                designation='Finance Officer',
                password=generate_password_hash('finance123'),
                is_active=True
            )
            db.session.add(accounts)
        
        if not User.query.get('LIB001'):
            library = User(
                employee_id='LIB001',
                name='Library Head',
                email='library@aimt.edu',
                phone='1234567893',
                role='Library Head',
                department='Library',
                designation='Librarian',
                password=generate_password_hash('lib123'),
                is_active=True
            )
            db.session.add(library)
        
        if not User.query.get('TCH001'):
            teacher = User(
                employee_id='TCH001',
                name='John Smith',
                email='john@aimt.edu',
                phone='1234567894',
                role='Faculty',
                department='Computer Science',
                designation='Professor',
                assigned_course='B.Tech CS',
                assigned_semester=1,
                password=generate_password_hash('teacher123'),
                is_active=True
            )
            db.session.add(teacher)
        
        if not User.query.get('NCT001'):
            staff = User(
                employee_id='NCT001',
                name='Mike Johnson',
                email='mike@aimt.edu',
                phone='1234567895',
                role='Non-Teaching',
                department='Administration',
                designation='Office Assistant',
                password=generate_password_hash('staff123'),
                is_active=True
            )
            db.session.add(staff)
        
        if not User.query.get('EATDS5713'):
            new_employee = User(
                employee_id='EATDS5713',
                name='New Employee',
                email='employee@aimt.edu',
                phone='1234567896',
                role='Faculty',
                department='Computer Science',
                designation='Lecturer',
                assigned_course='B.Tech CS',
                assigned_semester=2,
                password=generate_password_hash('password123'),
                is_active=True
            )
            db.session.add(new_employee)
        
        if Book.query.count() == 0:
            books = [
                Book(title='Python Programming', author='John Smith', isbn='978-0134685991', category='Programming', quantity=5, available_quantity=5, shelf_location='A-101'),
                Book(title='Data Structures', author='Alan Cohen', isbn='978-0262033848', category='Computer Science', quantity=3, available_quantity=3, shelf_location='A-102'),
                Book(title='Database Management', author='Sarah Johnson', isbn='978-0073523323', category='Database', quantity=4, available_quantity=4, shelf_location='B-201'),
                Book(title='Web Development', author='Mike Brown', isbn='978-1491950388', category='Web', quantity=2, available_quantity=2, shelf_location='B-202'),
                Book(title='Machine Learning', author='Tom Wilson', isbn='978-1491959107', category='AI', quantity=3, available_quantity=3, shelf_location='C-301'),
            ]
            for book in books:
                db.session.add(book)
        
        if Student.query.count() == 0:
            sample_students = [
                {'roll':'CS001','name':'Alice Johnson','email':'alice@aimt.edu','phone':'9876543210','course':'B.Tech CS','semester':1,'dept':'Computer Science'},
                {'roll':'CS002','name':'Bob Williams','email':'bob@aimt.edu','phone':'9876543211','course':'B.Tech CS','semester':1,'dept':'Computer Science'},
                {'roll':'IT001','name':'Charlie Brown','email':'charlie@aimt.edu','phone':'9876543212','course':'B.Tech IT','semester':3,'dept':'Information Technology'},
                {'roll':'IT002','name':'Diana Prince','email':'diana@aimt.edu','phone':'9876543213','course':'B.Tech IT','semester':3,'dept':'Information Technology'},
                {'roll':'ME001','name':'Edward Norton','email':'edward@aimt.edu','phone':'9876543214','course':'B.Tech ME','semester':5,'dept':'Mechanical Engineering'},
            ]
            for info in sample_students:
                student = Student(
                    roll_number=info['roll'],
                    name=info['name'],
                    email=info['email'],
                    phone=info['phone'],
                    course=info['course'],
                    semester=info['semester'],
                    department=info['dept']
                )
                db.session.add(student)
                db.session.flush()  # so student.id is available

                # create a corresponding user account for the student
                if not User.query.filter_by(employee_id=info['roll']).first():
                    user = User(
                        employee_id=info['roll'],
                        name=info['name'],
                        email=info['email'],
                        phone=info['phone'],
                        role='Student',
                        department=info['dept'],
                        designation='Student',
                        password=generate_password_hash('student123'),
                        is_active=True
                    )
                    db.session.add(user)
                    # link back to student record
                    student.user_id = user.employee_id

        
        db.session.commit()


if __name__ == '__main__':
    init_db()
    app.run(debug=True)
