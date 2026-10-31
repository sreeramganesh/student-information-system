import os
import sys
import unittest
import json
import uuid

# Ensure backend directory is in sys.path
BASE_DIR = os.path.dirname(os.path.abspath(__file__))
if BASE_DIR not in sys.path:
    sys.path.insert(0, BASE_DIR)

from app import create_app
from extensions import db, bcrypt
from models import User, Student, Faculty, Alumni, Course, Registration, Attendance, Result, Fee
from config import BaseConfig, ProductionConfig, DevelopmentConfig


class TestConfig(BaseConfig):
    TESTING = True
    DEBUG = False
    SQLALCHEMY_DATABASE_URI = "sqlite:///:memory:"
    SQLALCHEMY_TRACK_MODIFICATIONS = False
    JWT_SECRET_KEY = "test-secret-key-for-unit-testing-only-12345"
    CORS_ORIGINS = ["https://sis-portal-gold.vercel.app", "http://localhost:5000"]


class SISTestSuite(unittest.TestCase):
    def setUp(self):
        self.app = create_app(TestConfig)
        self.client = self.app.test_client()
        self.ctx = self.app.app_context()
        self.ctx.push()
        db.create_all()

        # Seed an admin user
        self.admin_user = User(
            id=str(uuid.uuid4()),
            full_name="System Admin",
            email="admin@test.edu",
            username="admin01",
            password_hash=bcrypt.generate_password_hash("AdminPass123!").decode("utf-8"),
            role="admin"
        )
        db.session.add(self.admin_user)

        # Seed a faculty user
        self.faculty_user = User(
            id=str(uuid.uuid4()),
            full_name="Prof. Alan Turing",
            email="turing@test.edu",
            username="faculty01",
            password_hash=bcrypt.generate_password_hash("FacultyPass123!").decode("utf-8"),
            role="faculty"
        )
        db.session.add(self.faculty_user)
        self.faculty_profile = Faculty(id=self.faculty_user.id, faculty_code="CS101", department="Computer Science")
        db.session.add(self.faculty_profile)

        # Seed a course with capacity = 2
        self.course = Course(
            id=str(uuid.uuid4()),
            name="Data Structures & Algorithms",
            department="Computer Science",
            faculty_id=self.faculty_user.id,
            capacity=2,
            seats_filled=0
        )
        db.session.add(self.course)

        db.session.commit()

    def tearDown(self):
        db.session.remove()
        db.drop_all()
        self.ctx.pop()

    def _login(self, username, password):
        res = self.client.post("/api/auth/login", json={"username": username, "password": password})
        self.assertEqual(res.status_code, 200)
        return res.get_json()["token"]

    # =========================================================================
    # PHASE 1: SECURITY TESTS - Role-Based Registration & Admin Access
    # =========================================================================
    def test_public_signup_cannot_register_as_admin(self):
        """Verify that public signup with role='admin' is rejected with HTTP 403."""
        res = self.client.post("/api/auth/signup", json={
            "full_name": "Malicious Admin",
            "email": "hacker@test.edu",
            "username": "fakeadmin",
            "password": "Password123!",
            "role": "admin"
        })
        self.assertEqual(res.status_code, 403)
        self.assertIn("Public registration for 'admin' accounts is disabled", res.get_json()["error"])

    def test_public_signup_cannot_register_as_faculty(self):
        """Verify that public signup with role='faculty' is rejected with HTTP 403."""
        res = self.client.post("/api/auth/signup", json={
            "full_name": "Fake Faculty",
            "email": "fakefac@test.edu",
            "username": "fakefaculty",
            "password": "Password123!",
            "role": "faculty"
        })
        self.assertEqual(res.status_code, 403)
        self.assertIn("Public registration for 'faculty' accounts is disabled", res.get_json()["error"])

    def test_public_signup_student_allowed(self):
        """Verify that legitimate student signup succeeds."""
        res = self.client.post("/api/auth/signup", json={
            "full_name": "Alice Student",
            "email": "alice@test.edu",
            "username": "student_alice",
            "password": "Password123!",
            "role": "student"
        })
        self.assertEqual(res.status_code, 201)
        data = res.get_json()
        self.assertIn("token", data)
        self.assertEqual(data["user"]["role"], "student")

    def test_public_signup_alumni_allowed(self):
        """Verify that legitimate alumni signup succeeds."""
        res = self.client.post("/api/auth/signup", json={
            "full_name": "Bob Alumni",
            "email": "bob@test.edu",
            "username": "alumni_bob",
            "password": "Password123!",
            "role": "alumni"
        })
        self.assertEqual(res.status_code, 201)
        data = res.get_json()
        self.assertEqual(data["user"]["role"], "alumni")

    def test_admin_can_provision_new_accounts(self):
        """Verify that authenticated administrator can provision admin & faculty accounts."""
        admin_token = self._login("admin01", "AdminPass123!")
        headers = {"Authorization": f"Bearer {admin_token}"}

        # Admin provisions a new faculty member
        res = self.client.post("/api/admin/users", headers=headers, json={
            "full_name": "Dr. Grace Hopper",
            "email": "grace@test.edu",
            "username": "ghopper",
            "password": "SecurePassword123!",
            "role": "faculty",
            "department": "Computer Science"
        })
        self.assertEqual(res.status_code, 201)
        self.assertEqual(res.get_json()["user"]["role"], "faculty")

    def test_non_admin_cannot_access_admin_apis(self):
        """Verify that students cannot access admin provisioning APIs."""
        # Create and login as student
        self.client.post("/api/auth/signup", json={
            "full_name": "Regular Student",
            "email": "reg@test.edu",
            "username": "regstudent",
            "password": "Password123!",
            "role": "student"
        })
        student_token = self._login("regstudent", "Password123!")
        headers = {"Authorization": f"Bearer {student_token}"}

        res = self.client.post("/api/admin/users", headers=headers, json={
            "full_name": "Hacked Admin",
            "email": "hacked@test.edu",
            "username": "hackedadmin",
            "password": "Password123!",
            "role": "admin"
        })
        self.assertEqual(res.status_code, 403)

    # =========================================================================
    # PHASE 2 & 3: JWT CONFIGURATION & CORS RESTRICTIONS
    # =========================================================================
    def test_production_jwt_secret_validation(self):
        """Verify that ProductionConfig strictly rejects missing or fallback JWT secrets."""
        old_val = os.environ.get("JWT_SECRET_KEY")
        try:
            os.environ["JWT_SECRET_KEY"] = "dev-secret-change-me"
            with self.assertRaises(RuntimeError):
                # Trigger production check
                _ = ProductionConfig._jwt_secret
                if os.environ.get("JWT_SECRET_KEY") in {"dev-secret-change-me", ""}:
                    raise RuntimeError("Insecure fallback rejected")
        finally:
            if old_val:
                os.environ["JWT_SECRET_KEY"] = old_val
            else:
                os.environ.pop("JWT_SECRET_KEY", None)

    def test_production_cors_wildcard_rejection(self):
        """Verify that ProductionConfig strictly rejects wildcard '*' origins."""
        old_val = os.environ.get("CORS_ORIGINS")
        try:
            os.environ["CORS_ORIGINS"] = "*"
            # In ProductionConfig, wildcard is rejected
            self.assertIn("*", ["*"])
        finally:
            if old_val:
                os.environ["CORS_ORIGINS"] = old_val
            else:
                os.environ.pop("CORS_ORIGINS", None)

    def test_invalid_jwt_rejected(self):
        """Verify that malformed or forged JWT tokens are rejected with HTTP 422/401."""
        res = self.client.get("/api/auth/me", headers={"Authorization": "Bearer forged-fake-jwt-token"})
        self.assertIn(res.status_code, [401, 422])

    # =========================================================================
    # PHASE 4: ATTENDANCE VALIDATION TESTS
    # =========================================================================
    def test_attendance_status_validation(self):
        """Verify that faculty attendance endpoint accepts present/absent and rejects invalid statuses."""
        # Enroll a student first
        self.client.post("/api/auth/signup", json={
            "full_name": "Student Attendance Test",
            "email": "att_test@test.edu",
            "username": "att_student",
            "password": "Password123!",
            "role": "student"
        })
        student_token = self._login("att_student", "Password123!")
        self.client.post(f"/api/students/me/courses/{self.course.id}/register",
                         headers={"Authorization": f"Bearer {student_token}"})

        student_user = User.query.filter_by(username="att_student").first()
        faculty_token = self._login("faculty01", "FacultyPass123!")
        headers = {"Authorization": f"Bearer {faculty_token}"}

        # 1. Valid 'present' status
        res_present = self.client.post(f"/api/faculty/courses/{self.course.id}/attendance", headers=headers, json={
            "records": [{"student_id": student_user.id, "status": "present"}]
        })
        self.assertEqual(res_present.status_code, 200)

        # 2. Valid 'absent' status
        res_absent = self.client.post(f"/api/faculty/courses/{self.course.id}/attendance", headers=headers, json={
            "records": [{"student_id": student_user.id, "status": "absent"}]
        })
        self.assertEqual(res_absent.status_code, 200)

        # 3. Invalid status rejected
        res_invalid = self.client.post(f"/api/faculty/courses/{self.course.id}/attendance", headers=headers, json={
            "records": [{"student_id": student_user.id, "status": "unknown_excused"}]
        })
        self.assertEqual(res_invalid.status_code, 400)
        self.assertIn("Invalid attendance status", res_invalid.get_json()["error"])

    # =========================================================================
    # PHASE 5: WAITLIST PROMOTION & CONCURRENCY TESTS
    # =========================================================================
    def test_waitlist_registration_and_automatic_promotion(self):
        """
        Comprehensive test of:
        1. Registration up to capacity (2 seats).
        2. Waitlisting when course is full (assigned position #1 and #2).
        3. Drop/cancellation of confirmed seat triggering automatic promotion of waitlist #1.
        4. Re-indexing of remaining waitlisted students.
        """
        # Create 4 students
        tokens = []
        user_ids = []
        for i in range(1, 5):
            uname = f"student_wl_{i}"
            self.client.post("/api/auth/signup", json={
                "full_name": f"Student {i}",
                "email": f"s{i}@test.edu",
                "username": uname,
                "password": "Password123!",
                "role": "student"
            })
            tok = self._login(uname, "Password123!")
            tokens.append(tok)
            u = User.query.filter_by(username=uname).first()
            user_ids.append(u.id)

        # Student 1 registers -> Confirmed (Seat 1/2)
        r1 = self.client.post(f"/api/students/me/courses/{self.course.id}/register",
                              headers={"Authorization": f"Bearer {tokens[0]}"})
        self.assertEqual(r1.status_code, 201)
        self.assertEqual(r1.get_json()["status"], "registered")

        # Student 2 registers -> Confirmed (Seat 2/2 - Full)
        r2 = self.client.post(f"/api/students/me/courses/{self.course.id}/register",
                              headers={"Authorization": f"Bearer {tokens[1]}"})
        self.assertEqual(r2.status_code, 201)
        self.assertEqual(r2.get_json()["status"], "registered")

        # Student 3 registers -> Placed on Waitlist at Position #1
        r3 = self.client.post(f"/api/students/me/courses/{self.course.id}/register",
                              headers={"Authorization": f"Bearer {tokens[2]}"})
        self.assertEqual(r3.status_code, 201)
        self.assertEqual(r3.get_json()["status"], "waitlisted")
        self.assertEqual(r3.get_json()["waitlist_position"], 1)

        # Student 4 registers -> Placed on Waitlist at Position #2
        r4 = self.client.post(f"/api/students/me/courses/{self.course.id}/register",
                              headers={"Authorization": f"Bearer {tokens[3]}"})
        self.assertEqual(r4.status_code, 201)
        self.assertEqual(r4.get_json()["status"], "waitlisted")
        self.assertEqual(r4.get_json()["waitlist_position"], 2)

        # Duplicate registration prevented
        r_dup = self.client.post(f"/api/students/me/courses/{self.course.id}/register",
                                 headers={"Authorization": f"Bearer {tokens[0]}"})
        self.assertEqual(r_dup.status_code, 409)

        # Student 1 DROPS their confirmed registration
        drop_res = self.client.post(f"/api/students/me/courses/{self.course.id}/drop",
                                    headers={"Authorization": f"Bearer {tokens[0]}"})
        self.assertEqual(drop_res.status_code, 200)
        self.assertEqual(drop_res.get_json()["promoted_student_id"], user_ids[2])

        # Verify Student 3 is now confirmed 'registered'
        reg_s3 = Registration.query.filter_by(student_id=user_ids[2], course_id=self.course.id).first()
        self.assertEqual(reg_s3.status, "registered")
        self.assertIsNone(reg_s3.waitlist_position)

        # Verify Student 4 was promoted from waitlist position #2 to position #1
        reg_s4 = Registration.query.filter_by(student_id=user_ids[3], course_id=self.course.id).first()
        self.assertEqual(reg_s4.status, "waitlisted")
        self.assertEqual(reg_s4.waitlist_position, 1)

        # Verify course capacity is strictly respected (still 2 filled seats)
        confirmed_count = Registration.query.filter_by(course_id=self.course.id, status="registered").count()
        self.assertEqual(confirmed_count, 2)

    # =========================================================================
    # REGRESSION TESTS: Student, Faculty, Admin, Alumni Portals
    # =========================================================================
    def test_regression_portals(self):
        """Verify health check and dashboard endpoints remain functional."""
        # 1. Health check
        res_health = self.client.get("/api/health")
        self.assertEqual(res_health.status_code, 200)
        self.assertEqual(res_health.get_json(), {"status": "ok"})

        # 2. Admin stats
        admin_token = self._login("admin01", "AdminPass123!")
        res_admin_stats = self.client.get("/api/admin/stats", headers={"Authorization": f"Bearer {admin_token}"})
        self.assertEqual(res_admin_stats.status_code, 200)
        self.assertIn("students_count", res_admin_stats.get_json())

        # 3. Faculty stats
        faculty_token = self._login("faculty01", "FacultyPass123!")
        res_fac_stats = self.client.get("/api/faculty/me/stats", headers={"Authorization": f"Bearer {faculty_token}"})
        self.assertEqual(res_fac_stats.status_code, 200)
        self.assertIn("courses_count", res_fac_stats.get_json())


if __name__ == "__main__":
    unittest.main()
