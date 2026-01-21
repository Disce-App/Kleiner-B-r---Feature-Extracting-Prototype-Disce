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
    
    use_mock = st.checkbox(
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
    
    # Task-Auswahl - Handle sowohl Liste als auch Dict
    task_choices = get_task_choices()
    
    # Wenn es eine Liste ist, konvertiere zu Dict {label: id}
    if isinstance(task_choices, list):
        task_dict = {}
        for tid in task_choices:
            t = get_task(tid)
            label = f"{t.get('scenario', tid)} ({t.get('target_register', '?')})"
            task_dict[label] = tid
        task_choices = task_dict
    
    selected_label = st.selectbox(
        "Welche Situation möchtest du üben?",
        options=list(task_choices.keys()),
        index=0,
    )
    
    task_id = task_choices[selected_label]
    task = get_task(task_id)



# =============================================================================
# PHASE 2: AUFNAHME
# =============================================================================

elif st.session_state.phase == "record":
    task = get_task(st.session_state.selected_task_id)
    
    st.header("2️⃣ Sprich jetzt!")
    
    # Aufgabe als Reminder
    st.info(f"**Aufgabe:** {task['user_prompt']}")
    
    # Timer-Info
    st.caption(f"⏱️ Empfohlene Zeit: {task['time_limit_seconds']} Sekunden")
    
    st.markdown("---")
    
    # Audio Recorder
    try:
        from audio_recorder_streamlit import audio_recorder
        
        st.markdown("### 🎙️ Klicke zum Aufnehmen:")
        
        audio_bytes = audio_recorder(
            pause_threshold=3.0,
            sample_rate=16000,
            key="speaking_recorder"
        )
        
        if audio_bytes:
            st.session_state.audio_bytes = audio_bytes
            st.success("✅ Aufnahme erhalten!")
            
            # Audio abspielen
            st.audio(audio_bytes, format="audio/wav")
            
            st.markdown("---")
            
            col1, col2 = st.columns(2)
            
            with col1:
                if st.button("🔄 Nochmal aufnehmen"):
                    st.session_state.audio_bytes = None
                    st.rerun()
            
            with col2:
                if st.button("✨ Feedback erhalten", type="primary"):
                    st.session_state.phase = "feedback"
                    st.rerun()
        else:
            st.warning("👆 Klicke auf das Mikrofon-Symbol um die Aufnahme zu starten.")
            
    except ImportError:
        st.error(
            "❌ Audio-Recorder nicht verfügbar. "
            "Bitte `audio-recorder-streamlit` installieren."
        )
        
        # Fallback für Testing: Text-Input
        st.markdown("---")
        st.markdown("**Fallback: Text eingeben (für Testing)**")
        
        manual_text = st.text_area(
            "Simulierter Sprechtext:",
            placeholder="Gib hier ein, was du sagen würdest...",
            height=150
        )
        
        if st.button("✨ Mit diesem Text Feedback erhalten"):
            # Speichere als "fake audio"
            st.session_state.audio_bytes = b"mock_audio"
            st.session_state.manual_text = manual_text
            st.session_state.phase = "feedback"
            st.rerun()
    
    # Zurück-Button
    st.markdown("---")
    if st.button("← Andere Aufgabe wählen"):
        st.session_state.phase = "select"
        st.session_state.audio_bytes = None
        st.rerun()


# =============================================================================
# PHASE 3: FEEDBACK
# =============================================================================

elif st.session_state.phase == "feedback":
    task = get_task(st.session_state.selected_task_id)
    
    st.header("3️⃣ Dein Feedback")
    
    # Berechne Aufnahmedauer
    if st.session_state.recording_start:
        duration = (datetime.now() - st.session_state.recording_start).total_seconds()
    else:
        duration = 60.0
    
    # Feedback generieren (wenn noch nicht vorhanden)
    if st.session_state.feedback_result is None:
        with st.spinner("🔍 Analysiere deine Aufnahme..."):
            
            # Audio verarbeiten
            audio_result = process_speaking_task(
                audio_bytes=st.session_state.audio_bytes,
                task_id=st.session_state.selected_task_id,
                duration_seconds=duration,
                use_mock=use_mock  # aus Sidebar
            )
            
            # Manueller Text überschreibt (für Fallback)
            if hasattr(st.session_state, 'manual_text') and st.session_state.manual_text:
                audio_result.transcript.text = st.session_state.manual_text
                audio_result.transcript.word_count = len(st.session_state.manual_text.split())
            
            # Feedback generieren
            feedback = generate_feedback(
                transcript=audio_result.transcript.text,
                task=task,
                prosody=audio_result.prosody,
                use_mock=use_mock
            )
            
            st.session_state.feedback_result = feedback
            st.session_state.audio_result = audio_result
    
    # Ergebnisse anzeigen
    feedback = st.session_state.feedback_result
    audio_result = st.session_state.audio_result
    
    # Tabs für verschiedene Ansichten
    tab_feedback, tab_transcript, tab_metrics = st.tabs([
        "💬 Feedback", 
        "📝 Transkript", 
        "📊 Metriken"
    ])
    
    with tab_feedback:
        # CEFR-Badge
        if feedback.cefr_label:
            col1, col2, col3 = st.columns([1, 2, 1])
            with col2:
                st.metric(
                    "Geschätztes Niveau", 
                    feedback.cefr_label,
                    delta=f"Score: {feedback.cefr_score:.1f}" if feedback.cefr_score else None
                )
        
        st.markdown("---")
        
        # Narratives Feedback
        st.markdown(format_feedback_markdown(feedback))
        
        # Mock-Hinweis
        if feedback.is_mock:
            st.caption("ℹ️ Mock-Modus: Dies ist simuliertes Feedback für Testing.")
    
    with tab_transcript:
        st.subheader("Dein Text")
        st.markdown(f"> {audio_result.transcript.text}")
        
        st.markdown("---")
        
        col1, col2 = st.columns(2)
        with col1:
            st.metric("Wörter", audio_result.transcript.word_count)
        with col2:
            st.metric("Dauer", f"{duration:.0f}s")
        
        if audio_result.transcript.is_mock:
            st.caption("ℹ️ Mock-Modus: Beispiel-Transkript")
    
    with tab_metrics:
        st.subheader("Prosodie & Sprechtempo")
        
        prosody = audio_result.prosody
        
        col1, col2, col3 = st.columns(3)
        
        with col1:
            wpm = prosody.speech_rate_wpm
            st.metric(
                "Sprechtempo", 
                f"{wpm:.0f} WPM" if wpm else "–",
                help="Wörter pro Minute (120-150 ist normal)"
            )
        
        with col2:
            st.metric(
                "Füllwörter",
                prosody.filler_count,
                help="'ähm', 'also', 'quasi', etc."
            )
        
        with col3:
            if prosody.fluency_score:
                st.metric("Flüssigkeit", f"{prosody.fluency_score:.0f}%")
            else:
                st.metric("Flüssigkeit", "–")
        
        st.markdown("---")
        
        # Disce-Metriken
        st.subheader("Disce-Dimensionen")
        
        disce = feedback.disce_metrics
        if disce:
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
        
        if prosody.is_mock:
            st.caption("ℹ️ Mock-Modus: Simulierte Prosodie-Werte")
    
    # Aktionen
    st.markdown("---")
    
    col1, col2, col3 = st.columns(3)
    
    with col1:
        if st.button("🔄 Nochmal versuchen"):
            st.session_state.phase = "record"
            st.session_state.audio_bytes = None
            st.session_state.feedback_result = None
            st.rerun()
    
    with col2:
        if st.button("📋 Andere Aufgabe"):
            reset_session()
            st.rerun()
    
    with col3:
        # Session speichern (für später)
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
