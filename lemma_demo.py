import sys
from pathlib import Path

from somajo import SoMaJo
from simplemma import lemmatize

def read_text_from_file(path_str: str) -> str:
    path = Path(path_str)
    if not path.exists():
        raise FileNotFoundError(f"Datei nicht gefunden: {path}")
    return path.read_text(encoding="utf-8")


def tokenize_and_split(text: str):
    """Verwendet SoMaJo, um Text in Sätze und Tokens zu zerlegen."""
    tokenizer = SoMaJo(language="de_CMC", split_sentences=True)
    docs = [text]
    return list(tokenizer.tokenize_text(docs))


def lemmatize_tokens(sentences):
    """
    Nimmt eine Liste von Sätzen (SoMaJo-Token-Objekte) und gibt
    eine parallele Struktur mit Lemmata zurück.
    """
    lang = "de"  # Sprachcode für simplemma

    lemma_sentences = []
    for sent in sentences:
        lemma_sent = []
        for tok in sent:
            word = tok.text
            # simplemma.lemmatize gibt die wahrscheinlichste Grundform zurück
            lemma = lemmatize(word, lang=lang)
            lemma_sent.append((word, lemma))
        lemma_sentences.append(lemma_sent)
    return lemma_sentences


if __name__ == "__main__":
    # 1) Datei prüfen
    if len(sys.argv) < 2:
        print("Bitte eine Textdatei angeben, z.B.:")
        print("    py lemma_demo.py input.txt")
        sys.exit(1)

    filename = sys.argv[1]
    text = read_text_from_file(filename)

    # 2) Tokenisierung + Satzsegmentierung
    sentences = tokenize_and_split(text)

    # 3) Lemmatisierung
    lemma_sentences = lemmatize_tokens(sentences)

    # 4) Ausgabe: Wort → Lemma
    for i, sent in enumerate(lemma_sentences, start=1):
        print(f"Satz {i}:")
        for word, lemma in sent:
            print(f"  {word:20s} -> {lemma}")
        print()
