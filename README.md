An AI-powered web application that automatically generates viva questions from study materials using Natural Language Processing (NLP). Students can upload notes, generate Easy, Medium, and Difficult questions, practise answering them, evaluate their answers, and track their performance through an interactive dashboard.

🚀 Features

Study Material Upload: Upload PDF and TXT files or paste notes directly.

Text Preprocessing: Tokenization, stop-word removal, stemming, lemmatization, and sentence segmentation.

NLP Analysis: Extract keywords, identify named entities, analyze parts of speech, and calculate word frequencies.

Automatic Question Generation: Generate questions at three difficulty levels using rule-based NLP techniques.

Viva Practice Mode: Answer questions, skip questions, view reference answers, and practise interactively.

Answer Evaluation: Evaluate student answers using TF-IDF similarity and concept coverage.

Text Summarization: Generate extractive summaries and identify important sentences.

Performance Dashboard: Visualize question difficulty, answer performance, topic-wise results, and revision areas.

Database Storage: Store study materials, generated questions, and practice attempts using SQLite.

Unit Testing: Test preprocessing, question generation, and answer evaluation.

🛠️ Technologies Used

Category

Technologies

Programming Language

Python

Backend

Flask

Frontend

HTML, CSS, JavaScript

NLP

NLTK, spaCy

Machine Learning

Scikit-learn, TF-IDF

PDF Processing

PyMuPDF

Database

SQLite

Charts and Visualization

Chart.js

Testing

pytest

📂 Project Structure

ai-viva-question-generator/
│
├── app.py
├── database.py
├── setup_nlp_data.py
├── requirements.txt
├── README.md
│
├── data/
│   └── sample_notes.txt
│
├── docs/
│   └── Project_Report.pdf
│
├── nlp/
│   ├── preprocessing.py
│   ├── keyword_extraction.py
│   ├── question_generation.py
│   ├── answer_evaluation.py
│   └── summarization.py
│
├── static/
│   ├── css/
│   │   └── style.css
│   └── js/
│       ├── main.js
│       └── charts.js
│
├── templates/
│   ├── base.html
│   ├── index.html
│   ├── upload.html
│   ├── analysis.html
│   ├── questions.html
│   ├── practice.html
│   ├── results.html
│   ├── dashboard.html
│   └── 404.html
│
└── tests/
    ├── test_preprocessing.py
    ├── test_question_generation.py
    └── test_answer_evaluation.py

⚙️ Installation and Setup

Prerequisites

Install the following before running the project:

Python 3.9 or later (Python 3.10–3.12 recommended)

pip package manager

Git

Visual Studio Code or another Python IDE

Step 1: Clone the Repository

git clone https://github.com/YOUR-USERNAME/ai-viva-question-generator.git
cd ai-viva-question-generator

Replace YOUR-USERNAME with your GitHub username.

Step 2: Create a Virtual Environment

Windows:

python -m venv venv
venv\Scripts\activate

macOS/Linux:

python3 -m venv venv
source venv/bin/activate

Step 3: Install Dependencies

python -m pip install --upgrade pip
pip install -r requirements.txt

Step 4: Download NLP Resources

python setup_nlp_data.py

This script prepares the required NLTK datasets and spaCy language model.

Step 5: Run the Application

python app.py

Open your browser and visit:

http://127.0.0.1:5000

The application initializes its SQLite database automatically when it starts.

🧪 How to Use

Open the application in your browser.

Upload a PDF or TXT file containing study notes, or paste your notes.

Analyze the text to view keywords, named entities, important sentences, and summaries.

Select the required difficulty level and generate viva questions.

Start the practice session and answer the generated questions.

Review your score, similarity percentage, identified concepts, and feedback.

Open the dashboard to analyze your performance and identify topics for revision.

You can also try the sample NLP notes included in the data/ directory.

🧠 Answer Evaluation Method

The application evaluates answers using TF-IDF cosine similarity and concept coverage.

Default scoring formula:

Score = 10 × (
    0.40 × TF-IDF Similarity
  + 0.60 × Concept Coverage
)

The score is calculated on a scale of 0 to 10.

Score

Evaluation

7 and above

Correct

4 to below 7

Partial

Below 4

Weak

The application identifies important concepts in the reference answer and checks how many are covered in the student's response.

An optional semantic similarity mode using Sentence Transformers is also supported.

🧪 Run Unit Tests

Run the following command from the project directory:

python -m pytest -q tests

The tests cover text preprocessing, question generation, and answer evaluation.

🔮 Future Enhancements

Integrate transformer-based question generation.

Add support for scanned PDFs using OCR.

Introduce user authentication and individual student profiles.

Support additional languages.

Export generated questions and results as PDF.

Add cloud deployment and persistent online storage.

Improve answer evaluation with advanced semantic similarity models.

🎯 Project Objective

The main objective of this project is to help students prepare for viva examinations efficiently by automatically generating relevant questions from their own study materials and providing immediate feedback on their answers.

👨‍💻 Author

Aman Khillare

AI Viva Question Generator Using Natural Language Processing

📄 License

This project is intended for educational and academic purposes. Add an open-source license, such as the MIT License, if you want others to reuse and modify the project under those terms.
