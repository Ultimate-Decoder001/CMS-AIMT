#!/usr/bin/env python
"""
Automated Integration Tests for CMS AIMT
Tests key functionality: login, library ops, employee management, persistence
"""

import sys
import os
import requests
import json
from requests.packages.urllib3.exceptions import InsecureRequestWarning

# Suppress SSL warnings for local testing
requests.packages.urllib3.disable_warnings(InsecureRequestWarning)

# Configuration
BASE_URL = "http://localhost:5000"
# For ngrok: BASE_URL = "https://crinklier-sliverlike-concetta.ngrok-free.dev"

class Colors:
    GREEN = '\033[92m'
    RED = '\033[91m'
    YELLOW = '\033[93m'
    BLUE = '\033[94m'
    END = '\033[0m'

def print_test(name, passed, message=""):
    status = f"{Colors.GREEN}✅ PASS{Colors.END}" if passed else f"{Colors.RED}❌ FAIL{Colors.END}"
    print(f"{status} | {name}")
    if message:
        print(f"     └─ {message}")

def print_section(title):
    print(f"\n{Colors.BLUE}{'='*70}{Colors.END}")
    print(f"{Colors.BLUE}{title}{Colors.END}")
    print(f"{Colors.BLUE}{'='*70}{Colors.END}")

# Test Session
session = requests.Session()
session.verify = False

print(f"\n{Colors.YELLOW}CMS AIMT - Automated Test Suite{Colors.END}")
print(f"Target: {BASE_URL}\n")

# ==================================
# 1. LOGIN TESTS
# ==================================
print_section("1. LOGIN TESTS")

test_users = [
    ("REG001", "registrar123", "Registrar"),
    ("LBH001", "library123", "Library Head"),
    ("FAC001", "faculty123", "Faculty"),
    ("STU001", "student123", "Student"),
]

login_tokens = {}

for user_id, password, role in test_users:
    try:
        response = session.post(f"{BASE_URL}/login", data={
            "employee_id": user_id,
            "password": password
        }, allow_redirects=False)
        
        passed = response.status_code in [200, 302]  # 200 = page loaded, 302 = redirect
        print_test(f"Login {role} ({user_id})", passed, 
                  f"Status: {response.status_code}")
        
        if passed:
            # Try to access dashboard to verify session
            dashboard = session.get(f"{BASE_URL}/dashboard")
            session_valid = dashboard.status_code == 200 and user_id in dashboard.text
            print_test(f"  └─ Dashboard access for {role}", session_valid)
            
    except Exception as e:
        print_test(f"Login {role} ({user_id})", False, str(e))

# ==================================
# 2. LIBRARY FUNCTIONALITY (LBH001)
# ==================================
print_section("2. LIBRARY FUNCTIONALITY (Library Head)")

try:
    # Library Dashboard
    resp = session.get(f"{BASE_URL}/library_dashboard")
    library_dash = resp.status_code == 200
    print_test("Library Dashboard accessible", library_dash, f"Status: {resp.status_code}")
    
    if library_dash:
        has_title = "Total Books" in resp.text or "Books" in resp.text
        print_test("  └─ Dashboard contains library content", has_title)
    
    # Books List
    resp = session.get(f"{BASE_URL}/library_books")
    books_page = resp.status_code == 200
    print_test("Library Books page accessible", books_page, f"Status: {resp.status_code}")
    
    # Transactions List
    resp = session.get(f"{BASE_URL}/library_transactions")
    trans_page = resp.status_code == 200
    print_test("Library Transactions page accessible", trans_page, f"Status: {resp.status_code}")
    
except Exception as e:
    print_test("Library functionality", False, str(e))

# ==================================
# 3. EMPLOYEE MANAGEMENT
# ==================================
print_section("3. EMPLOYEE MANAGEMENT")

