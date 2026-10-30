"""SQLite storage for documents, generated questions and practice attempts."""
import sqlite3
from contextlib import contextmanager
from pathlib import Path

DB_PATH = Path(__file__).parent / "viva.db"

SCHEMA = """
CREATE TABLE IF NOT EXISTS documents (
    id INTEGER PRIMARY KEY AUTOINCREMENT, title TEXT, text TEXT NOT NULL,
    words INTEGER, sentences INTEGER, created_at TEXT DEFAULT CURRENT_TIMESTAMP);
CREATE TABLE IF NOT EXISTS questions (
    id INTEGER PRIMARY KEY AUTOINCREMENT, doc_id INTEGER NOT NULL, difficulty TEXT, qtype TEXT, topic TEXT,
    question TEXT, answer TEXT, source TEXT, method TEXT, created_at TEXT DEFAULT CURRENT_TIMESTAMP,
    FOREIGN KEY (doc_id) REFERENCES documents(id));
CREATE TABLE IF NOT EXISTS attempts (
    id INTEGER PRIMARY KEY AUTOINCREMENT, session_id TEXT, question_id INTEGER, doc_id INTEGER,
    difficulty TEXT, topic TEXT, student_answer TEXT, score REAL, similarity REAL, coverage REAL,
    status TEXT, feedback TEXT, found TEXT, missing TEXT, created_at TEXT DEFAULT CURRENT_TIMESTAMP,
    FOREIGN KEY (question_id) REFERENCES questions(id));
"""


@contextmanager
def connect(path=None):
    conn = sqlite3.connect(str(path or DB_PATH))
    conn.row_factory = sqlite3.Row
    conn.execute("PRAGMA foreign_keys = ON")
    try:
        yield conn
        conn.commit()
    finally:
        conn.close()


def init_db(path=None):
    with connect(path) as c:
        c.executescript(SCHEMA)


def add_document(title, text, words, sentences, path=None):
    with connect(path) as c:
        return c.execute("INSERT INTO documents (title,text,words,sentences) VALUES (?,?,?,?)",
                         (title, text, words, sentences)).lastrowid


def get_document(doc_id, path=None):
    with connect(path) as c:
        r = c.execute("SELECT * FROM documents WHERE id=?", (doc_id,)).fetchone()
        return dict(r) if r else None


def list_documents(path=None):
    with connect(path) as c:
        return [dict(r) for r in c.execute("SELECT id,title,words,sentences,created_at FROM documents ORDER BY id DESC")]


def add_questions(doc_id, questions, path=None):
    ids = []
    with connect(path) as c:
        for q in questions:
            cur = c.execute("INSERT INTO questions (doc_id,difficulty,qtype,topic,question,answer,source,method) VALUES (?,?,?,?,?,?,?,?)",
                            (doc_id, q["difficulty"], q["qtype"], q["topic"], q["question"], q["answer"], q["source"], q["method"]))
            ids.append(cur.lastrowid)
    return ids


def get_questions(ids=None, doc_id=None, path=None):
    with connect(path) as c:
        if ids:
            marks = ",".join("?" * len(ids))
            rows = c.execute(f"SELECT * FROM questions WHERE id IN ({marks})", ids).fetchall()
            order = {i: n for n, i in enumerate(ids)}
            return sorted([dict(r) for r in rows], key=lambda r: order[r["id"]])
        if doc_id:
            return [dict(r) for r in c.execute("SELECT * FROM questions WHERE doc_id=? ORDER BY id", (doc_id,))]
        return []


def get_question(qid, path=None):
    with connect(path) as c:
        r = c.execute("SELECT * FROM questions WHERE id=?", (qid,)).fetchone()
        return dict(r) if r else None


def add_attempt(session_id, q, student_answer, result, path=None):
    with connect(path) as c:
        c.execute("""INSERT INTO attempts (session_id,question_id,doc_id,difficulty,topic,student_answer,score,similarity,
                     coverage,status,feedback,found,missing) VALUES (?,?,?,?,?,?,?,?,?,?,?,?,?)""",
                  (session_id, q["id"], q["doc_id"], q["difficulty"], q["topic"], student_answer, result["score"],
                   result["similarity"], result["coverage"], result["status"], result["feedback"],
                   ", ".join(result["found"]), ", ".join(result["missing"])))


def session_attempts(session_id, path=None):
    with connect(path) as c:
        return [dict(r) for r in c.execute(
            """SELECT a.*, q.question, q.answer AS reference FROM attempts a JOIN questions q ON q.id=a.question_id
               WHERE a.session_id=? ORDER BY a.id""", (session_id,))]


def dashboard_stats(path=None):
    """Compute every dashboard metric from real records."""
    with connect(path) as c:
        total_q = c.execute("SELECT COUNT(*) FROM questions").fetchone()[0]
        att = c.execute("SELECT COUNT(*), AVG(score) FROM attempts WHERE status!='skipped'").fetchone()
        skipped = c.execute("SELECT COUNT(*) FROM attempts WHERE status='skipped'").fetchone()[0]
        by_level = {r["difficulty"]: {"avg": round(r["a"], 2), "n": r["n"]} for r in c.execute(
            "SELECT difficulty, AVG(score) a, COUNT(*) n FROM attempts WHERE status!='skipped' GROUP BY difficulty")}
        by_topic = [{"topic": r["topic"], "avg": round(r["a"], 2), "n": r["n"]} for r in c.execute(
            "SELECT topic, AVG(score) a, COUNT(*) n FROM attempts WHERE status!='skipped' GROUP BY topic ORDER BY a")]
        status = {r["status"]: r["n"] for r in c.execute(
            "SELECT status, COUNT(*) n FROM attempts WHERE status!='skipped' GROUP BY status")}
        recent = [dict(r) for r in c.execute(
            "SELECT created_at, score, difficulty FROM attempts WHERE status!='skipped' ORDER BY id DESC LIMIT 20")][::-1]
    revision = [t for t in by_topic if t["avg"] < 5][:6]
    return {"total_questions": total_q, "attempted": att[0], "skipped": skipped,
            "average_score": round(att[1], 2) if att[1] is not None else None,
            "by_level": by_level, "by_topic": by_topic,
            "status": {"correct": status.get("correct", 0), "partial": status.get("partial", 0), "weak": status.get("weak", 0)},
            "revision": revision, "recent": recent}
