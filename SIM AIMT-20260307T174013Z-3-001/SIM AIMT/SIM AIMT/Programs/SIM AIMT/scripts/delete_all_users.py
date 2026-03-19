from app import app, db, User
import json, datetime, os

with app.app_context():
    users = []
    for u in User.query.all():
        users.append({
            'employee_id': u.employee_id,
            'name': u.name,
            'email': u.email,
            'phone': getattr(u, 'phone', None),
            'role': u.role,
            'department': u.department,
            'designation': u.designation,
            'is_active': u.is_active
        })

    os.makedirs('backups', exist_ok=True)
    fname = os.path.join('backups', f'users_backup_{datetime.datetime.now().strftime("%Y%m%d%H%M%S")}.json')
    with open(fname, 'w', encoding='utf-8') as f:
        json.dump(users, f, indent=2, ensure_ascii=False)
    print('Backup saved to', fname)

    # Delete all users
    deleted = User.query.delete()
    db.session.commit()
    print(f'Deleted {deleted} users from the database')
