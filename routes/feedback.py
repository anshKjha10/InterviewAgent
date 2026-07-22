import json
from flask import Blueprint, request, jsonify
from services.db import get_session_history, get_all_sessions

feedback_bp = Blueprint("feedback", __name__)


@feedback_bp.route("/api/feedback", methods=["GET"])
def get_feedback():
    session_id = request.args.get("session_id")
    if not session_id:
        return jsonify({"error": "session_id is required"}), 400

    history = get_session_history(int(session_id))
    if not history:
        return jsonify({"error": "No history found for this session"}), 404

    answered = [h for h in history if h.get("answer_text")]
    total_score = 0
    count = 0
    detailed = []

    for h in answered:
        fb_raw = h.get("feedback")
        try:
            fb = json.loads(fb_raw) if fb_raw else {}
        except Exception:
            fb = {}
        score = h.get("score") or fb.get("score", 0)
        total_score += score
        count += 1
        detailed.append({
            "question": h["question"],
            "answer": h["answer_text"],
            "score": score,
            "feedback": fb
        })

    avg_score = round(total_score / count, 1) if count else 0

    return jsonify({
        "session_id": session_id,
        "total_questions": len(history),
        "answered": count,
        "average_score": avg_score,
        "details": detailed
    })


@feedback_bp.route("/api/sessions", methods=["GET"])
def list_sessions():
    sessions = get_all_sessions()
    return jsonify({"sessions": sessions})
