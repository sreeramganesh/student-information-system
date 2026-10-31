import uuid
from datetime import datetime, date
from extensions import db


def gen_uuid():
    return str(uuid.uuid4())


# ============================================================
# AUTH / PROFILE — replaces Supabase's auth.users + profiles
# ============================================================
class User(db.Model):
    __tablename__ = "users"

    id = db.Column(db.String(36), primary_key=True, default=gen_uuid)
    full_name = db.Column(db.String(120), nullable=False)
    email = db.Column(db.String(120), unique=True, nullable=False)
    username = db.Column(db.String(60), unique=True, nullable=False)
    password_hash = db.Column(db.String(255), nullable=False)
    role = db.Column(db.String(20), nullable=False)  # student | faculty | admin | alumni
    phone = db.Column(db.String(20))
    created_at = db.Column(db.DateTime, default=datetime.utcnow)

    student = db.relationship("Student", backref="user", uselist=False, cascade="all, delete-orphan")
    faculty = db.relationship("Faculty", backref="user", uselist=False, cascade="all, delete-orphan")
    alumni = db.relationship("Alumni", backref="user", uselist=False, cascade="all, delete-orphan")

    def to_dict(self):
        return {"id": self.id, "full_name": self.full_name, "email": self.email,
                "role": self.role, "phone": self.phone}

    def __init__(self, **kwargs):
        super().__init__(**kwargs)


# ============================================================
# ROLE-SPECIFIC PROFILES
# ============================================================
class Student(db.Model):
    __tablename__ = "students"

    id = db.Column(db.String(36), db.ForeignKey("users.id"), primary_key=True)
    roll_no = db.Column(db.String(30), unique=True, nullable=False)
    department = db.Column(db.String(60))
    semester = db.Column(db.Integer)
    batch_year = db.Column(db.Integer)
    cgpa = db.Column(db.Numeric(3, 2))
    address = db.Column(db.String(255))
    profile_completed = db.Column(db.Boolean, default=False, nullable=False)

    def __init__(self, **kwargs):
        super().__init__(**kwargs)


class Faculty(db.Model):
    __tablename__ = "faculty"

    id = db.Column(db.String(36), db.ForeignKey("users.id"), primary_key=True)
    faculty_code = db.Column(db.String(30), unique=True, nullable=False)
    department = db.Column(db.String(60))
    office_hours = db.Column(db.String(120))

    def __init__(self, **kwargs):
        super().__init__(**kwargs)


class Alumni(db.Model):
    __tablename__ = "alumni"

    id = db.Column(db.String(36), db.ForeignKey("users.id"), primary_key=True)
    roll_no = db.Column(db.String(30))
    department = db.Column(db.String(60))
    batch_year = db.Column(db.Integer)
    current_employer = db.Column(db.String(120))

    def __init__(self, **kwargs):
        super().__init__(**kwargs)


# ============================================================
# ACADEMICS
# ============================================================
class Course(db.Model):
    __tablename__ = "courses"

    id = db.Column(db.String(36), primary_key=True, default=gen_uuid)
    name = db.Column(db.String(120), nullable=False)
    department = db.Column(db.String(60))
    faculty_id = db.Column(db.String(36), db.ForeignKey("faculty.id"))
    capacity = db.Column(db.Integer, default=60)
    seats_filled = db.Column(db.Integer, default=0)
    created_at = db.Column(db.DateTime, default=datetime.utcnow)

    faculty = db.relationship("Faculty", backref="courses")

    def __init__(self, **kwargs):
        super().__init__(**kwargs)


class Registration(db.Model):
    __tablename__ = "registrations"
    __table_args__ = (db.UniqueConstraint("student_id", "course_id"),)

    id = db.Column(db.String(36), primary_key=True, default=gen_uuid)
    student_id = db.Column(db.String(36), db.ForeignKey("students.id"), nullable=False)
    course_id = db.Column(db.String(36), db.ForeignKey("courses.id"), nullable=False)
    status = db.Column(db.String(20), default="registered")
    waitlist_position = db.Column(db.Integer)
    created_at = db.Column(db.DateTime, default=datetime.utcnow)

    student = db.relationship("Student", backref="registrations")
    course = db.relationship("Course", backref="registrations")

    def __init__(self, **kwargs):
        super().__init__(**kwargs)


