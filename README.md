# AI Viva Question Generator Using Natural Language Processing

A Flask web application that turns your study material (PDF, TXT or pasted notes) into **Easy / Medium / Difficult viva questions**, lets you practise answering them, **scores your answers with NLP**, and shows a **performance dashboard**. Everything runs locally - no paid APIs, no external LLM.

## Features

| Module | What it does |
|---|---|
| Upload | PDF (PyMuPDF), TXT or pasted notes; 10 MB limit; extension + `%PDF` signature checks; friendly errors for empty, scanned, corrupted, password-protected and unsupported files; word / sentence statistics |
| NLP Analysis | Sentence segmentation, tokenization, lowercasing, stop-word removal, punctuation removal, Porter stemming, WordNet lemmatization, POS tagging, spaCy NER, n-grams, word frequency, TF-IDF keywords, important sentences, extractive summary |
| Question generation | Rule/pattern-based, three difficulty levels, each question has a source passage + reference answer + topic + method label ("Rule-based"); duplicates removed; explains when the material is too thin instead of inventing content |
| Viva practice | One question at a time, difficulty badge, Submit / Show Reference / Skip / Next / Restart, live counters (answered, correct, skipped, remaining) |
| Answer evaluation | Score /10, similarity %, concepts found, missing concepts, feedback. TF-IDF + concept coverage by default; optional sentence-transformers |
| Dashboard | Chart.js charts computed from real SQLite records: level, topic, correct/partial/weak, recent trend, revision topics |

## Project structure

```
ai-viva-question-generator/
├── app.py                  Flask routes + JSON API
├── database.py             SQLite schema and queries
├── setup_nlp_data.py       Downloads NLTK data + spaCy model
├── requirements.txt
├── nlp/
│   ├── preprocessing.py        Module 2 pipeline
│   ├── keyword_extraction.py   TF-IDF keywords, sentence ranking
│   ├── question_generation.py  Rule-based generator
│   ├── answer_evaluation.py    Scoring (configurable weights)
│   └── summarization.py        Extractive summary
├── templates/              base, index, upload, analysis, questions, practice, results, dashboard, 404
├── static/css/style.css, static/js/main.js, static/js/charts.js
├── data/sample_notes.txt
└── tests/                  27 unit tests
```

## Installation (Windows, PowerShell or CMD)

Requires Python 3.9+ (3.10-3.12 recommended). Open a terminal in the project folder.

```powershell
# 1. Create and activate a virtual environment
python -m venv venv
venv\Scripts\activate
#   PowerShell blocked? run once:  Set-ExecutionPolicy -Scope CurrentUser RemoteSigned

# 2. Install dependencies
python -m pip install --upgrade pip
pip install -r requirements.txt

# 3. Download NLTK datasets and the spaCy model
python setup_nlp_data.py
#   (equivalent manual command for spaCy:  python -m spacy download en_core_web_sm)

# 4. Initialise the database (also happens automatically on first run)
python -c "import database; database.init_db(); print('database ready')"

# 5. Run the app
python app.py

# 6. Open in your browser
#    http://127.0.0.1:5000
```

macOS / Linux: use `python3` and `source venv/bin/activate`.

### Run in VS Code

1. `File > Open Folder...` and choose `ai-viva-question-generator`.
2. `Ctrl+Shift+P` -> **Python: Select Interpreter** -> choose `.\venv\Scripts\python.exe`.
3. Open a terminal (Ctrl + backtick) - it activates the venv automatically - then run steps 2-5 above.
4. Press `F5` (Python file -> `app.py`) or run `python app.py` in the terminal.

### Test with the sample notes

1. Open `http://127.0.0.1:5000` and click **Try Sample NLP Notes** (or upload `data/sample_notes.txt`).
2. **NLP Analysis** shows tokens, POS tags, entities, keywords and more.
3. **Questions** -> choose *All*, 10 questions -> **Generate**.
4. **Start Viva Practice** -> answer, skip, reveal references.
5. Finish -> **Results**, then **Analytics** for charts.

### Run the unit tests

```powershell
python -m pytest -q tests        # or: python -m unittest discover -s tests
```

### Optional: semantic similarity

```powershell
pip install sentence-transformers
```

The first scoring request downloads `all-MiniLM-L6-v2` (~90 MB, needs internet once). If the package or model is unavailable, the app silently falls back to TF-IDF scoring. Set `USE_SEMANTIC=0` to force the fallback. *Note: the semantic path was written to the library's documented API but could not be run in the build environment (no model download there); the TF-IDF path is what the tests and end-to-end checks exercised.*

## How scoring works

