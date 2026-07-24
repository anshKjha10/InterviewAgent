import os
from flask import Flask, send_from_directory
from flask_cors import CORS
from config import FLASK_SECRET_KEY, FLASK_DEBUG
from services.db import init_db
from routes.resume import resume_bp
from routes.interview import interview_bp
from routes.feedback import feedback_bp
from routes.roadmap import roadmap_bp

app = Flask(__name__, static_folder="static", static_url_path="")
app.secret_key = FLASK_SECRET_KEY
CORS(app)

app.register_blueprint(resume_bp)
app.register_blueprint(interview_bp)
app.register_blueprint(feedback_bp)
app.register_blueprint(roadmap_bp)


@app.route("/")
def index():
    return send_from_directory("static", "index.html")


@app.route("/<path:path>")
def serve_static(path):
    if os.path.exists(os.path.join("static", path)):
        return send_from_directory("static", path)
    return send_from_directory("static", "index.html")


@app.route("/api/health")
def health():
    return {"status": "ok", "message": "AI Interview Prep API is running"}


if __name__ == "__main__":
    init_db()
    port = int(os.getenv("PORT", 5000))
    print("[OK] Database initialized")
    print(f"[START] Starting AI Interview Prep Assistant on http://0.0.0.0:{port}")
    app.run(host="0.0.0.0", port=port, debug=FLASK_DEBUG, threaded=True)