class Attendance(db.Model):
    __tablename__ = "attendance"
    __table_args__ = (db.UniqueConstraint("student_id", "course_id", "class_date"),)

    id = db.Column(db.String(36), primary_key=True, default=gen_uuid)
    student_id = db.Column(db.String(36), db.ForeignKey("students.id"), nullable=False)
    course_id = db.Column(db.String(36), db.ForeignKey("courses.id"), nullable=False)
    class_date = db.Column(db.Date, default=date.today)
    status = db.Column(db.String(10), nullable=False)
    marked_by = db.Column(db.String(36), db.ForeignKey("faculty.id"))

    course = db.relationship("Course")

    def __init__(self, **kwargs):
        super().__init__(**kwargs)


class Marks(db.Model):
    __tablename__ = "marks"
    __table_args__ = (db.UniqueConstraint("student_id", "course_id", "assessment"),)

    id = db.Column(db.String(36), primary_key=True, default=gen_uuid)
    student_id = db.Column(db.String(36), db.ForeignKey("students.id"), nullable=False)
    course_id = db.Column(db.String(36), db.ForeignKey("courses.id"), nullable=False)
    assessment = db.Column(db.String(60), nullable=False)
    marks = db.Column(db.Numeric(5, 2))
    max_marks = db.Column(db.Numeric(5, 2), default=30)

    def __init__(self, **kwargs):
        super().__init__(**kwargs)


class Result(db.Model):
    __tablename__ = "results"
    __table_args__ = (db.UniqueConstraint("student_id", "course_id"),)

    id = db.Column(db.String(36), primary_key=True, default=gen_uuid)
    student_id = db.Column(db.String(36), db.ForeignKey("students.id"), nullable=False)
    course_id = db.Column(db.String(36), db.ForeignKey("courses.id"), nullable=False)
    internal = db.Column(db.Numeric(5, 2))
    external = db.Column(db.Numeric(5, 2))
    grade = db.Column(db.String(5))
    published = db.Column(db.Boolean, default=False)

    course = db.relationship("Course")

    def __init__(self, **kwargs):
        super().__init__(**kwargs)


class Fee(db.Model):
    __tablename__ = "fees"

    id = db.Column(db.String(36), primary_key=True, default=gen_uuid)
    student_id = db.Column(db.String(36), db.ForeignKey("users.id"), nullable=False)
    receipt_no = db.Column(db.String(40))
    description = db.Column(db.String(120))
    amount = db.Column(db.Numeric(10, 2), nullable=False)
    status = db.Column(db.String(10), nullable=False)
    fee_date = db.Column(db.Date, default=date.today)

    def __init__(self, **kwargs):
        super().__init__(**kwargs)


class TranscriptRequest(db.Model):
    __tablename__ = "transcript_requests"

    id = db.Column(db.String(36), primary_key=True, default=gen_uuid)
    student_id = db.Column(db.String(36), db.ForeignKey("users.id"), nullable=False)
    purpose = db.Column(db.String(120))
    delivery_email = db.Column(db.String(120))
    status = db.Column(db.String(20), default="pending")
    requested_at = db.Column(db.DateTime, default=datetime.utcnow)

    def __init__(self, **kwargs):
        super().__init__(**kwargs)


# ============================================================
# ADMISSION DETAILS (post-signup profile completion)
# ============================================================
class AdmissionDetail(db.Model):
    __tablename__ = "admission_details"

    id = db.Column(db.String(36), primary_key=True, default=gen_uuid)
    student_id = db.Column(db.String(36), db.ForeignKey("students.id"), unique=True, nullable=False)

    date_of_birth = db.Column(db.Date)
    gender = db.Column(db.String(15))
    nationality = db.Column(db.String(40), default="Indian")
    community = db.Column(db.String(20))

    parent_name = db.Column(db.String(120))
    parent_occupation = db.Column(db.String(60))
    parent_annual_income = db.Column(db.String(20))

    address_line = db.Column(db.String(255))
    pincode = db.Column(db.String(10))
    phone = db.Column(db.String(20))

    board_of_exam = db.Column(db.String(30))
    course_opted = db.Column(db.String(60))
    submitted_at = db.Column(db.DateTime, default=datetime.utcnow)

    def __init__(self, **kwargs):
        super().__init__(**kwargs)


class HscSubjectMark(db.Model):
    __tablename__ = "hsc_subject_marks"

    id = db.Column(db.String(36), primary_key=True, default=gen_uuid)
    student_id = db.Column(db.String(36), db.ForeignKey("students.id"), nullable=False)
    subject_name = db.Column(db.String(60), nullable=False)
    max_marks = db.Column(db.Numeric(5, 2), nullable=False)
    marks_obtained = db.Column(db.Numeric(5, 2), nullable=False)

    def __init__(self, **kwargs):
        super().__init__(**kwargs)
