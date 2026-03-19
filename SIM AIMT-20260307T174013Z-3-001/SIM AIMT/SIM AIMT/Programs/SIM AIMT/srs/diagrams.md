# Architecture Diagrams

## 1. Entity Relationship Diagram (ERD)

```mermaid
erDiagram
    %% Users and Roles
    USER ||--o{ LEAVE : "submits"
    USER ||--o{ ATTENDANCE : "marks/records"
    USER ||--o{ BOOK_TRANSACTION : "issues/returns"
    USER ||--o{ SALARY : "receives"
    USER ||--o{ EXPENSE : "submits/approves"
    USER ||--o{ STUDENT : "owns account for"
    USER ||--o{ NOTIFICATION : "receives"

    %% Library
    BOOK ||--o{ BOOK_TRANSACTION : "is issued in"

    %% Academic
    STUDENT ||--o{ STUDENT_ATTENDANCE : "has"
    STUDENT ||--o{ GRADE : "earns"
    STUDENT ||--o{ SUBJECT_ENROLLMENT : "enrolls in"
    SUBJECT ||--o{ SUBJECT_ENROLLMENT : "has"
    SUBJECT ||--o{ EXAM : "includes"
    EXAM ||--o{ MARK : "contains"
    STUDENT ||--o{ MARK : "receives"
    SUBJECT ||--o{ SUBJECT_ATTENDANCE : "records"
    STUDENT ||--o{ SUBJECT_ATTENDANCE : "has"

    %% User entity
    USER {
        string employee_id PK
        string name
        string email
        string role
        string password_hash
        string department
        string designation
        string phone
    }

    %% Leave/Attendance
    LEAVE {
        int id PK
        string employee_id FK
        string leave_type
        date start_date
        date end_date
        string reason
        string department
        string status
        string forwarded_by FK
        string approved_by FK
        datetime created_at
    }

    ATTENDANCE {
        int id PK
        string employee_id FK
        date date
        string status
        string marked_by FK
        string remarks
        datetime created_at
    }

    %% Library
    BOOK {
        int book_id PK
        string book_code
        string title
        string author
        string edition
        string isbn
        string category
        int quantity
        int available_quantity
        string shelf_location
        datetime created_at
    }

    BOOK_TRANSACTION {
        int id PK
        int book_id FK
        string employee_id FK
        date issue_date
        date due_date
        date return_date
        string status
    }

    %% Payroll / Expenses
    SALARY {
        int id PK
        string employee_id FK
        int month
        int year
        float basic_salary
        float hra
        float da
        float allowances
        float deductions
        float net_salary
        string payment_status
        date payment_date
        datetime created_at
    }

    EXPENSE {
        int id PK
        string category
        string description
        float amount
        date date
        string submitted_by FK
        string approved_by FK
        string status
        datetime created_at
    }

    %% Students / Academics
    STUDENT {
        int id PK
        string roll_number
        string name
        string first_name
        string last_name
        string father_name
        string email
        string phone
        string course
        int semester
        string department
        string user_id FK
        datetime created_at
    }

    STUDENT_ATTENDANCE {
        int id PK
        int student_id FK
        date date
        string status
        string marked_by FK
        string subject
        datetime created_at
    }

    GRADE {
        int id PK
        int student_id FK
        string subject
        float marks
        string grade
        int semester
        string exam_type
        string marked_by FK
        datetime created_at
    }

    SUBJECT {
        int id PK
        string code
        string name
        string department
        int semester
        int credits
        string faculty_id FK
        float max_marks
        datetime created_at
    }

    SUBJECT_ENROLLMENT {
        int id PK
        int student_id FK
        int subject_id FK
        datetime enrolled_date
    }

    EXAM {
        int id PK
        int subject_id FK
        string exam_type
        date exam_date
        float total_marks
        string created_by FK
        datetime created_at
    }

    MARK {
        int id PK
        int exam_id FK
        int student_id FK
        float marks_obtained
        string uploaded_by FK
        datetime created_at
    }

    SUBJECT_ATTENDANCE {
        int id PK
        int student_id FK
        int subject_id FK
        date date
        string status
        string marked_by FK
        datetime created_at
    }

    NOTIFICATION {
        int id PK
        string user_id FK
        string title
        string message
        bool is_read
        datetime created_at
    }
```

