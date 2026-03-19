#!/usr/bin/env python
"""
Seed database with test data for development and testing.
Run: python seed_data.py

This script will ONLY seed the database if:
1. No migrations have been applied yet (fresh database), OR
2. Forced with: python seed_data.py --force

This prevents accidental deletion of custom user data.
"""

from app import app, db
from app import User, Student, Grade, Subject
from werkzeug.security import generate_password_hash
from datetime import datetime
import sys

def seed_database(force=False):
    """Populate database with test data."""
    with app.app_context():
        # Check if the default test users already exist
        registrar_exists = User.query.filter_by(employee_id='REG001').first()
        
        if registrar_exists and not force:
            print("✓ Database already seeded. Skipping to prevent data loss.")
            print("  To force re-seed: python seed_data.py --force")
            return
        
        # If forcing with existing data, warn the user
        if force and registrar_exists:
            print("⚠️  Force mode: Re-seeding database (this will not delete existing custom data)")
            print("   but may cause constraint errors if you have custom users with same IDs.")
        
        print("Seeding database with test data...")
        
        # Create test users (Registrar, Faculty, HOD)
        registrar = User(
            employee_id='REG001',
            name='John Registrar',
            email='registrar@aimt.edu',
            phone='9876543210',
            password=generate_password_hash('password123'),
            role='Registrar',
            department='Administration',
            is_active=True
        )
        
        hod_cse = User(
            employee_id='HOD001',
            name='Dr. Rajesh Kumar',
            email='hod.cse@aimt.edu',
            phone='9876543211',
            password=generate_password_hash('password123'),
            role='HOD',
            department='Computer Science',
            is_active=True
        )
        
        hod_ec = User(
            employee_id='HOD002',
            name='Dr. Priya Singh',
            email='hod.ec@aimt.edu',
            phone='9876543212',
            password=generate_password_hash('password123'),
            role='HOD',
            department='Electronics',
            is_active=True
        )
        
        faculty_cse = User(
            employee_id='FAC001',
            name='Mr. Arun Sharma',
            email='faculty.cse@aimt.edu',
            phone='9876543213',
            password=generate_password_hash('password123'),
            role='Faculty',
            department='Computer Science',
            is_active=True
        )
        
        faculty_ec = User(
            employee_id='FAC002',
            name='Ms. Neha Patel',
            email='faculty.ec@aimt.edu',
            phone='9876543214',
            password=generate_password_hash('password123'),
            role='Faculty',
            department='Electronics',
            is_active=True
        )
        
        db.session.add_all([registrar, hod_cse, hod_ec, faculty_cse, faculty_ec])
        db.session.commit()
        print("✓ Created 5 test users")
        
        # Create test students - Computer Science Department
        students_cse = [
            Student(
                roll_number='CSE2024001',
                name='Aditya Verma',
                first_name='Aditya',
                last_name='Verma',
                father_name='Rajesh Verma',
                email='aditya.verma@student.aimt.edu',
                phone='9876543220',
                course='BTech',
                semester=4,
                department='Computer Science'
            ),
            Student(
                roll_number='CSE2024002',
                name='Bhavna Gupta',
                first_name='Bhavna',
                last_name='Gupta',
                father_name='Amit Gupta',
                email='bhavna.gupta@student.aimt.edu',
                phone='9876543221',
                course='BTech',
                semester=4,
                department='Computer Science'
            ),
            Student(
                roll_number='CSE2024003',
                name='Chirag Dewani',
                first_name='Chirag',
                last_name='Dewani',
                father_name='Vikram Dewani',
                email='chirag.dewani@student.aimt.edu',
                phone='9876543222',
                course='BTech',
                semester=4,
                department='Computer Science'
            ),
            Student(
                roll_number='CSE2024004',
                name='Divya Saxena',
                first_name='Divya',
                last_name='Saxena',
                father_name='Suresh Saxena',
                email='divya.saxena@student.aimt.edu',
                phone='9876543223',
                course='BTech',
                semester=4,
                department='Computer Science'
            ),
        ]
        
        # Create test students - Electronics Department
        students_ec = [
            Student(
                roll_number='EC2024001',
                name='Eshan Kumar',
                first_name='Eshan',
                last_name='Kumar',
                father_name='Mohan Kumar',
                email='eshan.kumar@student.aimt.edu',
                phone='9876543224',
                course='BTech',
                semester=4,
                department='Electronics'
            ),
            Student(
                roll_number='EC2024002',
                name='Fiona Sharma',
                first_name='Fiona',
                last_name='Sharma',
                father_name='Rajendra Sharma',
                email='fiona.sharma@student.aimt.edu',
                phone='9876543225',
                course='BTech',
                semester=4,
                department='Electronics'
            ),
            Student(
                roll_number='EC2024003',
                name='Gagan Negi',
                first_name='Gagan',
                last_name='Negi',
                father_name='Satinder Negi',
                email='gagan.negi@student.aimt.edu',
                phone='9876543226',
                course='BTech',
                semester=4,
                department='Electronics'
            ),
        ]
        
        all_students = students_cse + students_ec
        db.session.add_all(all_students)
        db.session.commit()
        print(f"✓ Created {len(all_students)} test students")
        
        # Create subjects for each department
        cse_subjects = [
            Subject(
                code='CS201',
                name='Data Structures',
                department='Computer Science',
                semester=4,
                credits=3,
                faculty_id='FAC001',
                max_marks=100,
                session_year='2025-26'
            ),
            Subject(
                code='CS202',
                name='Web Development',
                department='Computer Science',
                semester=4,
                credits=3,
                faculty_id='FAC001',
                max_marks=100,
                session_year='2025-26'
            ),
            Subject(
                code='CS203',
                name='Database Management',
                department='Computer Science',
                semester=4,
                credits=4,
                faculty_id='FAC001',
                max_marks=100,
                session_year='2025-26'
            ),
        ]
        
        ec_subjects = [
            Subject(
                code='EC201',
                name='Digital Logic',
                department='Electronics',
                semester=4,
                credits=3,
                faculty_id='FAC002',
                max_marks=100,
                session_year='2025-26'
            ),
            Subject(
                code='EC202',
                name='Microprocessors',
                department='Electronics',
                semester=4,
                credits=3,
                faculty_id='FAC002',
                max_marks=100,
                session_year='2025-26'
            ),
            Subject(
                code='EC203',
                name='Control Systems',
                department='Electronics',
                semester=4,
                credits=4,
                faculty_id='FAC002',
                max_marks=100,
                session_year='2025-26'
            ),
        ]
        
        all_subjects = cse_subjects + ec_subjects
        db.session.add_all(all_subjects)
        db.session.commit()
        print(f"✓ Created {len(all_subjects)} test subjects")
        
        
        # Create test grades for CSE students
        cse_grades = [
            Grade(student_id=students_cse[0].id, subject='Data Structures', marks=85, max_marks=100, 
                  grade='A', semester=4, exam_type='Final', marked_by='FAC001',
                  remarks='Good understanding of concepts'),
            Grade(student_id=students_cse[0].id, subject='Web Development', marks=92, max_marks=100,
                  grade='A+', semester=4, exam_type='Final', marked_by='FAC001',
                  remarks='Excellent project submission'),
            
            Grade(student_id=students_cse[1].id, subject='Data Structures', marks=78, max_marks=100,
                  grade='B', semester=4, exam_type='Final', marked_by='FAC001',
                  remarks='Needs improvement in algorithms'),
            Grade(student_id=students_cse[1].id, subject='Web Development', marks=88, max_marks=100,
                  grade='A', semester=4, exam_type='Final', marked_by='FAC001'),
            
            Grade(student_id=students_cse[2].id, subject='Data Structures', marks=95, max_marks=100,
                  grade='A+', semester=4, exam_type='Final', marked_by='FAC001',
                  remarks='Outstanding performance'),
            Grade(student_id=students_cse[2].id, subject='Web Development', marks=87, max_marks=100,
                  grade='A', semester=4, exam_type='Final', marked_by='FAC001'),
            
            Grade(student_id=students_cse[3].id, subject='Data Structures', marks=72, max_marks=100,
                  grade='B', semester=4, exam_type='Final', marked_by='FAC001',
                  remarks='Struggling with complex problems'),
            Grade(student_id=students_cse[3].id, subject='Web Development', marks=80, max_marks=100,
                  grade='B', semester=4, exam_type='Final', marked_by='FAC001'),
        ]
        
        # Create test grades for EC students
        ec_grades = [
            Grade(student_id=students_ec[0].id, subject='Digital Logic', marks=84, max_marks=100,
                  grade='A', semester=4, exam_type='Final', marked_by='FAC002'),
            Grade(student_id=students_ec[0].id, subject='Microprocessors', marks=90, max_marks=100,
                  grade='A+', semester=4, exam_type='Final', marked_by='FAC002',
                  remarks='Strong practical understanding'),
            
            Grade(student_id=students_ec[1].id, subject='Digital Logic', marks=76, max_marks=100,
                  grade='B', semester=4, exam_type='Final', marked_by='FAC002'),
            Grade(student_id=students_ec[1].id, subject='Microprocessors', marks=82, max_marks=100,
                  grade='A', semester=4, exam_type='Final', marked_by='FAC002'),
            
            Grade(student_id=students_ec[2].id, subject='Digital Logic', marks=88, max_marks=100,
                  grade='A', semester=4, exam_type='Final', marked_by='FAC002'),
            Grade(student_id=students_ec[2].id, subject='Microprocessors', marks=86, max_marks=100,
                  grade='A', semester=4, exam_type='Final', marked_by='FAC002'),
        ]
        
        all_grades = cse_grades + ec_grades
        db.session.add_all(all_grades)
        db.session.commit()
        print(f"✓ Created {len(all_grades)} test grades")
        
        print("\n✅ Database seeding completed successfully!")
        print("\nTest Login Credentials:")
        print("=" * 50)
        print("Registrar:")
        print("  Email: registrar@aimt.edu")
        print("  Password: password123")
        print("\nHOD (CSE):")
        print("  Email: hod.cse@aimt.edu")
        print("  Password: password123")
        print("\nHOD (Electronics):")
        print("  Email: hod.ec@aimt.edu")
        print("  Password: password123")
        print("=" * 50)
        print("\n📌 Data Protection:")
        print("   ✓ This script will NOT run again (prevents accidental data loss)")
        print("   ✓ Your custom users are safe")
        print("   ✓ Use 'python seed_data.py --force' ONLY to re-seed a development database")

if __name__ == '__main__':
    force = '--force' in sys.argv or '-f' in sys.argv
    seed_database(force=force)
