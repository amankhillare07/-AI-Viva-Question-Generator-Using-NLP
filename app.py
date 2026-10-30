"""Flask application - AI Viva Question Generator Using NLP."""
import os
import uuid

import fitz  # PyMuPDF
from flask import Flask, jsonify, redirect, render_template, request, session, url_for, flash
from werkzeug.utils import secure_filename

import database as db
from nlp import answer_evaluation as ev
from nlp.keyword_extraction import extract_keywords, rank_sentences
from nlp.preprocessing import analyze, clean_text, split_sentences, tokenize
from nlp.question_generation import generate_questions
from nlp.summarization import summarize

app = Flask(__name__)
app.secret_key = os.environ.get("SECRET_KEY", "dev-secret-change-me")
app.config["MAX_CONTENT_LENGTH"] = 10 * 1024 * 1024  # 10 MB upload limit
ALLOWED_EXT = {".pdf", ".txt"}
MIN_WORDS = 30
MAX_CHARS = 300_000

db.init_db()


# ---------------------------------------------------------------- helpers
def extract_pdf_text(data):
    """Extract text from PDF bytes. Raises ValueError with a friendly message on problems."""
    if not data.startswith(b"%PDF"):
        raise ValueError("This file is not a valid PDF (wrong file signature).")
    try:
        doc = fitz.open(stream=data, filetype="pdf")
    except Exception:
        raise ValueError("The PDF is corrupted or could not be opened.")
    if doc.needs_pass:
        raise ValueError("The PDF is password-protected.")
    pages = [p.get_text() for p in doc]
    doc.close()
    text = "\n".join(pages).strip()
    if len(text.split()) < 5:
        raise ValueError("No extractable text found. The PDF may be scanned images (OCR is not supported). "
                         "Try a text-based PDF or paste the notes instead.")
    return text


def text_stats(text):
    toks = [t for t in tokenize(text) if any(c.isalnum() for c in t)]
    return len(toks), len(split_sentences(text))


def current_doc():
    doc_id = session.get("doc_id")
    return db.get_document(doc_id) if doc_id else None


def level_counts(doc_id):
    qs = db.get_questions(doc_id=doc_id)
    return {lv: sum(1 for q in qs if q["difficulty"] == lv) for lv in ("Easy", "Medium", "Difficult")}


# ---------------------------------------------------------------- pages
@app.route("/")
def index():
    return render_template("index.html", doc=current_doc(), stats=db.dashboard_stats())


@app.route("/upload", methods=["GET", "POST"])
def upload():
    if request.method == "POST":
        pasted = (request.form.get("notes") or "").strip()
        file = request.files.get("pdf")
        title, text = "Pasted notes", ""
        try:
            if file and file.filename:
                name = secure_filename(file.filename)
                ext = os.path.splitext(name)[1].lower()
                if ext not in ALLOWED_EXT:
                    raise ValueError("Unsupported file type. Upload a .pdf or .txt file.")
                data = file.read()
                if not data:
                    raise ValueError("The uploaded file is empty.")
                title = name
                text = extract_pdf_text(data) if ext == ".pdf" else data.decode("utf-8", errors="ignore")
            elif pasted:
                text = pasted
            else:
                raise ValueError("Please upload a PDF or paste some notes.")
            text = clean_text(text)[:MAX_CHARS]
            if len(text.split()) < MIN_WORDS:
                raise ValueError(f"Not enough text: at least {MIN_WORDS} words are needed to generate questions.")
        except ValueError as e:
            flash(str(e), "danger")
            return render_template("upload.html", doc=current_doc(), notes=pasted), 400
        words, sents = text_stats(text)
        session["doc_id"] = db.add_document(title, text, words, sents)
        session.pop("question_ids", None)
        flash("Study material processed successfully.", "success")
        return redirect(url_for("upload"))
    return render_template("upload.html", doc=current_doc(), notes="")


@app.route("/sample")
def load_sample():
    path = os.path.join(os.path.dirname(__file__), "data", "sample_notes.txt")
    with open(path, encoding="utf-8") as f:
        text = clean_text(f.read())
    words, sents = text_stats(text)
    session["doc_id"] = db.add_document("sample_notes.txt", text, words, sents)
    flash("Sample NLP notes loaded.", "success")
    return redirect(url_for("upload"))


@app.route("/analysis")
def analysis():
    doc = current_doc()
    if not doc:
        flash("Upload study material first.", "warning")
        return redirect(url_for("upload"))
    report = analyze(doc["text"])
    summary = summarize(doc["text"])
    important = rank_sentences(doc["text"], top_n=5)
    return render_template("analysis.html", doc=doc, r=report, summary=summary, important=important)


