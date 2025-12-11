import spacy
import sys
from pathlib import Path

import requests
from somajo import SoMaJo
from HanTa import HanoverTagger as ht
from wordfreq import zipf_frequency 

LANGUAGETOOL_API_URL = "https://api.languagetool.org/v2/check"


# --- Helper -----------------------------------------------------------------


def read_text_from_file(path_str: str) -> str:
    path = Path(path_str)
    if not path.exists():
        raise FileNotFoundError(f"Datei nicht gefunden: {path}")
    return path.read_text(encoding="utf-8")


def mean(values):
    return sum(values) / len(values) if values else 0.0


def clamp01(x: float) -> float:
    """Begrenzt einen Wert hart auf [0, 1]."""
    return max(0.0, min(1.0, x))


# --- Tokenisierung & POS-Tagging -------------------------------------------


def tokenize_and_split(text: str):
    tokenizer = SoMaJo(language="de_CMC", split_sentences=True)
    docs = [text]
    return list(tokenizer.tokenize_text(docs))


def pos_tag_sentences(sentences):
    tagger = ht.HanoverTagger("morphmodel_ger.pgz")
    tagged_sentences = []
    for sent in sentences:
        words = [tok.text for tok in sent]
        tagged = tagger.tag_sent(words, taglevel=2)
        tagged_sentences.append(tagged)
    return tagged_sentences


def count_tokens(tagged_sentences) -> int:
    return sum(len(sent) for sent in tagged_sentences)


# --- Grammatik-Check --------------------------------------------------------


from requests.exceptions import RequestException


def check_grammar_with_languagetool(text: str):
    data = {
        "text": text,
        "language": "de-DE",
    }
    try:
        response = requests.post(LANGUAGETOOL_API_URL, data=data, timeout=10)
        response.raise_for_status()
        return response.json().get("matches", [])
    except RequestException as e:
        # Für Prototyp: nicht crashen, sondern ohne Grammatikfehler weiterrechnen
        print(f"[WARN] LanguageTool nicht erreichbar oder Timeout ({e}); "
              f"setze num_issues = 0.")
        return []



# --- Komplexität ------------------------------------------------------------


def sentence_lengths(tagged_sentences):
    return [len(sent) for sent in tagged_sentences]


def finite_verbs_per_sentence(tagged_sentences):
    """Zählt finite Verben pro Satz (VV(FIN), VA(FIN), VM(FIN))."""
    counts = []
    for sent in tagged_sentences:
        count = 0
        for token_tuple in sent:
            pos = token_tuple[-1]
            if pos.endswith("(FIN)") and (
                pos.startswith("VV") or pos.startswith("VA") or pos.startswith("VM")
            ):
                count += 1
        counts.append(count)
    return counts


def estimated_subclauses(tagged_sentences):
    """
    Nebensatz-Heuristik:
    - KOUS (unterordnende Konjunktion): dass, weil, obwohl, wenn, ...
    - PRELS (Relativpronomen): der, die, das, welcher, ...
    - PWS (w-Fragewörter in indirekten Fragen): was, wer, wo, ...
    + finites Verb im Satz -> 1 Nebensatz-Kandidat.
    """
    counts = []
    for sent in tagged_sentences:
        subord_count = 0
        finite_count = 0
        for token_tuple in sent:
            pos = token_tuple[-1]
            # Subordinierende Einleiter: KOUS, Relativpronomen, w-Wörter
            if pos in {"KOUS", "PRELS", "PWS"}:
                subord_count += 1
            # Finite Verben
            if pos.endswith("(FIN)") and (
                pos.startswith("VV") or pos.startswith("VA") or pos.startswith("VM")
            ):
                finite_count += 1
        counts.append(min(subord_count, finite_count))
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


def vorfeld_lengths(tagged_sentences):
    """
    Grobe Vorfeldlänge: Anzahl Tokens bis zum ersten finiten Verb im Satz.
    Nutzt POS-Tags mit (FIN).
    """
    lengths = []
    for sent in tagged_sentences:
        length = 0
        found_finite = False
        for token_tuple in sent:
            if len(token_tuple) < 3:
                continue
            word, lemma, pos = token_tuple[:3]
            if pos.endswith("(FIN)") and (
                pos.startswith("VV") or pos.startswith("VA") or pos.startswith("VM")
            ):
                found_finite = True
                break
            length += 1
        if found_finite:
            lengths.append(length)
    return lengths


# --- MATTR / Lexikalische Diversität ----------------------------------------


def get_token_sequence(tagged_sentences):
    """
    Liefert eine flache Liste normalisierter Wortformen (lowercased),
    um darauf z.B. MATTR zu berechnen.
    """
    tokens = []
    for sent in tagged_sentences:
        for token_tuple in sent:
            if len(token_tuple) >= 3:
                word, lemma, pos = token_tuple[:3]
            else:
                continue
            tokens.append(word.lower())
    return tokens


def moving_average_ttr(tokens, window_size=50):
    """
    Moving-Average Type-Token Ratio (MATTR) nach Covington & McFall:
    - schiebt ein Fenster der Länge window_size über die Tokens
    - berechnet für jedes Fenster TTR = unique_types / window_size
    - gibt Durchschnitt/Min/Max zurück
    """
    n = len(tokens)
    if n < window_size or window_size <= 0:
        return None  # Text zu kurz für sinnvolle MATTR

    ttrs = []
    for start in range(0, n - window_size + 1):
        window = tokens[start:start + window_size]
        ttrs.append(len(set(window)) / float(window_size))

    return {
        "window_size": window_size,
        "avg": sum(ttrs) / len(ttrs),
        "min": min(ttrs),
        "max": max(ttrs),
        "num_windows": len(ttrs),
    }


# --- Passiv -----------------------------------------------------------------

