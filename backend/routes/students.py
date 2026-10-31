from datetime import datetime
from flask import Blueprint, request, jsonify
from flask_jwt_extended import get_jwt_identity
from extensions import db
from models import (Student, Course, Registration, Attendance, Result, Fee,
                     User, AdmissionDetail, HscSubjectMark, TranscriptRequest)
from utils.decorators import role_required

students_bp = Blueprint("students", __name__, url_prefix="/api/students")


@students_bp.get("/me")
@role_required("student")
def get_my_profile():
    student = Student.query.get(get_jwt_identity())
    user = User.query.get(get_jwt_identity())
    if not student:
        return jsonify({"error": "Student record not found"}), 404
    return jsonify({
        "full_name": user.full_name, "email": user.email, "phone": user.phone,
        "roll_no": student.roll_no, "department": student.department,
        "semester": student.semester, "cgpa": float(student.cgpa) if student.cgpa else None,
        "address": student.address, "profile_completed": student.profile_completed,
    }), 200


@students_bp.put("/me")
@role_required("student")
def update_my_profile():
    data = request.get_json(force=True) or {}
    student_id = get_jwt_identity()
    user = User.query.get(student_id)
    student = Student.query.get(student_id)

    if "email" in data:
        user.email = data["email"].strip()
    if "phone" in data:
        user.phone = data["phone"].strip()
    if "address" in data:
        student.address = data["address"].strip()

    db.session.commit()
    return jsonify({"message": "Profile updated"}), 200


@students_bp.get("/me/courses")
@role_required("student")
def get_my_courses():
    student_id = get_jwt_identity()
    courses = Course.query.all()
    my_regs = {r.course_id: r for r in Registration.query.filter_by(student_id=student_id).all()}

    result = []
    for c in courses:
        reg = my_regs.get(c.id)
        result.append({
            "id": c.id, "name": c.name,
            "faculty_code": c.faculty.faculty_code if c.faculty else None,
            "seats_filled": c.seats_filled, "capacity": c.capacity,
            "status": reg.status if reg else "not_registered",
            "waitlist_position": reg.waitlist_position if reg else None,
        })
    return jsonify(result), 200


@students_bp.post("/me/courses/<course_id>/register")
@role_required("student")
def register_course(course_id):
    """
    Registers a student for a course with row-level locking to prevent race conditions.
    If capacity is available, enrolls the student; otherwise assigns an ordered waitlist position.
    """
    student_id = get_jwt_identity()

    # Lock the course row to prevent race conditions during concurrent registration
    course = Course.query.with_for_update().get(course_id)
    if not course:
        return jsonify({"error": "Course not found"}), 404

    if Registration.query.filter_by(student_id=student_id, course_id=course_id).first():
        return jsonify({"error": "Already registered or waitlisted for this course"}), 409

    confirmed_count = Registration.query.filter_by(course_id=course_id, status="registered").count()

    if confirmed_count < course.capacity:
        reg = Registration(student_id=student_id, course_id=course_id, status="registered", waitlist_position=None)
        course.seats_filled = confirmed_count + 1
        db.session.add(reg)
        db.session.commit()
        return jsonify({
            "status": "registered",
            "waitlist_position": None,
            "message": f"Successfully registered for {course.name}."
        }), 201
    else:
        # Determine highest existing waitlist position
        max_pos = db.session.query(db.func.max(Registration.waitlist_position)).filter_by(
            course_id=course_id, status="waitlisted"
        ).scalar() or 0
        next_pos = max_pos + 1
        reg = Registration(student_id=student_id, course_id=course_id, status="waitlisted", waitlist_position=next_pos)
        db.session.add(reg)
        db.session.commit()
        return jsonify({
            "status": "waitlisted",
            "waitlist_position": next_pos,
            "message": f"Course capacity reached. Placed on waitlist at position #{next_pos}."
        }), 201


@students_bp.route("/me/courses/<course_id>/drop", methods=["POST", "DELETE"])
@role_required("student")
def drop_course(course_id):
    """
    Drops a confirmed registration or cancels a waitlist entry.
    When a confirmed seat is vacated, the earliest waitlisted student is automatically promoted.
    """
    student_id = get_jwt_identity()

    course = Course.query.with_for_update().get(course_id)
    if not course:
        return jsonify({"error": "Course not found"}), 404

    reg = Registration.query.filter_by(student_id=student_id, course_id=course_id).first()
    if not reg:
        return jsonify({"error": "You are not registered or waitlisted for this course"}), 404

    was_registered = (reg.status == "registered")
    was_waitlist_pos = reg.waitlist_position

    db.session.delete(reg)
    db.session.flush()

    promoted_student_id = None

    if was_registered:
        # Find earliest eligible waitlisted student
        next_waitlisted = Registration.query.filter_by(
            course_id=course_id, status="waitlisted"
        ).order_by(
            Registration.waitlist_position.asc(),
            Registration.created_at.asc()
        ).first()

        if next_waitlisted:
            # Promote waitlisted student into the available seat
            next_waitlisted.status = "registered"
            next_waitlisted.waitlist_position = None
            promoted_student_id = next_waitlisted.student_id

            # Re-index remaining waitlisted students
            remaining = Registration.query.filter_by(
                course_id=course_id, status="waitlisted"
            ).order_by(Registration.waitlist_position.asc()).all()
            for idx, r in enumerate(remaining, start=1):
                r.waitlist_position = idx
        else:
            # No waitlist exists; update seat counter
            actual_confirmed = Registration.query.filter_by(course_id=course_id, status="registered").count()
            course.seats_filled = actual_confirmed
    else:
        # Student was waitlisted; decrement positions of students behind them
        if was_waitlist_pos:
            subsequent = Registration.query.filter(
                Registration.course_id == course_id,
                Registration.status == "waitlisted",
                Registration.waitlist_position > was_waitlist_pos
            ).order_by(Registration.waitlist_position.asc()).all()
            for r in subsequent:
                r.waitlist_position -= 1

    db.session.commit()

    return jsonify({
        "message": f"Successfully dropped {course.name}.",
        "promoted_student_id": promoted_student_id,
        "seats_filled": course.seats_filled,
        "capacity": course.capacity
    }), 200


