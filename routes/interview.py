import json
from flask import Blueprint, request, jsonify, Response, stream_with_context
from services.db import (
    get_resume, get_latest_resume, create_session, get_session,
    insert_question, insert_answer, get_session_history, get_analysis_cache
)
from services.llm import chat_complete, chat_stream, load_prompt

interview_bp = Blueprint("interview", __name__)

TOTAL_QUESTIONS = 5

INTERVIEW_PROMPT_MAP = {
    "hr": "hr_interviewer",
    "technical": "tech_interviewer",
    "coding": "coding_interviewer",
}


def build_resume_context(resume):
    if not resume:
        return "No resume provided. Ask questions based on a general software engineering candidate background."

    cached_analysis = get_analysis_cache(resume["id"])
    analysis_str = ""
    if cached_analysis:
        try:
            a = json.loads(cached_analysis)
            analysis_str = (
                f"\nRESUME SUMMARY:\n"
                f"- Name: {a.get('name', 'Candidate')}\n"
                f"- Years Exp: {a.get('experience_years', 'N/A')}\n"
                f"- Skills: {', '.join(a.get('skills', []))}\n"
                f"- Job Titles / Roles: {', '.join(a.get('job_titles', []))}\n"
                f"- Education: {a.get('education', 'N/A')}\n"
                f"- Key Strengths: {', '.join(a.get('strengths', []))}\n"
            )
        except Exception:
            pass

    return f"FULL RESUME TEXT:\n{resume['parsed_text'][:4000]}\n{analysis_str}"


@interview_bp.route("/api/mock-interview/start", methods=["POST"])
def start_interview():
    data = request.get_json()
    interview_type = data.get("interview_type", "hr")
    resume_id = data.get("resume_id")

    resume = None
    if resume_id:
        resume = get_resume(int(resume_id))
    if not resume:
        resume = get_latest_resume()

    resume_text = build_resume_context(resume)
    resume_db_id = resume["id"] if resume else None

    if interview_type not in INTERVIEW_PROMPT_MAP:
        return jsonify({"error": f"Unknown interview type: {interview_type}"}), 400

    try:
        session_id = create_session(resume_db_id, interview_type)
        prompt_name = INTERVIEW_PROMPT_MAP[interview_type]
        system_prompt = load_prompt(prompt_name)

        user_msg = (
            f"{resume_text}\n\n"
            f"The interview is starting now (Question 1 of {TOTAL_QUESTIONS}).\n"
            "MANDATORY: Introduce yourself briefly (1 sentence) and ask your FIRST question. "
            "Your question MUST explicitly reference a specific project, internship, or technical skill mentioned in the candidate's resume above."
        )
        first_question = chat_complete(system_prompt, user_msg)
        q_id = insert_question(session_id, first_question, 0)

        return jsonify({
            "session_id": session_id,
            "interview_type": interview_type,
            "question_id": q_id,
            "question": first_question,
            "q_index": 0,
            "total_questions": TOTAL_QUESTIONS
        })
    except Exception as e:
        return jsonify({"error": str(e)}), 400


@interview_bp.route("/api/mock-interview/answer", methods=["POST"])
def answer_question():
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

    resume = get_resume(session["resume_id"]) if session.get("resume_id") else None
    resume_text = build_resume_context(resume)
    prompt_name = INTERVIEW_PROMPT_MAP.get(session["interview_type"], "hr_interviewer")
    system_prompt = load_prompt(prompt_name)

    history_text = ""
    for h in get_session_history(int(session_id)):
        history_text += f"Q{h['q_index']+1}: {h['question']}\nA: {h['answer_text'] or '(not answered yet)'}\n\n"

    new_q_index = q_index + 1
    is_last_question = new_q_index >= TOTAL_QUESTIONS

    if is_last_question:
        prompt_instruction = (
            f"The candidate has just answered Question {q_index+1} of {TOTAL_QUESTIONS} (the final question!). "
            "Please briefly acknowledge their last response, congratulate them on finishing all 5 questions of the interview, "
            "and invite them to view their overall feedback and study roadmap."
        )
    else:
        prompt_instruction = (
            f"The candidate just answered Question {q_index+1} of {TOTAL_QUESTIONS}.\n"
            f"MANDATORY: Briefly acknowledge their answer (1 sentence). Then ask Question {new_q_index+1} of {TOTAL_QUESTIONS}.\n"
            f"Question {new_q_index+1} MUST explicitly target a DIFFERENT project, internship, technical accomplishment, or experience listed on their resume that hasn't been discussed yet."
        )

    messages = [
        {
            "role": "user",
            "content": (
                f"{resume_text}\n\n"
                f"INTERVIEW HISTORY SO FAR:\n{history_text}\n"
                f"{prompt_instruction}"
            )
        }
    ]

    def generate():
        collected = []
        yield f"data: [EVAL]{json.dumps(evaluation)}\n\n"

        for chunk in chat_stream(system_prompt, messages):
            collected.append(chunk)
            yield f"data: {chunk}\n\n"

        full_text = "".join(collected)
        if not is_last_question:
            new_q_id = insert_question(int(session_id), full_text, new_q_index)
            yield f"data: [DONE]{json.dumps({'question_id': new_q_id, 'q_index': new_q_index, 'total_questions': TOTAL_QUESTIONS})}\n\n"
        else:
            yield f"data: [FINISHED]{json.dumps({'session_id': session_id, 'q_index': TOTAL_QUESTIONS, 'total_questions': TOTAL_QUESTIONS})}\n\n"

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