def passive_voice_features(tagged_sentences):
    """
    Erkennt Passiv-Konstruktionen im Deutschen regelbasiert.
    
    Vorgangspassiv: werden + Partizip II ("wird geschrieben")
    Zustandspassiv: sein + Partizip II ("ist geschrieben")
    Modalpassiv: Modalverb + Partizip II + werden ("muss geschrieben werden")
    """
    nlp = get_spacy_nlp()
    
    # Rekonstruiere Text
    words = []
    for sent in tagged_sentences:
        for tok in sent:
            if len(tok) >= 1:
                words.append(tok[0])
    text = " ".join(words)
    
    doc = nlp(text)
    
    passive_counts = {
        "vorgangspassiv": 0,      # werden + PP
        "zustandspassiv": 0,      # sein + PP
        "modalpassiv": 0,         # Modalverb + PP + werden
    }
    
    passive_instances = []  # Für Debug/Anzeige
    total_clauses = 0       # Geschätzte Anzahl an Teilsätzen
    
    # Hilfslexikon
    werden_forms = {"werden", "wird", "wirst", "werdet", "wurde", "wurdest", 
                    "wurden", "wurdet", "werde", "würde", "würdest", "würden", "würdet"}
    sein_forms = {"sein", "ist", "bist", "sind", "seid", "war", "warst", 
                  "waren", "wart", "sei", "seist", "seien", "seid", "wäre", 
                  "wärst", "wären", "wärt"}
    modal_verbs = {"können", "müssen", "sollen", "wollen", "dürfen", "mögen",
                   "kann", "muss", "soll", "will", "darf", "mag",
                   "kannst", "musst", "sollst", "willst", "darfst", "magst",
                   "könnt", "müsst", "sollt", "wollt", "dürft", "mögt",
                   "konnte", "musste", "sollte", "wollte", "durfte", "mochte",
                   "konnten", "mussten", "sollten", "wollten", "durften", "mochten"}
    
    # Zähle Teilsätze (grob: finite Verben)
    for token in doc:
        verbform = token.morph.get("VerbForm")
        if verbform and "Fin" in verbform:
            total_clauses += 1
    
    # Suche nach Passiv-Mustern
    for sent in doc.sents:
        tokens = list(sent)
        
        for i, token in enumerate(tokens):
            token_lower = token.text.lower()
            
            # Partizip II finden
            verbform = token.morph.get("VerbForm")
            is_participle = verbform and "Part" in verbform
            
            if not is_participle:
                continue
            
            # Suche im Kontext (5 Tokens vorher und nachher) nach Hilfsverben
            context_start = max(0, i - 5)
            context_end = min(len(tokens), i + 5)
            context_tokens = [t.text.lower() for t in tokens[context_start:context_end]]
            context_lemmas = [t.lemma_.lower() for t in tokens[context_start:context_end]]
            
            # Vorgangspassiv: werden + Partizip II
            has_werden = any(t in werden_forms for t in context_tokens)
            # Zustandspassiv: sein + Partizip II (aber nicht Perfekt Aktiv!)
            has_sein = any(t in sein_forms for t in context_tokens)
            # Modalpassiv: Modalverb im Kontext
            has_modal = any(t in modal_verbs for t in context_tokens)
            
            if has_werden and has_modal:
                passive_counts["modalpassiv"] += 1
                passive_instances.append(f"Modalpassiv: ...{token.text}...")
            elif has_werden:
                passive_counts["vorgangspassiv"] += 1
                passive_instances.append(f"Vorgangspassiv: ...{token.text}...")
            elif has_sein and token.lemma_.lower() not in {"sein", "haben", "werden"}:
                # Zustandspassiv nur wenn kein Hilfsverb selbst
                # Heuristik: Wenn "worden" dabei ist, ist es Perfekt Passiv (→ Vorgangspassiv)
                if "worden" in context_tokens:
                    passive_counts["vorgangspassiv"] += 1
                    passive_instances.append(f"Perfekt Vorgangspassiv: ...{token.text}...")
                else:
                    passive_counts["zustandspassiv"] += 1
                    passive_instances.append(f"Zustandspassiv: ...{token.text}...")
    
    # Gesamtzahlen
    total_passive = sum(passive_counts.values())
    
    return {
        **passive_counts,
        "total_passive": total_passive,
        "total_clauses": total_clauses,
        "passive_ratio": round(total_passive / total_clauses, 3) if total_clauses > 0 else 0.0,
        "passive_instances": passive_instances[:10],  # Max 10 Beispiele
    }



# --- Lexik & Kohäsion -------------------------------------------------------


def lexical_features(tagged_sentences):
    tokens = []
    lemmas = []
    content_pos_count = 0
    total_tokens = 0

    for sent in tagged_sentences:
        for token_tuple in sent:
            if len(token_tuple) >= 3:
                word, lemma, pos = token_tuple[:3]
            else:
                continue

            w_norm = word.lower()
            l_norm = lemma.lower()
            tokens.append(w_norm)
            lemmas.append(l_norm)
            total_tokens += 1

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
    "und", 
    "oder", 
    "sondern", 
    "also", 
    "dann",
    "danach", 
    "später", 
    "gleichzeitig", 
    "dennoch",
    "darum", 
    "deswegen"
]


def cohesion_features(tagged_sentences):
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


def sentence_overlap(tagged_sentences):
    """
    Misst, wie viele Inhaltswörter zwischen benachbarten Sätzen geteilt werden.
    """

    def content_lemmas(sent):
        lemmas = []
        for token_tuple in sent:
            if len(token_tuple) < 3:
                continue
            word, lemma, pos = token_tuple[:3]
            if pos.startswith(("N", "V", "ADJ", "ADV")):
                lemmas.append(lemma.lower())
        return set(lemmas)

    overlaps = []
    prev = None
    for sent in tagged_sentences:
        cur = content_lemmas(sent)
        if prev is not None and prev and cur:
            inter = prev.intersection(cur)
            union = prev.union(cur)
            overlaps.append(len(inter) / len(union))
        prev = cur

    if not overlaps:
        return None

    return {
        "avg_overlap": mean(overlaps),
        "min_overlap": min(overlaps),
        "max_overlap": max(overlaps),
        "num_pairs": len(overlaps),
    }


