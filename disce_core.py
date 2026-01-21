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
    word_frequency_features,
    get_rare_words_list,
    passive_voice_features,
    negation_quantifier_features,
    dependency_tree_features,
    morphology_features,
    compute_dimension_scores,
    estimate_cefr_score_from_dims,
    estimate_cefr_label_from_dims,
    verb_mood_features,
    CONNECTOR_LIST,
    MODAL_PARTICLES,
    mean,
)


def build_sentence_data(sentences, tagged_sentences, dep_tree):
    sentence_texts = [
        " ".join(tok.text for tok in sent)
        for sent in sentences
    ]

    tree_depths = None
    if dep_tree is not None:
        tree_depths = dep_tree.get("sent_tree_depths")

    sentence_data = []
    for i, (sent_tokens, tagged) in enumerate(zip(sentences, tagged_sentences)):
        length = len(tagged)

        connector_count = 0
        modal_particle_count = 0
        for token_tuple in tagged:
            if len(token_tuple) < 1:
                continue
            word = token_tuple[0].lower()
            if word in CONNECTOR_LIST:
                connector_count += 1
            if word in MODAL_PARTICLES:
                modal_particle_count += 1

        depth = None
        if tree_depths is not None:
            max_idx = min(len(tree_depths), len(sentences))
            if i < max_idx:
                depth = tree_depths[i]

        sentence_data.append({
            "index": i,
            "text": sentence_texts[i],
            "length": length,
            "connector_count": connector_count,
            "modal_particle_count": modal_particle_count,
            "tree_depth": depth,
        })

    return sentence_data


def select_hotspots(sentence_data, max_per_type=3, max_total=10):
    """
    Wählt Sätze aus, die für Feedback & Übungen spannend sind.
    """
    if not sentence_data:
        return []

    reasons_by_index = {d["index"]: [] for d in sentence_data}

    # 1) Lange Sätze
    sorted_by_length = sorted(sentence_data, key=lambda d: d["length"], reverse=True)
    for d in sorted_by_length[:max_per_type]:
        reasons_by_index[d["index"]].append("long_sentence")

    # 2) Tiefe Sätze
    with_depth = [d for d in sentence_data if d.get("tree_depth") is not None]
    sorted_by_depth = sorted(with_depth, key=lambda d: d["tree_depth"], reverse=True)
    for d in sorted_by_depth[:max_per_type]:
        reasons_by_index[d["index"]].append("deep_tree")

    # 3) Kohäsions-Schwachstellen
    for d in sentence_data:
        if d["connector_count"] == 0 and d["length"] >= 15:
            reasons_by_index[d["index"]].append("low_cohesion_no_connectors")

    # 4) Informelle Sätze
    for d in sentence_data:
        if d["modal_particle_count"] >= 2:
            reasons_by_index[d["index"]].append("many_modal_particles")

    hotspots = []
    for d in sentence_data:
        reasons = reasons_by_index[d["index"]]
        if not reasons:
            continue
        hotspot = {
            "sentence_index": d["index"],
            "sentence_text": d["text"],
            "reasons": reasons,
            "features": {
                "length": d["length"],
                "connector_count": d["connector_count"],
                "modal_particle_count": d["modal_particle_count"],
                "tree_depth": d["tree_depth"],
            },
        }
        hotspots.append(hotspot)

    hotspots.sort(
        key=lambda h: (len(h["reasons"]), h["features"]["length"]),
        reverse=True,
    )

    return hotspots[:max_total]


