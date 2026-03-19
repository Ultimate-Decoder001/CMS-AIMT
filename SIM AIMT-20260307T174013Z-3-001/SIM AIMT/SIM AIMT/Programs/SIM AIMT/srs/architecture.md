# System Architecture

## 1. Overview
The AIMT College Management System is a monolithic Flask application that serves HTML templates and uses SQLite as the backend database. The application follows a traditional MVC-like structure where the Flask routes act as controllers, Jinja2 templates as views, and SQLAlchemy models as the data layer.

## 2. Components
### 2.1 Flask Application
- Single app instance defined in `app.py`
- Routes are grouped by module (library, attendance, accounts, etc.)

### 2.2 Database
- SQLite database file located in `instance/aimt_college.db`
- SQLAlchemy ORM handles model mapping.

### 2.3 Templates
- `templates/` contains Jinja2 HTML templates
- Shared layout in `base.html`

### 2.4 Static Assets
- `static/css/`, `static/js/` contain styles and scripts.

## 3. Data Flow
1. User interacts with the browser UI.
2. Request hits Flask route in `app.py`.
3. Route performs business logic and queries/modifies database.
4. Flask renders a template with data.

## 4. Deployment
- Run `python run.py` on a server.
- Consider using a production WSGI server (Gunicorn) and reverse proxy (Nginx) for production.
