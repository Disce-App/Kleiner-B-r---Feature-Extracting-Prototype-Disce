# pages/grosser_baer.py
"""
Großer Bär – Speaking Coach UI
Streamlit-Seite für Audio-Aufnahme und Feedback.
"""

import uuid
from datetime import datetime
import json

import streamlit as st
import requests

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

# Pretest-Loader
from config.pretest_loader import (
    load_pretest_config,
    init_pretest_state,
    should_show_pretest,
    render_pretest,
    render_level_recheck,
    get_pretest_data_for_airtable,
    get_pretest_data_for_coach_input,
    get_response as get_pretest_response,
)

# NEU: App-Config System
from config.app_config import (
    init_app_config,
    get_config,
    set_config,
    is_mock_mode,
    is_debug_mode,
    should_skip_pretest,
    is_airtable_enabled,
    log_payload,
    log_llm_call,
    log_error,
    log_event,
)

# Mistral Services (Voxtral + Mistral Chat)
try:
    from mistral_services import transcribe_audio, generate_coach_feedback, check_api_connection
    MISTRAL_AVAILABLE = True
except ImportError:
    MISTRAL_AVAILABLE = False


# =============================================================================
# KONFIGURATION
# =============================================================================

MAKE_WEBHOOK_URL = "https://hook.eu2.make.com/2f65yl8ut90pnq2jhbi1l1ft2ytecceh"
PRETEST_CONFIG_PATH = "config/pretest_config.json"


# =============================================================================
# PAGE CONFIG
# =============================================================================

st.set_page_config(
    page_title="Großer Bär – Speaking Coach",
    page_icon="🐻",
    layout="wide",
)

# =============================================================================
# CUSTOM THEME CSS
# =============================================================================

st.markdown("""
<style>
    /* =========================================================
       EXPANDER STYLING
       ========================================================= */
    
    /* Expander-Header (der klickbare Teil) → BRAUN */
    [data-testid="stExpander"] > details > summary {
        background-color: #8B4513 !important;
        color: #FFFDF5 !important;
        border-radius: 8px 8px 0 0;
        padding: 0.75rem 1rem;
        font-weight: 600;
    }
    
    /* Expander-Header Hover */
    [data-testid="stExpander"] > details > summary:hover {
        background-color: #A0522D !important;
    }
    
    /* Expander-Pfeil (>) weiß machen */
    [data-testid="stExpander"] > details > summary svg {
        fill: #FFFDF5 !important;
    }
    
    /* Expander-Inhalt (ausgeklappt) → HELLGRÜN */
    [data-testid="stExpander"] > details > div {
        background-color: #E8F5E9 !important;
        border: 1px solid #C8E6C9;
        border-top: none;
        border-radius: 0 0 8px 8px;
        padding: 1rem;
    }
    
    /* =========================================================
       EINGABEFELDER → CREME (nicht dunkelgrün!)
       ========================================================= */
    
    /* Text Areas (mehrzeilig) - z.B. Lernziel, Reflexion */
    [data-testid="stTextArea"] textarea {
        background-color: #E8F5E9 !important;
        border: 1px solid #A5D6A7 !important;
        border-radius: 8px;
    }
    
    /* Text Inputs (einzeilig) - z.B. Nutzercode */
    [data-testid="stTextInput"] input {
        background-color: #E8F5E9 !important;
        border: 1px solid #A5D6A7 !important;
        border-radius: 8px;
    }
    
    /* Selectbox / Dropdown */
    [data-testid="stSelectbox"] > div > div {
        background-color: #E8F5E9 !important;
        border: 1px solid #A5D6A7 !important;
        border-radius: 8px;
    }
    
    /* Fokus-State (wenn Feld aktiv) */
    [data-testid="stTextArea"] textarea:focus,
    [data-testid="stTextInput"] input:focus,
    [data-testid="stSelectbox"] > div > div:focus-within {
        border-color: #4CAF50 !important;
        box-shadow: 0 0 0 2px rgba(76, 175, 80, 0.2) !important;
    }
    
    /* Placeholder-Text */
    [data-testid="stTextArea"] textarea::placeholder,
    [data-testid="stTextInput"] input::placeholder {
        color: #9E9E9E !important;
    }
    
    /* =========================================================
       METRICS
       ========================================================= */
    
    [data-testid="stMetricValue"] {
        color: #2E7D32 !important;
    }
    
    /* =========================================================
       TABS
       ========================================================= */
    
    /* Aktiver Tab → Grün unterstrichen */
    .stTabs [data-baseweb="tab-list"] button[aria-selected="true"] {
        border-bottom-color: #4CAF50 !important;
        color: #2E7D32 !important;
    }
    
    /* =========================================================
       DIVIDER
       ========================================================= */
    
    hr {
        border-color: #C8E6C9 !important;
    }
</style>
""", unsafe_allow_html=True)

