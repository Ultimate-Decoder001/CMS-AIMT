# Database Migration Guide

This project uses **Flask-Migrate** (built on Alembic) for managing database schema changes without losing data.

## Overview

Flask-Migrate allows you to:
- Track schema changes over time
- Apply/rollback migrations safely
- Preserve data when updating the database
- Maintain version control of the database structure

## Setup (Already Complete)

The migration system has been initialized with:
- ✅ Flask-Migrate installed
- ✅ `migrations/` folder created
- ✅ Initial migration for the current schema
- ✅ Database created with all tables
- ✅ Test data seeded

## Common Migration Commands

### 1. **Creating a New Migration (After Model Changes)**

When you modify a model (add/remove fields, change column types), create a migration:

```bash
cd /home/sonu-kumar/CMS\ AIMT/SIM\ AIMT-20260307T174013Z-3-001/SIM\ AIMT/SIM\ AIMT/Programs/SIM\ AIMT
source ./linux_venv/bin/activate
flask db migrate -m "Add description field to grades"
```

This generates a new migration file in `migrations/versions/`.

### 2. **Applying Migrations (Update Database)**

After creating migrations, apply them to update the database:

```bash
flask db upgrade
```

### 3. **Rolling Back Migrations**

If you need to undo the last migration:

```bash
flask db downgrade
```

### 4. **Viewing Migration History**

See all applied migrations:

```bash
flask db history
```

### 5. **Seeding Test Data**

To populate the database with test data:

```bash
python seed_data.py
```

**Note:** The seed script checks if data exists before adding. To reset and reseed:

```bash
rm aimt_college.db
flask db upgrade
python seed_data.py
```

## Example Workflow: Adding a New Field

### Step 1: Modify the Model

Edit `app.py` and update the Grade model:

```python
class Grade(db.Model):
    # ... existing fields ...
    max_marks = db.Column(db.Float, default=100)          # ✓ Already added
    remarks = db.Column(db.Text)                          # ✓ Already added
    feedback = db.Column(db.Text)                         # NEW: Add this
```

### Step 2: Create Migration

```bash
flask db migrate -m "Add feedback field to grades"
```

This creates a migration file. Review it in `migrations/versions/`.

### Step 3: Apply Migration

```bash
flask db upgrade
```

The database is now updated with the new field. **No data is lost!**

## Test Data

The database is seeded with:

### Users (5 total)
- **Registrar** (REG001)
- **HOD Computer Science** (HOD001)
- **HOD Electronics** (HOD002)
- **Faculty CSE** (FAC001)
- **Faculty EC** (FAC002)

### Students (7 total)
- **4 Computer Science** students with grades
- **3 Electronics** students with grades

### Grades
- 14 grade records with marks, max_marks, and remarks

### Login Credentials

```
Email: registrar@aimt.edu
Password: password123

Email: hod.cse@aimt.edu
Password: password123

Email: hod.ec@aimt.edu
Password: password123
```

## File Structure

```
migrations/
├── alembic.ini                 # Configuration file
├── env.py                       # Migration environment setup
├── script.py.mako              # Migration script template
├── versions/                   # Migration files directory
│   └── xxxxx_initial_migration.py
└── README

app.py                          # Models defined here
config.py                       # Database configuration
seed_data.py                    # Script to populate test data
aimt_college.db                 # SQLite database
```

## Benefits of Using Migrations

✅ **Version Control**: Track all database changes  
✅ **Data Safety**: Preserve existing data when updating schema  
✅ **Team Collaboration**: Share schema changes consistently  
✅ **Rollback Support**: Undo changes if needed  
✅ **Audit Trail**: Know what changed and when  

## Troubleshooting

### Issue: "No migrations have been applied"
```bash
flask db upgrade
```

### Issue: Migration conflicts
1. Check existing migrations: `flask db history`
2. Create a new migration that resolves conflicts
3. Apply the migration: `flask db upgrade`

### Issue: Database migration mismatch
```bash
# Completely reset (loses data)
rm aimt_college.db
flask db upgrade
python seed_data.py
```

## Next Steps

You can now:
1. Make changes to models in `app.py`
2. Create migrations: `flask db migrate -m "Description"`
3. Apply them: `flask db upgrade`
4. Test the changes
5. No data loss!

For more info: https://flask-migrate.readthedocs.io/
