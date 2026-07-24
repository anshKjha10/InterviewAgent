import json
from flask import Blueprint, request, jsonify
from services.db import get_latest_resume, get_resume, get_session_history
from services.llm import chat_complete, load_prompt

roadmap_bp = Blueprint("roadmap", __name__)


def get_user_token():
    return request.headers.get("X-User-Token") or request.args.get("user_token")


@roadmap_bp.route("/api/roadmap", methods=["GET"])
def get_roadmap():
    resume_id = request.args.get("resume_id")
    session_id = request.args.get("session_id")
    user_token = get_user_token()

    resume = None
    if resume_id:
        resume = get_resume(int(resume_id), user_token=user_token)
    if not resume:
        resume = get_latest_resume(user_token=user_token)

    resume_text = resume["parsed_text"][:2000] if resume else "No resume provided. Generate a general software engineering study roadmap covering data structures, algorithms, system design, and behavioral interview prep."

    feedback_summary = ""
    if session_id:
        history = get_session_history(int(session_id))
        for h in history:
            if h.get("feedback"):
                try:
                    fb = json.loads(h["feedback"])
                    feedback_summary += f"Q: {h['question']}\nScore: {fb.get('score')}/10\nImprovements: {fb.get('improvements', [])}\n\n"
                except Exception:
                    pass

    system_prompt = load_prompt("roadmap_planner")
    user_msg = (
        f"Resume:\n{resume_text}\n\n"
        f"Interview Feedback:\n{feedback_summary or 'No interview feedback yet. Generate a general roadmap based on resume skills.'}"
    )

    raw = chat_complete(system_prompt, user_msg)

    try:
        roadmap = json.loads(raw)
    except json.JSONDecodeError:
        cleaned = raw.strip().strip("```json").strip("```").strip()
        try:
            roadmap = json.loads(cleaned)
        except Exception:
            roadmap = {"raw": raw}

    return jsonify({"resume_id": resume["id"] if resume else None, "roadmap": roadmap})
