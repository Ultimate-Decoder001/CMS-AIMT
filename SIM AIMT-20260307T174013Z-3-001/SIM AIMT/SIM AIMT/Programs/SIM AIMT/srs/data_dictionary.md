# Data Dictionary

## User
| Field | Type | Description |
|------|------|-------------|
| employee_id | String | Primary key (login ID) |
| password | String | Hashed password |
| role | String | User role (Registrar, Library, etc.) |
| name | String | Full name |
| email | String | Unique email |
| phone | String | Phone |
| department | String | Department |
| designation | String | Job title |
| is_active | Boolean | Active status |

## Book
| Field | Type | Description |
|------|------|-------------|
| book_id | Integer | Primary key |
| book_code | String | Auto-generated unique code |
| title | String | Book title |
| author | String | Book author |
| edition | String | Edition string (e.g., 2nd) |
| isbn | String | ISBN (unique) |
| category | String | Category |
| quantity | Integer | Total quantity |
| available_quantity | Integer | Quantity currently available |
| shelf_location | String | Shelf location |

## BookTransaction
| Field | Type | Description |
|------|------|-------------|
| id | Integer | Primary key |
| book_id | Integer | FK to Book |
| employee_id | String | FK to User |
| issue_date | Date | Issue date |
| due_date | Date | Due date |
| return_date | Date | Return date |
| status | String | Issued/Returned |

## Salary
... (and so on for other models)
