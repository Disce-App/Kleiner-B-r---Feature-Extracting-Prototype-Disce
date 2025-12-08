import streamlit as st
from disce_core import analyze_text_for_ui  # oder disce_core, wenn du auslagerst


st.set_page_config(page_title="Disce CEFR-Demo", layout="wide")

st.title("Disce – CEFR-Demo für Schreibkompetenz")
st.write("Gib einen deutschen Text ein und erhalte eine grobe Niveauschätzung (MERLIN-basiert).")

# Eingabe
default_text = "Schreibe hier deinen deutschen Text rein..."
text = st.text_area("Text eingeben", value=default_text, height=300)

if st.button("Analysieren"):
    if not text.strip():
        st.warning("Bitte zuerst einen Text eingeben.")
    else:
        with st.spinner("Analysiere Text..."):
            result = analyze_text_for_ui(text)

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
                    continue  # sonst doppelt mit register_informality
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

        st.subheader("Kommentar zur Schätzung")
        st.write(
            "Diese Schätzung basiert auf einem Regressionsmodell, das auf dem MERLIN-Korpus "
            "kalibriert wurde (B1–C1-Lernertexte). Die Grammatikdimension wird aktuell "
            "nur diagnostisch berechnet, fließt aber **noch nicht** in den CEFR-Score ein."
        )
