"""
Full manual API walkthrough for Dayflow HRMS.
- Talks directly to http://localhost:8000 (ensure uvicorn is running).
- Uses only the Python standard library (no pytest/requests).
- Seeds required records via SQLite where the API lacks creation endpoints.

Run: python manual_api_runner.py
"""

import json
import os
import sqlite3
import time
import urllib.error
import urllib.parse
import urllib.request
from datetime import date, datetime, timedelta
from pathlib import Path
from uuid import uuid4

BASE_URL = "http://localhost:8000"
DB_PATH = Path(__file__).resolve().parent / "dayflow.db"


def http_request(method: str, path: str, token: str | None = None, json_body=None, form_body=None, raw_body=None, headers=None):
    if sum(x is not None for x in (json_body, form_body, raw_body)) > 1:
        raise ValueError("Only one of json_body, form_body, raw_body is allowed")

    url = f"{BASE_URL}{path}"
    hdrs = {"Accept": "application/json"}
    if headers:
        hdrs.update(headers)

    data_bytes = None
    if json_body is not None:
        hdrs["Content-Type"] = "application/json"
        data_bytes = json.dumps(json_body).encode("utf-8")
    elif form_body is not None:
        hdrs["Content-Type"] = "application/x-www-form-urlencoded"
        data_bytes = urllib.parse.urlencode(form_body).encode("utf-8")
    elif raw_body is not None:
        data_bytes = raw_body

    if token:
        hdrs["Authorization"] = f"Bearer {token}"

    req = urllib.request.Request(url, data=data_bytes, headers=hdrs, method=method.upper())

    try:
        with urllib.request.urlopen(req, timeout=15) as resp:
            body = resp.read().decode("utf-8")
            try:
                parsed = json.loads(body) if body else None
            except json.JSONDecodeError:
                parsed = body
            return resp.status, parsed
    except urllib.error.HTTPError as e:
        body = e.read().decode("utf-8")
        try:
            parsed = json.loads(body)
        except json.JSONDecodeError:
            parsed = body
        return e.code, parsed
    except urllib.error.URLError as e:
        return 0, f"Connection error: {e.reason}"


def print_step(title: str):
    print(f"\n=== {title} ===")


def login(email: str, password: str):
    status, body = http_request(
        "POST",
        "/api/v1/auth/login",
        form_body={"username": email, "password": password},
    )
    print(f"Status: {status}\nResponse: {body}")
    if status == 200 and isinstance(body, dict):
        return body.get("access_token")
    return None


def register_user(email: str, password: str, role: str = "employee", is_active: bool = True):
    return http_request(
        "POST",
        "/api/v1/auth/register",
        json_body={
            "email": email,
            "password": password,
            "role": role,
            "is_active": is_active,
        },
    )


def ensure_company(conn: sqlite3.Connection) -> int:
    cur = conn.cursor()
    cur.execute("SELECT id FROM companies WHERE name=?", ("QA Co",))
    row = cur.fetchone()
    if row:
        return row[0]
    cur.execute("INSERT INTO companies (name) VALUES (?)", ("QA Co",))
    conn.commit()
    return cur.lastrowid


def sanitize_user_emails(conn: sqlite3.Connection):
    """Fix obvious bad emails that break FastAPI response validation (e.g., trailing quotes)."""
    cur = conn.cursor()
    cur.execute("SELECT id, email FROM users")
    existing = set()
    updates = []
    for user_id, email in cur.fetchall():
        if email is None:
            continue
        cleaned = (
            email.strip()
            .replace('"', "")
            .replace("'", "")
            .replace(" ", "")
            .replace(",", "")
        )
        base = cleaned
        suffix = 1
        while cleaned in existing:
            local, _, domain = base.partition("@");
            cleaned = f"{local}+dedup{suffix}@{domain}" if domain else f"{base}+dedup{suffix}"
            suffix += 1
        existing.add(cleaned)
        if cleaned != email:
            updates.append((cleaned, user_id))
    if updates:
        for cleaned, user_id in updates:
            cur.execute("UPDATE users SET email=? WHERE id=?", (cleaned, user_id))
        conn.commit()
    # Ensure admin email is correct and unique
    cur.execute("SELECT id FROM users WHERE email=?", ("admin@example.com",))
    admin_rows = cur.fetchall()
    if not admin_rows:
        cur.execute("UPDATE users SET email=? WHERE email LIKE ? LIMIT 1", ("admin@example.com", "admin@example.com%"))
    elif len(admin_rows) > 1:
        # keep first as admin@example.com, dedup others
        keep_id = admin_rows[0][0]
        for idx, row in enumerate(admin_rows[1:], start=1):
            cur.execute("UPDATE users SET email=? WHERE id=?", (f"admin+dedup{idx}@example.com", row[0]))
    conn.commit()


