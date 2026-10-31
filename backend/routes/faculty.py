from datetime import date
from flask import Blueprint, request, jsonify
from flask_jwt_extended import get_jwt_identity
from extensions import db
from models import Faculty, User, Course, Registration, Attendance, Marks, Result, Student
from utils.decorators import role_required

faculty_bp = Blueprint("faculty", __name__, url_prefix="/api/faculty")


@faculty_bp.get("/me")
@role_required("faculty")
def get_my_profile():
    faculty_id = get_jwt_identity()
    faculty = Faculty.query.get(faculty_id)
    user = User.query.get(faculty_id)
    if not faculty:
        return jsonify({"error": "Faculty record not found"}), 404
    return jsonify({
        "full_name": user.full_name, "email": user.email,
        "faculty_code": faculty.faculty_code, "department": faculty.department,
        "office_hours": faculty.office_hours,
    }), 200


@faculty_bp.put("/me")
@role_required("faculty")
def update_my_profile():
    data = request.get_json(force=True) or {}
    faculty_id = get_jwt_identity()
    user = User.query.get(faculty_id)
    faculty = Faculty.query.get(faculty_id)

    if "email" in data:
        user.email = data["email"].strip()
    if "office_hours" in data:
        faculty.office_hours = data["office_hours"].strip()

    db.session.commit()
    return jsonify({"message": "Profile updated"}), 200


@faculty_bp.get("/me/courses")
@role_required("faculty")
def get_my_courses():
    faculty_id = get_jwt_identity()
    courses = Course.query.filter_by(faculty_id=faculty_id).all()
    return jsonify([{
        "id": c.id, "name": c.name, "department": c.department,
        "capacity": c.capacity, "seats_filled": c.seats_filled,
    } for c in courses]), 200


@faculty_bp.get("/me/stats")
@role_required("faculty")
def get_my_stats():
    faculty_id = get_jwt_identity()
    courses = Course.query.filter_by(faculty_id=faculty_id).all()
    course_ids = [c.id for c in courses]

    students_count = Registration.query.filter(
        Registration.course_id.in_(course_ids), Registration.status == "registered"
    ).count() if course_ids else 0

    att = Attendance.query.filter(Attendance.course_id.in_(course_ids)).all() if course_ids else []
    avg_attendance = round((sum(1 for a in att if a.status == "present") / len(att)) * 100) if att else None

    results_pending = Result.query.filter(
        Result.course_id.in_(course_ids), Result.published == False  # noqa: E712
    ).count() if course_ids else 0

    return jsonify({
        "courses_count": len(courses), "students_count": students_count,
        "avg_attendance": avg_attendance, "results_pending": results_pending,
    }), 200


def _verify_owns_course(course_id, faculty_id):
    course = Course.query.get(course_id)
    if not course or course.faculty_id != faculty_id:
        return None
    return course


@faculty_bp.get("/courses/<course_id>/class-list")
@role_required("faculty")
def class_list(course_id):
    faculty_id = get_jwt_identity()
    if not _verify_owns_course(course_id, faculty_id):
        return jsonify({"error": "Not your course"}), 403

    regs = Registration.query.filter_by(course_id=course_id, status="registered").all()
    result = []
    for r in regs:
        att = Attendance.query.filter_by(student_id=r.student_id, course_id=course_id).all()
        pct = round((sum(1 for a in att if a.status == "present") / len(att)) * 100) if att else None
        result.append({
            "student_id": r.student_id, "roll_no": r.student.roll_no,
            "full_name": r.student.user.full_name, "attendance_pct": pct,
        })
    return jsonify(result), 200


ALLOWED_ATTENDANCE_STATUSES = {"present", "absent"}


@faculty_bp.post("/courses/<course_id>/attendance")
@role_required("faculty")
def submit_attendance(course_id):
    faculty_id = get_jwt_identity()
    if not _verify_owns_course(course_id, faculty_id):
        return jsonify({"error": "Not your course"}), 403

    data = request.get_json(force=True) or {}
    records = data.get("records", [])
    today = date.today()

    if not records:
        return jsonify({"error": "No attendance records provided"}), 400

    # Ensure attendance is only marked for students confirmed in this course
    enrolled_student_ids = {
        r.student_id for r in Registration.query.filter_by(course_id=course_id, status="registered").all()
    }

    # Validate all statuses and enrolled students before making changes
    for r in records:
        status_val = (r.get("status") or "").strip().lower()
        if status_val not in ALLOWED_ATTENDANCE_STATUSES:
            return jsonify({
                "error": f"Invalid attendance status '{r.get('status')}'. "
                         f"Allowed values are: {sorted(ALLOWED_ATTENDANCE_STATUSES)}"
            }), 400

        student_id = r.get("student_id")
        if student_id not in enrolled_student_ids:
            return jsonify({
                "error": f"Student '{student_id}' is not enrolled in this course."
            }), 400

    for r in records:
        status_val = r["status"].strip().lower()
        existing = Attendance.query.filter_by(
            student_id=r["student_id"], course_id=course_id, class_date=today
        ).first()
        if existing:
            existing.status = status_val
        else:
            db.session.add(Attendance(
                student_id=r["student_id"], course_id=course_id,
                class_date=today, status=status_val, marked_by=faculty_id,
            ))

    db.session.commit()
    return jsonify({"message": f"Attendance saved for {len(records)} students"}), 200


@faculty_bp.post("/marks")
@role_required("faculty")
def upload_marks():
    faculty_id = get_jwt_identity()
    data = request.get_json(force=True) or {}
    course_id, roll_no, assessment, marks_val = (
        data.get("course_id"), data.get("roll_no"), data.get("assessment"), data.get("marks")
    )

    if not _verify_owns_course(course_id, faculty_id):
        return jsonify({"error": "Not your course"}), 403

    student = Student.query.filter_by(roll_no=roll_no).first()
    if not student:
        return jsonify({"error": "No student found with that roll number"}), 404

    existing = Marks.query.filter_by(student_id=student.id, course_id=course_id, assessment=assessment).first()
    if existing:
        existing.marks = marks_val
    else:
        db.session.add(Marks(student_id=student.id, course_id=course_id,
                              assessment=assessment, marks=marks_val))

    db.session.commit()
    return jsonify({"message": f"Marks saved for {roll_no}"}), 200


@faculty_bp.post("/results")
@role_required("faculty")
def upload_result():
    faculty_id = get_jwt_identity()
    data = request.get_json(force=True) or {}
    course_id, roll_no = data.get("course_id"), data.get("roll_no")

    if not _verify_owns_course(course_id, faculty_id):
        return jsonify({"error": "Not your course"}), 403

    student = Student.query.filter_by(roll_no=roll_no).first()
    if not student:
        return jsonify({"error": "No student found with that roll number"}), 404

    existing = Result.query.filter_by(student_id=student.id, course_id=course_id).first()
    if existing:
        existing.internal = data.get("internal")
        existing.external = data.get("external")
        existing.grade = data.get("grade")
        existing.published = True
    else:
        db.session.add(Result(
            student_id=student.id, course_id=course_id,
            internal=data.get("internal"), external=data.get("external"),
            grade=data.get("grade"), published=True,
        ))

    db.session.commit()
    return jsonify({"message": f"Result published for {roll_no}"}), 200
