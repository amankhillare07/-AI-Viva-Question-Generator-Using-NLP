"""One-time download of NLTK datasets and the spaCy English model."""
import subprocess
import sys

import nltk

for pkg in ["punkt", "punkt_tab", "stopwords", "wordnet", "omw-1.4",
            "averaged_perceptron_tagger", "averaged_perceptron_tagger_eng"]:
    nltk.download(pkg, quiet=True)
    print("NLTK ok:", pkg)

try:
    import spacy
    spacy.load("en_core_web_sm")
    print("spaCy model already installed")
except Exception:
    subprocess.check_call([sys.executable, "-m", "spacy", "download", "en_core_web_sm"])
