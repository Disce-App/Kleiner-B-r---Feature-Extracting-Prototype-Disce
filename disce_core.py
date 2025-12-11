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
    sentence_type_counts,
    paragraph_stats,
    direct_speech_features,
    punctuation_features,
    lix_index,
    modal_particle_features,
    word_frequency_features,      # ✅ NEU
    get_rare_words_list,          # ✅ NEU
    passive_voice_features,
    negation_quantifier_features,
    dependency_tree_features,
    morphology_features, 
    compute_dimension_scores,
    estimate_cefr_score_from_dims,
    estimate_cefr_label_from_dims,
    verb_mood_features,
)


def analyze_text_for_ui(text: str, use_grammar_check: bool = False) -> dict:
    """
    Führt die komplette Analyse für ein Frontend aus und gibt ein Dict zurück,
    das leicht im UI verwendet werden kann.
    use_grammar_check=False: es werden KEINE LanguageTool-Requests gemacht.
    """
    # 1) Tokenisierung & POS
    sentences = tokenize_and_split(text)
    tagged_sentences = pos_tag_sentences(sentences)
    num_sentences = len(tagged_sentences)
    num_tokens = count_tokens(tagged_sentences)
    
    # ✅ DEBUG: Erste 15 Tags für UI-Anzeige sammeln
    debug_tags = []
    for sent in tagged_sentences:
        for tok in sent:
            debug_tags.append(tok)
            if len(debug_tags) >= 15:
                break
        if len(debug_tags) >= 15:
            break
    
    num_sentences = len(tagged_sentences)
    num_tokens = count_tokens(tagged_sentences)
    
    # ========== END DEBUG ============================
    
    num_sentences = len(tagged_sentences)


    # 2) Grammatik (für PoC: standardmäßig ausgeschaltet)
    if use_grammar_check:
        from features_viewer import check_grammar_with_languagetool
        matches = check_grammar_with_languagetool(text)
        num_issues = len(matches)
    else:
        matches = []
        num_issues = 0

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

    # 5) Weitere Features
    token_seq = get_token_sequence(tagged_sentences)
    mattr = moving_average_ttr(token_seq, window_size=50)
    sent_types = sentence_type_counts(tagged_sentences)
    para_info = paragraph_stats(text)
    direct_speech = direct_speech_features(tagged_sentences)
    punct_feats = punctuation_features(tagged_sentences)
    lix = lix_index(text, num_sentences, num_tokens)
    mp_feats = modal_particle_features(tagged_sentences)
    
    # 6) Wortfrequenz-Features ✅ NEU
    freq_feats = word_frequency_features(tagged_sentences)
    rare_words = get_rare_words_list(tagged_sentences)

    # 6b) Morphologie-Features (Tempus/Kasus) ✅ NEU
    morph_feats = morphology_features(tagged_sentences)

    # 6c) Verb-Modus (Konjunktiv) ✅ NEU
    mood_feats = verb_mood_features(tagged_sentences)

    # 6d) Passiv-Erkennung ✅ NEU
    passive_feats = passive_voice_features(tagged_sentences)

    # 6e) Negation & Quantoren ✅ NEU
    neg_quant_feats = negation_quantifier_features(tagged_sentences)

    # 7) Dependency-Baumtiefe (spaCy) ✅ NEU
    dep_tree = dependency_tree_features(text)

    # 8) Dimensionen
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
        freq_feats=freq_feats,  # ✅ NEU
        dep_tree=dep_tree, 
    )

    cefr_score = estimate_cefr_score_from_dims(dim_scores)
    cefr_label = estimate_cefr_label_from_dims(dim_scores)

    return {
        "num_sentences": num_sentences,
        "num_tokens": num_tokens,
        "num_issues": num_issues,
        "errors_per_100": errors_per_100_tokens,
        "dims": dim_scores,
        "cefr_score": cefr_score,
        "cefr_label": cefr_label,
        "lex_feats": lex_feats,
        "coh_feats": coh_feats,
        "overlap": overlap,
        "pronouns": pronouns,
        "sent_types": sent_types,
        "para_info": para_info,
        "direct_speech": direct_speech,
        "punct_feats": punct_feats,
        "lix": lix,
        "mp_feats": mp_feats,
        "freq_feats": freq_feats,      # ✅ NEU
        "rare_words": rare_words,       # ✅ NEU
        "passive_feats": passive_feats,
        "neg_quant_feats": neg_quant_feats,
        "mattr": mattr,
        "morph_feats": morph_feats,
        "dep_tree": dep_tree,
        "debug_tags": debug_tags,
        "mood_feats": mood_feats,
    }