# =============================================================================
# APP CONFIG INITIALISIERUNG (NEU)
# =============================================================================

init_app_config()

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

# Planungsfeld (Phase 1)
if "learner_goal" not in st.session_state:
    st.session_state.learner_goal = ""

if "learner_context" not in st.session_state:
    st.session_state.learner_context = ""

# Reflexionsfeld (Phase 3)
if "reflection_text" not in st.session_state:
    st.session_state.reflection_text = ""

if "reflection_saved" not in st.session_state:
    st.session_state.reflection_saved = False

# Nutzercode (Mini-Login)
if "user_code" not in st.session_state:
    st.session_state.user_code = ""

if "user_code_confirmed" not in st.session_state:
    st.session_state.user_code_confirmed = False

# Session-Speicherung
if "session_saved" not in st.session_state:
    st.session_state.session_saved = False

# Session-Zähler (für Level-Recheck)
if "session_count" not in st.session_state:
    st.session_state.session_count = 0

# =============================================================================
# PRETEST INITIALISIERUNG
# =============================================================================

init_pretest_state()
PRETEST_CONFIG = load_pretest_config(PRETEST_CONFIG_PATH)


# =============================================================================
# HELPER FUNCTIONS
# =============================================================================

def generate_user_code() -> str:
    """Generiert einen zufälligen 6-stelligen Nutzercode."""
    import random
    import string
    # Format: 3 Buchstaben + 3 Zahlen (z.B. ABC123)
    letters = ''.join(random.choices(string.ascii_uppercase, k=3))
    numbers = ''.join(random.choices(string.digits, k=3))
    return f"{letters}{numbers}"


def validate_user_code(code: str) -> tuple[bool, str]:
    """Validiert den Nutzercode. Gibt (is_valid, message) zurück."""
    if not code:
        return False, "Bitte gib einen Code ein."
    if len(code) < 4:
        return False, "Der Code muss mindestens 4 Zeichen haben."
    if len(code) > 20:
        return False, "Der Code darf maximal 20 Zeichen haben."
    if not code.replace("_", "").replace("-", "").isalnum():
        return False, "Nur Buchstaben, Zahlen, - und _ erlaubt."
    return True, "OK"


def reset_session():
    """Setzt die Session zurück für neue Aufnahme (behält Nutzercode + Pretest)."""
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
    st.session_state.session_saved = False
    # Session-Zähler erhöhen
    st.session_state.session_count += 1
    # user_code und pretest_responses bleiben erhalten!
    
    # Event loggen
    log_event("session", "Session zurückgesetzt", {"session_count": st.session_state.session_count})


def logout_user():
    """Loggt den Nutzer aus (löscht auch Nutzercode und Pretest)."""
    st.session_state.user_code = ""
    st.session_state.user_code_confirmed = False
    # Pretest zurücksetzen
    st.session_state.pretest_responses = {}
    st.session_state.pretest_completed = False
    st.session_state.pretest_completed_at = None
    st.session_state.pretest_current_module = 0
    st.session_state.session_count = 0
    reset_session()
    
    # Event loggen
    log_event("auth", "User ausgeloggt")


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

    # Pretest-Daten für Coach-Input holen
    pretest_data = get_pretest_data_for_coach_input()

    return {
        # Nutzer-Identifikation
        "user": {
            "code": st.session_state.get("user_code", ""),
            "is_anonymous": not st.session_state.get("user_code_confirmed", False),
        },
        # NEU: Pretest-Daten (CEFR-Selbsteinschätzung, MASQ-Scores, etc.)
        "pretest": pretest_data,
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
            "session_number": st.session_state.get("session_count", 0),
            "mode": mode,
            "started_at": recording_start.isoformat() if recording_start else None,
            "ended_at": now.isoformat(),
            "duration_seconds": duration,
        },
        # Planung der Lernenden (vor der Übung)
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


