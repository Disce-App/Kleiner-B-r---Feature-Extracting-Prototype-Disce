# pages/grosser_baer.py
"""
Großer Bär – Speaking Coach UI
Streamlit-Seite für Audio-Aufnahme und Feedback.
"""

import uuid
from datetime import datetime

import streamlit as st

# Großer Bär Imports
from grosser_baer import (
    get_task,
    get_task_choices,
    process_speaking_task,
    generate_feedback,
    format_feedback_markdown,
    SessionLogger,
)

# Kleiner Bär – deterministische Textanalyse
from disce_core import analyze_text_for_llm


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

if "kleiner_baer_result" not in st.session_state:
    st.session_state.kleiner_baer_result = None

if "coach_input" not in st.session_state:
    st.session_state.coach_input = None

if "session_id" not in st.session_state:
    st.session_state.session_id = str(uuid.uuid4())

# Neu: Planungsfeld (Phase 1)
if "learner_goal" not in st.session_state:
    st.session_state.learner_goal = ""

if "learner_context" not in st.session_state:
    st.session_state.learner_context = ""

# Reflexionsfeld (Phase 3)
if "reflection_text" not in st.session_state:
    st.session_state.reflection_text = ""

if "reflection_saved" not in st.session_state:
    st.session_state.reflection_saved = False


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
    st.session_state.kleiner_baer_result = None
    st.session_state.coach_input = None
    st.session_state.session_id = str(uuid.uuid4())
    st.session_state.learner_goal = ""
    st.session_state.learner_context = ""
    st.session_state.reflection_text = ""
    st.session_state.reflection_saved = False


def build_coach_input(
    transcript_text: str,
    task: dict,
    duration: float,
    mode: str,
    kleiner_baer_result: dict,
    learner_goal: str = "",
    learner_context: str = "",
    reflection: str = "",
) -> dict:
    """Baut den JSON-Block, der später an die LLM-Coach-API geht."""
    now = datetime.now()
    recording_start = st.session_state.get("recording_start")

    return {
        "task_metadata": {
            "task_id": st.session_state.selected_task_id,
            "situation": task.get("situation"),
            "task": task.get("task"),
            "target_level": task.get("level"),
            "target_register": task.get("register"),
            "time_limit_seconds": task.get("time_seconds"),
        },
        "session_metadata": {
            "session_id": st.session_state.get("session_id"),
            "mode": mode,
            "started_at": recording_start.isoformat() if recording_start else None,
            "ended_at": now.isoformat(),
            "duration_seconds": duration,
        },
        # Neu: Planung der Lernenden (vor der Übung)
        "learner_planning": {
            "goal": learner_goal,
            "context": learner_context,
            "submitted_at": recording_start.isoformat() if recording_start else None,
        },
        "transcript": transcript_text,
        "analysis": {
            "layer1_deterministic": kleiner_baer_result.get("metrics_summary", {}),
            "layer2_azure": None,
            "cefr": kleiner_baer_result.get("cefr", {}),
            "home_kpis": kleiner_baer_result.get("disce_metrics", {}),
            "hotspots": kleiner_baer_result.get("hotspots", []),
        },
        # Reflexion der Lernenden (nach der Übung)
        "reflection": {
            "text": reflection,
            "submitted_at": now.isoformat() if reflection else None,
        },
    }


def update_coach_input_with_reflection(reflection_text: str):
    """Aktualisiert den coach_input mit der Reflexion."""
    if st.session_state.coach_input:
        st.session_state.coach_input["reflection"] = {
            "text": reflection_text,
            "submitted_at": datetime.now().isoformat(),
        }


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
        help="Aktiviert Beispiel-Transkripte und Mock-Feedback für Testing",
    )

    st.markdown("---")

    if st.button("🔄 Neue Session"):
        reset_session()
        st.rerun()

    st.markdown("---")
    st.caption("Großer Bär v0.1 – Prototype")


