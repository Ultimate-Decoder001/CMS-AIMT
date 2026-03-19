import os
import sys
import pytest

# Ensure app directory is on path
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))

from app import app


@pytest.fixture
def client():
    app.config['TESTING'] = True
    with app.test_client() as client:
        yield client


def test_index_redirects_to_login(client):
    rv = client.get('/')
    assert rv.status_code in (301, 302)
    location = rv.headers.get('Location', '')
    assert '/login' in location


def test_add_student_get(client):
    # ensure the add student form uses roll number and initial password
    rv = client.get('/add_student')
    assert rv.status_code == 200
    assert b'Roll Number' in rv.data
    assert b'Initial Password' in rv.data
    assert b'Student Login ID' not in rv.data
    assert b'Mobile' not in rv.data


def test_student_login_get(client):
    rv = client.get('/student_login')
    assert rv.status_code == 200
    # page should refer to roll number
    assert b'Roll Number' in rv.data


def test_student_login_post_invalid_id(client):
    # posting an unknown roll number should show an error
    rv = client.post('/student_login', data={'roll_number': 'INVALID', 'password': 'x'})
    assert rv.status_code == 200
    assert b'Roll number not found' in rv.data or b'Roll Number' in rv.data

