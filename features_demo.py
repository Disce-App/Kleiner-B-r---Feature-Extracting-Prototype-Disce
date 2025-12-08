import sys
import json
from pathlib import Path

import requests
from somajo import SoMaJo
from HanTa import HanoverTagger as ht


LANGUAGETOOL_API_URL = "https://api.languagetool.org/v2/check"


# --- Helper -----------------------------------------------------------------


def read_text_from_file(path_str: str) -> str:
    path = Path(path_str)
    if not path.exists():
        raise FileNotFoundError(f"Datei nicht gefunden: {path}")
    return path.read_text(encoding="utf-8")


def mean(values):
    return sum(values) / len(values) if values else 0.0


# --- Tokenisierung & POS-Tagging -------------------------------------------


def tokenize_and_split(text: str):
    """Verwendet SoMaJo, um Text in Sätze und Tokens zu zerlegen."""
    tokenizer = SoMaJo(language="de_CMC", split_sentences=True)
    docs = [text]
    return list(tokenizer.tokenize_text(docs))


def pos_tag_sentences(sentences):
    """
    Nimmt eine Liste von Sätzen (SoMaJo-Token-Objekte) und gibt
    für jeden Satz eine Liste von Tuples zurück (Wort, Lemma, POS, ...).
    """
    tagger = ht.HanoverTagger("morphmodel_ger.pgz")

    tagged_sentences = []
    for sent in sentences:
        words = [tok.text for tok in sent]
        tagged = tagger.tag_sent(words)
        tagged_sentences.append(tagged)
    return tagged_sentences


def count_tokens(tagged_sentences) -> int:
    return sum(len(sent) for sent in tagged_sentences)


# --- Grammatik-Check (LanguageTool) ----------------------------------------


def check_grammar_with_languagetool(text: str):
    """
    Schickt den Text an die öffentliche LanguageTool-HTTP-API
    und gibt die gefundenen Fehler (Matches) zurück.
    """
    data = {
        "text": text,
        "language": "de-DE",
    }
    response = requests.post(LANGUAGETOOL_API_URL, data=data, timeout=10)
    response.raise_for_status()
    return response.json()["matches"]


# --- Komplexitäts-Metriken (auf POS-Basis) ---------------------------------


def sentence_lengths(tagged_sentences):
    """Gibt eine Liste der Satzlängen (in Tokens) zurück."""
    return [len(sent) for sent in tagged_sentences]


def finite_verbs_per_sentence(tagged_sentences):
    """Zählt finite Verben pro Satz (VV(FIN), VA(FIN), VM(FIN))."""
    counts = []
    for sent in tagged_sentences:
        count = 0
        for token_tuple in sent:
            pos = token_tuple[-1]  # letztes Element im Tuple = POS
            if pos.endswith("(FIN)") and (
                pos.startswith("VV") or pos.startswith("VA") or pos.startswith("VM")
            ):
                count += 1
        counts.append(count)
    return counts


def estimated_subclauses(tagged_sentences):
    """
    Sehr grobe Nebensatz-Heuristik:
    - KOUS (unterordnende Konjunktion) + finites Verb im Satz -> 1 Nebensatz-Kandidat.
    """
    counts = []
    for sent in tagged_sentences:
        kous_count = 0
        finite_count = 0
        for token_tuple in sent:
            pos = token_tuple[-1]
            if pos == "KOUS":
                kous_count += 1
            if pos.endswith("(FIN)") and (
                pos.startswith("VV") or pos.startswith("VA") or pos.startswith("VM")
            ):
                finite_count += 1
        counts.append(min(kous_count, finite_count))
    return counts


def complex_nps_per_sentence(tagged_sentences):
    """
    Zählt einfache komplexe Nominalphrasen:
    - Sequenzen ADJ(*) + NN/NNA (oder ADJ(*) + ADJ(*) + NN/NNA etc.)
    """
    counts = []

    for sent in tagged_sentences:
        pos_list = [token_tuple[-1] for token_tuple in sent]
        count = 0
        i = 0
        while i < len(pos_list) - 1:
            if pos_list[i].startswith("ADJ"):
                j = i
                saw_adj = False
                while j < len(pos_list) and pos_list[j].startswith("ADJ"):
                    saw_adj = True
                    j += 1
                if j < len(pos_list) and pos_list[j].startswith("NN") and saw_adj:
                    count += 1
                    i = j + 1
                else:
                    i += 1
            else:
                i += 1
        counts.append(count)
    return counts


# --- Lexikalische Diversität & Dichte --------------------------------------