## 2. Data Flow Diagrams (DFD)

### 2.1 Level 0 (Context)

```mermaid
flowchart LR
    A[User Browser] -->|HTTP/S| B[Web App (Flask)]
    B -->|SQL| C[(SQLite Database)]
    B -->|Email/SMS| D[External Notification Service]
```

### 2.2 Level 1 (Core Subsystems)

```mermaid
flowchart TD
    subgraph UI [User Interface]
        U1[Login/Logout]
        U2[Dashboard]
        U3[Library]
        U4[Academics]
        U5[Finance]
        U6[Notifications]
    end

    subgraph App [Flask Application]
        A1[Auth Service]
        A2[Library Service]
        A3[Attendance Service]
        A4[Academics Service]
        A5[Payroll & Expenses]
        A6[Notification Service]
    end

    subgraph DB [(SQLite)]
        D1[Users]
        D2[Books + Transactions]
        D3[Attendance]
        D4[Students + Grades]
        D5[Finance]
        D6[Notifications]
    end

    U1 --> A1
    U2 --> A1
    U3 --> A2
    U4 --> A4
    U5 --> A5
    U6 --> A6

    A1 --> D1
    A2 --> D2
    A3 --> D3
    A4 --> D4
    A5 --> D5
    A6 --> D6

    %% Cross-service interaction
    A1 --> A6
    A2 --> A6
    A4 --> A6
    A5 --> A6
```

### 2.3 Level 2 (Subsystem Detail)

#### 2.3.1 Library Subsystem

```mermaid
flowchart TD
    subgraph Library [Library Service]
        L1[View Books]
        L2[Issue Book]
        L3[Return Book]
        L4[Search / Filter]
        L5[Inventory Update]
    end

    subgraph DB[(SQLite)]
        B[Books Table]
        T[BookTransactions Table]
    end

    L1 --> B
    L2 --> B
    L2 --> T
    L3 --> T
    L3 --> B
    L4 --> B
    L5 --> B
```

#### 2.3.2 Attendance Subsystem

```mermaid
flowchart TD
    subgraph Attendance [Attendance Service]
        A1[Mark Attendance]
        A2[View Attendance]
        A3[Generate Reports]
    end

    subgraph DB[(SQLite)]
        AT[Attendance Table]
        S[Students Table]
    end

    A1 --> AT
    A2 --> AT
    A2 --> S
    A3 --> AT
    A3 --> S
```

#### 2.3.3 Finance Subsystem

```mermaid
flowchart TD
    subgraph Finance [Payroll & Expenses]
        F1[Create Salary Record]
        F2[Submit Expense]
        F3[Approve Expense]
        F4[Generate Reports]
    end

    subgraph DB[(SQLite)]
        SAL[Salaries Table]
        EXP[Expenses Table]
        USR[Users Table]
    end

    F1 --> SAL
    F2 --> EXP
    F3 --> EXP
    F4 --> SAL
    F4 --> EXP
    F1 --> USR
    F2 --> USR
    F3 --> USR
```

## 3. Deployment Diagram

```mermaid
flowchart LR
    subgraph Client
        U[User Browser]
    end

    subgraph Server[Application Server]
        A[Flask App (WSGI)]
        N[Gunicorn / uWSGI]
        W[Static Files]
    end

    subgraph Data[Persistence]
        DB[(SQLite DB)]
        FS[(Instance / Backups)]
    end

    subgraph Infra[Infrastructure]
        H[Host / VM / Container]
        L[Load Balancer (optional)]
    end

    U -->|HTTP/HTTPS| L
    L --> A
    A --> N
    N --> DB
    N --> FS
    H --> A
    H --> DB
    H --> FS
```

## 4. UML Diagrams (Mermaid)

### 3.1 Class Diagram (Core Domains)

