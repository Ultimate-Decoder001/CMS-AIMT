# Use Cases

## UC-1: User Login
**Actor:** Any registered user
**Preconditions:** User has valid credentials.
**Main Flow:**
1. User enters employee ID and password.
2. System authenticates credentials.
3. System redirects to role-specific dashboard.

## UC-2: Add New Book
**Actor:** Library staff (or permitted role)
**Preconditions:** User is logged in and has library role.
**Main Flow:**
1. User navigates to Add Book page.
2. User enters book details (title, author, edition, ISBN, quantity, etc.).
3. System validates uniqueness (book code, ISBN, title+author+edition).
4. System saves the book and redirects to manage books.

## UC-3: Issue Book
**Actor:** Library staff
**Main Flow:**
1. User selects a book and employee.
2. System creates an issue transaction with due date + status Issued.
3. System decrements available quantity.

## UC-4: Return Book
**Actor:** Library staff
**Main Flow:**
1. User selects an Issued transaction.
2. System marks it Returned, sets return date.
3. System increments available quantity.
