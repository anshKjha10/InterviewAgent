import json
from flask import Blueprint, request, jsonify, Response, stream_with_context
from services.db import (
    get_resume, get_latest_resume, create_session, get_session,
    insert_question, insert_answer, get_session_history
)
from services.llm import chat_complete, chat_stream, load_prompt

interview_bp = Blueprint("interview", __name__)

INTERVIEW_PROMPT_MAP = {
    "hr": "hr_interviewer",
    "technical": "tech_interviewer",
    "coding": "coding_interviewer",
}


@interview_bp.route("/api/mock-interview/start", methods=["POST"])
def start_interview():
    data = request.get_json()
    interview_type = data.get("interview_type", "hr")
    resume_id = data.get("resume_id")

    if resume_id:
        resume = get_resume(int(resume_id))
    else:
        resume = get_latest_resume()

    if not resume:
        return jsonify({"error": "No resume found. Please upload a resume first."}), 404

    if interview_type not in INTERVIEW_PROMPT_MAP:
        return jsonify({"error": f"Unknown interview type: {interview_type}"}), 400

    session_id = create_session(resume["id"], interview_type)

    prompt_name = INTERVIEW_PROMPT_MAP[interview_type]
    system_prompt = load_prompt(prompt_name)

    user_msg = (
        f"Resume context:\n{resume['parsed_text'][:3000]}\n\n"
        "The interview is starting now. Please introduce yourself briefly and ask your first question."
    )
    first_question = chat_complete(system_prompt, user_msg)

    q_id = insert_question(session_id, first_question, 0)

    return jsonify({
        "session_id": session_id,
        "interview_type": interview_type,
        "question_id": q_id,
        "question": first_question,
        "q_index": 0
    })


@interview_bp.route("/api/mock-interview/answer", methods=["POST"])
def answer_question():
    """
    Accepts the candidate's answer, evaluates it, then streams the next question.
    Uses Server-Sent Events (SSE) for streaming.
    """
    data = request.get_json()
    session_id = data.get("session_id")
    question_id = data.get("question_id")
    answer_text = data.get("answer")
    q_index = data.get("q_index", 0)

    if not all([session_id, question_id, answer_text]):
        return jsonify({"error": "Missing session_id, question_id, or answer"}), 400

    session = get_session(int(session_id))
    if not session:
        return jsonify({"error": "Session not found"}), 404

    # Evaluate the answer first (non-streaming)
    eval_prompt = load_prompt("evaluator")
    history = get_session_history(int(session_id))
    question_text = next(
        (h["question"] for h in history if h.get("q_index") == q_index), "Previous question"
    )
    eval_input = f"Question: {question_text}\n\nCandidate's Answer: {answer_text}"
    eval_raw = chat_complete(eval_prompt, eval_input)

    try:
        evaluation = json.loads(eval_raw)
    except json.JSONDecodeError:
        cleaned = eval_raw.strip().strip("```json").strip("```").strip()
        try:
            evaluation = json.loads(cleaned)
        except Exception:
            evaluation = {"score": 5, "summary": eval_raw, "strengths": [], "improvements": []}

    score = evaluation.get("score", 5)
    feedback_text = json.dumps(evaluation)
    insert_answer(int(question_id), answer_text, feedback_text, score)

    # Now stream the next question
    resume = get_resume(session["resume_id"])
    prompt_name = INTERVIEW_PROMPT_MAP.get(session["interview_type"], "hr_interviewer")
    system_prompt = load_prompt(prompt_name)

    history_text = ""
    for h in get_session_history(int(session_id)):
        history_text += f"Q{h['q_index']+1}: {h['question']}\nA: {h['answer_text'] or '(not answered yet)'}\n\n"

    messages = [
        {
            "role": "user",
            "content": (
                f"Resume context:\n{resume['parsed_text'][:2000]}\n\n"
                f"Interview history so far:\n{history_text}"
                f"The candidate just answered question {q_index+1}. "
                "Please acknowledge their answer briefly and then ask the next question."
            )
        }
    ]

    new_q_index = q_index + 1

    def generate():
        collected = []
        # First send the evaluation as a special SSE event
        yield f"data: [EVAL]{json.dumps(evaluation)}\n\n"

        for chunk in chat_stream(system_prompt, messages):
            collected.append(chunk)
            yield f"data: {chunk}\n\n"

        full_question = "".join(collected)
        # Save the next question to DB
        new_q_id = insert_question(int(session_id), full_question, new_q_index)
        yield f"data: [DONE]{json.dumps({'question_id': new_q_id, 'q_index': new_q_index})}\n\n"

    return Response(
        stream_with_context(generate()),
        mimetype="text/event-stream",
        headers={
            "Cache-Control": "no-cache",
            "X-Accel-Buffering": "no",
        }
    )


@interview_bp.route("/api/history", methods=["GET"])
def get_history():
    session_id = request.args.get("session_id")
    if not session_id:
        return jsonify({"error": "session_id is required"}), 400
    history = get_session_history(int(session_id))
    return jsonify({"session_id": session_id, "history": history})
