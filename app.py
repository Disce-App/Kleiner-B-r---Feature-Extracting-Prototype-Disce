import streamlit as st
from disce_core import analyze_text_for_ui

st.set_page_config(page_title="Disce CEFR-Demo", layout="wide")

st.title("Disce – CEFR-Demo für Schreibkompetenz")
st.write("Gib einen deutschen Text ein und erhalte eine grobe Niveauschätzung (MERLIN-basiert).")

# 🔧 Debug-Schalter in der Sidebar
st.sidebar.header("Debug")
debug_mode = st.sidebar.checkbox("Debug-Modus aktivieren", value=False)

# Eingabe
default_text = "Schreibe hier deinen deutschen Text rein..."
text = st.text_area("Text eingeben", value=default_text, height=300)

if st.button("Analysieren"):
    if not text.strip():
        st.warning("Bitte zuerst einen Text eingeben.")
    else:
        with st.spinner("Analysiere Text..."):
            result = analyze_text_for_ui(text)

        # Hauptergebnis anzeigen
        st.success(f"Fertig! Geschätztes Niveau: **{result['cefr_label']}** "
                   f"(Score: {result['cefr_score']:.2f})")

        # Spaltenlayout
        col1, col2 = st.columns(2)

        with col1:
            st.subheader("Grunddaten")
            st.write(f"- Sätze: `{result['num_sentences']}`")
            st.write(f"- Tokens: `{result['num_tokens']}`")

            st.subheader("Dimensionen (0–1)")
            dims = result["dims"]
            for name, val in dims.items():
                if name == "written_formality":
                    continue
                st.write(f"- **{name}**: {val:.3f}")

        with col2:
            st.subheader("Lesbarkeit (LIX)")
            lix = result["lix"]
            if lix is not None:
                st.write(f"- LIX: `{lix['lix']:.1f}`")
                st.write(f"- Lange Wörter (>=7): `{lix['num_long_words']}` "
                         f"({lix['share_long_words']:.2f} Anteil)")
            else:
                st.write("- LIX: nicht berechenbar")

            st.subheader("Lexik")
            lex = result["lex_feats"]
            st.write(f"- Unikate Wortformen: `{lex['unique_tokens']}`")
            st.write(f"- Unikate Lemmata: `{lex['unique_lemmas']}`")
            st.write(f"- TTR: `{lex['ttr']:.3f}`")
            st.write(f"- Lemma-TTR: `{lex['lemma_ttr']:.3f}`")

            # Wortfrequenz-Sektion
            st.subheader("Wortfrequenz (SUBTLEX-DE)")
            freq = result["freq_feats"]
            st.write(f"- Ø Zipf-Frequenz: `{freq['avg_zipf']:.2f}`")
            st.write(f"- Seltene Wörter (Zipf<3): `{freq['rare_word_count']}` ({freq['rare_word_share']:.1%})")
            st.write(f"- Sehr häufige (Zipf>5.5): `{freq['very_common_share']:.1%}`")
            st.write(f"- Schwierigkeitsscore: `{freq['difficulty_score']:.3f}`")

            # Seltene Wörter anzeigen
            rare_words = result.get("rare_words", [])
            if rare_words:
                with st.expander("🔍 Seltenste Wörter im Text"):
                    for w in rare_words[:10]:
                        st.write(f"- **{w['word']}** ({w['lemma']}, Zipf={w['zipf']})")

        st.subheader("Kommentar zur Schätzung")
        st.write(
            "Diese Schätzung basiert auf einem Regressionsmodell, das auf dem MERLIN-Korpus "
            "kalibriert wurde (B1–C1-Lernertexte). Die Grammatikdimension wird aktuell "
            "nur diagnostisch berechnet, fließt aber **noch nicht** in den CEFR-Score ein."
        )

        # 🔧 DEBUG-BEREICH (NUR wenn debug_mode UND result existiert)
        if debug_mode:
            st.markdown("---")
            st.subheader("🔧 Debug-Ansicht – Roh-Features")

            tab1, tab2, tab3, tab4 = st.tabs(
                ["Grammatik & Dimensionen", "Lexik & Wortfrequenz", "Kohäsion & Referenzen", "Struktur & Satztypen"]
            )

            with tab1:
                st.markdown("**Grammatik (LanguageTool)**")
                st.write(f"- Issues gesamt: `{result['num_issues']}`")
                st.write(f"- Fehler pro 100 Tokens: `{result['errors_per_100']:.2f}`")

                st.markdown("**Normalisierte Dimensionen (0–1)**")
                for name, val in result["dims"].items():
                    st.write(f"- `{name}`: **{val:.3f}**")

            with tab2:
                st.markdown("**Lexikalische Basiswerte**")
                lex = result["lex_feats"]
                st.write(f"- Unikate Wortformen: `{lex['unique_tokens']}`")
                st.write(f"- Unikate Lemmata: `{lex['unique_lemmas']}`")
                st.write(f"- TTR: `{lex['ttr']:.3f}`")
                st.write(f"- Lemma-TTR: `{lex['lemma_ttr']:.3f}`")
                st.write(f"- Anteil Inhaltswörter: `{lex['content_word_share']:.3f}`")

                st.markdown("**Wortfrequenz (wordfreq)**")
                freq = result["freq_feats"]
                st.write(f"- Ø Zipf-Frequenz: `{freq['avg_zipf']:.2f}`")
                st.write(f"- Median Zipf: `{freq['median_zipf']:.2f}`")
                st.write(f"- Min/Max Zipf: `{freq['min_zipf']:.2f}` / `{freq['max_zipf']:.2f}`")
                st.write(f"- Seltene Wörter (Zipf<3): `{freq['rare_word_count']}` ({freq['rare_word_share']:.1%})")
                st.write(f"- Sehr häufige (Zipf>5.5): `{freq['very_common_share']:.1%}`")
                st.write(f"- Unbekannte Wörter: `{freq['unknown_count']}` ({freq['unknown_share']:.1%})")
                st.write(f"- Schwierigkeitsscore: `{freq['difficulty_score']:.3f}`")

                rare_words = result.get("rare_words", [])
                if rare_words:
                    st.markdown("**Seltenste Wörter:**")
                    st.table(rare_words[:20])

                st.markdown("**Dependency-Baumtiefe (spaCy)**")
                dep = result.get("dep_tree")
                if dep and dep.get("num_sents_parsed", 0) > 0:
                    st.write(f"- Ø Baumtiefe pro Satz: `{dep['avg_tree_depth']:.2f}`")
                    st.write(f"- Min/Max Baumtiefe: `{dep['min_tree_depth']}` / `{dep['max_tree_depth']}`")
                    st.write(f"- Sätze (spaCy): `{dep['num_sents_parsed']}`")
                else:
                    st.write("_Keine Daten (spaCy nicht geladen oder Fehler)._")

            with tab3:
                st.markdown("**Konnektoren**")
                coh = result["coh_feats"]
                st.write(f"- Konnektoren gesamt: `{coh['connector_count']}`")
                st.write(f"- Verschiedene Konnektoren: `{coh['connector_type_count']}`")
                st.write(f"- Dichte (pro 100 Tokens): `{coh['connector_density_per_100_tokens']:.2f}`")
                if coh["connectors_used"]:
                    st.write("Verwendete Konnektoren: " + ", ".join(coh["connectors_used"]))

                st.markdown("**Lexikalische Wiederaufnahme (Overlap)**")
                overlap = result["overlap"]
                if overlap:
                    st.write(f"- Ø Overlap benachbarter Sätze: `{overlap['avg_overlap']:.3f}`")
                    st.write(f"- Min/Max Overlap: `{overlap['min_overlap']:.3f}` / `{overlap['max_overlap']:.3f}`")
                    st.write(f"- Satzpaare: `{overlap['num_pairs']}`")
                else:
                    st.write("_Zu wenig Daten für Overlap._")

                st.markdown("**Pronomen & Referenzen**")
                pron = result["pronouns"]
                st.write(f"- Pronomen gesamt: `{pron['total_pronouns']}`")
                st.write(f"- Anteil Pronomen: `{pron['share_pronouns']:.3f}`")
                st.write(f"- 3.-Person-Referenzen: `{pron['third_person_refs']}`")
                st.json(pron["by_person"])

            with tab4:
                st.markdown("**Satztypen**")
                st.json(result["sent_types"])

                st.markdown("**Absatzstruktur**")
                st.json(result["para_info"])

                st.markdown("**Direkte Rede**")
                st.json(result["direct_speech"])

                st.markdown("**Interpunktion**")
                st.json(result["punct_feats"])

                st.markdown("**Modalpartikeln**")
                st.json(result["mp_feats"])