def send_session_to_airtable() -> tuple[bool, str]:
    """
    Sendet die Session-Daten an Make Webhook → Airtable.
    Make verteilt die Daten auf pretest_responses und Sessions.
    """
    # NEU: Prüfe ob Airtable aktiviert ist
    if not is_airtable_enabled():
        log_event("airtable", "Airtable deaktiviert – Senden übersprungen")
        return True, "Session lokal gespeichert (Airtable deaktiviert)"
    
    try:
        coach_input = st.session_state.get("coach_input", {})
        kleiner_baer_result = st.session_state.get("kleiner_baer_result", {})
        task = get_task(st.session_state.selected_task_id) if st.session_state.selected_task_id else {}
        
        # CEFR-Daten aus Analyse
        cefr_data = kleiner_baer_result.get("cefr", {})
        
        # Session-Metadaten
        session_meta = coach_input.get("session_metadata", {})
        task_meta = coach_input.get("task_metadata", {})
        learner_planning = coach_input.get("learner_planning", {})
        reflection = coach_input.get("reflection", {})
        
        # Pretest-Daten holen
        pretest_data = get_pretest_data_for_airtable()
        
        # =====================================================================
        # FLACHER PAYLOAD (alle Felder auf oberster Ebene)
        # =====================================================================
        payload = {
            # --- Identifikation ---
            "session_id": st.session_state.get("session_id", ""),
            "user_code": st.session_state.get("user_code", "ANON"),
            "session_number": st.session_state.get("session_count", 0),
            "created_at": datetime.now().isoformat(),
            
            # --- Session-Daten ---
            "mode": session_meta.get("mode", "unknown"),
            "task_id": task_meta.get("task_id", ""),
            "task_situation": task_meta.get("situation", ""),
            "target_register": task_meta.get("target_register", ""),
            "target_level": task_meta.get("target_level", ""),
            "time_limit_seconds": task_meta.get("time_limit_seconds", 0),
            "duration_seconds": session_meta.get("duration_seconds", 0),
            "learner_goal": learner_planning.get("goal", ""),
            "learner_context": learner_planning.get("context", ""),
            "transcript": coach_input.get("transcript", ""),
            "reflection": reflection.get("text", ""),
            "cefr_label": cefr_data.get("label", ""),
            "cefr_score": cefr_data.get("score", 0.0),
            "metrics_json": json.dumps(kleiner_baer_result.get("disce_metrics", {})),
            
            # --- Pretest-Daten (NEU) ---
            "pretest_completed": pretest_data.get("pretest_completed", False),
            "pretest_completed_at": pretest_data.get("pretest_completed_at", ""),
            "cefr_self_overall": pretest_data.get("cefr_self_overall", ""),
            "cefr_self_speaking": pretest_data.get("cefr_self_speaking", ""),
            "has_official_cert": pretest_data.get("has_official_cert", False),
            "official_cert_type": pretest_data.get("official_cert_type", ""),
            "learning_duration_months": pretest_data.get("learning_duration_months", 0),
            "learning_context": pretest_data.get("learning_context", ""),
            "native_language": pretest_data.get("native_language", ""),
            "other_languages": pretest_data.get("other_languages", ""),
            "masq_total": pretest_data.get("masq_total", 0),
            "masq_level": pretest_data.get("masq_level", ""),
            "masq_pe_mean": pretest_data.get("masq_pe_mean", 0),
            "masq_ps_mean": pretest_data.get("masq_ps_mean", 0),
            "masq_pk_mean": pretest_data.get("masq_pk_mean", 0),
            "masq_mt_mean": pretest_data.get("masq_mt_mean", 0),
            "masq_da_mean": pretest_data.get("masq_da_mean", 0),
        }
        
        # An Make Webhook senden
        response = requests.post(
            MAKE_WEBHOOK_URL,
            json=payload,
            headers={"Content-Type": "application/json"},
            timeout=10,
        )
        
        # NEU: Payload loggen
        response_data = None
        try:
            response_data = response.json()
        except:
            response_data = {"status_code": response.status_code, "text": response.text[:200]}
        
        log_payload("make_webhook", payload, response_data)
        
        if response.status_code == 200:
            return True, "Session erfolgreich gespeichert!"
        else:
            log_error("airtable", f"HTTP {response.status_code}", {"response": response.text[:500]})
            return False, f"Fehler beim Speichern: HTTP {response.status_code}"
            
    except requests.exceptions.Timeout:
        log_error("airtable", "Timeout", {"url": MAKE_WEBHOOK_URL})
        return False, "Timeout: Server antwortet nicht."
    except requests.exceptions.RequestException as e:
        log_error("airtable", "RequestException", {"error": str(e)})
        return False, f"Verbindungsfehler: {str(e)}"
    except Exception as e:
        log_error("airtable", "Exception", {"error": str(e)})
        return False, f"Fehler: {str(e)}"