def ensure_employee_profile(conn: sqlite3.Connection, user_email: str, company_id: int) -> int:
    cur = conn.cursor()
    cur.execute("SELECT id FROM users WHERE email=?", (user_email,))
    user_row = cur.fetchone()
    if not user_row:
        raise RuntimeError(f"User {user_email} not found in DB")
    user_id = user_row[0]
    cur.execute("SELECT id FROM employee_profiles WHERE user_id=?", (user_id,))
    row = cur.fetchone()
    if row:
        return row[0]
    emp_id = f"EMP-{int(time.time())}-{user_id}"
    cur.execute(
        """
        INSERT INTO employee_profiles (
            user_id, company_id, employee_id, first_name, last_name,
            phone, nationality, address
        ) VALUES (?, ?, ?, ?, ?, ?, ?, ?)
        """,
        (user_id, company_id, emp_id, "QA", "User", "1234567890", "Wonderland", "123 Test St"),
    )
    conn.commit()
    return cur.lastrowid


def ensure_leave_balance(conn: sqlite3.Connection, employee_profile_id: int):
    cur = conn.cursor()
    year = date.today().year
    for leave_type in ("paid", "sick", "unpaid"):
        cur.execute(
            """
            SELECT id FROM leave_balances
            WHERE employee_profile_id=? AND leave_type=? AND year=?
            """,
            (employee_profile_id, leave_type, year),
        )
        if cur.fetchone():
            continue
        cur.execute(
            """
            INSERT INTO leave_balances (employee_profile_id, leave_type, total_days, used_days, remaining_days, year)
            VALUES (?, ?, ?, ?, ?, ?)
            """,
            (employee_profile_id, leave_type, 30, 0, 30, year),
        )
    conn.commit()


def normalize_leave_enums(conn: sqlite3.Connection):
    """Normalize leave enums to lowercase values expected by LeaveType ('paid', 'sick', 'unpaid')."""
    cur = conn.cursor()
    cur.execute("UPDATE leave_balances SET leave_type='paid' WHERE upper(leave_type)='PAID'")
    cur.execute("UPDATE leave_balances SET leave_type='sick' WHERE upper(leave_type)='SICK'")
    cur.execute("UPDATE leave_balances SET leave_type='unpaid' WHERE upper(leave_type)='UNPAID'")
    cur.execute("UPDATE leave_requests SET leave_type='paid' WHERE upper(leave_type)='PAID'")
    cur.execute("UPDATE leave_requests SET leave_type='sick' WHERE upper(leave_type)='SICK'")
    cur.execute("UPDATE leave_requests SET leave_type='unpaid' WHERE upper(leave_type)='UNPAID'")
    conn.commit()


def multipart_request(path: str, token: str, field_name: str, filename: str, content_type: str, data: bytes):
    boundary = f"----Boundary{uuid4().hex}"
    lines = []
    lines.append(f"--{boundary}")
    lines.append(
        f"Content-Disposition: form-data; name=\"{field_name}\"; filename=\"{filename}\""
    )
    lines.append(f"Content-Type: {content_type}")
    lines.append("")
    body_start = "\r\n".join(lines).encode("utf-8") + b"\r\n"
    body_end = f"\r\n--{boundary}--\r\n".encode("utf-8")
    raw_body = body_start + data + body_end
    headers = {"Content-Type": f"multipart/form-data; boundary={boundary}"}
    return http_request("POST", path, token=token, raw_body=raw_body, headers=headers)