@app.route("/questions", methods=["GET", "POST"])
def questions():
    doc = current_doc()
    if not doc:
        flash("Upload study material first.", "warning")
        return redirect(url_for("upload"))
    result = None
    if request.method == "POST":
        difficulty = request.form.get("difficulty", "All")
        if difficulty not in ("All", "Easy", "Medium", "Difficult"):
            difficulty = "All"
        try:
            count = max(1, min(50, int(request.form.get("count", 10))))
        except ValueError:
            count = 10
        result = generate_questions(doc["text"], difficulty, count)
        if result["questions"]:
            ids = db.add_questions(doc["id"], result["questions"])
            session["question_ids"] = ids
            for q, i in zip(result["questions"], ids):
                q["id"] = i
        else:
            flash("No questions could be generated. " + " ".join(result["notes"]), "warning")
        result["difficulty"] = difficulty
    return render_template("questions.html", doc=doc, result=result)


@app.route("/practice")
def practice():
    doc = current_doc()
    ids = session.get("question_ids")
    if not doc or not ids:
        flash("Generate questions first.", "warning")
        return redirect(url_for("questions" if doc else "upload"))
    qs = db.get_questions(ids=ids)
    session["session_id"] = uuid.uuid4().hex
    payload = [{"id": q["id"], "difficulty": q["difficulty"], "qtype": q["qtype"], "topic": q["topic"],
                "question": q["question"], "method": q["method"]} for q in qs]
    return render_template("practice.html", doc=doc, qs=payload, session_id=session["session_id"],
                           semantic=ev.semantic_available())


@app.route("/results/<session_id>")
def results(session_id):
    rows = db.session_attempts(session_id)
    answered = [r for r in rows if r["status"] != "skipped"]
    summary = {"total": len(rows), "answered": len(answered), "skipped": len(rows) - len(answered),
               "correct": sum(r["status"] == "correct" for r in rows),
               "partial": sum(r["status"] == "partial" for r in rows),
               "weak": sum(r["status"] == "weak" for r in rows),
               "avg": round(sum(r["score"] for r in answered) / len(answered), 2) if answered else None}
    return render_template("results.html", rows=rows, s=summary)


@app.route("/results")
def results_latest():
    sid = session.get("session_id")
    if not sid:
        flash("No practice session yet.", "info")
        return redirect(url_for("practice"))
    return redirect(url_for("results", session_id=sid))


@app.route("/dashboard")
def dashboard():
    return render_template("dashboard.html", stats=db.dashboard_stats())


# ---------------------------------------------------------------- JSON API
@app.post("/api/evaluate")
def api_evaluate():
    data = request.get_json(silent=True) or {}
    q = db.get_question(data.get("question_id"))
    answer = (data.get("answer") or "").strip()
    if not q:
        return jsonify(error="Unknown question."), 404
    if not answer:
        return jsonify(error="Please type an answer before submitting."), 400
    if len(answer) > 5000:
        return jsonify(error="Answer is too long (max 5000 characters)."), 400
    result = ev.evaluate_answer(answer, q["answer"])
    db.add_attempt(data.get("session_id", "anon"), q, answer, result)
    return jsonify(result)


@app.post("/api/skip")
def api_skip():
    data = request.get_json(silent=True) or {}
    q = db.get_question(data.get("question_id"))
    if not q:
        return jsonify(error="Unknown question."), 404
    skipped = {"score": 0.0, "similarity": 0.0, "coverage": 0.0, "status": "skipped",
               "feedback": "Skipped.", "found": [], "missing": []}
    db.add_attempt(data.get("session_id", "anon"), q, "", skipped)
    return jsonify(ok=True)


@app.get("/api/reference/<int:qid>")
def api_reference(qid):
    q = db.get_question(qid)
    if not q:
        return jsonify(error="Unknown question."), 404
    return jsonify(reference=q["answer"], source=q["source"])


@app.get("/api/dashboard")
def api_dashboard():
    return jsonify(db.dashboard_stats())


@app.errorhandler(413)
def too_large(_):
    flash("File too large. Maximum size is 10 MB.", "danger")
    return render_template("upload.html", doc=current_doc(), notes=""), 413


@app.errorhandler(404)
def not_found(_):
    return render_template("404.html"), 404


if __name__ == "__main__":
    app.run(debug=True)