def lexical_features(tagged_sentences):
    """
    Berechnet einfache Lexik-Metriken:
    - unique_tokens, unique_lemmas
    - TTR (Type-Token-Ratio)
    - Lemma-TTR
    - Anteil Inhaltswörter (N, V, ADJ, ADV)
    """
    tokens = []
    lemmas = []
    content_pos_count = 0
    total_tokens = 0

    for sent in tagged_sentences:
        for token_tuple in sent:
            # HanTa: (Wort, Lemma, POS, ...)
            if len(token_tuple) >= 3:
                word, lemma, pos = token_tuple[:3]
            else:
                # Falls etwas schief geht, einfach überspringen
                continue

            # Normalisieren
            w_norm = word.lower()
            l_norm = lemma.lower()
            tokens.append(w_norm)
            lemmas.append(l_norm)
            total_tokens += 1

            # Grobe Inhaltswort-Heuristik: Wortarten, die mit N, V, ADJ, ADV beginnen
            if pos.startswith(("N", "V", "ADJ", "ADV")):
                content_pos_count += 1

    unique_tokens = len(set(tokens))
    unique_lemmas = len(set(lemmas))

    ttr = unique_tokens / total_tokens if total_tokens > 0 else 0.0
    lemma_ttr = unique_lemmas / total_tokens if total_tokens > 0 else 0.0
    content_word_share = content_pos_count / total_tokens if total_tokens > 0 else 0.0

    return {
        "unique_tokens": unique_tokens,
        "unique_lemmas": unique_lemmas,
        "ttr": ttr,
        "lemma_ttr": lemma_ttr,
        "content_word_share": content_word_share,
    }


# --- Einfache Kohäsion / Konnektoren --------------------------------------


CONNECTOR_LIST = [
    "aber",
    "denn",
    "doch",
    "jedoch",
    "trotzdem",
    "daher",
    "deshalb",
    "allerdings",
    "obwohl",
    "weil",
    "während",
    "hingegen",
    "außerdem",
    "zudem",
]


def cohesion_features(tagged_sentences):
    """
    Zählt einfache Konnektoren anhand einer Handliste.
    Später kann man diese Liste durch DiMLex ersetzen.
    """
    total_tokens = 0
    connector_count = 0
    connector_types_used = set()

    for sent in tagged_sentences:
        for token_tuple in sent:
            if len(token_tuple) >= 3:
                word, lemma, pos = token_tuple[:3]
            else:
                continue

            w_norm = word.lower()
            total_tokens += 1

            if w_norm in CONNECTOR_LIST:
                connector_count += 1
                connector_types_used.add(w_norm)

    density = connector_count / total_tokens * 100 if total_tokens > 0 else 0.0

    return {
        "connector_count": connector_count,
        "connector_type_count": len(connector_types_used),
        "connector_density_per_100_tokens": density,
        "connectors_used": sorted(list(connector_types_used)),
    }




# --- main ------------------------------------------------------------------


if __name__ == "__main__":
    if len(sys.argv) < 2:
        print("Bitte eine Textdatei angeben, z.B.:")
        print("    py features_demo.py input.txt")
        sys.exit(1)

    filename = sys.argv[1]
    text = read_text_from_file(filename)

    # 1) Tokenisierung + Satzsegmentierung
    sentences = tokenize_and_split(text)

    # 2) POS-Tagging
    tagged_sentences = pos_tag_sentences(sentences)

    # 3) Grundlegende Zählwerte
    num_sentences = len(tagged_sentences)
    num_tokens = count_tokens(tagged_sentences)

    # 4) Grammatik-Check
    matches = check_grammar_with_languagetool(text)
    num_issues = len(matches)
    errors_per_100_tokens = (num_issues / num_tokens * 100) if num_tokens > 0 else 0.0

        # 5) Komplexitäts-Metriken
    lengths = sentence_lengths(tagged_sentences)
    finite_verbs = finite_verbs_per_sentence(tagged_sentences)
    subclauses = estimated_subclauses(tagged_sentences)
    complex_nps = complex_nps_per_sentence(tagged_sentences)

    # 5b) Lexik- und Kohäsions-Metriken
    lex_feats = lexical_features(tagged_sentences)
    coh_feats = cohesion_features(tagged_sentences)

    # 6) Feature-JSON bauen
    features = {
        "num_sentences": num_sentences,
        "num_tokens": num_tokens,
        "errors": {
            "num_issues": num_issues,
            "errors_per_100_tokens": errors_per_100_tokens,
        },
        "syntax_complexity": {
            "sentence_length": {
                "avg": mean(lengths),
                "min": min(lengths) if lengths else 0,
                "max": max(lengths) if lengths else 0,
            },
            "finite_verbs_per_sentence": {
                "avg": mean(finite_verbs),
                "values": finite_verbs,
            },
            "estimated_subclauses_per_sentence": {
                "avg": mean(subclauses),
                "values": subclauses,
            },
            "complex_nps_per_sentence": {
                "avg": mean(complex_nps),
                "values": complex_nps,
            },
        },
        "lexical": lex_feats,
        "cohesion": coh_feats,
    }

    # 7) JSON ausgeben
    print(json.dumps(features, ensure_ascii=False, indent=2))
