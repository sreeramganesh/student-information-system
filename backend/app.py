import os
# pyrefly: ignore [missing-import]
from flask import Flask, send_from_directory
from flask_cors import CORS
from config import Config
from extensions import db, migrate, jwt, bcrypt

BASE_DIR = os.path.dirname(os.path.abspath(__file__))
FRONTEND_DIR = os.path.abspath(os.path.join(BASE_DIR, "..", "frontend"))


def create_app():
    app = Flask(__name__)
    app.config.from_object(Config)

    db.init_app(app)
    migrate.init_app(app, db)
    jwt.init_app(app)
    bcrypt.init_app(app)
    CORS(app, resources={r"/api/*": {"origins": app.config["CORS_ORIGINS"]}})

    from routes.auth import auth_bp
    from routes.students import students_bp
    from routes.faculty import faculty_bp
    from routes.admin import admin_bp
    from routes.alumni import alumni_bp

    app.register_blueprint(auth_bp)
    app.register_blueprint(students_bp)
    app.register_blueprint(faculty_bp)
    app.register_blueprint(admin_bp)
    app.register_blueprint(alumni_bp)

    @app.get("/api/health")
    def health():
        return {"status": "ok"}, 200

    @app.get("/")
    def index():
        return send_from_directory(FRONTEND_DIR, "login.html")

    @app.get("/<path:filename>")
    def serve_frontend(filename):
        # Handle rewritten path with frontend/ prefix if any
        if filename.startswith("frontend/"):
            filename = filename[len("frontend/"):]

        if not filename or filename in ("login", "index"):
            return send_from_directory(FRONTEND_DIR, "login.html")

        safe_path = os.path.abspath(os.path.join(FRONTEND_DIR, filename))
        if not safe_path.startswith(FRONTEND_DIR):
            return {"error": "Not found"}, 404

        allowed_extensions = {
            ".html", ".css", ".js", ".png", ".jpg", ".jpeg",
            ".svg", ".ico", ".woff", ".woff2", ".ttf"
        }

        ext = os.path.splitext(filename)[1].lower()
        if ext in allowed_extensions and os.path.isfile(safe_path):
            return send_from_directory(FRONTEND_DIR, filename)

        # Support clean URLs like /login, /student, /faculty, /admin, /alumni
        if not ext and os.path.isfile(safe_path + ".html"):
            return send_from_directory(FRONTEND_DIR, filename + ".html")

        return {"error": "Not found"}, 404

    return app


app = create_app()

if __name__ == "__main__":
    app.run(debug=True, host="0.0.0.0", port=5000)

