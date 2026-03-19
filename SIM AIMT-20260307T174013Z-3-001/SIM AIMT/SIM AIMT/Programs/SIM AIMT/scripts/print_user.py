import sqlite3
import os

EMP='LBH001'

base_dir = os.path.abspath(os.path.join(os.path.dirname(__file__), '..'))

candidates = [
    os.path.join(base_dir, 'aimt_college.db'),
    os.path.join(base_dir, 'instance', 'aimt_college.db'),
    os.path.join(os.path.dirname(base_dir), 'instance', 'aimt_college.db'),
]

db_path = None
for p in candidates:
    if os.path.exists(p):
        db_path = p
        break

if not db_path:
    print('DB not found. Tried:\n' + '\n'.join(candidates))
    raise SystemExit(2)

print('Using DB:', db_path)
conn = sqlite3.connect(db_path)
cur = conn.cursor()
cur.execute('SELECT employee_id,name,role,department,designation,is_active FROM users WHERE employee_id=?', (EMP,))
row = cur.fetchone()
print('LBH001:', row)
cur.close()
conn.close()
