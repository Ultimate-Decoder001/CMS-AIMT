import sqlite3
import os
import sys

# Usage: python update_role.py LBH001 Library
EMP = sys.argv[1] if len(sys.argv) > 1 else 'LBH001'
ROLE = sys.argv[2] if len(sys.argv) > 2 else 'Library'

base_dir = os.path.abspath(os.path.join(os.path.dirname(__file__), '..'))
# Try common locations for the DB
candidates = [
    os.path.join(base_dir, 'aimt_college.db'),
    os.path.join(base_dir, 'instance', 'aimt_college.db'),
    os.path.join(os.path.dirname(base_dir), 'instance', 'aimt_college.db'),
    os.path.join(os.path.dirname(os.path.dirname(base_dir)), 'instance', 'aimt_college.db'),
]

db_path = None
for p in candidates:
    if os.path.exists(p):
        db_path = p
        break

if not db_path:
    print('DB not found. Tried:', '\n'.join(candidates))
    sys.exit(2)

conn = sqlite3.connect(db_path)
cur = conn.cursor()
cur.execute('UPDATE users SET role=? WHERE employee_id=?', (ROLE, EMP))
conn.commit()
print('rows_modified=', cur.rowcount)
conn.close()
