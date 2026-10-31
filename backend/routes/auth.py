from flask import Blueprint, request, jsonify
from flask_jwt_extended import create_access_token, jwt_required, get_jwt_identity
from extensions import db, bcrypt
from models import User, Student, Faculty, Alumni

auth_bp = Blueprint("auth", __name__, url_prefix="/api/auth")

ALLOWED_ROLES = {"student", "faculty", "admin", "alumni"}


@auth_bp.post("/signup")
def signup():
    data = request.get_json(force=True) or {}
    full_name = (data.get("full_name") or "").strip()
    email = (data.get("email") or "").strip().lower()
    username = (data.get("username") or "").strip()
    password = data.get("password") or ""
    role = data.get("role")

    if not all([full_name, email, username, password, role]):
        return jsonify({"error": "full_name, email, username, password, and role are all required"}), 400
    if role not in ALLOWED_ROLES:
        return jsonify({"error": f"role must be one of {sorted(ALLOWED_ROLES)}"}), 400
    if len(password) < 8:
        return jsonify({"error": "Password must be at least 8 characters"}), 400

    if User.query.filter((User.email == email) | (User.username == username)).first():
        return jsonify({"error": "An account with that email or username already exists"}), 409

    user = User(
        full_name=full_name, email=email, username=username,
        password_hash=bcrypt.generate_password_hash(password).decode("utf-8"),
        role=role,
    )
    db.session.add(user)
    db.session.flush()

    if role == "student":
        db.session.add(Student(id=user.id, roll_no=username))
    elif role == "faculty":
        db.session.add(Faculty(id=user.id, faculty_code=username))
    elif role == "alumni":
        db.session.add(Alumni(id=user.id, roll_no=username))

    db.session.commit()

    token = create_access_token(identity=user.id, additional_claims={"role": user.role})
    return jsonify({"token": token, "user": user.to_dict()}), 201


@auth_bp.post("/login")
def login():
    data = request.get_json(force=True) or {}
    identifier = (data.get("username") or data.get("email") or "").strip()
    password = data.get("password") or ""

    if not identifier or not password:
        return jsonify({"error": "username/email and password are required"}), 400

    user = User.query.filter((User.username == identifier) | (User.email == identifier.lower())).first()

    if not user or not bcrypt.check_password_hash(user.password_hash, password):
        return jsonify({"error": "Invalid login credentials"}), 401

    token = create_access_token(identity=user.id, additional_claims={"role": user.role})
    return jsonify({"token": token, "user": user.to_dict()}), 200


@auth_bp.get("/me")
@jwt_required()
def me():
    user = User.query.get(get_jwt_identity())
    if not user:
        return jsonify({"error": "User not found"}), 404
    return jsonify(user.to_dict()), 200