# =============================================================================
# MISTRAL FEEDBACK WRAPPER CLASS
# =============================================================================

class MistralFeedback:
    """Wrapper-Klasse für Mistral-generiertes Feedback."""
    def __init__(self, text: str, cefr_data: dict):
        self.text = text
        self.cefr_label = cefr_data.get("label", "")
        self.cefr_score = cefr_data.get("score", 0)
        self.is_mock = False


# =============================================================================
# HEADER
# =============================================================================

st.title("🐻 Großer Bär – Speaking Coach")
st.markdown(
    "Übe gesprochenes Deutsch mit strukturiertem Feedback. "
    "Wähle eine Aufgabe, nimm dich auf, und erhalte Analyse + Coaching."
)

# =============================================================================
# SIDEBAR
# =============================================================================

with st.sidebar:
    # -------------------------------------------------------------------------
    # MINI-LOGIN: Nutzercode
    # -------------------------------------------------------------------------
    st.header("👤 Dein Nutzercode")

    if st.session_state.user_code_confirmed:
        # Eingeloggt: Code anzeigen
        st.success(f"✅ Eingeloggt als: **{st.session_state.user_code}**")
        st.caption("Dein Code verknüpft alle deine Sessions.")
        
        # Pretest-Status anzeigen
        if st.session_state.get("pretest_completed", False):
            cefr_self = get_pretest_response("cefr_speaking", "–")
            st.info(f"📊 Selbsteinschätzung: **{cefr_self}**")
            st.caption(f"Sessions: {st.session_state.get('session_count', 0)}")

        if st.button("🚪 Ausloggen", use_container_width=True):
            logout_user()
            st.rerun()

    else:
        # Nicht eingeloggt: Login-Formular
        st.markdown(
            "Gib deinen persönlichen Code ein, um deine Sessions zu verknüpfen. "
            "Du kannst einen eigenen Code wählen oder einen generieren lassen."
        )

        # Code-Eingabe
        user_code_input = st.text_input(
            "Dein Code:",
            value=st.session_state.user_code,
            max_chars=20,
            placeholder="z.B. ANNA2024 oder XYZ123",
            key="user_code_input",
        )

        col_login1, col_login2 = st.columns(2)

        with col_login1:
            if st.button("✅ Bestätigen", use_container_width=True):
                is_valid, message = validate_user_code(user_code_input)
                if is_valid:
                    st.session_state.user_code = user_code_input.upper()
                    st.session_state.user_code_confirmed = True
                    log_event("auth", "User eingeloggt", {"user_code": user_code_input.upper()})
                    st.rerun()
                else:
                    st.error(message)

        with col_login2:
            if st.button("🎲 Generieren", use_container_width=True):
                new_code = generate_user_code()
                st.session_state.user_code = new_code
                st.session_state.user_code_confirmed = True
                log_event("auth", "User generiert", {"user_code": new_code})
                st.rerun()

        st.caption("💡 Merke dir deinen Code, um später weiterzumachen!")

    st.markdown("---")

    # -------------------------------------------------------------------------
    # EINSTELLUNGEN (jetzt aus Config-System)
    # -------------------------------------------------------------------------
    st.header("⚙️ Einstellungen")

    # NEU: Mock-Modus aus Config-System lesen/schreiben
    mock_mode_toggle = st.checkbox(
        "🎭 Mock-Modus (ohne APIs)",
        value=is_mock_mode(),
        help="Aktiviert Beispiel-Transkripte und Mock-Feedback für Testing",
    )
    set_config("mock_mode", mock_mode_toggle)

    # API-Status anzeigen
    if not is_mock_mode():
        if MISTRAL_AVAILABLE:
            st.success("✅ Mistral API verfügbar")
        else:
            st.error("❌ Mistral API nicht verfügbar")
            st.caption("Aktiviere Mock-Modus oder prüfe mistral_services.py")

    # NEU: Debug-Modus Toggle (nur für Entwickler)
    if is_debug_mode():
        st.warning("🐛 Debug-Modus aktiv")
        
        # Zeige aktuelle Config
        with st.expander("🔧 Debug-Info"):
            st.caption(f"Session ID: {st.session_state.get('session_id', '–')[:8]}...")
            st.caption(f"Phase: {st.session_state.get('phase', '–')}")
            st.caption(f"Airtable: {'✅' if is_airtable_enabled() else '❌'}")
            st.caption(f"Pretest: {'✅' if st.session_state.get('pretest_completed') else '❌'}")

    st.markdown("---")

    if st.button("🔄 Neue Session", use_container_width=True):
        reset_session()
        st.rerun()

    # NEU: Link zum Admin-Dashboard
    st.markdown("---")
    st.page_link("pages/admin.py", label="🛠️ Admin Dashboard", icon="⚙️")

    st.markdown("---")
    st.caption("Großer Bär v0.6.1 – Eingabefelder Fix")


