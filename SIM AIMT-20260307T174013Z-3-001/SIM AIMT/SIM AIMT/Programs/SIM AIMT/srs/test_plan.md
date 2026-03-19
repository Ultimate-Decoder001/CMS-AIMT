# Test Plan

## 1. Test Objectives
- Verify functional requirements are met.
- Ensure security of authentication and role enforcement.
- Validate data persistence and integrity.

## 2. Test Scope
- All web routes and user flows.
- Database operations (CRUD).
- UI behavior for library search/sort.

## 3. Test Types
### 3.1 Unit Tests
- Test route handlers for expected responses.
- Validate model behaviors.

### 3.2 Integration Tests
- End-to-end tests using Flask test client.

### 3.3 Manual Tests
- Perform typical user flows (login, add book, issue/return, etc.)

## 4. Test Artifacts
- `Programs/SIM AIMT/tests/test_routes.py` (existing tests)

## 5. Execution
Run:
```bash
pytest -q
```
