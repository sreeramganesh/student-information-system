from flask import Blueprint, request, jsonify
from flask_jwt_extended import get_jwt_identity
from extensions import db
from models import User, Student, Faculty, Course, Registration, Attendance, Result, Fee
from utils.decorators import role_required

admin_bp = Blueprint("admin", __name__, url_prefix="/api/admin")


@admin_bp.get("/me")
@role_required("admin")
def get_my_profile():
    user = User.query.get(get_jwt_identity())
    return jsonify(user.to_dict()), 200


@admin_bp.put("/me")
@role_required("admin")
def update_my_profile():
    data = request.get_json(force=True) or {}
    user = User.query.get(get_jwt_identity())
    if "email" in data:
        user.email = data["email"].strip()
    db.session.commit()
    return jsonify({"message": "Profile updated"}), 200


@admin_bp.get("/stats")
@role_required("admin")
def get_stats():
    students_count = Student.query.count()
    faculty_count = Faculty.query.count()
    courses_count = Course.query.count()

    fees = Fee.query.all()
    outstanding = sum(float(f.amount) for f in fees if f.status != "paid")
    overdue_count = sum(1 for f in fees if f.status == "overdue")

    return jsonify({
        "students_count": students_count, "faculty_count": faculty_count,
        "courses_count": courses_count, "fees_outstanding": outstanding,
        "overdue_count": overdue_count,
    }), 200


@admin_bp.get("/students")
@role_required("admin")
def list_students():
    students = Student.query.all()
    return jsonify([{
        "roll_no": s.roll_no, "full_name": s.user.full_name,
        "department": s.department, "semester": s.semester,
    } for s in students]), 200


@admin_bp.get("/faculty")
@role_required("admin")
def list_faculty():
    faculty = Faculty.query.all()
    return jsonify([{
        "faculty_code": f.faculty_code, "full_name": f.user.full_name,
        "department": f.department, "course_count": len(f.courses),
        "id": f.id,
    } for f in faculty]), 200


@admin_bp.get("/courses")
@role_required("admin")
def list_courses():
    courses = Course.query.all()
    return jsonify([{
        "id": c.id, "name": c.name, "department": c.department,
        "faculty_name": c.faculty.user.full_name if c.faculty else None,
        "seats_filled": c.seats_filled, "capacity": c.capacity,
    } for c in courses]), 200


@admin_bp.post("/courses")
@role_required("admin")
def add_course():
    data = request.get_json(force=True) or {}
    name = (data.get("name") or "").strip()
    if not name:
        return jsonify({"error": "Course name is required"}), 400

    course = Course(
        name=name, department=data.get("department"),
        faculty_id=data.get("faculty_id") or None,
        capacity=data.get("capacity") or 60,
    )
    db.session.add(course)
    db.session.commit()
    return jsonify({"message": "Course added", "id": course.id}), 201


@admin_bp.get("/fees")
@role_required("admin")
def list_fees():
    fees = Fee.query.all()
    return jsonify([{
        "description": f.description, "amount": float(f.amount),
        "fee_date": f.fee_date.isoformat() if f.fee_date else None,
        "status": f.status,
    } for f in fees]), 200


@admin_bp.get("/reports")
@role_required("admin")
def get_reports():
    att = Attendance.query.all()
    avg_attendance = round((sum(1 for a in att if a.status == "present") / len(att)) * 100) if att else None

    by_student = {}
    for a in att:
        by_student.setdefault(a.student_id, {"held": 0, "present": 0})
        by_student[a.student_id]["held"] += 1
        if a.status == "present":
            by_student[a.student_id]["present"] += 1
    below_75 = sum(1 for v in by_student.values() if (v["present"] / v["held"]) * 100 < 75)

    total_courses = Course.query.count()
    published_course_ids = {r.course_id for r in Result.query.filter_by(published=True).all()}

    return jsonify({
        "avg_attendance": avg_attendance, "below_75_count": below_75,
        "results_published": len(published_course_ids), "total_courses": total_courses,
    }), 200
