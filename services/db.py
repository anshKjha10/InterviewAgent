import sqlite3
from config import DB_PATH


def get_conn():
    conn = sqlite3.connect(DB_PATH)
    conn.row_factory = sqlite3.Row
    return conn


def init_db():
    conn = get_conn()
    c = conn.cursor()
    c.executescript("""
        CREATE TABLE IF NOT EXISTS resumes (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            filename TEXT NOT NULL,
            parsed_text TEXT NOT NULL,
            analysis_json TEXT,
            created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
        );

        CREATE TABLE IF NOT EXISTS resumes_v2_migration (done INTEGER);

        CREATE TABLE IF NOT EXISTS sessions (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            resume_id INTEGER,
            interview_type TEXT NOT NULL,
            created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
            FOREIGN KEY (resume_id) REFERENCES resumes(id)
        );

        CREATE TABLE IF NOT EXISTS questions (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            session_id INTEGER NOT NULL,
            question TEXT NOT NULL,
            q_index INTEGER NOT NULL,
            FOREIGN KEY (session_id) REFERENCES sessions(id)
        );

        CREATE TABLE IF NOT EXISTS answers (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            question_id INTEGER NOT NULL,
            answer_text TEXT NOT NULL,
            feedback TEXT,
            score INTEGER,
            FOREIGN KEY (question_id) REFERENCES questions(id)
        );
    """)
    conn.commit()
    conn.close()
    try:
        conn2 = get_conn()
        conn2.execute("ALTER TABLE resumes ADD COLUMN analysis_json TEXT")
        conn2.commit()
        conn2.close()
    except Exception:
        pass


def save_analysis_cache(resume_id: int, analysis_json: str):
    conn = get_conn()
    conn.execute(
        "UPDATE resumes SET analysis_json = ? WHERE id = ?",
        (analysis_json, resume_id)
    )
    conn.commit()
    conn.close()


def get_analysis_cache(resume_id: int):
    conn = get_conn()
    row = conn.execute(
        "SELECT analysis_json FROM resumes WHERE id = ?", (resume_id,)
    ).fetchone()
    conn.close()
    if row and row["analysis_json"]:
        return row["analysis_json"]
    return None


def insert_resume(filename, parsed_text):
    conn = get_conn()
    c = conn.cursor()
    c.execute(
        "INSERT INTO resumes (filename, parsed_text) VALUES (?, ?)",
        (filename, parsed_text)
    )
    conn.commit()
    resume_id = c.lastrowid
    conn.close()
    return resume_id


def get_resume(resume_id):
    conn = get_conn()
    row = conn.execute("SELECT * FROM resumes WHERE id = ?", (resume_id,)).fetchone()
    conn.close()
    return dict(row) if row else None


def get_latest_resume():
    conn = get_conn()
    row = conn.execute("SELECT * FROM resumes ORDER BY created_at DESC LIMIT 1").fetchone()
    conn.close()
    return dict(row) if row else None


def create_session(resume_id, interview_type):
    conn = get_conn()
    c = conn.cursor()
    c.execute(
        "INSERT INTO sessions (resume_id, interview_type) VALUES (?, ?)",
        (resume_id, interview_type)
    )
    conn.commit()
    session_id = c.lastrowid
    conn.close()
    return session_id


def get_session(session_id):
    conn = get_conn()
    row = conn.execute("SELECT * FROM sessions WHERE id = ?", (session_id,)).fetchone()
    conn.close()
    return dict(row) if row else None


def insert_question(session_id, question, q_index):
    conn = get_conn()
    c = conn.cursor()
    c.execute(
        "INSERT INTO questions (session_id, question, q_index) VALUES (?, ?, ?)",
        (session_id, question, q_index)
    )
    conn.commit()
    qid = c.lastrowid
    conn.close()
    return qid


def insert_answer(question_id, answer_text, feedback, score):
    conn = get_conn()
    c = conn.cursor()
    c.execute(
        "INSERT INTO answers (question_id, answer_text, feedback, score) VALUES (?, ?, ?, ?)",
        (question_id, answer_text, feedback, score)
    )
    conn.commit()
    conn.close()


def get_session_history(session_id):
    conn = get_conn()
    rows = conn.execute("""
        SELECT q.question, q.q_index, a.answer_text, a.feedback, a.score
        FROM questions q
        LEFT JOIN answers a ON a.question_id = q.id
        WHERE q.session_id = ?
        ORDER BY q.q_index
    """, (session_id,)).fetchall()
    conn.close()
    return [dict(r) for r in rows]


def get_all_sessions():
    conn = get_conn()
    rows = conn.execute("""
        SELECT s.*, r.filename, COUNT(q.id) as q_count
        FROM sessions s
        LEFT JOIN resumes r ON r.id = s.resume_id
        LEFT JOIN questions q ON q.session_id = s.id
        GROUP BY s.id
        ORDER BY s.created_at DESC
    """).fetchall()
    conn.close()
    return [dict(r) for r in rows]
