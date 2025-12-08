import pandas as pd
from sklearn.preprocessing import StandardScaler
from sklearn.linear_model import Ridge

from features_viewer import (
    tokenize_and_split,
    pos_tag_sentences,
    count_tokens,
    sentence_lengths,
    finite_verbs_per_sentence,
    estimated_subclauses,
    complex_nps_per_sentence,
    vorfeld_lengths,
    lexical_features,
    cohesion_features,
    sentence_overlap,
    pronoun_stats,
    get_token_sequence,
    moving_average_ttr,
    direct_speech_features,
    lix_index,
    modal_particle_features,
    compute_dimension_scores,
    # check_grammar_with_languagetool,  # optional, siehe analyze_text
)


def analyze_text(text: str, use_grammar_check: bool = False) -> dict:
    """
    Führt die komplette Analyse-Pipeline für einen Text aus
    und gibt NUR die normalisierten Dimensionen (0–1) zurück.

    use_grammar_check=False: num_issues=0, um keine tausenden LanguageTool-API-Calls zu machen.
    """
    sentences = tokenize_and_split(text)
    tagged_sentences = pos_tag_sentences(sentences)

    num_sentences = len(tagged_sentences)
    num_tokens = count_tokens(tagged_sentences)

    # 1) Grammatikfehler
    if use_grammar_check:
        from features_viewer import check_grammar_with_languagetool
        matches = check_grammar_with_languagetool(text)
        num_issues = len(matches)
    else:
        num_issues = 0

    # 2) Komplexität
    lengths = sentence_lengths(tagged_sentences)
    finite_verbs = finite_verbs_per_sentence(tagged_sentences)
    subclauses = estimated_subclauses(tagged_sentences)
    complex_nps = complex_nps_per_sentence(tagged_sentences)
    vorfeld = vorfeld_lengths(tagged_sentences)

    # 3) Lexik & Kohäsion
    lex_feats = lexical_features(tagged_sentences)
    coh_feats = cohesion_features(tagged_sentences)
    overlap = sentence_overlap(tagged_sentences)
    pronouns = pronoun_stats(tagged_sentences)

    # 4) Weitere Features
    token_seq = get_token_sequence(tagged_sentences)
    mattr = moving_average_ttr(token_seq, window_size=50)
    direct_speech = direct_speech_features(tagged_sentences)
    lix = lix_index(text, num_sentences, num_tokens)
    mp_feats = modal_particle_features(tagged_sentences)

    dims = compute_dimension_scores(
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
    )

    return dims


def main():
    # 1) MERLIN-CSV laden
    df = pd.read_csv("merlin_de.csv", encoding="utf-8")

    records = []
    for i, row in df.iterrows():
        text = str(row["text"])
        cefr = str(row["cefr"]).strip().upper()  # z.B. "B1", "B2", ...

        dims = analyze_text(text, use_grammar_check=False)
        dims["cefr"] = cefr
        records.append(dims)

        if (i + 1) % 50 == 0:
            print(f"{i+1} Texte verarbeitet...")

    feats_df = pd.DataFrame(records)
    feats_df.to_csv("merlin_de_with_features.csv", index=False, encoding="utf-8")
    print("Feature-Tabelle gespeichert: merlin_de_with_features.csv")

    # 2) Modell-Training: CEFR als kontinuierliche Skala 1..6

    dim_names = [
        "grammar_accuracy",
        "syntactic_complexity",
        "lexical_diversity",
        "cohesion",
        "text_difficulty",
        "register_informality",
    ]

    # Nur Zeilen mit CEFR-Label
    feats_df = feats_df[feats_df["cefr"].notna()].copy()

    # X: deine Dimensionen
    X = feats_df[dim_names].values

    # y: CEFR als 1..6 (A1=1, A2=2, B1=3, B2=4, C1=5, C2=6)
    cefr_to_num = {"A1": 1, "A2": 2, "B1": 3, "B2": 4, "C1": 5, "C2": 6}
    feats_df = feats_df[feats_df["cefr"].isin(cefr_to_num.keys())].copy()
    X = feats_df[dim_names].values
    y = feats_df["cefr"].map(cefr_to_num).astype(float).values

    print("CEFR-Stufen im Korpus:", sorted(feats_df["cefr"].unique()))

    # Features standardisieren
    scaler = StandardScaler()
    X_scaled = scaler.fit_transform(X)

    # Ridge-Regression fitten
    reg = Ridge(alpha=1.0)
    reg.fit(X_scaled, y)

    coefs = reg.coef_
    intercept = reg.intercept_

    print("\nVorgeschlagene Gewichte (Ridge-Regression auf CEFR 1..6):")
    print("WEIGHTS = {")
    for name, w in zip(dim_names, coefs):
        print(f'    "{name}": {float(w):.4f},')
    print("}")
    print("INTERCEPT =", float(intercept))

    # Skalierungsparameter ausgeben, damit du sie im Produkt benutzen kannst
    print("\nFeature-Skalierung (Mittelwerte):")
    print("MEANS = {")
    for name, m in zip(dim_names, scaler.mean_):
        print(f'    "{name}": {float(m):.6f},')
    print("}")
    print("STDS = {")
    for name, s in zip(dim_names, scaler.scale_):
        print(f'    "{name}": {float(s):.6f},')
    print("}")


if __name__ == "__main__":
    main()