```mermaid
classDiagram
    class User {
        +String employee_id
        +String name
        +String email
        +String role
        +String password_hash
        +String department
        +String designation
        +String phone
    }

    class Book {
        +int book_id
        +String book_code
        +String title
        +String author
        +String edition
        +String isbn
        +String category
        +int quantity
        +int available_quantity
        +String shelf_location
        +datetime created_at
    }

    class BookTransaction {
        +int id
        +date issue_date
        +date due_date
        +date return_date
        +String status
    }

    class Student {
        +int id
        +String roll_number
        +String name
        +String course
        +int semester
    }

    class Grade {
        +int id
        +float marks
        +String grade
        +String exam_type
    }

    class Notification {
        +int id
        +String title
        +String message
        +bool is_read
    }

    User "1" -- "*" BookTransaction : "issues/returns"
    User "1" -- "*" Notification : "receives"
    User "1" -- "*" Student : "owns"
    User "1" -- "*" Grade : "marks"
    Book "1" -- "*" BookTransaction : "has"
    Student "1" -- "*" Grade : "earns"
```

### 3.2 Sequence Diagram (Book Issue / Return)

```mermaid
sequenceDiagram
    participant U as User
    participant UI as UI (Browser)
    participant S as Server (Flask)
    participant DB as Database

    U->>UI: Click "Issue Book"
    UI->>S: POST /issue_book
    S->>DB: SELECT book, user
    DB-->>S: book + user
    S->>DB: INSERT BookTransaction
    S->>DB: UPDATE Book.available_quantity
    S-->>UI: 200 OK
    UI-->>U: Success message

    U->>UI: Click "Return Book"
    UI->>S: POST /return_book
    S->>DB: UPDATE BookTransaction (return_date,status)
    S->>DB: UPDATE Book.available_quantity
    S-->>UI: 200 OK
    UI-->>U: Success message
```

### 3.3 Component Diagram (High-level)

```mermaid
flowchart LR
    subgraph Browser
        A[Web UI]
    end

    subgraph Server [Application Server]
        B[Flask App]
        C[Auth / Sessions]
        D[Business Logic]
        E[Templates + Static Assets]
    end

    subgraph Data [Persistence]
        F[(SQLite DB)]
        G[(File System / Instance folder)]
    end

    A -->|HTTP| B
    B --> C
    B --> D
    B --> E
    D --> F
    D --> G
```

## 4. Notes
- Diagrams are written in **Mermaid** so they render automatically in many Markdown viewers (including GitHub and VS Code).
- You can extend the ERD with more entities (e.g., `ExpenseCategory`, `Department`, `ExamType`) as needed.
- The DFD Level 1 shows the major subsystems; for deeper detail, add Level 2 diagrams per subsystem.
- The sequence diagram demonstrates the main user flows (login, book issue/return, etc.).

## 5. Exporting Diagrams as Images

### 5.1 Files Provided
The following Mermaid source files are available under `srs/diagrams/`:

- `erd.mmd`
- `dfd_level0.mmd`, `dfd_level1.mmd`, `dfd_library.mmd`, `dfd_attendance.mmd`, `dfd_finance.mmd`
- `deployment.mmd`
- `class_diagram.mmd`
- `sequence_book_issue_return.mmd`
- `component.mmd`

### 5.2 Rendering (Mermaid CLI)
To convert Mermaid diagrams into SVG/PNG, you can use **Mermaid CLI** (`mmdc`).

#### Install (requires Node.js + npm)
```bash
npm install -g @mermaid-js/mermaid-cli
```

#### Render an image
```bash
mmdc -i srs/diagrams/erd.mmd -o srs/diagrams/erd.svg
mmdc -i srs/diagrams/dfd_level1.mmd -o srs/diagrams/dfd_level1.png
```

### 5.3 Notes
- If `mmdc` is not found, install Node.js and npm first.
- You can render all diagrams with a simple shell loop once `mmdc` is installed:

```bash
for src in srs/diagrams/*.mmd; do
  out="${src%.mmd}.svg"
  mmdc -i "$src" -o "$out"
done
```
