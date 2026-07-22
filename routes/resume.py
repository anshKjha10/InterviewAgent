import os
import json
from flask import Blueprint, request, jsonify
from werkzeug.utils import secure_filename
from config import UPLOAD_FOLDER, ALLOWED_EXTENSIONS
from services.pdf_parser import extract_text_from_pdf
from services.db import insert_resume, get_resume, get_latest_resume
from services.llm import chat_complete, load_prompt

resume_bp = Blueprint("resume", __name__)

os.makedirs(UPLOAD_FOLDER, exist_ok=True)


def allowed_file(filename):
    return "." in filename and filename.rsplit(".", 1)[1].lower() in ALLOWED_EXTENSIONS


@resume_bp.route("/api/upload-resume", methods=["POST"])
def upload_resume():
    if "file" not in request.files:
        return jsonify({"error": "No file part"}), 400
    file = request.files["file"]
    if file.filename == "":
        return jsonify({"error": "No file selected"}), 400
    if not allowed_file(file.filename):
        return jsonify({"error": "Only PDF files are allowed"}), 400

    filename = secure_filename(file.filename)
    filepath = os.path.join(UPLOAD_FOLDER, filename)
    file.save(filepath)

    parsed_text = extract_text_from_pdf(filepath)
    if not parsed_text.strip():
        return jsonify({"error": "Could not extract text from PDF"}), 400

    resume_id = insert_resume(filename, parsed_text)
    return jsonify({"resume_id": resume_id, "filename": filename, "message": "Resume uploaded successfully"})


@resume_bp.route("/api/resume-summary", methods=["GET"])
def resume_summary():
    resume_id = request.args.get("resume_id")
    if resume_id:
        resume = get_resume(int(resume_id))
    else:
        resume = get_latest_resume()

    if not resume:
        return jsonify({"error": "No resume found"}), 404

    system_prompt = load_prompt("resume_analyzer")
    raw = chat_complete(system_prompt, f"Analyze this resume:\n\n{resume['parsed_text']}")

    try:
        analysis = json.loads(raw)
    except json.JSONDecodeError:
        # Attempt to strip code fences if present
        cleaned = raw.strip().strip("```json").strip("```").strip()
        try:
            analysis = json.loads(cleaned)
        except Exception:
            analysis = {"raw": raw}

    return jsonify({
        "resume_id": resume["id"],
        "filename": resume["filename"],
        "analysis": analysis
    })