# =============================================================================
# CHECK: Nutzercode erforderlich
# =============================================================================

# Aktuell: Code ist optional, aber empfohlen
if not st.session_state.user_code_confirmed:
    st.info(
        "💡 **Tipp:** Gib in der Sidebar deinen Nutzercode ein, "
        "um deine Sessions zu verknüpfen und deinen Fortschritt zu tracken."
    )


# =============================================================================
# PRETEST FLOW (vor dem Hauptinhalt)
# =============================================================================

# Pretest nur anzeigen, wenn Nutzer eingeloggt ist UND Pretest nicht übersprungen
if st.session_state.user_code_confirmed:
    
    # NEU: Prüfe ob Pretest übersprungen werden soll (aus Admin-Config)
    if not should_skip_pretest():
        # Prüfe ob Pretest nötig
        if should_show_pretest(PRETEST_CONFIG):
            pretest_done = render_pretest(PRETEST_CONFIG)
            if not pretest_done:
                st.stop()  # Blockiere Hauptinhalt bis Pretest fertig
        
        # Prüfe Level-Recheck (alle N Sessions)
        if st.session_state.get("pretest_show_recheck", False):
            render_level_recheck(PRETEST_CONFIG)
            st.markdown("---")
    else:
        # Debug-Hinweis wenn Pretest übersprungen
        if is_debug_mode():
            st.warning("⏭️ Pretest wird übersprungen (Admin-Einstellung)")


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
- *Ich möchte flüssiger sprechen, ohne lange Pausen.*
- *Ich will formeller klingen – weniger umgangssprachlich.*
- *Ich übe, meine Argumente klar zu strukturieren.*
- *Ich möchte Konjunktiv II sicher verwenden.*
- *Ich will meine Nervosität in den Griff bekommen.*
- *Ich übe, höflich aber bestimmt zu formulieren.*
            """
        )

    learner_goal_input = st.text_area(
        "Was ist dein Ziel für diese Übung?",
        value=st.session_state.learner_goal,
        height=80,
        placeholder="z.B. Ich möchte heute üben, meine Punkte klar und strukturiert zu präsentieren.",
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
            placeholder="z.B. Ich habe nächste Woche ein echtes Meeting mit meinem Chef.",
            key="learner_context_input",
        )

    # Meta-Prompt aus Task anzeigen (falls vorhanden)
    if task.get("meta_prompts", {}).get("plan"):
        st.info(f"💡 **Planungshinweis:** {task['meta_prompts']['plan']}")

    # Weiter-Button
    st.markdown("---")
    col1, col2, col3 = st.columns([1, 2, 1])
    with col2:
        # Button-Text anpassen je nachdem ob Ziel eingegeben
        if not learner_goal_input.strip():
            st.caption("💡 Tipp: Ein konkretes Lernziel hilft dir, fokussiert zu bleiben.")

        if st.button("🎙️ Aufnahme starten", type="primary", use_container_width=True):
            # Ziel und Kontext speichern
            st.session_state.learner_goal = learner_goal_input.strip()
            st.session_state.learner_context = (
                st.session_state.get("learner_context_input", "").strip()
            )
            st.session_state.selected_task_id = task_id
            st.session_state.phase = "record"
            st.session_state.recording_start = datetime.now()
            
            # Event loggen
            log_event("session", "Aufnahme gestartet", {"task_id": task_id})
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
    if not is_mock_mode():
        # Echter Modus: Audio-Aufnahme
        try:
            from audio_recorder_streamlit import audio_recorder

            st.markdown("### 🎙️ Klicke zum Aufnehmen:")

            audio_bytes = audio_recorder(
                text="🎙️ Klicken zum Aufnehmen",
                recording_color="#C62828",   # Dunkelrot (Aufnahme = "Achtung!")
                neutral_color="#4CAF50",     # Grün (bereit) – passt zum Theme
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

            if is_mock_mode():
                # =============================================================
                # MOCK-MODUS (wie bisher)
                # =============================================================
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
                        "learner_goal": st.session_state.learner_goal,
                        "learner_context": st.session_state.learner_context,
                        "user_code": st.session_state.user_code,
                        # NEU: MASQ-Scores aus Pretest
                        "masq_scores": st.session_state.get("pretest_responses", {}).get("masq_scores", {}),
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
                    reflection="",
                )
                st.session_state.coach_input = coach_input

                # 3) Mock-Feedback (altes System)
                feedback = generate_feedback(
                    transcript=transcript_text,
                    task=task,
                    prosody=None,
                    use_mock=True,
                )

                st.session_state.feedback_result = feedback
                st.session_state.transcript_text = transcript_text
                
                # NEU: Mock-LLM-Call loggen
                log_llm_call("mock_feedback", coach_input, "Mock-Feedback generiert")

            else:
                # =============================================================
                # ECHTER MODUS MIT MISTRAL
                # =============================================================
                
                # 1) Audio transkribieren mit Voxtral (wenn Audio vorhanden)
                if st.session_state.audio_bytes and MISTRAL_AVAILABLE:
                    with st.spinner("🎙️ Transkribiere Audio mit Voxtral..."):
                        try:
                            transcript_text = transcribe_audio(st.session_state.audio_bytes)
                            log_event("voxtral", "Transkription erfolgreich", {"length": len(transcript_text)})
                        except Exception as e:
                            st.error(f"❌ Voxtral-Fehler: {str(e)}")
                            log_error("voxtral", str(e))
                            transcript_text = st.session_state.transcript or "Transkription fehlgeschlagen."
                else:
                    # Fallback: Text aus Mock-Eingabe oder Platzhalter
                    transcript_text = st.session_state.transcript or "Kein Text vorhanden."
                
                st.session_state.transcript_text = transcript_text

                # 2) Kleiner Bär: deterministische Analyse
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
                        "user_code": st.session_state.user_code,
                        # NEU: MASQ-Scores aus Pretest
                        "masq_scores": st.session_state.get("pretest_responses", {}).get("masq_scores", {}),
                    },
                )
                st.session_state.kleiner_baer_result = kb_result

                # 3) Coach-Input-Block bauen
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

                # 4) Mistral Coaching-Feedback
                if MISTRAL_AVAILABLE:
                    with st.spinner("🤖 Generiere Coaching-Feedback mit Mistral..."):
                        try:
                            mistral_feedback_text = generate_coach_feedback(coach_input)
                            feedback = MistralFeedback(mistral_feedback_text, kb_result.get("cefr", {}))
                            
                            # NEU: LLM-Call loggen
                            log_llm_call("mistral_coach", coach_input, mistral_feedback_text)
                            
                        except Exception as e:
                            st.error(f"❌ Mistral-Fehler: {str(e)}")
                            log_error("mistral", str(e), {"coach_input_keys": list(coach_input.keys())})
                            # Fallback auf Mock-Feedback
                            feedback = generate_feedback(
                                transcript=transcript_text,
                                task=task,
                                prosody=None,
                                use_mock=True,
                            )
                else:
                    # Mistral nicht verfügbar → Mock-Feedback
                    st.warning("⚠️ Mistral nicht verfügbar, nutze Mock-Feedback")
                    feedback = generate_feedback(
                        transcript=transcript_text,
                        task=task,
                        prosody=None,
                        use_mock=True,
                    )

                st.session_state.feedback_result = feedback

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
    tabs_list = ["💬 Feedback", "📝 Transkript", "📊 Metriken"]
    
    # NEU: LLM-Input Tab nur anzeigen wenn in Config aktiviert
    if get_config("show_llm_input_tab", True):
        tabs_list.append("🔌 LLM-Input")
    
    tabs = st.tabs(tabs_list)
    tab_feedback = tabs[0]
    tab_transcript = tabs[1]
    tab_metrics = tabs[2]
    tab_api = tabs[3] if len(tabs) > 3 else None

    # -------------------------------------------------------------------------
    # Tab: Feedback
    # -------------------------------------------------------------------------
    with tab_feedback:
        # CEFR-Badge (wenn möglich aus Kleiner Bär)
        col1, col2, col3 = st.columns([1, 2, 1])
        with col2:
            if cefr_from_kb:
                # Zeige auch Selbsteinschätzung zum Vergleich
                cefr_self = get_pretest_response("cefr_speaking")
                delta_text = f"Score: {cefr_from_kb.get('score', 0.0):.2f}"
                if cefr_self:
                    delta_text += f" | Selbst: {cefr_self}"
                
                st.metric(
                    "Geschätztes Niveau",
                    cefr_from_kb.get("label", "–"),
                    delta=delta_text,
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

        # Feedback anzeigen - unterscheide zwischen Mistral und Mock
        if hasattr(feedback, 'text'):
            # Mistral-Feedback (neues Format)
            st.markdown(feedback.text)
        else:
            # Altes Mock-Format
            st.markdown(format_feedback_markdown(feedback))

        # Hinweis zum Modus
        if hasattr(feedback, "is_mock") and feedback.is_mock:
            st.caption("ℹ️ Mock-Modus: Dies ist simuliertes Feedback für Testing.")
        elif not is_mock_mode() and MISTRAL_AVAILABLE:
            st.caption("🤖 Feedback generiert mit Mistral")

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

        if is_mock_mode():
            st.caption("ℹ️ Mock-Modus: Eingegebener Text")
        elif not is_mock_mode() and MISTRAL_AVAILABLE:
            st.caption("🎙️ Transkribiert mit Voxtral")

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
                help="Wörter pro Minute (120-150 ist normal)",
            )

        with col2:
            # Mock: Zähle typische Füllwörter
            filler_words = ["ähm", "also", "quasi", "sozusagen", "halt", "eigentlich"]
            filler_count = sum(transcript_text.lower().count(fw) for fw in filler_words)
            st.metric("Füllwörter", filler_count, help="ähm, also, quasi, etc.")

        with col3:
            st.metric("Flüssigkeit", "–" if is_mock_mode() else "75%")

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

        # NEU: MASQ-Profil anzeigen (wenn Pretest abgeschlossen)
        st.markdown("---")
        st.subheader("Metakognitives Profil (MASQ)")
        
        masq_scores = st.session_state.get("pretest_responses", {}).get("masq_scores", {})
        if masq_scores and masq_scores.get("factors"):
            factors = masq_scores.get("factors", {})
            cols = st.columns(5)
            factor_labels = {
                "PE": ("Planung", "Planning & Evaluation"),
                "PS": ("Problemlösung", "Problem-Solving"),
                "PK": ("Selbstbild", "Person Knowledge"),
                "DA": ("Fokus", "Directed Attention"),
                "MT": ("Übersetzung", "Mental Translation"),
            }
            for col, (key, (short, full)) in zip(cols, factor_labels.items()):
                if key in factors:
                    mean = factors[key].get("mean", 0)
                    # MT ist negativ (niedrig = gut)
                    if key == "MT":
                        col.metric(short, f"{mean:.1f}/5", delta="↓ besser", delta_color="inverse", help=full)
                    else:
                        col.metric(short, f"{mean:.1f}/5", help=full)
            
            st.caption(f"Gesamtscore: {masq_scores.get('total', 0)} – {masq_scores.get('level_label', '')}")
        else:
            st.info("MASQ-Profil wird nach dem Pretest angezeigt.")

        if is_mock_mode():
            st.caption(
                "ℹ️ Mock-Modus: Audio-Prosodie ist noch simuliert – "
                "Textmetriken sind bereits echt."
            )

    # -------------------------------------------------------------------------
    # Tab: LLM-Input (nur wenn aktiviert)
    # -------------------------------------------------------------------------
    if tab_api:
        with tab_api:
            st.subheader("LLM-Coach Input (JSON)")
            st.write(
                "Dieser Block wird an die LLM-Coach-API gesendet. "
                "Er enthält Task-Metadaten, Transkript, Pretest-Daten und deterministische Analyse "
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

    # Leitfragen als Inspiration – angepasst ans Lernziel + MASQ-basiert
    with st.expander("💡 Leitfragen zur Reflexion", expanded=False):
        reflection_prompts = """