# =============================================================================
# PHASE 1: AUFGABE WÄHLEN + ZIEL SETZEN
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

    # =========================================================================
    # PLANUNGSFELD: Persönliches Lernziel
    # =========================================================================
    st.markdown("---")
    st.subheader("🎯 Dein Lernziel für diese Session")

    st.markdown(
        "Bevor du startest: Was möchtest du heute konkret üben oder verbessern? "
        "Das hilft dir, fokussiert zu bleiben – und dem Coach, dir gezieltes Feedback zu geben."
    )

    # Leitfragen als Inspiration
    with st.expander("💡 Beispiele für Lernziele", expanded=False):
        st.markdown(
            """
            - „Ich möchte flüssiger sprechen, ohne lange Pausen."
            - „Ich will formeller klingen – weniger umgangssprachlich."
            - „Ich übe, meine Argumente klar zu strukturieren."
            - „Ich möchte Konjunktiv II sicher verwenden."
            - „Ich will meine Nervosität in den Griff bekommen."
            - „Ich übe, höflich aber bestimmt zu formulieren."
            """
        )

    learner_goal_input = st.text_area(
        "Was ist dein Ziel für diese Übung?",
        value=st.session_state.learner_goal,
        height=80,
        placeholder="z.B. „Ich möchte heute üben, meine Punkte klar und strukturiert zu präsentieren."",
        key="learner_goal_input",
    )

    # Optionales Kontextfeld
    with st.expander("📝 Optionaler Kontext (für wen / warum)", expanded=False):
        st.markdown(
            "Falls du einen konkreten Anlass hast, kannst du ihn hier beschreiben. "
            "Das macht das Feedback noch passender."
        )
        learner_context_input = st.text_area(
            "Kontext (optional):",
            value=st.session_state.learner_context,
            height=60,
            placeholder="z.B. „Ich habe nächste Woche ein echtes Meeting mit meinem Chef."",
            key="learner_context_input",
        )
    
    # Falls Expander nicht geöffnet, brauchen wir trotzdem den Wert
    if "learner_context_input" not in dir():
        learner_context_input = st.session_state.learner_context

    # Meta-Prompt aus Task anzeigen (falls vorhanden)
    if task.get("meta_prompts", {}).get("plan"):
        st.info(f"💡 **Planungshinweis:** {task['meta_prompts']['plan']}")

    # Weiter-Button
    st.markdown("---")
    col1, col2, col3 = st.columns([1, 2, 1])
    with col2:
        # Button-Text anpassen je nachdem ob Ziel eingegeben
        button_text = "🎙️ Aufnahme starten"
        if not learner_goal_input.strip():
            st.caption("💡 Tipp: Ein konkretes Lernziel hilft dir, fokussiert zu bleiben.")
        
        if st.button(button_text, type="primary", use_container_width=True):
            # Ziel und Kontext speichern
            st.session_state.learner_goal = learner_goal_input.strip()
            st.session_state.learner_context = learner_context_input.strip() if learner_context_input else ""
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
    st.caption(
        f"⏱️ Ziel: {task['time_seconds']} Sekunden | Register: {task['register']}"
    )

    # Lernziel anzeigen (zur Erinnerung)
    if st.session_state.learner_goal:
        st.success(f"🎯 **Dein Fokus:** {st.session_state.learner_goal}")

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
                key="speaking_recorder",
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
            st.error(
                "❌ Audio-Recorder nicht verfügbar. "
                "Aktiviere den Mock-Modus in der Sidebar."
            )

    else:
        # Mock-Modus: Text-Eingabe statt Audio
        st.warning("🧪 **Mock-Modus aktiv** – Gib deinen Text ein statt zu sprechen:")

        mock_text = st.text_area(
            "Dein Sprechtext (simuliert):",
            height=150,
            placeholder=(
                "Guten Tag, ich möchte kurz den aktuellen Projektstand "
                "zusammenfassen..."
            ),
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
# PHASE 3: FEEDBACK + REFLEXION
# =============================================================================

elif st.session_state.phase == "feedback":
    st.header("3️⃣ Dein Feedback")

    task = get_task(st.session_state.selected_task_id)

    # Berechne Aufnahmedauer
    if st.session_state.recording_start:
        duration = (
            datetime.now() - st.session_state.recording_start
        ).total_seconds()
    else:
        duration = 60.0

    # Feedback generieren (wenn noch nicht vorhanden)
    if st.session_state.feedback_result is None:
        with st.spinner("🔍 Analysiere deine Aufnahme..."):

            if MOCK_MODE:
                # Mock: Verwende eingegebenen Text, Feedback ist simuliert
                transcript_text = (
                    st.session_state.transcript
                    or "Dies ist ein Mock-Transkript für Testing."
                )

                # 1) Kleiner Bär: deterministische Analyse (Schicht 1 + CEFR + KPIs)
                kb_result = analyze_text_for_llm(
                    transcript_text,
                    context={
                        "source": "grosser_baer",
                        "mode": "mock_speaking",
                        "task_id": st.session_state.selected_task_id,
                        "target_level": task.get("level"),
                        "target_register": task.get("register"),
                        "time_limit_seconds": task.get("time_seconds"),
                        # Lernziel für spätere LLM-Nutzung
                        "learner_goal": st.session_state.learner_goal,
                        "learner_context": st.session_state.learner_context,
                    },
                )
                st.session_state.kleiner_baer_result = kb_result

                # 2) Coach-Input-Block bauen
                coach_input = build_coach_input(
                    transcript_text=transcript_text,
                    task=task,
                    duration=duration,
                    mode="mock_speaking",
                    kleiner_baer_result=kb_result,
                    learner_goal=st.session_state.learner_goal,
                    learner_context=st.session_state.learner_context,
                    reflection="",  # wird später ergänzt
                )
                st.session_state.coach_input = coach_input

                # 3) Narratives Feedback (weiterhin Mock / LLM später)
                feedback = generate_feedback(
                    transcript=transcript_text,
                    task=task,
                    prosody=None,
                    use_mock=True,
                )

                st.session_state.feedback_result = feedback
                st.session_state.transcript_text = transcript_text

            else:
                # Echter Modus: Audio verarbeiten
                audio_result = process_speaking_task(
                    audio_bytes=st.session_state.audio_bytes,
                    task_id=st.session_state.selected_task_id,
                    duration_seconds=duration,
                    use_mock=False,
                )

                transcript_text = audio_result.transcript.text

                # 1) Kleiner Bär über das Transkript laufen lassen
                kb_result = analyze_text_for_llm(
                    transcript_text,
                    context={
                        "source": "grosser_baer",
                        "mode": "speaking",
                        "task_id": st.session_state.selected_task_id,
                        "target_level": task.get("level"),
                        "target_register": task.get("register"),
                        "time_limit_seconds": task.get("time_seconds"),
                        "learner_goal": st.session_state.learner_goal,
                        "learner_context": st.session_state.learner_context,
                    },
                )
                st.session_state.kleiner_baer_result = kb_result

                # 2) Coach-Input-Block (hier später um Azure-Daten ergänzen)
                coach_input = build_coach_input(
                    transcript_text=transcript_text,
                    task=task,
                    duration=duration,
                    mode="speaking",
                    kleiner_baer_result=kb_result,
                    learner_goal=st.session_state.learner_goal,
                    learner_context=st.session_state.learner_context,
                    reflection="",
                )
                st.session_state.coach_input = coach_input

                # 3) Narratives Feedback (Claude/LLM, aktuell noch Mock-Logik)
                feedback = generate_feedback(
                    transcript=transcript_text,
                    task=task,
                    prosody=audio_result.prosody,
                    use_mock=False,
                )

                st.session_state.feedback_result = feedback
                st.session_state.audio_result = audio_result
                st.session_state.transcript_text = transcript_text

    # Ergebnisse aus Session holen
    feedback = st.session_state.feedback_result
    transcript_text = st.session_state.get("transcript_text", "")

    kleiner_baer_result = st.session_state.get("kleiner_baer_result")
    coach_input = st.session_state.get("coach_input")
    cefr_from_kb = None
    if kleiner_baer_result and "cefr" in kleiner_baer_result:
        cefr_from_kb = kleiner_baer_result["cefr"]

    # Lernziel zur Erinnerung anzeigen
    if st.session_state.learner_goal:
        st.info(f"🎯 **Dein Fokus war:** {st.session_state.learner_goal}")

    # Tabs für verschiedene Ansichten
    tab_feedback, tab_transcript, tab_metrics, tab_api = st.tabs(
        ["💬 Feedback", "📝 Transkript", "📊 Metriken", "🔌 LLM-Input"]
    )

    # -------------------------------------------------------------------------
    # Tab: Feedback
    # -------------------------------------------------------------------------
    with tab_feedback:
        # CEFR-Badge (wenn möglich aus Kleiner Bär)
        col1, col2, col3 = st.columns([1, 2, 1])
        with col2:
            if cefr_from_kb:
                st.metric(
                    "Geschätztes Niveau",
                    cefr_from_kb.get("label", "–"),
                    delta=f"Score: {cefr_from_kb.get('score', 0.0):.2f}",
                )
            elif hasattr(feedback, "cefr_label") and feedback.cefr_label:
                st.metric(
                    "Geschätztes Niveau",
                    feedback.cefr_label,
                    delta=(
                        f"Score: {feedback.cefr_score:.1f}"
                        if hasattr(feedback, "cefr_score") and feedback.cefr_score
                        else None
                    ),
                )

        st.markdown("---")

        # Narratives Feedback
        st.markdown(format_feedback_markdown(feedback))

        # Mock-Hinweis
        if hasattr(feedback, "is_mock") and feedback.is_mock:
            st.caption("ℹ️ Mock-Modus: Dies ist simuliertes Feedback für Testing.")

    # -------------------------------------------------------------------------
    # Tab: Transkript
    # -------------------------------------------------------------------------
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

    # -------------------------------------------------------------------------
    # Tab: Metriken
    # -------------------------------------------------------------------------
    with tab_metrics:
        st.subheader("Prosodie & Sprechtempo")

        col1, col2, col3 = st.columns(3)

        with col1:
            word_count = len(transcript_text.split()) if transcript_text else 0
            wpm = (word_count / duration * 60) if duration > 0 else 0
            st.metric(
                "Sprechtempo",
                f"{wpm:.0f} WPM",
                help="Wörter pro Minute (120–150 ist normal)",
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

        disce = None
        if kleiner_baer_result:
            # Echte KPIs aus Kleiner Bär / build_disce_metrics
            disce = kleiner_baer_result.get("disce_metrics")
        elif hasattr(feedback, "disce_metrics") and feedback.disce_metrics:
            # Fallback, falls Feedback sie intern schon mitbringt
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
                val = float(disce.get(key, 0))
                col.metric(label, f"{val:.0%}")
        else:
            st.info("Noch keine Disce-Metriken verfügbar.")

        if MOCK_MODE:
            st.caption(
                "ℹ️ Mock-Modus: Audio-Prosidie ist noch simuliert – "
                "Textmetriken sind bereits echt."
            )

    # -------------------------------------------------------------------------
    # Tab: LLM-Input
    # -------------------------------------------------------------------------
    with tab_api:
        st.subheader("LLM-Coach Input (JSON)")
        st.write(
            "Dieser Block wird später an die LLM-Coach-API gesendet. "
            "Er enthält Task-Metadaten, Transkript und deterministische Analyse "
            "nach dem Disce-Diagnostikmodell."
        )

        if coach_input:
            st.json(coach_input)
        else:
            st.info(
                "Noch kein Coach-Input verfügbar. "
                "Bitte zuerst eine Aufgabe abschließen."
            )

    # =========================================================================
    # REFLEXIONSFELD (nach den Tabs)
    # =========================================================================
    st.markdown("---")
    st.header("4️⃣ Deine Reflexion")

    st.markdown(
        "Nimm dir einen Moment, um über deine Übung nachzudenken. "
        "Das hilft dir, das Gelernte zu verankern."
    )

    # Leitfragen als Inspiration – angepasst ans Lernziel
    with st.expander("💡 Leitfragen zur Reflexion", expanded=False):
        reflection_prompts = """
- **Was ist mir gut gelungen?** (z.B. Wortwahl, Struktur, Flüssigkeit)
- **Was war schwierig?** (z.B. ein bestimmtes Wort, die Satzstellung, das Tempo)
- **Was will ich beim nächsten Mal anders machen?**
- **Welchen konkreten Aspekt übe ich als Nächstes?**
"""
        # Falls Lernziel vorhanden, zusätzliche Frage
        if st.session_state.learner_goal:
            reflection_prompts += f"\n- **Bezogen auf dein Ziel** („{st.session_state.learner_goal}"): Wie gut hast du es erreicht?"
        
        st.markdown(reflection_prompts)

    # Reflexions-Textfeld
    reflection_input = st.text_area(
        "Deine Gedanken:",
        value=st.session_state.reflection_text,
        height=120,
        placeholder="Was nimmst du aus dieser Übung mit? Was machst du nächstes Mal anders?",
        key="reflection_input",
    )

    # Speichern-Button für Reflexion
    col_ref1, col_ref2 = st.columns([3, 1])
    with col_ref2:
        if st.button("✅ Reflexion speichern", type="primary", use_container_width=True):
            st.session_state.reflection_text = reflection_input
            update_coach_input_with_reflection(reflection_input)
            st.session_state.reflection_saved = True
            st.rerun()

    # Bestätigung anzeigen
    if st.session_state.reflection_saved and st.session_state.reflection_text:
        st.success("✅ Reflexion gespeichert!")
        st.markdown(f"**Deine Reflexion:** _{st.session_state.reflection_text}_")

    # =========================================================================
    # AKTIONEN
    # =========================================================================
    st.markdown("---")

    col1, col2, col3 = st.columns(3)

    with col1:
        if st.button("🔄 Nochmal versuchen"):
            st.session_state.phase = "record"
            st.session_state.audio_bytes = None
            st.session_state.transcript = None
            st.session_state.feedback_result = None
            st.session_state.kleiner_baer_result = None
            st.session_state.coach_input = None
            st.session_state.reflection_text = ""
            st.session_state.reflection_saved = False
            st.rerun()

    with col2:
        if st.button("📋 Andere Aufgabe"):
            reset_session()
            st.rerun()

    with col3:
        if st.button("💾 Session speichern"):
            # Stelle sicher, dass Reflexion im coach_input ist
            if st.session_state.reflection_text:
                update_coach_input_with_reflection(st.session_state.reflection_text)
            st.info("Session-Export kommt in v0.2!")


# =============================================================================
# FOOTER
# =============================================================================

st.markdown("---")
st.caption(
    "🐻 Großer Bär nutzt Kleiner Bär für Textanalyse. "
    "Feedback wird mit Claude generiert (oder Mock im Testmodus)."
)
