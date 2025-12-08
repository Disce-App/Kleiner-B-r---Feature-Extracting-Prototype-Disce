import sys
from pathlib import Path

import requests  # HTTP-Bibliothek für den Aufruf der LanguageTool-API
from somajo import SoMaJo


LANGUAGETOOL_API_URL = "https://api.languagetool.org/v2/check"


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


def check_grammar_with_languagetool(text: str):
    """
    Schickt den Text an die öffentliche LanguageTool-HTTP-API
    und gibt die gefundenen Fehler (Matches) zurück.
    Doku: https://dev.languagetool.org/public-http-api.html
    """
    data = {
        "text": text,
        "language": "de-DE",  # Deutsch (Deutschland)
    }
    response = requests.post(LANGUAGETOOL_API_URL, data=data, timeout=10)
    response.raise_for_status()
    return response.json()["matches"]


def count_tokens(sentences) -> int:
    return sum(len(sent) for sent in sentences)


if __name__ == "__main__":
    # 1) Dateiname als Argument prüfen
    if len(sys.argv) < 2:
        print("Bitte eine Textdatei angeben, z.B.:")
        print("    py grammar_demo.py input.txt")
        sys.exit(1)

    filename = sys.argv[1]
    text = read_text_from_file(filename)

    # 2) SoMaJo: Sätze & Tokens
    sentences = tokenize_and_split(text)
    num_tokens = count_tokens(sentences)

    print(f"Anzahl Sätze:  {len(sentences)}")
    print(f"Anzahl Tokens: {num_tokens}")
    print()

    # 3) LanguageTool: Grammatik- und Rechtschreibfehler
    matches = check_grammar_with_languagetool(text)

    print(f"Gefundene Issues (LanguageTool): {len(matches)}")

    # 4) Fehler/100 Wörter als einfache Accuracy-Metrik
    if num_tokens > 0:
        errors_per_100 = len(matches) / num_tokens * 100
        print(f"Fehler pro 100 Tokens (grob): {errors_per_100:.2f}")
    print()

    # 5) Erste 5 Fehler mit Kontext ausgeben
    for i, m in enumerate(matches[:5], start=1):
        msg = m.get("message", "")
        rule_id = m.get("rule", {}).get("id", "")
        offset = m.get("offset", 0)
        length = m.get("length", 0)
        error_text = text[offset:offset + length]

        print(f"Issue {i}:")
        print(f"  Regel:   {rule_id}")
        print(f"  Stelle:  \"{error_text}\"")
        print(f"  Hinweis: {msg}")
        print()