**Was ist mir gut gelungen?**
- Wortwahl, Struktur, Flüssigkeit

**Was war schwierig?**
- Ein bestimmtes Wort, die Satzstellung, das Tempo

**Strategien (Problem-Solving):**
- Hast du Wörter umschrieben, wenn dir etwas nicht eingefallen ist?
- Hast du dich selbst korrigiert?

**Mentale Übersetzung:**
- Hast du während des Sprechens im Kopf übersetzt?
- Konntest du direkt auf Deutsch denken?

**Fokus & Konzentration:**
- Konntest du dich auf die Aufgabe konzentrieren?
- Warst du abgelenkt?

**Was will ich beim nächsten Mal anders machen?**
"""
        # Falls Lernziel vorhanden, zusätzliche Frage
        if st.session_state.learner_goal:
            reflection_prompts += (
                f"\n**Bezogen auf dein Ziel** "
                f"({st.session_state.learner_goal}): Wie gut hast du es erreicht?"
            )

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
            log_event("session", "Reflexion gespeichert", {"length": len(reflection_input)})
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
            st.session_state.session_saved = False
            st.rerun()

    with col2:
        if st.button("📋 Andere Aufgabe"):
            reset_session()
            st.rerun()

    with col3:
        # Session speichern Button mit Webhook-Anbindung
        if st.session_state.session_saved:
            st.success("✅ Gespeichert!")
        else:
            if st.button("💾 Session speichern", type="primary"):
                # Reflexion aktualisieren falls vorhanden
                if reflection_input:
                    st.session_state.reflection_text = reflection_input
                    update_coach_input_with_reflection(reflection_input)
                
                # An Airtable senden
                with st.spinner("Speichere Session..."):
                    success, message = send_session_to_airtable()
                
                if success:
                    st.session_state.session_saved = True
                    st.rerun()
                else:
                    st.error(f"❌ {message}")


# =============================================================================
# FOOTER
# =============================================================================

st.markdown("---")
st.caption(
    "🐻 Großer Bär v0.6.1 – Eingabefelder Fix mit Kleiner Bär Textanalyse + Mistral"
)