def build_metrics_summary(
    text,
    num_sentences,
    num_tokens,
    lengths,
    subclauses,
    complex_nps,
    vorfeld,
    lex_feats,
    coh_feats,
    overlap,
    lix,
    freq_feats,
    dim_scores,
    cefr_score,
    cefr_label,
    dep_tree,
    morph_feats,
    mood_feats,
    passive_feats,
    neg_quant_feats,
):
    """
    Baut ein kompaktes, LLM-freundliches Summary-Objekt der wichtigsten Metriken.
    """
    avg_sentence_length = mean(lengths) if lengths else 0.0
    avg_subclauses = mean(subclauses) if subclauses else 0.0
    avg_complex_nps = mean(complex_nps) if complex_nps else 0.0
    avg_vorfeld = mean(vorfeld) if vorfeld else 0.0

    dep_info = dep_tree or {}
    passive_info = passive_feats or {}
    negq_info = neg_quant_feats or {}
    morph_info = morph_feats or {}
    mood_info = mood_feats or {}
    lex_info = lex_feats or {}
    freq_info = freq_feats or {}
    coh_info = coh_feats or {}
    overlap_info = overlap or {}

    summary = {
        "cefr": {
            "score": cefr_score,
            "label": cefr_label,
        },
        "dims": dim_scores,
        "text_stats": {
            "num_sentences": num_sentences,
            "num_tokens": num_tokens,
            "avg_sentence_length": avg_sentence_length,
        },
        "syntax": {
            "avg_sentence_length": avg_sentence_length,
            "avg_subclauses_per_sentence": avg_subclauses,
            "avg_complex_nps_per_sentence": avg_complex_nps,
            "avg_vorfeld_length": avg_vorfeld,
            "avg_tree_depth": dep_info.get("avg_tree_depth", 0.0),
            "passive_ratio": passive_info.get("passive_ratio", 0.0),
            "oblique_case_ratio": morph_info.get("oblique_case_ratio", 0.0),
        },
        "lexicon": {
            "ttr": lex_info.get("ttr", 0.0),
            "lemma_ttr": lex_info.get("lemma_ttr", 0.0),
            "content_word_share": lex_info.get("content_word_share", 0.0),
            "avg_zipf": freq_info.get("avg_zipf", 0.0),
            "rare_word_share": freq_info.get("rare_word_share", 0.0),
            "difficulty_score": freq_info.get("difficulty_score", 0.0),
        },
        "discourse": {
            "connector_density_per_100_tokens": coh_info.get(
                "connector_density_per_100_tokens", 0.0
            ),
            "avg_overlap": overlap_info.get("avg_overlap", 0.0),
        },
        "style": {
            "register_informality": dim_scores.get("register_informality", 0.0),
            "written_formality": dim_scores.get("written_formality", 0.0),
            "modal_particle_density_per_100_tokens": None,
            "subjunctive_share": mood_info.get("subjunctive_share", 0.0),
            "hedging_ratio": negq_info.get("hedging_ratio", 0.0),
            "assertion_strength": negq_info.get("assertion_strength", 0.0),
        },
        "readability": {
            "lix": lix.get("lix") if lix else None,
            "share_long_words": lix.get("share_long_words") if lix else None,
        },
        "passive": {
            "total_passive": passive_info.get("total_passive", 0),
            "passive_ratio": passive_info.get("passive_ratio", 0.0),
            "vorgangspassiv": passive_info.get("vorgangspassiv", 0),
            "zustandspassiv": passive_info.get("zustandspassiv", 0),
            "modalpassiv": passive_info.get("modalpassiv", 0),
        },
        "negation_quantifiers": {
            "negation_per_100": negq_info.get("negation_per_100", 0.0),
            "quantifier_per_100": negq_info.get("quantifier_per_100", 0.0),
            "hedging_ratio": negq_info.get("hedging_ratio", 0.0),
            "assertion_strength": negq_info.get("assertion_strength", 0.0),
        },
    }

    return summary


def build_disce_metrics(metrics_summary: dict, context: dict | None = None) -> dict:
    """
    Baut ein DisceMetrics-Objekt für den Bonsai-Visualizer.
    """
    context = context or {}

    dims = metrics_summary.get("dims", {})
    cefr = metrics_summary.get("cefr", {})
    text_stats = metrics_summary.get("text_stats", {})

    raw_score = float(cefr.get("score", 3.5))
    cefr_level = int(round(1 + (raw_score - 2.5) * (3 / 3.5)))
    cefr_level = max(1, min(4, cefr_level))

    writing_score = float(dims.get("lexical_diversity", 0.7))
    cohesion_score = float(dims.get("cohesion", 0.4))
    difficulty = float(dims.get("text_difficulty", 0.5))

    task_exam_fit = 1.0 - abs(difficulty - 0.6)

    goal_progress = context.get("goal_progress")
    if goal_progress is None:
        ntok = text_stats.get("num_tokens", 0)
        synt_comp = float(dims.get("syntactic_complexity", 0.3))
        goal_progress = max(0.1, min(1.0, (ntok / 400.0) * 0.4 + synt_comp * 0.6))

    engagement_streak = int(context.get("engagement_streak", 0))
    milestones_achieved = int(context.get("milestones_achieved", 0))
    session_completion_rate = float(context.get("session_completion_rate", 0.0))
    consistency_score = float(context.get("consistency_score", 0.0))

    cross_skill_correlation = float(context.get("cross_skill_correlation", 0.7))
    readiness_velocity = float(context.get("readiness_velocity", 0.4))
    weekly_delta = float(context.get("weekly_delta", 0.05))

    speaking_score = float(context.get("speaking_score", writing_score * 0.9))
    listening_score = float(context.get("listening_score", writing_score * 0.9))
    reading_score = float(context.get("reading_score", writing_score * 1.0))

    exam_ready = bool(context.get("exam_ready", False))
    presentation_ready = bool(context.get("presentation_ready", False))
    interview_ready = bool(context.get("interview_ready", False))
    authority_ready = bool(context.get("authority_ready", False))

    return {
        "level_match": float(context.get("level_match", 0.7)),
        "prosody_intelligibility": float(context.get("prosody_intelligibility", 0.7)),
        "sentence_cohesion": cohesion_score,
        "task_exam_fit": task_exam_fit,
        "goal_progress": goal_progress,
        "speaking_score": speaking_score,
        "writing_score": writing_score,
        "listening_score": listening_score,
        "reading_score": reading_score,
        "engagement_streak": engagement_streak,
        "session_completion_rate": session_completion_rate,
        "consistency_score": consistency_score,
        "exam_ready": exam_ready,
        "presentation_ready": presentation_ready,
        "interview_ready": interview_ready,
        "authority_ready": authority_ready,
        "milestones_achieved": milestones_achieved,
        "cefr_level": cefr_level,
        "cross_skill_correlation": cross_skill_correlation,
        "readiness_velocity": readiness_velocity,
        "weekly_delta": weekly_delta,
    }


