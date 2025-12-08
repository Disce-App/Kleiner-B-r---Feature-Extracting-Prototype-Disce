import sys
from pathlib import Path

from somajo import SoMaJo
from HanTa import HanoverTagger as ht


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


# --- Komplexitäts-Metriken -------------------------------------------------


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
            # Endung "(FIN)" und Verb-Tag am Anfang
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
            # mindestens ein adjektivisches Tag, das mit "ADJ" beginnt
            if pos_list[i].startswith("ADJ"):
                j = i
                saw_adj = False
                while j < len(pos_list) and pos_list[j].startswith("ADJ"):
                    saw_adj = True
                    j += 1
                # danach ein Nomen (NN oder NNA etc.)
                if j < len(pos_list) and pos_list[j].startswith("NN") and saw_adj:
                    count += 1
                    i = j + 1  # hinter dem Nomen weitermachen
                else:
                    i += 1
            else:
                i += 1
        counts.append(count)
    return counts


def mean(values):
    return sum(values) / len(values) if values else 0.0


# --- main ------------------------------------------------------------------


if __name__ == "__main__":
    if len(sys.argv) < 2:
        print("Bitte eine Textdatei angeben, z.B.:")
        print("    py pos_demo.py input.txt")
        sys.exit(1)

    filename = sys.argv[1]
    text = read_text_from_file(filename)

    # 1) Tokenisierung + Satzsegmentierung mit SoMaJo
    sentences = tokenize_and_split(text)

    # 2) POS-Tagging mit HanTa
    tagged_sentences = pos_tag_sentences(sentences)

    # Optional: detailierte Ausgabe (Wort -> Lemma, POS)
    print("=== Detailansicht (Wort, Lemma, POS) ===")
    for i, sent in enumerate(tagged_sentences, start=1):
        print(f"Satz {i}:")
        for token_tuple in sent:
            # HanTa gibt i.d.R. (Wort, Lemma, POS) zurück
            if len(token_tuple) >= 3:
                word, lemma, pos = token_tuple[:3]
                print(f"  {word:20s} -> {lemma:20s} [{pos}]")
            else:
                print(f"  {token_tuple}")
        print()

    # Debug: Beispiel-Tuple aus dem ersten Satz
    print("DEBUG: Beispiel-Tuple aus dem ersten Satz:")
    if tagged_sentences and tagged_sentences[0]:
        print("  ", tagged_sentences[0][0], " (len =", len(tagged_sentences[0][0]), ")")
    print()

    # 3) Komplexitäts-Metriken berechnen
    lengths = sentence_lengths(tagged_sentences)
    finite_verbs = finite_verbs_per_sentence(tagged_sentences)
    subclauses = estimated_subclauses(tagged_sentences)
    complex_nps = complex_nps_per_sentence(tagged_sentences)

    print("=== Syntaktische Komplexitätsmetriken (Heuristiken) ===")
    print(f"Anzahl Sätze:                       {len(tagged_sentences)}")
    if lengths:
        print(f"Durchschnittliche Satzlänge:       {mean(lengths):.2f} Tokens")
        print(f"Min/Max Satzlänge:                 {min(lengths)} / {max(lengths)} Tokens")
    if finite_verbs:
        print(f"Ø finites Verb pro Satz:           {mean(finite_verbs):.2f}")
    if subclauses:
        print(f"Ø geschätzte Nebensätze pro Satz:  {mean(subclauses):.2f}")
    if complex_nps:
        print(f"Ø komplexe NPs (ADJ+NN) pro Satz:  {mean(complex_nps):.2f}")