```
TF-IDF only :  score = 10 * (0.40 * tfidf_cosine + 0.60 * concept_coverage)
With semantic: score = 10 * (0.20 * tfidf_cosine + 0.30 * semantic_cosine + 0.50 * concept_coverage)
correct >= 7   partial 4-7   weak < 4
```
Weights and thresholds are constants at the top of `nlp/answer_evaluation.py`. Concept coverage = share of the reference answer's key lemmas (up to 8) that appear in the student's answer.

## Example generated questions and evaluations (from `data/sample_notes.txt`, TF-IDF mode)

**[Easy / Definition]** What is Natural Language Processing?

- Reference answer (source text): Natural Language Processing is a field of artificial intelligence that enables computers to understand, interpret, and generate human language.
- Student answer: "Natural language processing is an AI field that lets computers understand and generate human language."
- Result: **5.6 / 10**, similarity 45.9%, concept coverage 62.5%, status *partial*; missing concepts: intelligence, artificial, interpret

**[Easy / Definition]** What is Natural Language Processing?

- Reference answer (source text): Natural Language Processing is a field of artificial intelligence that enables computers to understand, interpret, and generate human language.
- Student answer: "It is the process of splitting text into tokens."
- Result: **0.8 / 10**, similarity 0.0%, concept coverage 12.5%, status *weak*; missing concepts: intelligence, artificial, understand, interpret, language, computer, generate

**[Medium / Comparison]** Explain the difference between stemming and lemmatization.

- Reference answer (source text): Unlike stemming, lemmatization produces valid words, whereas stemming can produce non-words such as "studi". Lemmatization is slower than stemming because it needs a dictionary lookup.
- Student answer: "Stemming chops suffixes off words to get a root form, while lemmatization uses a dictionary to return valid words but is slower."
- Result: **4.4 / 10**, similarity 15.4%, concept coverage 62.5%, status *partial*; missing concepts: non-words, lookup, studi

**[Difficult / Analysis]** Critically analyse this claim from the notes: "The main advantage of TF-IDF is that it down-weights words that appear in many documents, so it is more useful than Bag-of-Words for classification tasks."

- Reference answer (source text): The main advantage of TF-IDF is that it down-weights words that appear in many documents, so it is more useful than Bag-of-Words for classification tasks. A limitation of TF-IDF is that it ignores word order and cannot capture sem...
- Student answer: "TF-IDF is better because it reduces the weight of very common words, so rare informative words matter more for classification."
- Result: **1.3 / 10**, similarity 14.7%, concept coverage 12.5%, status *weak*; missing concepts: down-weights, bag-of-words, limitation, advantage, document, semantic, ignores

Notice the TF-IDF-only mode is **strict on paraphrases**: a reasonable answer in different words scores "partial". This is the main reason to install sentence-transformers.

## Known limitations

- **Rule-based question generation is not human-level understanding.** It matches surface patterns (definitions, "because", "unlike", advantages/limitations). Some questions will be awkward or too literal; texts without such patterns produce fewer questions (the app says so).
- **Reference answers are source sentences**, not model-written answers, so they can be verbose.
- **Scoring measures textual overlap, not factual correctness.** Cosine similarity can reward a wrong answer that reuses the right words and punish a right answer in new words. Use scores as study guidance only.
- Scanned/image-only PDFs are rejected (no OCR). Very long PDFs are truncated at 300,000 characters.
- Single-user local app: no login, one browser session per document. Bootstrap and Chart.js load from a CDN, so the pages need internet access (download them into `static/` for fully offline use).
- The Flask dev server and the default `SECRET_KEY` are for local use only (set `SECRET_KEY` for anything shared).

## Possible future improvements

OCR for scanned PDFs; transformer-based question generation (e.g. T5) with rule-based fallback; per-user accounts; spaced-repetition scheduling; exporting results to PDF/CSV; multi-document question banks; calibrated scoring weights using teacher-graded answers.

## Troubleshooting

| Problem | Fix |
|---|---|
| `LookupError: Resource punkt ... not found` | Run `python setup_nlp_data.py` |
| `OSError: [E050] Can't find model 'en_core_web_sm'` | `python -m spacy download en_core_web_sm` (the app still runs, NER is just disabled) |
| `venv\Scripts\activate` is blocked | `Set-ExecutionPolicy -Scope CurrentUser RemoteSigned`, reopen the terminal |
| `pip install PyMuPDF` fails | Upgrade pip and use Python 3.9-3.12 (64-bit) |
| Charts or styling missing | The CDN needs internet; check your connection |
| "No extractable text" for a PDF | It is a scan - paste the text or use a text-based PDF |
| Port 5000 already in use | Edit the last line of `app.py`: `app.run(debug=True, port=5001)` |
| Want a clean slate | Stop the app and delete `viva.db` |