@students_bp.delete("/me/courses/<course_id>")
@role_required("student")
def delete_course_registration(course_id):
    return drop_course(course_id)


@students_bp.get("/me/attendance")
@role_required("student")
def get_my_attendance():
    student_id = get_jwt_identity()
    rows = Attendance.query.filter_by(student_id=student_id).all()

    by_course = {}
    for r in rows:
        name = r.course.name if r.course else "Unknown"
        by_course.setdefault(name, {"held": 0, "attended": 0})
        by_course[name]["held"] += 1
        if r.status == "present":
            by_course[name]["attended"] += 1

    subjects = [{
        "course_name": name, "held": v["held"], "attended": v["attended"],
        "percentage": round((v["attended"] / v["held"]) * 100) if v["held"] else 0,
    } for name, v in by_course.items()]

    total_held = sum(v["held"] for v in by_course.values())
    total_attended = sum(v["attended"] for v in by_course.values())
    overall = round((total_attended / total_held) * 100) if total_held else 0

    return jsonify({"overall_percentage": overall, "subjects": subjects}), 200


@students_bp.get("/me/grades")
@role_required("student")
def get_my_grades():
    student_id = get_jwt_identity()
    results = Result.query.filter_by(student_id=student_id, published=True).all()
    return jsonify([{
        "course_name": r.course.name if r.course else "Unknown",
        "internal": float(r.internal) if r.internal is not None else None,
        "external": float(r.external) if r.external is not None else None,
        "grade": r.grade,
    } for r in results]), 200


@students_bp.get("/me/fees")
@role_required("student")
def get_my_fees():
    student_id = get_jwt_identity()
    fees = Fee.query.filter_by(student_id=student_id).order_by(Fee.fee_date.desc()).all()
    total = sum(float(f.amount) for f in fees)
    paid = sum(float(f.amount) for f in fees if f.status == "paid")
    return jsonify({
        "total": total, "paid": paid, "due": total - paid,
        "records": [{
            "receipt_no": f.receipt_no, "description": f.description,
            "amount": float(f.amount), "status": f.status,
            "fee_date": f.fee_date.isoformat() if f.fee_date else None,
        } for f in fees],
    }), 200


@students_bp.get("/me/admission")
@role_required("student")
def get_my_admission():
    student_id = get_jwt_identity()
    adm = AdmissionDetail.query.filter_by(student_id=student_id).first()
    if not adm:
        return jsonify(None), 200

    marks = HscSubjectMark.query.filter_by(student_id=student_id).all()
    return jsonify({
        "date_of_birth": adm.date_of_birth.isoformat() if adm.date_of_birth else None,
        "gender": adm.gender, "nationality": adm.nationality, "community": adm.community,
        "parent_name": adm.parent_name, "parent_occupation": adm.parent_occupation,
        "parent_annual_income": adm.parent_annual_income,
        "address_line": adm.address_line, "pincode": adm.pincode, "phone": adm.phone,
        "board_of_exam": adm.board_of_exam, "course_opted": adm.course_opted,
        "marks": [{"subject_name": m.subject_name, "max_marks": float(m.max_marks),
                   "marks_obtained": float(m.marks_obtained)} for m in marks],
    }), 200


@students_bp.post("/me/admission")
@role_required("student")
def submit_admission():
    student_id = get_jwt_identity()
    data = request.get_json(force=True) or {}

    if AdmissionDetail.query.filter_by(student_id=student_id).first():
        return jsonify({"error": "Admission record already submitted"}), 409

    dob = data.get("date_of_birth")
    adm = AdmissionDetail(
        student_id=student_id,
        date_of_birth=datetime.strptime(dob, "%Y-%m-%d").date() if dob else None,
        gender=data.get("gender"), nationality=data.get("nationality"),
        community=data.get("community"), parent_name=data.get("parent_name"),
        parent_occupation=data.get("parent_occupation"),
        parent_annual_income=data.get("parent_annual_income"),
        address_line=data.get("address_line"), pincode=data.get("pincode"),
        phone=data.get("phone"), board_of_exam=data.get("board_of_exam"),
        course_opted=data.get("course_opted"),
    )
    db.session.add(adm)

    for m in data.get("marks", []):
        if m.get("subject_name"):
            db.session.add(HscSubjectMark(
                student_id=student_id, subject_name=m["subject_name"],
                max_marks=m["max_marks"], marks_obtained=m["marks_obtained"],
            ))

    student = Student.query.get(student_id)
    student.profile_completed = True
    if data.get("address_line"):
        student.address = data["address_line"]

    db.session.commit()
    return jsonify({"success": True, "message": "Profile saved successfully"}), 201


@students_bp.post("/me/transcript-requests")
@role_required("student")
def request_transcript():
    data = request.get_json(force=True) or {}
    tr = TranscriptRequest(
        student_id=get_jwt_identity(),
        purpose=data.get("purpose"),
        delivery_email=data.get("delivery_email"),
    )
    db.session.add(tr)
    db.session.commit()
    return jsonify({"message": "Transcript request submitted"}), 201
