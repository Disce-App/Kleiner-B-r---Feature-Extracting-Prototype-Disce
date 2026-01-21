# pages/grosser_baer.py
"""
Großer Bär – Speaking Coach UI
Streamlit-Seite für Audio-Aufnahme und Feedback.
"""

import streamlit as st
from datetime import datetime

# Großer Bär Imports
from grosser_baer import (
    get_task,
    get_task_choices,
    process_speaking_task,
    generate_feedback,
    format_feedback_markdown,
    SessionLogger,
)

# =============================================================================
# PAGE CONFIG
# =============================================================================

st.set_page_config(
    page_title="Großer Bär – Speaking Coach",
    page_icon="🐻",
    layout="wide",
)

# =============================================================================
# SESSION STATE INITIALISIERUNG
# =============================================================================

if "phase" not in st.session_state:
    st.session_state.phase = "select"  # select → record → feedback

if "selected_task_id" not in st.session_state:
    st.session_state.selected_task_id = None

if "audio_bytes" not in st.session_state:
    st.session_state.audio_bytes = None

if "transcript" not in st.session_state:
    st.session_state.transcript = None

if "feedback_result" not in st.session_state:
    st.session_state.feedback_result = None

if "recording_start" not in st.session_state:
    st.session_state.recording_start = None


# =============================================================================
# HELPER FUNCTIONS
# =============================================================================

def reset_session():
    """Setzt die Session zurück für neue Aufnahme."""
    st.session_state.phase = "select"
    st.session_state.selected_task_id = None
    st.session_state.audio_bytes = None
    st.session_state.transcript = None
    st.session_state.feedback_result = None
    st.session_state.recording_start = None


# =============================================================================
# HEADER
# =============================================================================

st.title("🐻 Großer Bär – Speaking Coach")
st.markdown(
    "Übe gesprochenes Deutsch mit strukturiertem Feedback. "
    "Wähle eine Aufgabe, nimm dich auf, und erhalte Analyse + Coaching."
)

# Sidebar
with st.sidebar:
    st.header("⚙️ Einstellungen")
    
    MOCK_MODE = st.checkbox(
        "Mock-Modus (ohne APIs)", 
        value=True,
        help="Aktiviert Beispiel-Transkripte und Mock-Feedback für Testing"
    )
    
    st.markdown("---")
    
    if st.button("🔄 Neue Session"):
        reset_session()
        st.rerun()
    
    st.markdown("---")
    st.caption("Großer Bär v0.1 – Prototype")


# =============================================================================
# PHASE 1: AUFGABE WÄHLEN
# =============================================================================

if st.session_state.phase == "select":
    st.header("1️⃣ Wähle deine Sprechaufgabe")
    
    # Task-Auswahl: get_task_choices() gibt Liste von (label, id) Tuples
    task_choices_list = get_task_choices()
    
    # Baue ein Dict: {label: id}
    task_choices = {label: tid for label, tid in task_choices_list}
    
    selected_label = st.selectbox(
        "Welche Situation möchtest du üben?",
        options=list(task_choices.keys()),
        index=0,
    )
    
    task_id = task_choices[selected_label]
    task = get_task(task_id)
    
    # Task-Details anzeigen
    with st.expander("📋 Aufgabendetails", expanded=True):
        st.markdown(f"**Szenario:** {task['situation']}")
        st.markdown(f"**Zielregister:** {task['register']}")
        st.markdown(f"**Zeitrahmen:** {task['time_seconds']} Sekunden")
        st.markdown("---")
        st.markdown("**Deine Aufgabe:**")
        st.info(task["task"])
        
        if task.get("example_phrases"):
            st.markdown("**Beispielphrasen:**")
            for phrase in task["example_phrases"]:
                st.markdown(f"- _{phrase}_")
    
    # Weiter-Button
    col1, col2, col3 = st.columns([1, 2, 1])
    with col2:
        if st.button("🎙️ Aufnahme starten", type="primary", use_container_width=True):
            st.session_state.selected_task_id = task_id
            st.session_state.phase = "record"
            st.session_state.recording_start = datetime.now()
            st.rerun()


# =============================================================================
# PHASE 2: AUFNAHME
# =============================================================================

