import streamlit as st

from disce_core import analyze_text_for_ui
from bonsai_disce_tree import generate_disce_bonsai_figure


# -------------------------------------------------------------------
# Page-Konfiguration
# -------------------------------------------------------------------

st.set_page_config(page_title="Disce CEFR-Demo", layout="wide")
st.title("Disce CEFR-Demo für Schreibkompetenz")
st.write(
    "Gib einen deutschen Text ein und erhalte eine grobe Niveauschätzung "
    "(MERLIN-basiert) plus Profil über mehrere Dimensionen."
)

# Debug-Schalter in der Sidebar
st.sidebar.header("Debug")
debug_mode = st.sidebar.checkbox("Debug-Modus aktivieren", value=False)

# -------------------------------------------------------------------
# Kontext-Auswahl
# -------------------------------------------------------------------

st.subheader("Kontext des Textes")

context_options = [
    "Prüfung – B2/C1/C2-Bereitschaft (realistische Aufgaben)",
    "Präsentation – Struktur, Timing, souveräne Q&A‑Phase",
    "Interview – klare, knappe Antworten; Register passend zur Situation",
    "Behörde – höflich, aber bestimmt (Klärung & Lösungen)",
    "Alltag – natürliches, erwachsenes Deutsch im echten Leben",
    "Essay – argumentativ / reflektierend",
    "Akademischer Essay / Hausarbeit",
    "Freies Schreiben / Tagebuch / Reflexion",
    "Anderer Kontext …",
]

selected_context = st.selectbox(
    "In welchem Kontext ist der Text entstanden?",
    options=context_options,
    index=0,
)

if selected_context == "Anderer Kontext …":
    context_detail = st.text_input(
        "Kontext kurz beschreiben",
        placeholder="z.B. E-Mail an Professorin, Blogartikel, LinkedIn-Post …",
    )
else:
    context_detail = st.text_input(
        "Optional: Kontext genauer beschreiben",
        value="",
        placeholder="z.B. B2-Telc-Vorbereitung, interne Projektpräsentation, Masterbewerbung …",
    )

# -------------------------------------------------------------------
# Texteingabe
# -------------------------------------------------------------------

default_text = "Schreibe hier deinen deutschen Text rein..."
text = st.text_area("Text eingeben", value=default_text, height=300)

