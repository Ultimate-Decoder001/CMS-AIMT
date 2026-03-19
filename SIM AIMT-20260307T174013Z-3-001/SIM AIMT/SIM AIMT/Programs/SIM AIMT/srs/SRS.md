# Software Requirements Specification (SRS)

## 1. Introduction
### 1.1 Purpose
This SRS defines the requirements for the AIMT College Management System (CMS), a web-based application for managing college operations.

### 1.2 Scope
The system provides role-based access to functions such as library management, attendance and leave tracking, payroll, student grades, and reports.

### 1.3 Definitions
- **CMS:** College Management System
- **RBAC:** Role-Based Access Control
- **UI:** User Interface
- **DB:** Database

## 2. Overall Description
### 2.1 Product Perspective
A standalone web application built with Flask, backed by SQLite, and served via a standard browser.

### 2.2 Interfaces
- Web UI (HTML + Bootstrap)
- SQLite database stored in `instance/aimt_college.db`

### 2.3 User Roles
- Registrar / Director / Dean (full access)
- Library staff
- HR staff
- Accounts staff
- Faculty (teaching staff)
- Students

## 3. Functional Requirements
### 3.1 Authentication
- FR1: Login using employee ID + password
- FR2: Passwords stored hashed
- FR3: Role-based access control on all views

### 3.2 Library Management
- FR4: Add/Edit/Delete books (edition + auto-generated code)
- FR5: Issue books to employees
- FR6: Return books, update availability
- FR7: Search + sort books on dashboard
- FR8: View transactions history

### 3.3 Attendance & Leave
- FR9: Mark attendance (present/absent/late)
- FR10: Submit/approve leave requests

### 3.4 Accounts
- FR11: Manage salaries
- FR12: Track expenses

### 3.5 Students
- FR13: Manage student attendance/grades
- FR14: Student dashboard (view own records)

## 4. Non-Functional Requirements
- NFR1: Secure password storage
- NFR2: Fast page loads (<2s)
- NFR3: Responsive UI
- NFR4: Modular code for maintainability

## 5. Data Dictionary
See `data_dictionary.md`.

## 6. Traceability
See `traceability_matrix.md`.