elif st.session_state.phase == "record":
    st.header("2️⃣ Sprich jetzt!")
    
    task = get_task(st.session_state.selected_task_id)
    
    # Aufgabe anzeigen
    st.info(f"**Aufgabe:** {task['task']}")
    st.caption(f"⏱️ Ziel: {task['time_seconds']} Sekunden | Register: {task['register']}")
    
    # Meta-Prompt (Planungshinweis)
    if task.get("meta_prompts", {}).get("plan"):
        st.markdown(f"💡 *{task['meta_prompts']['plan']}*")
    
    st.markdown("---")
    
    # Audio-Aufnahme oder Mock-Modus
    if not MOCK_MODE:
        # Echter Modus: Audio-Aufnahme
        try:
            from audio_recorder_streamlit import audio_recorder
            
            st.markdown("### 🎙️ Klicke zum Aufnehmen:")
            
            audio_bytes = audio_recorder(
                text="🎙️ Klicken zum Aufnehmen",
                recording_color="#e74c3c",
                neutral_color="#3498db",
                icon_size="2x",
                pause_threshold=3.0,
                sample_rate=16000,
                key="speaking_recorder"
            )
            
            if audio_bytes:
                st.session_state.audio_bytes = audio_bytes
                st.success("✅ Aufnahme erhalten!")
                st.audio(audio_bytes, format="audio/wav")
                
                col1, col2 = st.columns(2)
                with col1:
                    if st.button("🔄 Nochmal aufnehmen"):
                        st.session_state.audio_bytes = None
                        st.rerun()
                with col2:
                    if st.button("📤 Zur Analyse senden", type="primary"):
                        st.session_state.phase = "feedback"
                        st.rerun()
            else:
                st.warning("👆 Klicke auf das Mikrofon um die Aufnahme zu starten.")
                
        except ImportError:
            st.error("❌ Audio-Recorder nicht verfügbar. Aktiviere den Mock-Modus in der Sidebar.")
    
    else:
        # Mock-Modus: Text-Eingabe statt Audio
        st.warning("🧪 **Mock-Modus aktiv** – Gib deinen Text ein statt zu sprechen:")
        
        mock_text = st.text_area(
            "Dein Sprechtext (simuliert):",
            height=150,
            placeholder="Guten Tag, ich möchte kurz den aktuellen Projektstand zusammenfassen..."
        )
        
        if mock_text:
            st.session_state.transcript = mock_text
            if st.button("📤 Mit diesem Text Feedback erhalten", type="primary"):
                st.session_state.phase = "feedback"
                st.rerun()
    
    # Abbrechen-Option
    st.markdown("---")
    if st.button("← Andere Aufgabe wählen"):
        st.session_state.phase = "select"
        st.session_state.audio_bytes = None
        st.session_state.transcript = None
        st.rerun()


# =============================================================================
# PHASE 3: FEEDBACK
# =============================================================================

