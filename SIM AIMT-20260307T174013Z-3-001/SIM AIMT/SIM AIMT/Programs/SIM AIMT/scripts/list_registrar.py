from app import app, User

with app.app_context():
    regs = User.query.filter_by(role='Registrar').all()
    if not regs:
        print('No Registrar accounts found')
    else:
        for r in regs:
            print(r.employee_id, '-', r.name, '-', r.email)