from app import app, db, User
from werkzeug.security import generate_password_hash

with app.app_context():
    if User.query.filter_by(employee_id='ADMIN001').first():
        print('ADMIN001 already exists')
    else:
        reg = User(
            employee_id='ADMIN001',
            name='Registrar',
            email='registrar@aimt.edu',
            phone='1234567890',
            role='Registrar',
            department='Administration',
            designation='Registrar',
            password=generate_password_hash('admin123'),
            is_active=True
        )
        db.session.add(reg)
        db.session.commit()
        print('Created ADMIN001')
