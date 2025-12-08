import sys
from pathlib import Path
from somajo import SoMaJo


def tokenize_and_split(text: str):
    # Tokenizer + Satzsegmentierer für Deutsch (CMC = Chat/Online-Sprache)
    tokenizer = SoMaJo(language="de_CMC", split_sentences=True)
    docs = [text]
    # Gibt eine Liste von Sätzen zurück, jeder Satz ist eine Liste von Token-Objekten
    return list(tokenizer.tokenize_text(docs))


def read_text_from_file(path_str: str) -> str:
    path = Path(path_str)
    if not path.exists():
        raise FileNotFoundError(f"Datei nicht gefunden: {path}")
    # UTF-8 ist sinnvoll, Editor kann das; falls es kracht, können wir das noch anpassen
    return path.read_text(encoding="utf-8")


if __name__ == "__main__":
    # Prüfen, ob ein Dateiname als Argument übergeben wurde
    if len(sys.argv) < 2:
        print("Bitte eine Textdatei angeben, z.B.:")
        print("    py tokenize_demo.py input.txt")
        sys.exit(1)

    filename = sys.argv[1]
    text = read_text_from_file(filename)

    sentences = tokenize_and_split(text)

    for i, sent in enumerate(sentences, start=1):
        print(f"Satz {i}:")
        print(" ".join(tok.text for tok in sent))
        print()