def main():
    print("Base URL:", BASE_URL)
    print("Ensure the API is running (e.g., uvicorn app.main:app --reload).")

    # Pre-sanitize DB emails before any API calls
    if DB_PATH.exists():
        with sqlite3.connect(DB_PATH) as pre_conn:
            sanitize_user_emails(pre_conn)
            normalize_leave_enums(pre_conn)

    # Root
    print_step("Ping root")
    print(http_request("GET", "/"))

    # Admin login
    print_step("Login as seeded admin")
    admin_token = login("admin@example.com", "adminpassword")
    if not admin_token:
        print("Admin login failed; cannot proceed.")
        return

    # Prepare test users
    unique_suffix = int(time.time())
    emp_email = f"qa_emp_{unique_suffix}@example.com"
    emp_password = "EmpPassword123!"
    admin_created_email = f"qa_admin_created_{unique_suffix}@example.com"

    print_step("Register employee via /auth/register")
    print(register_user(emp_email, emp_password))

    print_step("Admin creates another user via /users")
    status, body = http_request(
        "POST",
        "/api/v1/users/",  # trailing slash avoids 307 from FastAPI
        token=admin_token,
        json_body={
            "email": admin_created_email,
            "password": "TempPass123!",
            "role": "employee",
            "is_active": True,
        },
    )
    print(f"Status: {status}\nResponse: {body}")

    # Login employee
    print_step("Login as new employee")
    emp_token = login(emp_email, emp_password)
    if not emp_token:
        print("Employee login failed; stopping early.")
        return

    # Seed data via SQLite for missing creation APIs
    conn = sqlite3.connect(DB_PATH)
    sanitize_user_emails(conn)
    normalize_leave_enums(conn)
    company_id = ensure_company(conn)
    employee_profile_id = ensure_employee_profile(conn, emp_email, company_id)
    ensure_leave_balance(conn, employee_profile_id)

    # Auth endpoints
    print_step("/auth/users/me")
    print(http_request("GET", "/api/v1/auth/users/me", token=emp_token))

    print_step("/auth/logout")
    print(http_request("POST", "/api/v1/auth/logout", token=emp_token))

    # Users endpoints
    print_step("List users (admin)")
    print(http_request("GET", "/api/v1/users?skip=0&limit=10", token=admin_token))

    # Grab user id from DB for detail/update/delete
    cur = conn.cursor()
    cur.execute("SELECT id FROM users WHERE email=?", (emp_email,))
    emp_user_id = cur.fetchone()[0]
    cur.execute("SELECT id FROM users WHERE email=?", (admin_created_email,))
    admin_created_row = cur.fetchone()
    admin_created_user_id = admin_created_row[0] if admin_created_row else None

    print_step("Get user by id (admin)")
    print(http_request("GET", f"/api/v1/users/{emp_user_id}", token=admin_token))

    print_step("Update user (self)")
    print(
        http_request(
            "PUT",
            f"/api/v1/users/{emp_user_id}",
            token=emp_token,
            json_body={"email": emp_email, "password": emp_password, "is_active": True},
        )
    )

    if admin_created_user_id:
        print_step("Delete admin-created user")
        print(http_request("DELETE", f"/api/v1/users/{admin_created_user_id}", token=admin_token))
    else:
        print_step("Delete admin-created user")
        print("Skipped (user creation failed)")

    # Settings
    print_step("Get my settings")
    print(http_request("GET", "/api/v1/settings/me", token=emp_token))
    print_step("Update my settings")
    print(
        http_request(
            "PUT",
            "/api/v1/settings/me",
            token=emp_token,
            json_body={"receive_notifications": False, "theme": "dark", "language": "en"},
        )
    )

    # Dashboard
    print_step("Employee dashboard")
    print(http_request("GET", "/api/v1/dashboard/me", token=emp_token))
    print_step("Admin dashboard")
    print(http_request("GET", "/api/v1/dashboard/admin", token=admin_token))

    # Employees
    print_step("Employee profile (me)")
    print(http_request("GET", "/api/v1/employees/me", token=emp_token))
    print_step("Employee profile by id (admin)")
    print(http_request("GET", f"/api/v1/employees/{employee_profile_id}", token=admin_token))

    print_step("Update own profile limited fields")
    print(
        http_request(
            "PUT",
            f"/api/v1/employees/{employee_profile_id}",
            token=emp_token,
            json_body={"phone": "9876543210", "address": "456 Updated Ave"},
        )
    )

    print_step("Upload profile picture")
    dummy_bytes = b"PNG-DATA"
    print(
        multipart_request(
            "/api/v1/employees/me/profile-picture",
            token=emp_token,
            field_name="file",
            filename="avatar.png",
            content_type="image/png",
            data=dummy_bytes,
        )
    )

    # Bank details
    print_step("Add bank details")
    bank_payload = {
        "employee_profile_id": employee_profile_id,
        "account_number": "1234567890",
        "bank_name": "QA Bank",
        "ifsc_code": "QABK0001",
        "branch_name": "Main",
    }
    print(http_request("POST", "/api/v1/employees/me/bank-details", token=emp_token, json_body=bank_payload))

    print_step("My bank details")
    print(http_request("GET", "/api/v1/employees/me/bank-details", token=emp_token))
    print_step("Employee bank details (admin)")
    print(http_request("GET", f"/api/v1/employees/{employee_profile_id}/bank-details", token=admin_token))

    # Update/delete bank detail (grab id)
    cur.execute("SELECT id FROM bank_details WHERE employee_profile_id=? ORDER BY id DESC LIMIT 1", (employee_profile_id,))
    bank_id = cur.fetchone()[0]
    print_step("Update bank detail")
    print(
        http_request(
            "PUT",
            f"/api/v1/employees/bank-details/{bank_id}",
            token=emp_token,
            json_body={"branch_name": "Updated Branch"},
        )
    )
    print_step("Delete bank detail")
    print(http_request("DELETE", f"/api/v1/employees/bank-details/{bank_id}", token=emp_token))

    # Skills
    print_step("Add my skill (creates skill if missing)")
    print(http_request("POST", "/api/v1/employees/me/skills?skill_in=Python", token=emp_token))
    print_step("List my skills")
    print(http_request("GET", "/api/v1/employees/me/skills", token=emp_token))
    cur.execute("SELECT id FROM skills WHERE name=?", ("Python",))
    skill_row = cur.fetchone()
    if skill_row:
        skill_id = skill_row[0]
        print_step("Admin assign skill to employee")
        print(http_request("POST", f"/api/v1/employees/{employee_profile_id}/skills?skill_id={skill_id}", token=admin_token))
        print_step("Remove my skill")
        print(http_request("DELETE", f"/api/v1/employees/me/skills/{skill_id}", token=emp_token))
        print_step("Admin remove skill from employee")
        print(http_request("DELETE", f"/api/v1/employees/{employee_profile_id}/skills/{skill_id}", token=admin_token))
    else:
        print_step("Skill ID lookup")
        print("Skipped (skill creation failed)")

    # Certifications
    cert_payload = {
        "employee_profile_id": employee_profile_id,
        "name": "PMP",
        "issuing_organization": "PMI",
        "issue_date": str(date.today()),
        "expiry_date": None,
        "credential_id": "PMP-1234",
    }
    print_step("Add my certification")
    print(http_request("POST", "/api/v1/employees/me/certifications", token=emp_token, json_body=cert_payload))
    print_step("List my certifications")
    print(http_request("GET", "/api/v1/employees/me/certifications", token=emp_token))
    cur.execute("SELECT id FROM certifications WHERE employee_profile_id=? ORDER BY id DESC LIMIT 1", (employee_profile_id,))
    cert_id = cur.fetchone()[0]
    print_step("List employee certifications (admin)")
    print(http_request("GET", f"/api/v1/employees/{employee_profile_id}/certifications", token=admin_token))
    print_step("Update certification")
    print(http_request("PUT", f"/api/v1/employees/certifications/{cert_id}", token=emp_token, json_body={"credential_id": "PMP-9999"}))
    print_step("Delete certification")
    print(http_request("DELETE", f"/api/v1/employees/certifications/{cert_id}", token=emp_token))

    # Attendance: check-in/out
    print_step("Attendance check-in")
    print(http_request("POST", "/api/v1/attendance/check-in", token=emp_token))
    print_step("Attendance check-out")
    print(http_request("POST", "/api/v1/attendance/check-out", token=emp_token))

    print_step("My attendance history")
    print(http_request("GET", "/api/v1/attendance/me", token=emp_token))
    print_step("Daily attendance (admin)")
    print(http_request("GET", f"/api/v1/attendance/daily?day={date.today()}", token=admin_token))
    print_step("Weekly attendance (admin)")
    print(http_request("GET", f"/api/v1/attendance/weekly?day_in_week={date.today()}", token=admin_token))

    # Manual attendance for yesterday to enable correction scenarios
    yesterday = date.today() - timedelta(days=1)
    manual_payload = {
        "employee_profile_id": employee_profile_id,
        "date": str(yesterday),
        "check_in_time": str(datetime.combine(yesterday, datetime.min.time()).replace(hour=9, minute=0)),
        "check_out_time": str(datetime.combine(yesterday, datetime.min.time()).replace(hour=17, minute=0)),
        "status": "present",
        "notes": "Manual entry",
    }
    print_step("Manual attendance entry (admin)")
    print(http_request("POST", "/api/v1/attendance/manual", token=admin_token, json_body=manual_payload))

    print_step("All attendance (admin)")
    print(http_request("GET", "/api/v1/attendance/all?skip=0&limit=20", token=admin_token))

    # Attendance correction requests
    cur.execute("SELECT id FROM attendances WHERE employee_profile_id=? ORDER BY id DESC LIMIT 1", (employee_profile_id,))
    attendance_id_latest = cur.fetchone()[0]
    correction_payload = {
        "attendance_id": attendance_id_latest,
        "reason": "Missed checkout",
        "requested_check_in_time": None,
        "requested_check_out_time": str(datetime.now()),
    }
    print_step("Create attendance correction")
    print(http_request("POST", "/api/v1/attendance-correction/", token=emp_token, json_body=correction_payload))

    print_step("Pending corrections (admin)")
    pending = http_request("GET", "/api/v1/attendance-correction/pending", token=admin_token)
    print(pending)
    if isinstance(pending, tuple) and isinstance(pending[1], list) and pending[1]:
        corr_id = pending[1][0].get("id")
        print_step("Approve correction (admin)")
        print(http_request("PUT", f"/api/v1/attendance-correction/{corr_id}/approve", token=admin_token))

    print_step("My correction requests")
    print(http_request("GET", "/api/v1/attendance-correction/me", token=emp_token))

    # Leave
    leave_start = date.today() + timedelta(days=2)
    leave_end = leave_start + timedelta(days=2)
    leave_payload = {
        "employee_profile_id": employee_profile_id,
        "leave_type": "paid",
        "start_date": str(leave_start),
        "end_date": str(leave_end),
        "total_days": 3,
        "reason": "Vacation",
    }
    print_step("Apply for leave")
    print(http_request("POST", "/api/v1/leave/apply", token=emp_token, json_body=leave_payload))

    print_step("My leave requests")
    print(http_request("GET", "/api/v1/leave/my-requests", token=emp_token))
    print_step("Pending leave requests (admin)")
    pending_leave = http_request("GET", "/api/v1/leave/pending", token=admin_token)
    print(pending_leave)
    if isinstance(pending_leave, tuple) and isinstance(pending_leave[1], list) and pending_leave[1]:
        leave_id = pending_leave[1][0].get("id")
        print_step("Approve leave (admin)")
        print(http_request("PUT", f"/api/v1/leave/{leave_id}/approve", token=admin_token))

    # Cancel a new pending leave to hit cancel
    cancel_start = date.today() + timedelta(days=5)
    cancel_end = cancel_start + timedelta(days=1)
    cancel_payload = {
        "employee_profile_id": employee_profile_id,
        "leave_type": "paid",
        "start_date": str(cancel_start),
        "end_date": str(cancel_end),
        "total_days": 2,
        "reason": "Personal",
    }
    http_request("POST", "/api/v1/leave/apply", token=emp_token, json_body=cancel_payload)
    cur.execute("SELECT id FROM leave_requests WHERE employee_profile_id=? AND status='pending' ORDER BY id DESC LIMIT 1", (employee_profile_id,))
    cancel_row = cur.fetchone()
    if cancel_row:
        cancel_id = cancel_row[0]
        print_step("Cancel pending leave (self)")
        print(http_request("PUT", f"/api/v1/leave/{cancel_id}/cancel", token=emp_token))
    else:
        print_step("Cancel pending leave (self)")
        print("Skipped (no pending leave found)")

    print_step("Leave balance (self)")
    print(http_request("GET", "/api/v1/leave/balance", token=emp_token))
    print_step("Leave balance (admin for employee)")
    print(http_request("GET", f"/api/v1/leave/balance?employee_profile_id={employee_profile_id}", token=admin_token))

    # Salary
    salary_payload = {
        "employee_profile_id": employee_profile_id,
        "basic_salary": 50000,
        "hra": 10000,
        "standard_allowance": 5000,
        "performance_bonus": 2000,
        "lta": 1000,
        "fixed_allowance": 3000,
        "professional_tax": 200,
        "pf_contribution": 1500,
    }
    print_step("Create salary structure (admin)")
    print(http_request("POST", "/api/v1/salary/structure", token=admin_token, json_body=salary_payload))

    print_step("My salary structure")
    print(http_request("GET", "/api/v1/salary/me", token=emp_token))

    cur.execute("SELECT id FROM salary_structures WHERE employee_profile_id=?", (employee_profile_id,))
    salary_id = cur.fetchone()[0]
    print_step("Update salary structure (admin)")
    print(http_request("PUT", f"/api/v1/salary/structure/{salary_id}", token=admin_token, json_body={"performance_bonus": 3000}))

    print_step("All payroll data (admin)")
    print(http_request("GET", "/api/v1/salary/all", token=admin_token))
    print_step("Salary slip (admin for employee)")
    print(http_request("GET", f"/api/v1/salary/{employee_profile_id}/slip", token=admin_token))

    print("\nAll endpoints exercised. Review statuses/responses above.")


if __name__ == "__main__":
    main()