PERSONAL_PRONOUNS = {
    "ich": "1sg",
    "wir": "1pl",
    "du": "2sg",
    "ihr": "2pl",
    "er": "3sg",
    "sie": "3sg_pl",  # sg/pl zusammengefasst
    "es": "3sg",
    "man": "indef",
}


def pronoun_stats(tagged_sentences):
    total_tokens = 0
    pronoun_counts = {label: 0 for label in set(PERSONAL_PRONOUNS.values())}
    third_person_refs = 0

    for sent in tagged_sentences:
        for token_tuple in sent:
            if len(token_tuple) < 3:
                continue
            word, lemma, pos = token_tuple[:3]
            w_norm = word.lower()
            total_tokens += 1

            if pos.startswith("P"):
                label = PERSONAL_PRONOUNS.get(w_norm)
                if label:
                    pronoun_counts[label] += 1
                    if label in {"3sg", "3pl", "3sg_pl"}:
                        third_person_refs += 1

    total_pronouns = sum(pronoun_counts.values())
    share_pronouns = total_pronouns / total_tokens if total_tokens > 0 else 0.0

    return {
        "total_pronouns": total_pronouns,
        "share_pronouns": share_pronouns,
        "by_person": pronoun_counts,
        "third_person_refs": third_person_refs,
    }


# --- Satztypen, Absätze, direkte Rede, Interpunktion ------------------------


def sentence_type_counts(tagged_sentences):
    declarative = 0
    interrogative = 0
    exclamative = 0
    other = 0

    for sent in tagged_sentences:
        if not sent:
            continue
        last_word = sent[-1][0]
        if last_word.endswith("?"):
            interrogative += 1
        elif last_word.endswith("!"):
            exclamative += 1
        elif last_word.endswith(".") or last_word in {".", "…"}:
            declarative += 1
        else:
            other += 1

    return {
        "declarative": declarative,
        "interrogative": interrogative,
        "exclamative": exclamative,
        "other": other,
    }


def paragraph_stats(text: str):
    """
    Sehr einfache Absatz-Info:
    - Absätze via doppeltem Zeilenumbruch \n\n
    - zählt nur Absätze mit Inhalt (nicht reine Leerzeilen)
    """
    raw_pars = text.split("\n\n")
    paragraphs = [p for p in raw_pars if p.strip()]
    num_pars = len(paragraphs)
    lengths_chars = [len(p) for p in paragraphs]

    return {
        "num_paragraphs": num_pars,
        "avg_length_chars": mean(lengths_chars) if lengths_chars else 0.0,
        "min_length_chars": min(lengths_chars) if lengths_chars else 0,
        "max_length_chars": max(lengths_chars) if lengths_chars else 0,
    }


QUOTE_TOKENS = {'"', "„", "“", "‚", "‘", "«", "»", "”", "‚", "’"}


def direct_speech_features(tagged_sentences):
    inside = False
    inside_count = 0
    total_tokens = 0

    for sent in tagged_sentences:
        for token_tuple in sent:
            if len(token_tuple) < 1:
                continue
            word = token_tuple[0]
            total_tokens += 1

            if word in QUOTE_TOKENS:
                inside = not inside
                continue

            if inside:
                inside_count += 1

    share = inside_count / total_tokens if total_tokens > 0 else 0.0

    return {
        "tokens_inside_quotes": inside_count,
        "share_inside_quotes": share,
    }


PUNCT_CHARS = set(".,;:!?…()[]{}-–—")


def punctuation_features(tagged_sentences):
    total_tokens = 0
    punct_tokens = 0
    comma_tokens = 0

    for sent in tagged_sentences:
        for token_tuple in sent:
            if len(token_tuple) < 1:
                continue
            word = token_tuple[0]
            total_tokens += 1

            if word == ",":
                comma_tokens += 1
                punct_tokens += 1
            elif word and all(ch in PUNCT_CHARS for ch in word):
                punct_tokens += 1

    density = punct_tokens / total_tokens * 100 if total_tokens > 0 else 0.0

    return {
        "punctuation_tokens": punct_tokens,
        "punctuation_per_100_tokens": density,
        "comma_tokens": comma_tokens,
    }


# --- Lesbarkeit (LIX) -------------------------------------------------------


def lix_index(text: str, num_sentences: int, num_tokens: int):
    """
    Sehr grobe Lesbarkeitsmetrik nach LIX.
    Nutzt Rohtext (für Wortlänge) + schon berechnete Satz- und Tokenanzahl.
    """
    if num_sentences == 0 or num_tokens == 0:
        return None

    raw_tokens = [
        w.strip(".,;:!?…()[]{}\"'„“‚‘«»”")
        for w in text.split()
    ]
    raw_tokens = [w for w in raw_tokens if w]

    if not raw_tokens:
        return None

    long_words = [w for w in raw_tokens if len(w) >= 7]
    lix = (len(raw_tokens) / num_sentences) + (len(long_words) * 100 / len(raw_tokens))

    return {
        "lix": lix,
        "num_long_words": len(long_words),
        "share_long_words": len(long_words) / len(raw_tokens) if raw_tokens else 0.0,
    }


# --- Stil / Register: Modalpartikeln ----------------------------------------


MODAL_PARTICLES = {
    "ja", "halt", "eben", "doch", "mal", "eigentlich",
    "denn", "schon", "wohl", "ruhig", "bloß", "nur"
}


def modal_particle_features(tagged_sentences):
    total_tokens = 0
    mp_count = 0
    types = set()

    for sent in tagged_sentences:
        for token_tuple in sent:
            if len(token_tuple) < 1:
                continue
            word = token_tuple[0].lower()
            total_tokens += 1
            if word in MODAL_PARTICLES:
                mp_count += 1
                types.add(word)

    density = mp_count / total_tokens * 100 if total_tokens > 0 else 0.0
    return {
        "modal_particles": mp_count,
        "modal_particle_types": len(types),
        "modal_particle_density_per_100_tokens": density,
        "modal_particles_used": sorted(list(types)),
    }


# --- Morphologie: Tempus & Kasus aus HanTa ----------------------------------