elif st.session_state.phase == "feedback":
    st.header("3️⃣ Dein Feedback")
    
    task = get_task(st.session_state.selected_task_id)
    
    # Berechne Aufnahmedauer
    if st.session_state.recording_start:
        duration = (datetime.now() - st.session_state.recording_start).total_seconds()
    else:
        duration = 60.0
    
    # Feedback generieren (wenn noch nicht vorhanden)
    if st.session_state.feedback_result is None:
        with st.spinner("🔍 Analysiere deine Aufnahme..."):
            
            if MOCK_MODE:
                # Mock: Verwende eingegebenen Text, aber echte Kleiner Bär Analyse!
                transcript_text = st.session_state.transcript or "Dies ist ein Mock-Transkript für Testing."
    
                # Importiere Kleiner Bär für echte Analyse
                from kleiner_baer import extract_features
    
                # Echte Feature-Extraktion auf den Text
                features = extract_features(transcript_text)
                
                # Features in Session speichern für Anzeige
                st.session_state.kleiner_baer_features = features
    
                # Feedback erstellen (noch Mock, aber mit echten Features)
                feedback = generate_feedback(
                    transcript=transcript_text,
                    task=task,
                    prosody=None,
                    use_mock=True  # Feedback bleibt Mock, aber Features sind echt
                )

                
                st.session_state.feedback_result = feedback
                st.session_state.transcript_text = transcript_text
                
            else:
                # Echter Modus: Audio verarbeiten
                audio_result = process_speaking_task(
                    audio_bytes=st.session_state.audio_bytes,
                    task_id=st.session_state.selected_task_id,
                    duration_seconds=duration,
                    use_mock=False
                )
                
                feedback = generate_feedback(
                    transcript=audio_result.transcript.text,
                    task=task,
                    prosody=audio_result.prosody,
                    use_mock=False
                )
                
                st.session_state.feedback_result = feedback
                st.session_state.audio_result = audio_result
                st.session_state.transcript_text = audio_result.transcript.text
    
    # Ergebnisse anzeigen
    feedback = st.session_state.feedback_result
    transcript_text = st.session_state.get("transcript_text", "")
    
    # Tabs für verschiedene Ansichten
    tab_feedback, tab_transcript, tab_metrics = st.tabs([
        "💬 Feedback", 
        "📝 Transkript", 
        "📊 Metriken"
    ])
    
    with tab_feedback:
        # CEFR-Badge
        if hasattr(feedback, 'cefr_label') and feedback.cefr_label:
            col1, col2, col3 = st.columns([1, 2, 1])
            with col2:
                st.metric(
                    "Geschätztes Niveau", 
                    feedback.cefr_label,
                    delta=f"Score: {feedback.cefr_score:.1f}" if hasattr(feedback, 'cefr_score') and feedback.cefr_score else None
                )
        
        st.markdown("---")
        
        # Narratives Feedback
        st.markdown(format_feedback_markdown(feedback))
        
        # Mock-Hinweis
        if hasattr(feedback, 'is_mock') and feedback.is_mock:
            st.caption("ℹ️ Mock-Modus: Dies ist simuliertes Feedback für Testing.")
    
    with tab_transcript:
        st.subheader("Dein Text")
        st.markdown(f"> {transcript_text}")
        
        st.markdown("---")
        
        col1, col2 = st.columns(2)
        with col1:
            word_count = len(transcript_text.split()) if transcript_text else 0
            st.metric("Wörter", word_count)
        with col2:
            st.metric("Dauer", f"{duration:.0f}s")
        
        if MOCK_MODE:
            st.caption("ℹ️ Mock-Modus: Eingegebener Text")
    
    with tab_metrics:
        st.subheader("Prosodie & Sprechtempo")
        
        col1, col2, col3 = st.columns(3)
        
        with col1:
            word_count = len(transcript_text.split()) if transcript_text else 0
            wpm = (word_count / duration * 60) if duration > 0 else 0
            st.metric(
                "Sprechtempo", 
                f"{wpm:.0f} WPM",
                help="Wörter pro Minute (120-150 ist normal)"
            )
        
        with col2:
            # Mock: Zähle typische Füllwörter
            filler_words = ["ähm", "also", "quasi", "sozusagen", "halt", "eigentlich"]
            filler_count = sum(transcript_text.lower().count(fw) for fw in filler_words)
            st.metric("Füllwörter", filler_count, help="'ähm', 'also', 'quasi', etc.")
        
        with col3:
            st.metric("Flüssigkeit", "–" if MOCK_MODE else "75%")
        
        st.markdown("---")
        
        # Disce-Metriken
        st.subheader("Disce-Dimensionen")
        
        if hasattr(feedback, 'disce_metrics') and feedback.disce_metrics:
            disce = feedback.disce_metrics
            cols = st.columns(5)
            metrics = [
                ("Register", "level_match"),
                ("Prosodie", "prosody_intelligibility"),
                ("Kohäsion", "sentence_cohesion"),
                ("Task-Fit", "task_exam_fit"),
                ("Fortschritt", "goal_progress"),
            ]
            for col, (label, key) in zip(cols, metrics):
                val = disce.get(key, 0)
                col.metric(label, f"{val:.0%}")
        else:
            st.info("Detaillierte Metriken sind im Mock-Modus begrenzt verfügbar.")
        
        if MOCK_MODE:
            st.caption("ℹ️ Mock-Modus: Simulierte Prosodie-Werte")
    
    # Aktionen
    st.markdown("---")
    
    col1, col2, col3 = st.columns(3)
    
    with col1:
        if st.button("🔄 Nochmal versuchen"):
            st.session_state.phase = "record"
            st.session_state.audio_bytes = None
            st.session_state.transcript = None
            st.session_state.feedback_result = None
            st.rerun()
    
    with col2:
        if st.button("📋 Andere Aufgabe"):
            reset_session()
            st.rerun()
    
    with col3:
        if st.button("💾 Session speichern"):
            st.info("Session-Export kommt in v0.2!")


# =============================================================================
# FOOTER
# =============================================================================

st.markdown("---")
st.caption(
    "🐻 Großer Bär nutzt Kleiner Bär für Textanalyse. "
    "Feedback wird mit Claude generiert (oder Mock im Testmodus)."
)