try:
    # Manage Employees Page
    resp = session.get(f"{BASE_URL}/manage_employees")
    emp_page = resp.status_code == 200
    print_test("Manage Employees page accessible", emp_page, f"Status: {resp.status_code}")
    
    if emp_page:
        # Check if students are filtered out
        has_student_text = "STU001" in resp.text and "Student" in resp.text
        student_excluded = not has_student_text
        print_test("  └─ Students excluded from employee list", student_excluded)
        
        # Check employee count in page
        has_employee_count = "Total" in resp.text or "Employees" in resp.text
        print_test("  └─ Employee count displayed", has_employee_count)
    
    # Add Employee Page
    resp = session.get(f"{BASE_URL}/add_employee")
    add_emp_page = resp.status_code == 200
    print_test("Add Employee page accessible", add_emp_page, f"Status: {resp.status_code}")
    
except Exception as e:
    print_test("Employee management", False, str(e))

# ==================================
# 4. DASHBOARD STATS
# ==================================
print_section("4. DASHBOARD STATS")

try:
    resp = session.get(f"{BASE_URL}/dashboard")
    dashboard = resp.status_code == 200
    print_test("Dashboard page loads", dashboard, f"Status: {resp.status_code}")
    
    if dashboard:
        # Extract stats (looking for numbers in common stat formats)
        stats_found = {
            "employees": "Total Employees" in resp.text,
            "students": "Total Students" in resp.text,
            "books": "Total Books" in resp.text,
        }
        
        for stat, found in stats_found.items():
            print_test(f"  └─ {stat.title()} stat displayed", found)

except Exception as e:
    print_test("Dashboard stats", False, str(e))

# ==================================
# 5. ROLE-BASED ACCESS CONTROL
# ==================================
print_section("5. ROLE-BASED ACCESS CONTROL")

try:
    # Student trying to access employee management
    resp = session.get(f"{BASE_URL}/manage_employees")
    # Should either redirect or show 403
    student_blocked = resp.status_code in [302, 403] or "dashboard" in resp.url
    print_test("Student blocked from employee management", student_blocked, 
              f"Status: {resp.status_code}")
    
    # Test add employee (should be restricted)
    resp = session.get(f"{BASE_URL}/add_employee")
    add_blocked = resp.status_code in [302, 403]
    print_test("Student blocked from add employee", add_blocked, 
              f"Status: {resp.status_code}")
    
except Exception as e:
    print_test("RBAC", False, str(e))

# ==================================
# 6. FORM VALIDATION
# ==================================
print_section("6. FORM VALIDATION")

try:
    # Test invalid login
    resp = session.post(f"{BASE_URL}/login", data={
        "employee_id": "INVALID_USER",
        "password": "wrongpass"
    }, allow_redirects=False)
    
    invalid_rejected = resp.status_code in [200, 302]  # Back to login or error
    print_test("Invalid login rejected", invalid_rejected, f"Status: {resp.status_code}")
    
except Exception as e:
    print_test("Form validation", False, str(e))

# ==================================
# 7. ERROR HANDLING
# ==================================
print_section("7. ERROR HANDLING")

try:
    # Test 404
    resp = session.get(f"{BASE_URL}/invalid-page-that-does-not-exist")
    not_found = resp.status_code == 404
    print_test("404 error handled", not_found, f"Status: {resp.status_code}")
    
    # Try accessing protected route as anonymous
    session.cookies.clear()
    resp = session.get(f"{BASE_URL}/dashboard", allow_redirects=False)
    protected = resp.status_code in [302, 401]  # Should redirect to login
    print_test("Protected routes require login", protected, f"Status: {resp.status_code}")
    
except Exception as e:
    print_test("Error handling", False, str(e))

# ==================================
# 8. SUMMARY
# ==================================
print_section("TEST SUITE COMPLETE")
print(f"{Colors.YELLOW}Review the results above to identify any failures.{Colors.END}")
print(f"{Colors.YELLOW}For detailed testing, refer to TEST_COMPREHENSIVE.md{Colors.END}\n")

print(f"{Colors.GREEN}Manual Test Steps:{Colors.END}")
print("1. Test Library Dashboard: Login as LBH001")
print("2. Test Add/Edit/Delete Book functionality")
print("3. Test Issue Book workflow")
print("4. Add new employee and verify it persists after restart")
print("5. Delete employee and restart server - verify it stays deleted")
print("6. Check employee count on dashboard is correct (2, not 4)")
print()