def morphology_features(tagged_sentences):
    """
    Extrahiert Tempus- und Kasus-Verteilungen mit spaCy (nicht HanTa).
    HanTa liefert keine morphologischen Details, spaCy schon.
    """
    nlp = get_spacy_nlp()
    
    # Rekonstruiere den Text aus den tagged_sentences
    words = []
    for sent in tagged_sentences:
        for tok in sent:
            if len(tok) >= 1:
                words.append(tok[0])
    text = " ".join(words)
    
    doc = nlp(text)
    
    tense_counts = {"present": 0, "past": 0, "perfect": 0}
    case_counts = {"nominative": 0, "genitive": 0, "dative": 0, "accusative": 0}
    
    total_finite_verbs = 0
    total_case_marked = 0
    
    for token in doc:
        # Tempus aus Verben
        if token.pos_ == "VERB" or token.pos_ == "AUX":
            tense = token.morph.get("Tense")
            verbform = token.morph.get("VerbForm")
            
            # Finite Verben (nicht Infinitiv, nicht Partizip)
            if verbform and "Fin" in verbform:
                total_finite_verbs += 1
                if tense:
                    if "Pres" in tense:
                        tense_counts["present"] += 1
                    elif "Past" in tense:
                        tense_counts["past"] += 1
            
            # Partizip II (für Perfekt/Passiv)
            if verbform and "Part" in verbform:
                tense_counts["perfect"] += 1
        
        # Kasus aus Nomen, Pronomen, Artikeln
        if token.pos_ in {"NOUN", "PROPN", "PRON", "DET"}:
            case = token.morph.get("Case")
            if case:
                if "Nom" in case:
                    case_counts["nominative"] += 1
                    total_case_marked += 1
                elif "Gen" in case:
                    case_counts["genitive"] += 1
                    total_case_marked += 1
                elif "Dat" in case:
                    case_counts["dative"] += 1
                    total_case_marked += 1
                elif "Acc" in case:
                    case_counts["accusative"] += 1
                    total_case_marked += 1
    
    # Anteile berechnen
    tense_shares = {}
    for t, count in tense_counts.items():
        tense_shares[f"{t}_share"] = round(count / total_finite_verbs, 3) if total_finite_verbs > 0 else 0.0
    
    case_shares = {}
    for c, count in case_counts.items():
        case_shares[f"{c}_share"] = round(count / total_case_marked, 3) if total_case_marked > 0 else 0.0
    
    return {
        **tense_counts,
        **case_counts,
        "total_finite_verbs": total_finite_verbs,
        "total_case_marked": total_case_marked,
        **tense_shares,
        **case_shares,
        "past_tense_ratio": round(
            (tense_counts["past"] + tense_counts["perfect"]) / total_finite_verbs, 3
        ) if total_finite_verbs > 0 else 0.0,
        "oblique_case_ratio": round(
            (case_counts["genitive"] + case_counts["dative"]) / total_case_marked, 3
        ) if total_case_marked > 0 else 0.0,
    }


def verb_mood_features(tagged_sentences):
    """
    Erkennt Verb-Modi: Indikativ, Konjunktiv I, Konjunktiv II, Imperativ.
    Nutzt spaCy's morphologische Analyse.
    
    Konjunktiv I: Subjunctive + Präsens (sei, habe, komme)
    Konjunktiv II: Subjunctive + Präteritum (wäre, hätte, käme)
    würde-Form: "würde" + Infinitiv (analytischer Konjunktiv II)
    """
    nlp = get_spacy_nlp()
    
    # Rekonstruiere Text
    words = []
    for sent in tagged_sentences:
        for tok in sent:
            if len(tok) >= 1:
                words.append(tok[0])
    text = " ".join(words)
    
    doc = nlp(text)
    
    mood_counts = {
        "indicative": 0,
        "subjunctive_1": 0,  # Konjunktiv I
        "subjunctive_2": 0,  # Konjunktiv II
        "imperative": 0,
        "wuerde_form": 0,    # würde + Infinitiv
    }
    
    total_finite_verbs = 0
    
    for i, token in enumerate(doc):
        if token.pos_ not in {"VERB", "AUX"}:
            continue
            
        verbform = token.morph.get("VerbForm")
        
        # Nur finite Verben zählen
        if not verbform or "Fin" not in verbform:
            continue
            
        total_finite_verbs += 1
        
        mood = token.morph.get("Mood")
        tense = token.morph.get("Tense")
        
        if mood:
            if "Imp" in mood:
                mood_counts["imperative"] += 1
            elif "Sub" in mood:
                # Konjunktiv I vs II unterscheiden
                if tense and "Past" in tense:
                    mood_counts["subjunctive_2"] += 1
                else:
                    # Präsens oder unmarkiert → K1
                    mood_counts["subjunctive_1"] += 1
            elif "Ind" in mood:
                mood_counts["indicative"] += 1
        
        # würde-Form erkennen (analytischer Konjunktiv II)
        if token.lemma_.lower() == "werden" and mood and "Sub" in mood:
            # Prüfe ob danach ein Infinitiv kommt
            for j in range(i + 1, min(i + 5, len(doc))):
                next_token = doc[j]
                next_verbform = next_token.morph.get("VerbForm")
                if next_verbform and "Inf" in next_verbform:
                    mood_counts["wuerde_form"] += 1
                    break
    
    # Anteile berechnen
    mood_shares = {}
    for m, count in mood_counts.items():
        mood_shares[f"{m}_share"] = round(count / total_finite_verbs, 3) if total_finite_verbs > 0 else 0.0
    
    # Konjunktiv gesamt
    total_subjunctive = mood_counts["subjunctive_1"] + mood_counts["subjunctive_2"] + mood_counts["wuerde_form"]
    
    return {
        **mood_counts,
        "total_finite_verbs": total_finite_verbs,
        "total_subjunctive": total_subjunctive,
        "subjunctive_share": round(total_subjunctive / total_finite_verbs, 3) if total_finite_verbs > 0 else 0.0,
        **mood_shares,
    }


# --- Wortfrequenz-Features (SUBTLEX-DE via wordfreq) ------------------------