if st.button("Analysieren"):
    if not text.strip():
        st.warning("Bitte zuerst einen Text eingeben.")
    else:
        with st.spinner("Analysiere Text..."):
            result = analyze_text_for_ui(text)

        # Kontext ans Result anhängen (für UI / spätere Logik)
        result["context"] = {
            "selected": selected_context,
            "detail": context_detail.strip() or None,
        }

        # Hauptergebnis (CEFR)
        st.success(
            f"Fertig! Geschätztes Niveau: **{result['cefr_label']}** "
            f"(Score: {result['cefr_score']:.2f})"
        )

        # -------------------------------------------------------------------
        # Haupt-Tabs
        # -------------------------------------------------------------------
        tab_ov, tab_dims, tab_struct, tab_lex, tab_prag, tab_hot = st.tabs(
            [
                "Übersicht",
                "Dimensionen",
                "Struktur & Grammatik",
                "Lexik & Frequenz",
                "Pragmatik",
                "Satz‑Hotspots",
            ]
        )

        dims = result.get("dims", {}) or {}

        # ---------------------------------------------------------------
        # Tab 1: Übersicht
        # ---------------------------------------------------------------
        with tab_ov:
            st.subheader("Übersicht")

            # Kontext anzeigen
            ctx = result.get("context", {})
            ctx_label = ctx.get("selected", "–")
            ctx_detail = ctx.get("detail")

            st.markdown("**Kontext**")
            if ctx_detail:
                st.write(f"{ctx_label} — {ctx_detail}")
            else:
                st.write(ctx_label)

            st.markdown("---")

            col1, col2, col3 = st.columns(3)
            with col1:
                st.metric("Sätze", result.get("num_sentences", 0))
            with col2:
                st.metric("Tokens", result.get("num_tokens", 0))
            with col3:
                lix = result.get("lix")
                if lix is not None:
                    st.metric("LIX", f"{lix['lix']:.1f}")
                else:
                    st.metric("LIX", "–")

            st.markdown("---")

            # Disce-Dimensionen kompakt
            st.markdown("**Disce‑Dimensionen (0–1)**")
            c1, c2, c3 = st.columns(3)
            c4, c5, c6 = st.columns(3)

            c1.metric("Grammatik", f"{dims.get('grammar_accuracy', 0.0):.3f}")
            c2.metric(
                "Syntaktische Komplexität",
                f"{dims.get('syntactic_complexity', 0.0):.3f}",
            )
            c3.metric(
                "Lexikalische Vielfalt",
                f"{dims.get('lexical_diversity', 0.0):.3f}",
            )
            c4.metric("Kohäsion", f"{dims.get('cohesion', 0.0):.3f}")
            c5.metric(
                "Textschwierigkeit",
                f"{dims.get('text_difficulty', 0.0):.3f}",
            )
            c6.metric(
                "Informalität",
                f"{dims.get('register_informality', 0.0):.3f}",
            )

            st.markdown("---")

            # Bonsai
            st.subheader("Bonsai‑Visualisierung (Prototype)")
            fig = generate_disce_bonsai_figure(result)
            st.pyplot(fig, use_container_width=True)

        # ---------------------------------------------------------------
        # Tab 2: Dimensionen
        # ---------------------------------------------------------------
        with tab_dims:
            st.subheader("Dimensionen (0–1)")

            st.write(
                "Die Skalen sind intern normiert (0–1). "
                "Sie dienen vor allem zum Vergleich zwischen Texten."
            )

            rows = [
                (
                    "Grammatik‑Genauigkeit",
                    "grammar_accuracy",
                    "Fehlerfreiheit, Stabilität der Formen.",
                ),
                (
                    "Syntaktische Komplexität",
                    "syntactic_complexity",
                    "Satzverschachtelung, Nebensätze, Relativsätze, Baumtiefe.",
                ),
                (
                    "Lexikalische Vielfalt",
                    "lexical_diversity",
                    "Varianz im Wortschatz (MATTR, Anteil Inhaltswörter).",
                ),
                (
                    "Kohäsion",
                    "cohesion",
                    "Verknüpfung zwischen Sätzen (Konnektoren, Wiederaufnahme).",
                ),
                (
                    "Textschwierigkeit",
                    "text_difficulty",
                    "Lesbarkeit (LIX) + Wortfrequenz (SUBTLEX‑DE).",
                ),
                (
                    "Register‑Informalität",
                    "register_informality",
                    "0 = eher formell, 1 = eher informell (Pronomen, direkte Rede, "
                    "Modalpartikeln).",
                ),
            ]

            for label, key, desc in rows:
                val = dims.get(key, 0.0)
                with st.expander(f"{label} — {val:.3f}", expanded=False):
                    st.write(desc)

        # ---------------------------------------------------------------
        # Tab 3: Struktur & Grammatik
        # ---------------------------------------------------------------
        with tab_struct:
            st.subheader("Struktur & Grammatik")

            # Syntaktische Tiefe
            dep = result.get("dep_tree")
            with st.expander("Syntaktische Tiefe (spaCy)", expanded=True):
                if dep and dep.get("num_sents_parsed", 0) > 0:
                    st.write(
                        f"- Ø Baumtiefe: `{dep['avg_tree_depth']:.2f}` "
                        f"(Min: `{dep['min_tree_depth']}`, "
                        f"Max: `{dep['max_tree_depth']}`)"
                    )
                else:
                    st.write("- Keine Daten")

            # Morphologie
            morph = result.get("morph_feats", {}) or {}
            with st.expander("Morphologie (Tempus/Kasus)", expanded=False):
                if morph:
                    st.markdown("**Tempus**")
                    st.write(
                        f"- Präsens: `{morph['present']}` "
                        f"({morph['present_share']:.1%})"
                    )
                    st.write(
                        f"- Präteritum: `{morph['past']}` "
                        f"({morph['past_share']:.1%})"
                    )
                    st.write(
                        f"- Partizip II: `{morph['perfect']}` "
                        f"({morph['perfect_share']:.1%})"
                    )
                    st.write(
                        f"- Vergangenheits-Ratio: "
                        f"`{morph['past_tense_ratio']:.1%}`"
                    )

                    st.markdown("---")
                    st.markdown("**Kasus**")
                    st.write(
                        f"- Nominativ: `{morph['nominative']}` "
                        f"({morph['nominative_share']:.1%})"
                    )
                    st.write(
                        f"- Genitiv: `{morph['genitive']}` "
                        f"({morph['genitive_share']:.1%})"
                    )
                    st.write(
                        f"- Dativ: `{morph['dative']}` "
                        f"({morph['dative_share']:.1%})"
                    )
                    st.write(
                        f"- Akkusativ: `{morph['accusative']}` "
                        f"({morph['accusative_share']:.1%})"
                    )
                    st.write(
                        f"- Oblique-Ratio (Gen+Dat): "
                        f"`{morph['oblique_case_ratio']:.1%}`"
                    )
                else:
                    st.write("- Keine Daten")

            # Passiv
            pv = result.get("passive_feats", {}) or {}
            with st.expander("Passivformen", expanded=False):
                if pv and pv.get("total_clauses", 0) > 0:
                    st.write(f"- Vorgangspassiv: `{pv['vorgangspassiv']}`")
                    st.write(f"- Zustandspassiv: `{pv['zustandspassiv']}`")
                    st.write(f"- Modalpassiv: `{pv['modalpassiv']}`")
                    st.write(
                        f"- **Passiv gesamt: `{pv['total_passive']}` "
                        f"({pv['passive_ratio']:.1%})**"
                    )
                    if pv.get("passive_instances"):
                        with st.expander("Beispiele", expanded=False):
                            for ex in pv["passive_instances"]:
                                st.write(f"- {ex}")
                else:
                    st.write("- Keine Daten")

            # Verb-Modus
            mood = result.get("mood_feats", {}) or {}
            with st.expander("Verb‑Modus", expanded=False):
                if mood and mood.get("total_finite_verbs", 0) > 0:
                    st.write(
                        f"- Indikativ: `{mood['indicative']}` "
                        f"({mood['indicative_share']:.1%})"
                    )
                    st.write(
                        f"- Konjunktiv I: `{mood['subjunctive_1']}` "
                        f"({mood['subjunctive_1_share']:.1%})"
                    )
                    st.write(
                        f"- Konjunktiv II: `{mood['subjunctive_2']}` "
                        f"({mood['subjunctive_2_share']:.1%})"
                    )
                    st.write(
                        f"- würde‑Form: `{mood['wuerde_form']}` "
                        f"({mood['wuerde_form_share']:.1%})"
                    )
                    st.write(
                        f"- Imperativ: `{mood['imperative']}` "
                        f"({mood['imperative_share']:.1%})"
                    )
                    st.write(
                        f"- **Konjunktiv gesamt: "
                        f"`{mood['total_subjunctive']}` "
                        f"({mood['subjunctive_share']:.1%})**"
                    )
                else:
                    st.write("- Keine Daten")

        # ---------------------------------------------------------------
        # Tab 4: Lexik & Frequenz
        # ---------------------------------------------------------------
        with tab_lex:
            st.subheader("Lexik & Frequenz")

            lex = result.get("lex_feats", {}) or {}
            freq = result.get("freq_feats", {}) or {}
            rare_words = result.get("rare_words", []) or []

            col1, col2 = st.columns(2)
            with col1:
                st.markdown("**Lexikalische Kennzahlen**")
                st.write(f"- Unikate Wortformen: `{lex.get('unique_tokens', 0)}`")
                st.write(f"- Unikate Lemmata: `{lex.get('unique_lemmas', 0)}`")
                st.write(f"- TTR: `{lex.get('ttr', 0.0):.3f}`")
                st.write(f"- Lemma-TTR: `{lex.get('lemma_ttr', 0.0):.3f}`")

            with col2:
                st.markdown("**Wortfrequenz (SUBTLEX‑DE)**")
                st.write(f"- Ø Zipf-Frequenz: `{freq.get('avg_zipf', 0.0):.2f}`")
                st.write(
                    f"- Seltene Wörter (Zipf<3): "
                    f"`{freq.get('rare_word_count', 0)}` "
                    f"({freq.get('rare_word_share', 0.0):.1%})"
                )
                st.write(
                    f"- Sehr häufige (Zipf>5.5): "
                    f"`{freq.get('very_common_share', 0.0):.1%}`"
                )
                st.write(
                    f"- Schwierigkeitsscore: "
                    f"`{freq.get('difficulty_score', 0.0):.3f}`"
                )

            with st.expander("Seltenste Wörter im Text", expanded=False):
                if not rare_words:
                    st.write("Keine Liste verfügbar.")
                else:
                    for w in rare_words[:10]:
                        st.write(
                            f"- **{w['word']}** "
                            f"({w['lemma']}, Zipf={w['zipf']})"
                        )

        # ---------------------------------------------------------------
        # Tab 5: Pragmatik
        # ---------------------------------------------------------------
        with tab_prag:
            st.subheader("Pragmatik: Negation, Quantoren, Hedging")

            nq = result.get("neg_quant_feats", {}) or {}

            if nq:
                col_neg, col_quant = st.columns(2)
                with col_neg:
                    st.write(
                        f"**Negation:** `{nq['negation']}` "
                        f"({nq['negation_per_100']:.1f} pro 100 Tokens)"
                    )
                    st.write(f"**Restriktive:** `{nq['restrictive']}`")
                with col_quant:
                    st.write(
                        f"**Universelle Q.:** "
                        f"`{nq['universal_quantifier']}`"
                    )
                    st.write(
                        f"**Partielle Q.:** "
                        f"`{nq['partial_quantifier']}`"
                    )

                st.write(
                    f"- Hedging-Ratio: `{nq['hedging_ratio']:.1%}` "
                    "(hoch = vorsichtig)"
                )
                st.write(
                    f"- Assertion-Strength: "
                    f"`{nq['assertion_strength']:.1%}` "
                    "(hoch = starke Behauptungen)"
                )

                examples = nq.get("examples", {}) or {}
                has_examples = any(examples.get(k) for k in examples)
                if has_examples:
                    with st.expander("Beispiele", expanded=False):
                        for category, words in examples.items():
                            if not words:
                                continue
                            label = {
                                "negation": "Negation",
                                "universal_quantifier": "Universell",
                                "partial_quantifier": "Partiell",
                                "restrictive": "Restriktiv",
                            }.get(category, category)
                            st.write(f"**{label}:** {', '.join(words)}")
            else:
                st.write("- Keine Daten")

        # ---------------------------------------------------------------
        # Tab 6: Satz-Hotspots
        # ---------------------------------------------------------------
        with tab_hot:
            st.subheader("Satz‑Hotspots (für Feedback)")

            hotspots = result.get("hotspots", []) or []
            if not hotspots:
                st.write("- Keine Hotspots gefunden.")
            else:
                for h in hotspots:
                    header = (
                        f"Satz {h['sentence_index']} – "
                        f"Gründe: {', '.join(h['reasons'])}"
                    )
                    with st.expander(header, expanded=False):
                        st.write(h["sentence_text"])
                        feats = h.get("features", {}) or {}
                        st.markdown(
                            f"Länge: {feats.get('length', 0)}, "
                            f"Konnektoren: {feats.get('connector_count', 0)}, "
                            f"Modalpartikeln: {feats.get('modal_particle_count', 0)}"
                        )

        # ---------------------------------------------------------------
        # Kommentar zur Schätzung
        # ---------------------------------------------------------------
        st.markdown("---")
        st.subheader("Kommentar zur Schätzung")
        st.write(
            "Diese Schätzung basiert auf einem Regressionsmodell, das auf dem "
            "MERLIN‑Korpus kalibriert wurde (B1–C1‑Lernertexte). "
            "Die Grammatikdimension wird aktuell nur diagnostisch berechnet, "
            "fließt aber **noch nicht** in den CEFR‑Score ein."
        )

        # -------------------------------------------------------------------
        # DEBUG-Bereich (nur wenn debug_mode)
        # -------------------------------------------------------------------
        if debug_mode:
            st.markdown("---")
            st.subheader("Debug-Ansicht Roh-Features")

            dbg1, dbg2, dbg3, dbg4 = st.tabs(
                [
                    "Grammatik & Dimensionen",
                    "Lexik & Frequenz",
                    "Kohäsion & Referenzen",
                    "Struktur & Satztypen",
                ]
            )

            with dbg1:
                st.markdown("**Grammatik (LanguageTool)**")
                st.write(f"- Issues gesamt: `{result.get('num_issues', 0)}`")
                st.write(
                    f"- Fehler pro 100 Tokens: "
                    f"`{result.get('errors_per_100', 0.0):.2f}`"
                )
                st.markdown("**Normalisierte Dimensionen (0–1)**")
                for name, val in dims.items():
                    st.write(f"- `{name}`: **{val:.3f}**")

                st.markdown("**Morphologie (Tempus/Kasus)**")
                morph = result.get("morph_feats", {}) or {}
                if morph:
                    st.json(morph)
                else:
                    st.write("_Keine Morphologie-Daten._")

                st.markdown("**Verb-Modus (Konjunktiv)**")
                mood = result.get("mood_feats", {}) or {}
                if mood:
                    st.json(mood)
                else:
                    st.write("_Keine Modus-Daten._")

                st.markdown("**Negation & Quantoren**")
                nq = result.get("neg_quant_feats", {}) or {}
                if nq:
                    st.json(nq)
                else:
                    st.write("_Keine Negationsdaten._")

            with dbg2:
                st.markdown("**Lexik**")
                st.json(result.get("lex_feats", {}))
                st.markdown("**Wortfrequenz (SUBTLEX‑DE)**")
                st.json(result.get("freq_feats", {}))
                st.markdown("**Seltenste Wörter**")
                st.json(result.get("rare_words", []))

            with dbg3:
                st.markdown("**Kohäsion (Konnektoren)**")
                st.json(result.get("coh_feats", {}))
                st.markdown("**Pronomen & Referenzen**")
                st.json(result.get("pronouns", {}))

            with dbg4:
                st.markdown("**Dependency‑Bäume**")
                st.json(result.get("dep_tree", {}))
                st.markdown("**Satztypen / Absatzstruktur / Interpunktion**")
                st.json(
                    {
                        "sent_types": result.get("sent_types", {}),
                        "paragraphs": result.get("paragraphs", {}),
                        "punctuation": result.get("punct_feats", {}),
                    }
                )
