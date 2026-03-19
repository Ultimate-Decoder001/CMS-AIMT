# Deployment Guide

## 1. Prerequisites
- Python 3.12+
- Virtual environment support (`python3 -m venv`)

## 2. Setup
1. Create and activate venv:
   ```bash
   python3 -m venv ~/sim_aimt_venv
   source ~/sim_aimt_venv/bin/activate
   ```
2. Install dependencies:
   ```bash
   pip install -r requirements.txt
   ```
3. Run the app:
   ```bash
   python run.py
   ```

## 3. Production Deployment (Recommended)
1. Install a WSGI server (e.g., Gunicorn):
   ```bash
   pip install gunicorn
   ```
2. Run:
   ```bash
   gunicorn -w 4 -b 0.0.0.0:8000 app:app
   ```
3. Use Nginx as a reverse proxy to serve static files and proxy to Gunicorn.

## 4. Backup
- Copy `instance/aimt_college.db` to a safe location.
- Backup `backups/users_backup_*.json` as needed.