def word_frequency_features(tagged_sentences):
    """
    Berechnet Wortfrequenz-basierte Features mit der wordfreq-Bibliothek.
    Nutzt SUBTLEX-DE und andere deutsche Korpora.
    
    Zipf-Skala: 1-2 = sehr selten, 3-4 = selten, 4-5 = mittel, 5-6 = häufig, 6-7 = sehr häufig
    """
    zipf_values = []
    rare_count = 0
    very_common_count = 0
    unknown_count = 0
    total_content_words = 0
    
    for sent in tagged_sentences:
        for token_tuple in sent:
            if len(token_tuple) < 3:
                continue
            word, lemma, pos = token_tuple[:3]
            
            if not pos.startswith(("N", "V", "ADJ", "ADV")):
                continue
            
            lemma_lower = lemma.lower()
            total_content_words += 1
            
            zipf = zipf_frequency(lemma_lower, "de")
            
            if zipf == 0:
                zipf = zipf_frequency(word.lower(), "de")
                if zipf == 0:
                    unknown_count += 1
                    zipf = 2.0
            
            zipf_values.append(zipf)
            
            if zipf < 3.0:
                rare_count += 1
            elif zipf > 5.5:
                very_common_count += 1
    
    if not zipf_values:
        return {
            "avg_zipf": 0.0,
            "min_zipf": 0.0,
            "max_zipf": 0.0,
            "median_zipf": 0.0,
            "rare_word_count": 0,
            "rare_word_share": 0.0,
            "very_common_share": 0.0,
            "unknown_count": 0,
            "unknown_share": 0.0,
            "difficulty_score": 0.5,
        }
    
    sorted_zipf = sorted(zipf_values)
    n = len(sorted_zipf)
    median_zipf = sorted_zipf[n // 2] if n % 2 == 1 else (sorted_zipf[n // 2 - 1] + sorted_zipf[n // 2]) / 2
    
    avg_zipf = sum(zipf_values) / len(zipf_values)
    
    difficulty_raw = (6.0 - avg_zipf) / (6.0 - 2.5)
    difficulty_score = max(0.0, min(1.0, difficulty_raw))
    
    return {
        "avg_zipf": round(avg_zipf, 3),
        "min_zipf": round(min(zipf_values), 3),
        "max_zipf": round(max(zipf_values), 3),
        "median_zipf": round(median_zipf, 3),
        "rare_word_count": rare_count,
        "rare_word_share": round(rare_count / total_content_words, 3) if total_content_words > 0 else 0.0,
        "very_common_share": round(very_common_count / total_content_words, 3) if total_content_words > 0 else 0.0,
        "unknown_count": unknown_count,
        "unknown_share": round(unknown_count / total_content_words, 3) if total_content_words > 0 else 0.0,
        "difficulty_score": round(difficulty_score, 3),
    }


def get_rare_words_list(tagged_sentences, threshold=3.0, max_words=20):
    """
    Gibt eine Liste der seltensten Wörter im Text zurück.
    """
    rare_words = []
    
    for sent in tagged_sentences:
        for token_tuple in sent:
            if len(token_tuple) < 3:
                continue
            word, lemma, pos = token_tuple[:3]
            
            if not pos.startswith(("N", "V", "ADJ", "ADV")):
                continue
            
            lemma_lower = lemma.lower()
            zipf = zipf_frequency(lemma_lower, "de")
            
            if zipf == 0:
                zipf = zipf_frequency(word.lower(), "de")
            
            if 0 < zipf < threshold:
                rare_words.append({
                    "word": word,
                    "lemma": lemma,
                    "zipf": round(zipf, 2),
                    "pos": pos
                })
    
    seen_lemmas = set()
    unique_rare = []
    for w in sorted(rare_words, key=lambda x: x["zipf"]):
        if w["lemma"].lower() not in seen_lemmas:
            seen_lemmas.add(w["lemma"].lower())
            unique_rare.append(w)
        if len(unique_rare) >= max_words:
            break
    
    return unique_rare

# --- Dependency-Parsing mit spaCy: Baumtiefe ---------------------------------

_spacy_nlp = None


def get_spacy_nlp():
    """
    Lazy-Loader für das deutsche spaCy-Modell.
    Wird nur einmal initialisiert und danach wiederverwendet.
    """
    global _spacy_nlp
    if _spacy_nlp is None:
        _spacy_nlp = spacy.load("de_core_news_sm")
    return _spacy_nlp


def dependency_tree_features(text: str):
    """
    Berechnet Baumtiefen-Features auf Basis des Dependency-Parsers.
    - Für jeden Satz: maximale Tiefe vom Token zur Wurzel
    - Liefert Aggregatwerte über alle Sätze
    """
    nlp = get_spacy_nlp()
    doc = nlp(text)

    sent_depths = []

    for sent in doc.sents:
        max_depth = 0
        for token in sent:
            depth = 0
            head = token
            # Kette nach oben bis zur Wurzel (head == token)
            while head.head != head:
                depth += 1
                head = head.head
            if depth > max_depth:
                max_depth = depth
        sent_depths.append(max_depth)

    if not sent_depths:
        return {
            "avg_tree_depth": 0.0,
            "min_tree_depth": 0,
            "max_tree_depth": 0,
            "num_sents_parsed": 0,
        }

    return {
        "avg_tree_depth": mean(sent_depths),
        "min_tree_depth": min(sent_depths),
        "max_tree_depth": max(sent_depths),
        "num_sents_parsed": len(sent_depths),
    }


# --- Dimensionen 0–1 --------------------------------------------------------


def compute_dimension_scores(
    num_tokens,
    num_issues,
    lengths,
    finite_verbs,
    subclauses,
    complex_nps,
    vorfeld,
    lex_feats,
    coh_feats,
    overlap,
    mattr,
    pronouns,
    direct_speech,
    lix,
    mp_feats,
    freq_feats=None,
    dep_tree=None,
):
    """
    Errechnet normalisierte Dimensionen im Bereich [0,1].
    Schwellenwerte sind heuristisch und später leicht anpassbar.
    """
    dims = {}

    # 1) Grammatik-Genauigkeit: 1 = keine Fehler, 0 ~ sehr viele Fehler
    if num_tokens > 0:
        errors_per_100 = num_issues / num_tokens * 100.0
        # 0 Fehler -> ~1.0, >= 20 Fehler/100 -> 0.0
        score = 1.0 - (errors_per_100 / 20.0)
        dims["grammar_accuracy"] = clamp01(score)
    else:
        dims["grammar_accuracy"] = 0.0

        # 2) Syntaktische Komplexität
    if lengths:
        avg_len = mean(lengths)
        finite_mean = mean(finite_verbs) if finite_verbs else 0.0
        sub_mean = mean(subclauses) if subclauses else 0.0
        cnps_mean = mean(complex_nps) if complex_nps else 0.0
        vorfeld_mean = mean(vorfeld) if vorfeld else 0.0

        # Heuristische Skalen
        avg_len_norm = clamp01((avg_len - 8.0) / (25.0 - 8.0))
        finite_norm = clamp01((finite_mean - 1.0) / (2.5 - 1.0))
        sub_norm = clamp01((sub_mean - 0.0) / (2.0 - 0.0))
        cnps_norm = clamp01((cnps_mean - 0.0) / (2.0 - 0.0))
        vorfeld_norm = clamp01((vorfeld_mean - 0.0) / (6.0 - 0.0))

        # ✅ NEU: Baumtiefe (spaCy)
        # Typischer Bereich: 2 (sehr einfach) bis 8 (komplex)
        if dep_tree and dep_tree.get("num_sents_parsed", 0) > 0:
            tree_depth = dep_tree.get("avg_tree_depth", 0.0)
            tree_depth_norm = clamp01((tree_depth - 2.0) / (8.0 - 2.0))
        else:
            tree_depth_norm = 0.0

        # Gewichtung mit Baumtiefe (20%)
        dims["syntactic_complexity"] = (
            0.25 * avg_len_norm
            + 0.15 * finite_norm
            + 0.15 * sub_norm
            + 0.10 * cnps_norm
            + 0.10 * vorfeld_norm
            + 0.25 * tree_depth_norm      # ✅ NEU
        )
    else:
        dims["syntactic_complexity"] = 0.0

    # 3) Lexikalische Diversität
    content_share = lex_feats.get("content_word_share", 0.0) if lex_feats else 0.0
    lemma_ttr = lex_feats.get("lemma_ttr", 0.0) if lex_feats else 0.0

    if mattr is not None:
        mattr_avg = mattr.get("avg", 0.0)
        # 0.3–0.7 typischer MATTR-Bereich
        mattr_norm = clamp01((mattr_avg - 0.3) / (0.7 - 0.3))
    else:
        mattr_norm = clamp01((lemma_ttr - 0.2) / (0.6 - 0.2))

    # 0.4–0.7 Inhaltswort-Anteil
    content_norm = clamp01((content_share - 0.4) / (0.7 - 0.4))
    dims["lexical_diversity"] = 0.7 * mattr_norm + 0.3 * content_norm

    # 4) Kohäsion
    conn_density = coh_feats.get("connector_density_per_100_tokens", 0.0) if coh_feats else 0.0
    # einfache Normierung: 0–10 Konnektoren/100 Tokens
    conn_norm = clamp01(conn_density / 10.0)

    if overlap is not None:
        ov = overlap.get("avg_overlap", 0.0)
        # 0.0–0.5 Jaccard-Overlap
        overlap_norm = clamp01(ov / 0.5)
    else:
        overlap_norm = 0.0

    dims["cohesion"] = 0.5 * conn_norm + 0.5 * overlap_norm

    # 5) Textschwierigkeit (Lesbarkeit + Wortfrequenz) – höher = schwieriger
    if lix is not None:
        lix_value = lix.get("lix", 0.0)
        # 20 (leicht) – 60 (schwer)
        lix_norm = clamp01((lix_value - 20.0) / (60.0 - 20.0))
    else:
        lix_norm = 0.0

    if freq_feats is not None:
        freq_difficulty = freq_feats.get("difficulty_score", 0.0)
        rare_share = freq_feats.get("rare_word_share", 0.0)
        # Rare words boost: bis zu 0.2 extra, wenn > 20% seltene Wörter
        rare_boost = clamp01(rare_share / 0.2) * 0.2
        freq_score = clamp01(freq_difficulty + rare_boost)
        # Kombiniere LIX (40%) und Wortfrequenz (60%)
        dims["text_difficulty"] = 0.4 * lix_norm + 0.6 * freq_score
    else:
        dims["text_difficulty"] = lix_norm

    # 6) Register / Informalität (grob)
    pron_share = pronouns.get("share_pronouns", 0.0) if pronouns else 0.0
    # 0.05–0.20 Pronomen-Anteil
    pron_norm = clamp01((pron_share - 0.05) / (0.2 - 0.05))

    direct_share = direct_speech.get("share_inside_quotes", 0.0) if direct_speech else 0.0
    # bis ca. 30% Tokens in direkter Rede
    direct_norm = clamp01(direct_share / 0.3)

    mp_density = mp_feats.get("modal_particle_density_per_100_tokens", 0.0) if mp_feats else 0.0
    # bis ca. 5 Modalpartikeln/100 Tokens
    mp_norm = clamp01(mp_density / 5.0)

    dims["register_informality"] = (pron_norm + direct_norm + mp_norm) / 3.0
    dims["written_formality"] = 1.0 - dims["register_informality"]

    return dims


# --- CEFR-Schätzer (basierend auf MERLIN-Ridge-Modell) ----------------------


WEIGHTS = {
    "grammar_accuracy":     0.0000,
    "syntactic_complexity": 0.1085,   # war -0.1085 -> jetzt positiv
    "lexical_diversity":    0.1116,   # war -0.1116 -> jetzt positiv
    "cohesion":             0.0972,
    "text_difficulty":      0.7111,
    "register_informality": 0.0000,   # war 0.0991 -> jetzt neutralisiert
}

INTERCEPT = 2.96999031945789

MEANS = {
    "grammar_accuracy":     1.000000,
    "syntactic_complexity": 0.297293,
    "lexical_diversity":    0.780302,
    "cohesion":             0.041663,
    "text_difficulty":      0.350778,
    "register_informality": 0.106771,
}

STDS = {
    "grammar_accuracy":     1.000000,
    "syntactic_complexity": 0.200858,
    "lexical_diversity":    0.044508,
    "cohesion":             0.052577,
    "text_difficulty":      0.256159,
    "register_informality": 0.076954,
}


def estimate_cefr_score_from_dims(dims: dict) -> float:
    """
    Kontinuierlicher Score, grob: 1~A1, 2~A2, 3~B1, 4~B2, 5~C1, 6~C2.
    """
    z = INTERCEPT
    for name, w in WEIGHTS.items():
        x = float(dims.get(name, 0.0))
        std = STDS.get(name, 0.0)
        if std > 0:
            x_scaled = (x - MEANS[name]) / std
        else:
            x_scaled = 0.0
        z += w * x_scaled

    # Auf 1..6 clampen
    if z < 1.0:
        z = 1.0
    elif z > 6.0:
        z = 6.0
    return z


def estimate_cefr_label_from_dims(dims: dict) -> str:
    """
    Mappt den Score auf eine CEFR-Stufe.
    Schwellen sind heuristisch und können später mit MERLIN-Verteilungen
    feinjustiert werden.
    """
    score = estimate_cefr_score_from_dims(dims)

    # Heuristische Bänder:
    #  <1.5   -> A1
    #  1.5–2.5 -> A2
    #  2.5–3.5 -> B1
    #  3.5–4.2 -> B2
    #  4.2–5.3 -> C1
    #  >=5.3   -> C2
    if score < 1.5:
        return "A1"
    elif score < 2.5:
        return "A2"
    elif score < 3.5:
        return "B1"
    elif score < 4.2:
        return "B2"
    elif score < 5.3:
        return "C1"
    else:
        return "C2"


# --- main (Visualizer) ------------------------------------------------------


if __name__ == "__main__":
    if len(sys.argv) < 2:
        print("Bitte eine Textdatei angeben, z.B.:")
        print("    py features_viewer.py input.txt")
        sys.exit(1)

    filename = sys.argv[1]
    text = read_text_from_file(filename)

    # 1) Tokenisierung & POS
    sentences = tokenize_and_split(text)
    tagged_sentences = pos_tag_sentences(sentences)

    num_sentences = len(tagged_sentences)
    num_tokens = count_tokens(tagged_sentences)

    # 2) Grammatik
    matches = check_grammar_with_languagetool(text)
    num_issues = len(matches)
    errors_per_100_tokens = (num_issues / num_tokens * 100) if num_tokens > 0 else 0.0

    # 3) Komplexität
    lengths = sentence_lengths(tagged_sentences)
    finite_verbs = finite_verbs_per_sentence(tagged_sentences)
    subclauses = estimated_subclauses(tagged_sentences)
    complex_nps = complex_nps_per_sentence(tagged_sentences)
    vorfeld = vorfeld_lengths(tagged_sentences)

    # 4) Lexik & Kohäsion
    lex_feats = lexical_features(tagged_sentences)
    coh_feats = cohesion_features(tagged_sentences)
    overlap = sentence_overlap(tagged_sentences)
    pronouns = pronoun_stats(tagged_sentences)

    # 5) Zusätzliche Features
    token_seq = get_token_sequence(tagged_sentences)
    mattr = moving_average_ttr(token_seq, window_size=50)
    sent_types = sentence_type_counts(tagged_sentences)
    para_info = paragraph_stats(text)
    direct_speech = direct_speech_features(tagged_sentences)
    punct_feats = punctuation_features(tagged_sentences)
    lix = lix_index(text, num_sentences, num_tokens)
    mp_feats = modal_particle_features(tagged_sentences)
    freq_feats = word_frequency_features(tagged_sentences)  # ✅ NEU
    rare_words = get_rare_words_list(tagged_sentences)       # ✅ NEU


    # 6) Dimensionen 0–1
    dim_scores = compute_dimension_scores(
        num_tokens=num_tokens,
        num_issues=num_issues,
        lengths=lengths,
        finite_verbs=finite_verbs,
        subclauses=subclauses,
        complex_nps=complex_nps,
        vorfeld=vorfeld,
        lex_feats=lex_feats,
        coh_feats=coh_feats,
        overlap=overlap,
        mattr=mattr,
        pronouns=pronouns,
        direct_speech=direct_speech,
        lix=lix,
        mp_feats=mp_feats,
        freq_feats=freq_feats,
    )

    # --- Visualisierung -----------------------------------------------------

    print("=== Grunddaten ===")
    print(f"Sätze:          {num_sentences}")
    print(f"Tokens:         {num_tokens}")
    print()

    print("=== Grammatik (LanguageTool) ===")
    print(f"Issues gesamt:           {num_issues}")
    print(f"Fehler pro 100 Tokens:   {errors_per_100_tokens:.2f}")
    print()

    print("=== Syntaktische Komplexität (Heuristiken) ===")
    if lengths:
        print(f"Ø Satzlänge (Tokens):    {mean(lengths):.2f}")
        print(f"Min/Max Satzlänge:       {min(lengths)} / {max(lengths)}")
    print(f"Ø finite Verben/Satz:    {mean(finite_verbs):.2f}")
    print(f"Ø Nebensatz-Kandidaten:  {mean(subclauses):.2f}")
    print(f"Ø komplexe NPs/Satz:     {mean(complex_nps):.2f}")
    print()

    print("=== Wortstellungs-Highlight (Vorfeld) ===")
    if vorfeld:
        print(f"Ø Vorfeldlänge (Tokens): {mean(vorfeld):.2f}")
        print(f"Min/Max Vorfeldlänge:    {min(vorfeld)} / {max(vorfeld)}")
    else:
        print("Vorfeld:                  keine finiten Verben gefunden")
    print()

    print("=== Lesbarkeit (LIX) ===")
    if lix is not None:
        print(f"LIX:                    {lix['lix']:.1f}")
        print(
            f"Lange Wörter (>=7):     {lix['num_long_words']} "
            f"({lix['share_long_words']:.2f} Anteil)"
        )
    else:
        print("LIX:                    nicht berechenbar")
    print()

    print("=== Lexik ===")
    print(f"Unikate Wortformen:      {lex_feats['unique_tokens']}")
    print(f"Unikate Lemmata:         {lex_feats['unique_lemmas']}")
    print(f"TTR (Types/Tokens):      {lex_feats['ttr']:.3f}")
    print(f"Lemma-TTR:               {lex_feats['lemma_ttr']:.3f}")
    print(f"Anteil Inhaltswörter:    {lex_feats['content_word_share']:.3f}")
    if mattr is not None:
        print(
            f"MATTR (window={mattr['window_size']}): "
            f"{mattr['avg']:.3f} (min {mattr['min']:.3f}, "
            f"max {mattr['max']:.3f}, windows={mattr['num_windows']})"
        )
    else:
        print("MATTR:                    zu kurzer Text für gewähltes Fenster")
    print()

    print("=== Kohäsion (Konnektoren, einfache Liste) ===")
    print(f"Konnektoren gesamt:      {coh_feats['connector_count']}")
    print(f"Verschiedene Konnektoren:{coh_feats['connector_type_count']}")
    print(
        f"Dichte (pro 100 Tokens): "
        f"{coh_feats['connector_density_per_100_tokens']:.2f}"
    )
    if coh_feats["connectors_used"]:
        print("Verwendete Konnektoren:  " + ", ".join(coh_feats["connectors_used"]))
    print()

    print("=== Kohäsion (lexikalische Wiederaufnahme) ===")
    if overlap:
        print(f"Ø Overlap benachb. Sätze:{overlap['avg_overlap']:.3f}")
        print(
            f"Min/Max Overlap:         "
            f"{overlap['min_overlap']:.3f} / {overlap['max_overlap']:.3f}"
        )
        print(f"Satzpaare:               {overlap['num_pairs']}")
    else:
        print("Zu wenig Daten für Overlap.")
    print()

    print("=== Pronomen & Referenzen ===")
    print(f"Pronomen gesamt:        {pronouns['total_pronouns']}")
    print(f"Anteil Pronomen:        {pronouns['share_pronouns']:.3f}")
    print(f"3.-Person-Referenzen:   {pronouns['third_person_refs']}")
    print(f"nach Person:            {pronouns['by_person']}")
    print()

    print("=== Satztypen ===")
    print(f"Aussage-Sätze:           {sent_types['declarative']}")
    print(f"Fragesätze:              {sent_types['interrogative']}")
    print(f"Ausrufe:                 {sent_types['exclamative']}")
    print(f"Sonstige:                {sent_types['other']}")
    print()

    print("=== Absatzstruktur ===")
    print(f"Absätze:                 {para_info['num_paragraphs']}")
    print(
        f"Ø Absatzlänge (Zeichen): {para_info['avg_length_chars']:.1f} "
        f"(min {para_info['min_length_chars']}, "
        f"max {para_info['max_length_chars']})"
    )
    print()

    print("=== Direkte Rede ===")
    print(f"Tokens in Anführungsz.:  {direct_speech['tokens_inside_quotes']}")
    print(f"Anteil direkter Rede:    {direct_speech['share_inside_quotes']:.3f}")
    print()

    print("=== Interpunktion ===")
    print(f"Punktuationstokens:      {punct_feats['punctuation_tokens']}")
    print(
        f"Punktuation/100 Tokens:  "
        f"{punct_feats['punctuation_per_100_tokens']:.2f}"
    )
    print(f"Komma-Tokens:            {punct_feats['comma_tokens']}")
    print()

    print("=== Stilindikatoren (Modalpartikeln) ===")
    print(f"Modalpartikeln gesamt:   {mp_feats['modal_particles']}")
    print(f"Versch. Modalpartikeln:  {mp_feats['modal_particle_types']}")
    print(
        f"Dichte/100 Tokens:       "
        f"{mp_feats['modal_particle_density_per_100_tokens']:.2f}"
    )
    if mp_feats["modal_particles_used"]:
        print(
            "Verwendete Partikeln:    "
            + ", ".join(mp_feats["modal_particles_used"])
        )
    print()

    print()
    
    print("=== Wortfrequenz (SUBTLEX-DE) ===")
    print(f"Ø Zipf-Frequenz:        {freq_feats['avg_zipf']:.2f}")
    print(f"Median Zipf:            {freq_feats['median_zipf']:.2f}")
    print(f"Min/Max Zipf:           {freq_feats['min_zipf']:.2f} / {freq_feats['max_zipf']:.2f}")
    print(f"Seltene Wörter (Zipf<3):{freq_feats['rare_word_count']} ({freq_feats['rare_word_share']:.1%})")
    print(f"Sehr häufige (Zipf>5.5):{freq_feats['very_common_share']:.1%}")
    print(f"Unbekannte Wörter:      {freq_feats['unknown_count']} ({freq_feats['unknown_share']:.1%})")
    print(f"Schwierigkeitsscore:    {freq_feats['difficulty_score']:.3f}")
    if rare_words:
        print("Seltenste Wörter:")
        for w in rare_words[:10]:
            print(f"  - {w['word']} ({w['lemma']}, Zipf={w['zipf']})")

    print("=== Normalisierte Dimensionen (0–1) ===")
    for name, value in dim_scores.items():
        print(f"{name:22s}: {value:.3f}")
    print()

    

    # --- CEFR-Schätzung -----------------------------------------------------

    cefr_score = estimate_cefr_score_from_dims(dim_scores)
    cefr_label = estimate_cefr_label_from_dims(dim_scores)

    print("=== CEFR-Schätzung (heuristisch, MERLIN-basiert) ===")
    print(f"Score: {cefr_score:.2f}  ->  Level: {cefr_label}")
    print()
