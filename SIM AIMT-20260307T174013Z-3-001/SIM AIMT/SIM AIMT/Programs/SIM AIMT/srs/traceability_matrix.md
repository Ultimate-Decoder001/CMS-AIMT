# Traceability Matrix

| Requirement | Implemented In (Code/Template) | Notes |
|-----------|------------------------------|-------|
| FR1: Login (employee ID) | `app.py` `/login` route | `login_user` from Flask-Login |
| FR4: Add/Edit/Delete books | `app.py` routes: `/add_book`, `/edit_book`, `/delete_book` | Templates: `add_book.html`, `edit_book.html` |
| FR7: Issue/Return books | `app.py` routes: `/issue_book`, `/return_book` | Template: `library_transactions.html` |
| FR10: Search + sort library | `app.py` route: `/library_dashboard` | Template: `library_dashboard.html` |
| NFR2: Password hashing | `werkzeug.security.generate_password_hash` in `app.py` | |
