from flask import Blueprint, request, jsonify
from flask_jwt_extended import get_jwt_identity
from extensions import db
from models import Alumni, User, Fee, TranscriptRequest
from utils.decorators import role_required

alumni_bp = Blueprint("alumni", __name__, url_prefix="/api/alumni")


@alumni_bp.get("/me")
@role_required("alumni")
def get_my_profile():
    alumni_id = get_jwt_identity()
    alumni = Alumni.query.get(alumni_id)
    user = User.query.get(alumni_id)
    if not alumni:
        return jsonify({"error": "Alumni record not found"}), 404
    return jsonify({
        "full_name": user.full_name, "email": user.email, "phone": user.phone,
        "roll_no": alumni.roll_no, "department": alumni.department,
        "batch_year": alumni.batch_year, "current_employer": alumni.current_employer,
    }), 200


@alumni_bp.put("/me")
@role_required("alumni")
def update_my_profile():
    data = request.get_json(force=True) or {}
    alumni_id = get_jwt_identity()
    user = User.query.get(alumni_id)
    alumni = Alumni.query.get(alumni_id)

    if "email" in data:
        user.email = data["email"].strip()
    if "phone" in data:
        user.phone = data["phone"].strip()
    if "current_employer" in data:
        alumni.current_employer = data["current_employer"].strip()

    db.session.commit()
    return jsonify({"message": "Profile updated"}), 200


@alumni_bp.get("/me/fees")
@role_required("alumni")
def get_my_fees():
    alumni_id = get_jwt_identity()
    fees = Fee.query.filter_by(student_id=alumni_id).order_by(Fee.fee_date.desc()).all()
    total = sum(float(f.amount) for f in fees)
    paid = sum(float(f.amount) for f in fees if f.status == "paid")
    return jsonify({
        "total": total, "paid": paid, "due": total - paid,
        "records": [{
            "description": f.description, "amount": float(f.amount),
            "fee_date": f.fee_date.isoformat() if f.fee_date else None,
            "status": f.status,
        } for f in fees],
    }), 200


@alumni_bp.get("/me/transcript-requests")
@role_required("alumni")
def list_my_transcripts():
    alumni_id = get_jwt_identity()
    reqs = TranscriptRequest.query.filter_by(student_id=alumni_id).order_by(
        TranscriptRequest.requested_at.desc()
    ).all()
    return jsonify([{
        "purpose": r.purpose, "status": r.status,
        "requested_at": r.requested_at.isoformat() if r.requested_at else None,
    } for r in reqs]), 200


@alumni_bp.post("/me/transcript-requests")
@role_required("alumni")
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