def analyze_text_for_ui(text: str, use_grammar_check: bool = False) -> dict:
    """
    Führt die komplette Analyse für ein Frontend aus und gibt ein Dict zurück,
    das leicht im UI verwendet werden kann.
    """
    # 1) Tokenisierung & POS
    sentences = tokenize_and_split(text)
    tagged_sentences = pos_tag_sentences(sentences)
    num_sentences = len(tagged_sentences)
    num_tokens = count_tokens(tagged_sentences)

    # DEBUG: Erste 15 Tags für UI-Anzeige sammeln
    debug_tags = []
    for sent in tagged_sentences:
        for tok in sent:
            debug_tags.append(tok)
            if len(debug_tags) >= 15:
                break
        if len(debug_tags) >= 15:
            break

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

    # 6) Wortfrequenz-Features
    freq_feats = word_frequency_features(tagged_sentences)
    rare_words = get_rare_words_list(tagged_sentences)

    # 6b) Morphologie-Features (Tempus/Kasus)
    morph_feats = morphology_features(tagged_sentences)

    # 6c) Verb-Modus (Konjunktiv)
    mood_feats = verb_mood_features(tagged_sentences)

    # 6d) Passiv-Erkennung
    passive_feats = passive_voice_features(tagged_sentences)

    # 6e) Negation & Quantoren
    neg_quant_feats = negation_quantifier_features(tagged_sentences)

    # 7) Dependency-Baumtiefe (spaCy)
    dep_tree = dependency_tree_features(text)

    # 7b) Satzdaten + Hotspots (für LLM & UI)
    sentence_data = build_sentence_data(sentences, tagged_sentences, dep_tree)
    hotspots = select_hotspots(sentence_data)

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
        freq_feats=freq_feats,
        dep_tree=dep_tree,
    )

    cefr_score = estimate_cefr_score_from_dims(dim_scores)
    cefr_label = estimate_cefr_label_from_dims(dim_scores)

    # 9) Kompaktes Metrics-Summary für LLM / Reports
    metrics_summary = build_metrics_summary(
        text=text,
        num_sentences=num_sentences,
        num_tokens=num_tokens,
        lengths=lengths,
        subclauses=subclauses,
        complex_nps=complex_nps,
        vorfeld=vorfeld,
        lex_feats=lex_feats,
        coh_feats=coh_feats,
        overlap=overlap,
        lix=lix,
        freq_feats=freq_feats,
        dim_scores=dim_scores,
        cefr_score=cefr_score,
        cefr_label=cefr_label,
        dep_tree=dep_tree,
        morph_feats=morph_feats,
        mood_feats=mood_feats,
        passive_feats=passive_feats,
        neg_quant_feats=neg_quant_feats,
    )
    disce_metrics = build_disce_metrics(metrics_summary, context={})

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
        "freq_feats": freq_feats,
        "rare_words": rare_words,
        "passive_feats": passive_feats,
        "neg_quant_feats": neg_quant_feats,
        "mattr": mattr,
        "morph_feats": morph_feats,
        "dep_tree": dep_tree,
        "debug_tags": debug_tags,
        "mood_feats": mood_feats,
        "sentence_data": sentence_data,
        "hotspots": hotspots,
        "metrics_summary": metrics_summary,
        "disce_metrics": disce_metrics,
    }


# ============================================================
# API-Interface für externe Systeme (Großer Bär, Make.com, LLM)
# ============================================================

def analyze_text_for_llm(text: str, context: dict | None = None) -> dict:
    """
    Schlankes, stabiles Analyse-Interface für andere Systeme.
    Wrapper um analyze_text_for_ui – extrahiert nur die LLM-relevanten Teile.
    """
    context = context or {}

    # Volle Analyse durchführen
    ui_result = analyze_text_for_ui(text)

    # Nur die relevanten Teile extrahieren
    return {
        "original_text": text,
        "context": context,
        "metrics_summary": ui_result.get("metrics_summary", {}),
        "hotspots": ui_result.get("hotspots", []),
        "cefr": {
            "score": ui_result.get("cefr_score"),
            "label": ui_result.get("cefr_label"),
        },
        "disce_metrics": ui_result.get("disce_metrics", {}),
    }
