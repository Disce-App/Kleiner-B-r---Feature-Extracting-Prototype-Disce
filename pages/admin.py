"""
🛠️ Admin Dashboard für Großer Bär
Debugging, Logging, Konfiguration und Screen Navigator.
"""

import streamlit as st
import json
from datetime import datetime
import uuid

# Config laden
from config.app_config import (
    init_app_config,
    get_config,
    set_config,
    get_logs,
    clear_logs,
    export_state_as_json,
    DEFAULT_SETTINGS,
)

# Pretest-Config (optional)
try:
    from config.pretest_loader import load_pretest_config
    PRETEST_AVAILABLE = True
except ImportError:
    PRETEST_AVAILABLE = False


# =============================================================================
# PAGE CONFIG
# =============================================================================

st.set_page_config(
    page_title="Admin – Großer Bär",
    page_icon="🛠️",
    layout="wide"
)


# =============================================================================
# SCREEN NAVIGATOR: Mock-Daten für realistische Tests
# =============================================================================

MOCK_DATA = {
    "transcript": """Guten Tag, mein Name ist Maria Schneider. Ich freue mich, heute die Möglichkeit zu haben, mich Ihnen vorzustellen.

Ich habe meinen Master in Wirtschaftsinformatik an der TU München abgeschlossen und arbeite seit drei Jahren als Projektmanagerin bei einem mittelständischen IT-Unternehmen.

In meiner aktuellen Position bin ich verantwortlich für die Koordination von agilen Entwicklungsteams und die Kommunikation mit unseren internationalen Kunden. Dabei habe ich besonders meine Fähigkeiten in der interkulturellen Zusammenarbeit und im Stakeholder-Management ausgebaut.

Für diese Position bringe ich nicht nur meine technische Expertise mit, sondern auch meine Leidenschaft für innovative Lösungen und meine Erfahrung in der Führung von cross-funktionalen Teams.

Ich freue mich auf Ihre Fragen.""",

    "learner_goal": "Ich möchte meine Vorstellung klar strukturieren und professionell wirken.",
    
    "learner_context": "Ich habe nächste Woche ein echtes Bewerbungsgespräch bei einem großen Konzern.",
    
    "pretest_responses": {
        "cefr_overall": {"value": "B2", "answered_at": "2026-01-23T14:30:00"},
        "cefr_speaking": {"value": "B2", "answered_at": "2026-01-23T14:30:15"},
        "has_official_cert": {"value": True, "answered_at": "2026-01-23T14:30:20"},
        "official_cert_type": {"value": "Goethe B2 (bestanden)", "answered_at": "2026-01-23T14:30:25"},
        "native_language": {"value": "Spanisch", "answered_at": "2026-01-23T14:29:00"},
        "other_languages": {"value": "Englisch (C1), Französisch (A2)", "answered_at": "2026-01-23T14:29:10"},
        "learning_duration_months": {"value": 36, "answered_at": "2026-01-23T14:29:30"},
        "learning_context": {"value": ["university", "work", "living_dach"], "answered_at": "2026-01-23T14:29:45"},
        "masq_scores": {
            "factors": {
                "PE": {"mean": 4.0, "sum": 8, "items": 2},
                "PS": {"mean": 3.7, "sum": 11, "items": 3},
                "PK": {"mean": 3.3, "sum": 10, "items": 3},
                "DA": {"mean": 3.5, "sum": 7, "items": 2},
                "MT": {"mean": 2.5, "sum": 5, "items": 2}
            },
            "total": 31,
            "level": "medium",
            "level_label": "Mittlere metakognitive Awareness"
        }
    },
    
    "kleiner_baer_result": {
        "metrics_summary": {
            "word_count": 142,
            "sentence_count": 8,
            "avg_sentence_length": 17.75,
            "type_token_ratio": 0.72,
            "lexical_density": 0.58,
            "filler_count": 0,
            "filler_ratio": 0.0,
            "connector_count": 5,
            "modal_verb_count": 2,
            "subjunctive_count": 0,
            "formal_markers": ["freue mich", "Möglichkeit", "verantwortlich", "Expertise"],
            "informal_markers": []
        },
        "cefr": {
            "label": "B2",
            "score": 0.72,
            "confidence": 0.81,
            "indicators": {
                "vocabulary": "B2",
                "syntax": "B2",
                "coherence": "B2"
            }
        },
        "disce_metrics": {
            "level_match": 0.85,
            "prosody_intelligibility": 0.78,
            "sentence_cohesion": 0.82,
            "task_exam_fit": 0.90,
            "goal_progress": 0.75
        },
        "hotspots": [
            {
                "type": "strength",
                "text": "klare Struktur",
                "severity": "positive",
                "suggestion": "Gute chronologische Gliederung: Ausbildung → Erfahrung → Stärken"
            },
            {
                "type": "register_match",
                "text": "formell-professionell",
                "severity": "positive",
                "suggestion": "Angemessenes Register für Bewerbungsgespräch"
            }
        ],
        "register_analysis": {
            "target": "formell-professionell",
            "detected": "formell-professionell",
            "match_score": 0.90,
            "formal_features": 4,
            "informal_features": 0
        }
    },
    
    "feedback_text": """## 🎯 Aufgabenerfüllung

Sie haben die Aufgabe gut erfüllt: Ihr Werdegang ist klar nachvollziehbar, und Sie haben einen Bogen zur angestrebten Position geschlagen. Besonders stark: Die Verbindung zwischen Ihrer Erfahrung und den Anforderungen der neuen Rolle.

## 🧱 Struktur & roter Faden

Ihre Präsentation folgt einer klaren Chronologie (Ausbildung → aktuelle Position → Stärken → Abschluss). Der rote Faden ist durchgehend erkennbar. 

**Tipp:** Der Einstieg könnte noch prägnanter sein – statt der Floskel "Ich freue mich..." könnten Sie direkt mit Ihrem Kurzprofil starten.

## 🎭 Ton & Wirkung

Der Ton ist angemessen formell-professionell. Sie klingen kompetent und selbstsicher. Die Formulierung "Leidenschaft für innovative Lösungen" wirkt authentisch.

## 💬 Sprache im Detail

- **Zeitformen:** Korrekt eingesetzt (Perfekt für Vergangenes, Präsens für Aktuelles)
- **Wortschatz:** Guter Einsatz von Fachbegriffen (Stakeholder-Management, cross-funktional)
- **Satzbau:** Variiert und angemessen komplex

## 📌 Fokus fürs nächste Mal

**Einstieg schärfen:** Probieren Sie einen direkteren Einstieg wie: "Ich bin Projektmanagerin mit Schwerpunkt agile Methoden und bringe drei Jahre Erfahrung in der IT-Branche mit."
"""
}


# Screen-Definitionen mit allen nötigen States
SCREEN_DEFINITIONS = {
    "login": {
        "name": "🔐 Login",
        "description": "Nutzercode-Eingabe in der Sidebar",
        "category": "Auth",
        "states": {
            "user_code_confirmed": False,
            "user_code": "",
        }
    },
    "pretest_cefr": {
        "name": "📋 Pretest: CEFR",
        "description": "CEFR-Selbsteinschätzung (Modul 0)",
        "category": "Pretest",
        "states": {
            "user_code_confirmed": True,
            "user_code": "TEST_NAV",
            "pretest_completed": False,
            "pretest_current_module": 0,
            "pretest_responses": {},
        }
    },
    "pretest_masq": {
        "name": "📋 Pretest: MASQ",
        "description": "MASQ-Fragebogen (Modul 1)",
        "category": "Pretest",
        "states": {
            "user_code_confirmed": True,
            "user_code": "TEST_NAV",
            "pretest_completed": False,
            "pretest_current_module": 1,
            "pretest_responses": {
                "cefr_overall": {"value": "B2", "answered_at": "2026-01-23T14:30:00"},
                "cefr_speaking": {"value": "B2", "answered_at": "2026-01-23T14:30:15"},
                "has_official_cert": {"value": False, "answered_at": "2026-01-23T14:30:20"},
                "learning_duration_months": {"value": 24, "answered_at": "2026-01-23T14:29:30"},
                "learning_context": {"value": ["university", "self_study"], "answered_at": "2026-01-23T14:29:45"},
                "native_language": {"value": "Englisch", "answered_at": "2026-01-23T14:29:00"},
            },
        }
    },
    "level_recheck": {
        "name": "🔄 Level-Recheck",
        "description": "Niveau-Nachfrage (alle 5 Sessions)",
        "category": "Pretest",
        "states": {
            "user_code_confirmed": True,
            "user_code": "TEST_NAV",
            "pretest_completed": True,
            "pretest_show_recheck": True,
            "session_count": 5,
            "phase": "select",
        }
    },
    "phase_select": {
        "name": "1️⃣ Task-Auswahl",
        "description": "Aufgabe wählen + Lernziel setzen",
        "category": "Coach-Loop",
        "states": {
            "user_code_confirmed": True,
            "user_code": "TEST_NAV",
            "pretest_completed": True,
            "pretest_show_recheck": False,
            "phase": "select",
            "selected_task_id": None,
        }
    },
    "phase_record": {
        "name": "2️⃣ Aufnahme",
        "description": "Mock-Texteingabe / Audio-Aufnahme",
        "category": "Coach-Loop",
        "states": {
            "user_code_confirmed": True,
            "user_code": "TEST_NAV",
            "pretest_completed": True,
            "phase": "record",
            "selected_task_id": "cv_self_presentation",
            "recording_start": None,  # Wird dynamisch gesetzt
        }
    },
    "phase_feedback": {
        "name": "3️⃣ Feedback",
        "description": "Feedback-Anzeige mit allen Tabs",
        "category": "Coach-Loop",
        "requires_mock_data": True,
        "states": {
            "user_code_confirmed": True,
            "user_code": "TEST_NAV",
            "pretest_completed": True,
            "phase": "feedback",
            "selected_task_id": "cv_self_presentation",
        }
    },
}


def apply_screen_state(screen_id: str, use_mock_data: bool = True):
    """Setzt alle States für einen bestimmten Screen."""
    
    if screen_id not in SCREEN_DEFINITIONS:
        return False, f"Screen '{screen_id}' nicht gefunden"
    
    screen = SCREEN_DEFINITIONS[screen_id]
    
    # States setzen
    for key, value in screen["states"].items():
        if key == "recording_start" and value is None:
            st.session_state[key] = datetime.now()
        else:
            st.session_state[key] = value
    
    # Mock-Daten laden wenn nötig
    if use_mock_data and screen.get("requires_mock_data"):
        # Pretest-Daten
        if not st.session_state.get("pretest_responses"):
            st.session_state.pretest_responses = MOCK_DATA["pretest_responses"].copy()
        
        # Session-Daten
        st.session_state.session_id = str(uuid.uuid4())
        st.session_state.learner_goal = MOCK_DATA["learner_goal"]
        st.session_state.learner_context = MOCK_DATA["learner_context"]
        st.session_state.transcript = MOCK_DATA["transcript"]
        st.session_state.transcript_text = MOCK_DATA["transcript"]
        st.session_state.recording_start = datetime.now()
        
        # Analyse-Daten
        st.session_state.kleiner_baer_result = MOCK_DATA["kleiner_baer_result"].copy()
        
        # Coach-Input bauen
        st.session_state.coach_input = {
            "user": {
                "code": st.session_state.get("user_code", "TEST_NAV"),
                "is_anonymous": False,
            },
            "pretest": {
                "self_assessment": {
                    "cefr_overall": "B2",
                    "cefr_speaking": "B2",
                },
                "masq": MOCK_DATA["pretest_responses"]["masq_scores"],
            },
            "task_metadata": {
                "task_id": "cv_self_presentation",
                "situation": "Sie sind in einem Bewerbungsgespräch.",
                "task": "Stellen Sie sich und Ihren beruflichen Werdegang vor.",
                "target_level": "B2-C1",
                "target_register": "formell-professionell",
                "time_limit_seconds": 90,
            },
            "session_metadata": {
                "session_id": st.session_state.session_id,
                "mode": "mock_speaking",
                "duration_seconds": 85,
            },
            "learner_planning": {
                "goal": MOCK_DATA["learner_goal"],
                "context": MOCK_DATA["learner_context"],
            },
            "transcript": MOCK_DATA["transcript"],
            "analysis": {
                "layer1_deterministic": MOCK_DATA["kleiner_baer_result"]["metrics_summary"],
                "cefr": MOCK_DATA["kleiner_baer_result"]["cefr"],
                "home_kpis": MOCK_DATA["kleiner_baer_result"]["disce_metrics"],
                "hotspots": MOCK_DATA["kleiner_baer_result"]["hotspots"],
            },
            "reflection": {"text": "", "submitted_at": None},
        }
        
        # Mock-Feedback erstellen
        class MockFeedback:
            def __init__(self):
                self.text = MOCK_DATA["feedback_text"]
                self.cefr_label = "B2"
                self.cefr_score = 0.72
                self.is_mock = True
        
        st.session_state.feedback_result = MockFeedback()
    
    # Pretest-Daten für alle Screens außer Login
    if use_mock_data and screen_id not in ["login", "pretest_cefr"]:
        if not st.session_state.get("pretest_responses"):
            st.session_state.pretest_responses = MOCK_DATA["pretest_responses"].copy()
    
    return True, f"Screen '{screen['name']}' geladen"


# =============================================================================
# JSON SCHEMAS (Erwartete Strukturen mit Beispielwerten)
# =============================================================================

JSON_SCHEMAS = {
    # =========================================================================
    # CONFIG
    # =========================================================================
    "app_config": {
        "mock_mode": True,
        "debug_mode": False,
        "skip_pretest": False,
        "disable_airtable": False,
        "log_payloads": True,
        "log_llm_calls": True,
        "show_metrics_tab": True,
        "show_llm_input_tab": True,
    },
    
    "pretest_config": {
        "version": "1.0",
        "modules": [
            {
                "id": "cefr_self_assessment",
                "title": "CEFR-Selbsteinschätzung",
                "questions": ["..."]
            },
            {
                "id": "masq_short",
                "title": "MASQ – Metakognitive Awareness",
                "scoring": {
                    "factors": ["PE", "PS", "PK", "DA", "MT"],
                    "scale": "1-5"
                }
            }
        ],
        "level_recheck_interval": 5
    },
    
    # =========================================================================
    # PRETEST
    # =========================================================================
    "pretest_responses": MOCK_DATA["pretest_responses"],
    
    "masq_scores": MOCK_DATA["pretest_responses"]["masq_scores"],
    
    # =========================================================================
    # SESSION
    # =========================================================================
    "coach_input": {
        "user": {
            "code": "ABC123",
            "is_anonymous": False
        },
        "pretest": {
            "completed": True,
            "cefr_self_speaking": "B2",
            "masq_level": "medium",
        },
        "task_metadata": {
            "task_id": "cv_self_presentation",
            "situation": "Sie sind in einem Bewerbungsgespräch.",
            "task": "Stellen Sie sich und Ihren beruflichen Werdegang vor.",
            "target_level": "B2-C1",
            "target_register": "formell-professionell",
            "time_limit_seconds": 90
        },
        "session_metadata": {
            "session_id": "550e8400-e29b-41d4-a716-446655440000",
            "session_number": 3,
            "mode": "speaking",
            "duration_seconds": 85
        },
        "learner_planning": {
            "goal": "Ich möchte meine Vorstellung klar strukturieren",
            "context": "Bewerbungsgespräch nächste Woche"
        },
        "transcript": "[Transkript der Aufnahme]",
        "analysis": {
            "layer1_deterministic": {},
            "cefr": {"label": "B2", "score": 0.72},
            "home_kpis": {},
            "hotspots": []
        },
        "reflection": {
            "text": "",
            "submitted_at": None
        }
    },
    
    "current_task": {
        "id": "cv_self_presentation",
        "title": "Lebenslauf vorstellen im Bewerbungsgespräch",
        "situation": "Sie sind in einem Bewerbungsgespräch.",
        "task": "Stellen Sie sich und Ihren beruflichen Werdegang vor.",
        "time_seconds": 90,
        "register": "formell-professionell",
        "cefr_target": "B2-C1",
    },
    
    "session_metadata": {
        "session_id": "550e8400-e29b-41d4-a716-446655440000",
        "user_code": "ABC123",
        "session_count": 3,
        "phase": "feedback",
    },
    
    # =========================================================================
    # ANALYSE (Kleiner Bär Output)
    # =========================================================================
    "kleiner_baer_result": MOCK_DATA["kleiner_baer_result"],
    
    "cefr_estimation": MOCK_DATA["kleiner_baer_result"]["cefr"],
    
    "disce_metrics": MOCK_DATA["kleiner_baer_result"]["disce_metrics"],
    
    "hotspots": MOCK_DATA["kleiner_baer_result"]["hotspots"],
    
    # =========================================================================
    # LOGS
    # =========================================================================
    "payload_log_entry": {
        "timestamp": "2026-01-23T15:03:00",
        "endpoint": "make_webhook",
        "payload": {"session_id": "...", "user_code": "ABC123"},
        "response": {"status_code": 200}
    },
    
    "llm_call_log_entry": {
        "timestamp": "2026-01-23T15:02:00",
        "prompt_type": "gpt_coach",
        "model": "gpt-4o-mini",
        "input": {"coach_input": "..."},
        "output": "## Feedback...",
        "tokens_used": {"total": 1170}
    },
    
    "error_log_entry": {
        "timestamp": "2026-01-23T15:02:15",
        "error_type": "whisper",
        "message": "Audio file too short"
    },
    
    "event_log_entry": {
        "timestamp": "2026-01-23T14:55:00",
        "event_type": "auth",
        "message": "User eingeloggt"
    }
}


# =============================================================================
# AUTH CHECK (einfacher Passwortschutz)
# =============================================================================

def check_admin_auth() -> bool:
    """Einfacher Passwortschutz für Admin-Bereich."""
    
    if st.session_state.get("admin_authenticated", False):
        return True
    
    st.title("🔐 Admin-Zugang")
    st.markdown("Bitte Passwort eingeben, um auf das Admin-Dashboard zuzugreifen.")
    
    try:
        correct_password = st.secrets.get("ADMIN_PASSWORD", "disce2026")
    except:
        correct_password = "disce2026"
    
    password = st.text_input("Passwort", type="password", key="admin_password_input")
    
    if st.button("Anmelden", type="primary"):
        if password == correct_password:
            st.session_state.admin_authenticated = True
            st.rerun()
        else:
            st.error("❌ Falsches Passwort")
    
    st.caption("💡 Tipp: Setze `ADMIN_PASSWORD` in deinen Streamlit Secrets.")
    
    return False


# =============================================================================
# JSON VIEWER HELPER (mit Schema + Live-Daten)
# =============================================================================

def render_json_with_schema(
    live_data, 
    schema_key: str, 
    title: str, 
    description: str = "",
    expanded: bool = False
):
    """
    Rendert einen JSON-Block mit zwei Tabs:
    1. 📐 Schema – Erwartete Struktur mit Beispielwerten
    2. 📊 Live – Aktuelle Daten aus der Session
    """
    
    schema = JSON_SCHEMAS.get(schema_key, {})
    has_live_data = live_data and (
        (isinstance(live_data, dict) and len(live_data) > 0) or
        (isinstance(live_data, list) and len(live_data) > 0)
    )
    
    # Status-Icon
    if has_live_data:
        status_icon = "✅"
        status_text = "Daten vorhanden"
    else:
        status_icon = "⬜"
        status_text = "Noch keine Daten"
    
    with st.expander(f"{status_icon} {title}", expanded=expanded):
        if description:
            st.caption(description)
        
        # Zwei Tabs: Schema und Live-Daten
        tab_schema, tab_live = st.tabs(["📐 Schema (Beispiel)", "📊 Live-Daten"])
        
        with tab_schema:
            if schema:
                st.json(schema)
                st.caption("☝️ So sieht die erwartete Struktur aus")
            else:
                st.info("Kein Schema definiert")
        
        with tab_live:
            if has_live_data:
                st.json(live_data)
                
                # Download-Button
                try:
                    json_str = json.dumps(live_data, indent=2, ensure_ascii=False, default=str)
                    st.download_button(
                        "📥 Herunterladen",
                        data=json_str,
                        file_name=f"{schema_key}.json",
                        mime="application/json",
                        key=f"dl_{schema_key}_{id(live_data)}"
                    )
                except Exception as e:
                    st.warning(f"Export fehlgeschlagen: {e}")
            else:
                st.info("🔹 Noch keine Daten vorhanden")
                st.caption(get_data_hint(schema_key))


def get_data_hint(schema_key: str) -> str:
    """Gibt einen Hinweis, wann diese Daten befüllt werden."""
    hints = {
        "pretest_responses": "→ Wird befüllt, wenn der User den Pretest abschließt",
        "masq_scores": "→ Wird im MASQ-Modul des Pretests berechnet",
        "coach_input": "→ Wird erstellt, wenn eine Sprechübung abgeschlossen wird",
        "current_task": "→ Wird gesetzt, wenn eine Aufgabe ausgewählt wird",
        "session_metadata": "→ Enthält Daten der aktuellen Session",
        "kleiner_baer_result": "→ Wird nach der Textanalyse befüllt (Phase 3)",
        "cefr_estimation": "→ Teil der Kleiner-Bär-Analyse",
        "disce_metrics": "→ Teil der Kleiner-Bär-Analyse",
        "hotspots": "→ Erkannte Problemstellen aus der Analyse",
        "payloads": "→ Wenn Daten an Airtable gesendet werden",
        "llm_calls": "→ Wenn GPT-Feedback generiert wird",
        "errors": "→ Bei Fehlern in der App",
        "events": "→ Bei Login, Session-Start, etc.",
    }
    return hints.get(schema_key, "→ Nutze den Screen Navigator oder Mock-Generatoren")


def get_all_jsons() -> dict:
    """Sammelt alle relevanten JSONs aus der App."""
    
    jsons = {
        "config": {},
        "pretest": {},
        "session": {},
        "analysis": {},
        "logs": {},
    }
    
    # =========================================================================
    # 1. KONFIGURATION
    # =========================================================================
    
    jsons["config"]["app_config"] = {
        "data": st.session_state.get("app_config", DEFAULT_SETTINGS),
        "description": "Aktuelle App-Einstellungen",
        "source": "session_state.app_config"
    }
    
    if PRETEST_AVAILABLE:
        try:
            pretest_config = load_pretest_config()
            jsons["config"]["pretest_config"] = {
                "data": pretest_config,
                "description": "Pretest-Konfiguration (Module, Fragen)",
                "source": "config/pretest_config.json"
            }
        except:
            jsons["config"]["pretest_config"] = {
                "data": {},
                "description": "Nicht geladen",
                "source": "config/pretest_config.json"
            }
    
    # =========================================================================
    # 2. PRETEST-DATEN
    # =========================================================================
    
    jsons["pretest"]["pretest_responses"] = {
        "data": st.session_state.get("pretest_responses", {}),
        "description": "Alle Pretest-Antworten",
        "source": "session_state.pretest_responses"
    }
    
    masq = st.session_state.get("pretest_responses", {}).get("masq_scores", {})
    jsons["pretest"]["masq_scores"] = {
        "data": masq,
        "description": "Berechnete MASQ-Scores",
        "source": "pretest_responses.masq_scores"
    }
    
    # =========================================================================
    # 3. SESSION-DATEN
    # =========================================================================
    
    jsons["session"]["coach_input"] = {
        "data": st.session_state.get("coach_input", {}),
        "description": "JSON für LLM-Coach-API ⭐",
        "source": "session_state.coach_input"
    }
    
    task_id = st.session_state.get("selected_task_id")
    task_data = {}
    if task_id:
        try:
            from grosser_baer import get_task
            task_data = get_task(task_id)
        except:
            task_data = {"task_id": task_id}
    jsons["session"]["current_task"] = {
        "data": task_data,
        "description": f"Aktuelle Aufgabe",
        "source": "grosser_baer.get_task()"
    }
    
    jsons["session"]["session_metadata"] = {
        "data": {
            "session_id": st.session_state.get("session_id"),
            "user_code": st.session_state.get("user_code"),
            "session_count": st.session_state.get("session_count", 0),
            "phase": st.session_state.get("phase"),
            "recording_start": str(st.session_state.get("recording_start", "")),
            "learner_goal": st.session_state.get("learner_goal", ""),
            "learner_context": st.session_state.get("learner_context", ""),
            "reflection_text": st.session_state.get("reflection_text", ""),
            "transcript": (st.session_state.get("transcript", "") or "")[:200] + "..." 
                if len(st.session_state.get("transcript", "") or "") > 200 
                else st.session_state.get("transcript", ""),
        },
        "description": "Metadaten der aktuellen Session",
        "source": "session_state"
    }
    
    # =========================================================================
    # 4. ANALYSE-DATEN
    # =========================================================================
    
    kb = st.session_state.get("kleiner_baer_result", {})
    
    jsons["analysis"]["kleiner_baer_result"] = {
        "data": kb,
        "description": "Vollständige Kleiner-Bär-Analyse",
        "source": "session_state.kleiner_baer_result"
    }
    
    jsons["analysis"]["cefr_estimation"] = {
        "data": kb.get("cefr", {}),
        "description": "CEFR-Level-Schätzung",
        "source": "kleiner_baer_result.cefr"
    }
    
    jsons["analysis"]["disce_metrics"] = {
        "data": kb.get("disce_metrics", {}),
        "description": "Disce-KPIs",
        "source": "kleiner_baer_result.disce_metrics"
    }
    
    jsons["analysis"]["hotspots"] = {
        "data": kb.get("hotspots", []),
        "description": "Erkannte Problemstellen",
        "source": "kleiner_baer_result.hotspots"
    }
    
    # =========================================================================
    # 5. LOGS
    # =========================================================================
    
    logs = st.session_state.get("debug_logs", {})
    
    jsons["logs"]["payloads"] = {
        "data": logs.get("payloads", []),
        "description": "Gesendete Payloads",
        "source": "debug_logs.payloads"
    }
    
    jsons["logs"]["llm_calls"] = {
        "data": logs.get("llm_calls", []),
        "description": "LLM-Aufrufe",
        "source": "debug_logs.llm_calls"
    }
    
    jsons["logs"]["errors"] = {
        "data": logs.get("errors", []),
        "description": "Fehler",
        "source": "debug_logs.errors"
    }
    
    jsons["logs"]["events"] = {
        "data": logs.get("events", []),
        "description": "Events",
        "source": "debug_logs.events"
    }
    
    return jsons


# =============================================================================
# MAIN ADMIN UI
# =============================================================================

def render_admin_dashboard():
    """Hauptfunktion für Admin-Dashboard."""
    
    init_app_config()
    
    st.title("🛠️ Admin Dashboard")
    st.caption("Debugging, Logging, Konfiguration und Screen Navigator für Großer Bär")
    
    # Tabs – NEU: Screen Navigator als erster Tab
    tab_nav, tab_json, tab_settings, tab_state, tab_logs, tab_actions = st.tabs([
        "🧭 Screen Navigator",
        "📋 JSON Viewer",
        "⚙️ Einstellungen",
        "📊 Session State",
        "📝 Logs",
        "🔧 Actions"
    ])
    
    # =========================================================================
    # TAB 0: SCREEN NAVIGATOR (NEU)
    # =========================================================================
    with tab_nav:
        st.header("🧭 Screen Navigator")
        st.markdown(
            "Springe direkt zu jedem Screen der App – ideal für UX-Testing. "
            "Mock-Daten werden automatisch geladen."
        )
        
        # Aktuellen Status anzeigen
        col_status1, col_status2, col_status3, col_status4 = st.columns(4)
        with col_status1:
            st.metric("Phase", st.session_state.get("phase", "–"))
        with col_status2:
            st.metric("User", st.session_state.get("user_code", "–") or "–")
        with col_status3:
            pretest_done = "✅" if st.session_state.get("pretest_completed") else "❌"
            st.metric("Pretest", pretest_done)
        with col_status4:
            st.metric("Task", st.session_state.get("selected_task_id", "–") or "–")
        
        st.markdown("---")
        
        # Screens nach Kategorie gruppieren
        categories = {}
        for screen_id, screen in SCREEN_DEFINITIONS.items():
            cat = screen.get("category", "Sonstige")
            if cat not in categories:
                categories[cat] = []
            categories[cat].append((screen_id, screen))
        
        # Screen-Buttons in Spalten nach Kategorie
        for category, screens in categories.items():
            st.subheader(f"{category}")
            
            cols = st.columns(len(screens))
            for col, (screen_id, screen) in zip(cols, screens):
                with col:
                    # Button mit Description als Tooltip-artige Caption
                    if st.button(
                        screen["name"], 
                        key=f"nav_{screen_id}",
                        use_container_width=True,
                        help=screen["description"]
                    ):
                        success, message = apply_screen_state(screen_id, use_mock_data=True)
                        if success:
                            st.success(message)
                            st.markdown("👉 **Gehe jetzt zur Coach-App:**")
                            st.page_link(
                                "pages/grosser_baer.py", 
                                label="🐻 Großer Bär öffnen", 
                                icon="🐻"
                            )
                        else:
                            st.error(message)
                    st.caption(screen["description"])
        
        st.markdown("---")
        
        # Quick-Links
        st.subheader("🔗 Quick Links")
        col1, col2 = st.columns(2)
        with col1:
            st.page_link("pages/grosser_baer.py", label="🐻 Zur Coach-App", icon="🐻")
        with col2:
            if st.button("🔄 Alle States zurücksetzen", use_container_width=True):
                keys_to_keep = ["admin_authenticated", "app_config"]
                keys_to_delete = [k for k in st.session_state.keys() if k not in keys_to_keep]
                for key in keys_to_delete:
                    del st.session_state[key]
                st.success("States zurückgesetzt!")
                st.rerun()
        
        # Hilfe-Text
        with st.expander("ℹ️ Wie funktioniert der Screen Navigator?"):
            st.markdown("""
**So nutzt du den Screen Navigator:**

1. **Klicke auf einen Screen-Button** – die nötigen Session-States werden automatisch gesetzt
2. **Gehe zur Coach-App** – der entsprechende Screen wird angezeigt
3. **Teste die UI** – prüfe Look & Feel, Texte, Interaktionen

**Mock-Daten:**
- Für den **Feedback-Screen** werden realistische Beispieldaten geladen:
  - Transkript einer Bewerbungsvorstellung
  - CEFR-Analyse (B2)
  - MASQ-Scores
  - Vollständiges Coach-Feedback

**Kategorien:**
- **Auth:** Login-Flow
- **Pretest:** CEFR-Selbsteinschätzung, MASQ, Level-Recheck
- **Coach-Loop:** Die 3 Hauptphasen (Auswahl → Aufnahme → Feedback)
            """)
    
    # =========================================================================
    # TAB 1: JSON VIEWER
    # =========================================================================
    with tab_json:
        st.header("📋 Alle JSONs")
        st.markdown(
            "Jedes JSON hat zwei Ansichten: "
            "**📐 Schema** (erwartete Struktur) und **📊 Live** (aktuelle Daten)"
        )
        
        all_jsons = get_all_jsons()
        
        # Kategorie-Tabs
        json_tabs = st.tabs([
            "🎯 Session & Coach",
            "🔬 Analyse",
            "📝 Pretest",
            "⚙️ Config",
            "📊 Logs"
        ])
        
        # -----------------------------------------------------------------
        # SESSION & COACH
        # -----------------------------------------------------------------
        with json_tabs[0]:
            st.subheader("🎯 Session & Coach-Input")
            st.caption("Diese JSONs sind zentral für den Coach-Loop")
            
            item = all_jsons["session"]["coach_input"]
            render_json_with_schema(
                item["data"],
                "coach_input",
                "coach_input ⭐ (LLM-Input)",
                f"{item['description']} | `{item['source']}`",
                expanded=True
            )
            
            item = all_jsons["session"]["current_task"]
            render_json_with_schema(
                item["data"],
                "current_task",
                "current_task",
                f"{item['description']} | `{item['source']}`"
            )
            
            item = all_jsons["session"]["session_metadata"]
            render_json_with_schema(
                item["data"],
                "session_metadata",
                "session_metadata",
                f"{item['description']} | `{item['source']}`"
            )
        
        # -----------------------------------------------------------------
        # ANALYSE
        # -----------------------------------------------------------------
        with json_tabs[1]:
            st.subheader("🔬 Analyse-Daten (Kleiner Bär)")
            st.caption("Output der deterministischen Textanalyse")
            
            item = all_jsons["analysis"]["kleiner_baer_result"]
            render_json_with_schema(
                item["data"],
                "kleiner_baer_result",
                "kleiner_baer_result (komplett)",
                f"{item['description']} | `{item['source']}`",
                expanded=True
            )
            
            item = all_jsons["analysis"]["cefr_estimation"]
            render_json_with_schema(
                item["data"],
                "cefr_estimation",
                "cefr_estimation",
                f"{item['description']} | `{item['source']}`"
            )
            
            item = all_jsons["analysis"]["disce_metrics"]
            render_json_with_schema(
                item["data"],
                "disce_metrics",
                "disce_metrics",
                f"{item['description']} | `{item['source']}`"
            )
            
            item = all_jsons["analysis"]["hotspots"]
            render_json_with_schema(
                item["data"],
                "hotspots",
                "hotspots",
                f"{item['description']} | `{item['source']}`"
            )
        
        # -----------------------------------------------------------------
        # PRETEST
        # -----------------------------------------------------------------
        with json_tabs[2]:
            st.subheader("📝 Pretest-Daten")
            st.caption("Selbsteinschätzung und MASQ-Scores")
            
            item = all_jsons["pretest"]["pretest_responses"]
            render_json_with_schema(
                item["data"],
                "pretest_responses",
                "pretest_responses (alle Antworten)",
                f"{item['description']} | `{item['source']}`",
                expanded=True
            )
            
            item = all_jsons["pretest"]["masq_scores"]
            render_json_with_schema(
                item["data"],
                "masq_scores",
                "masq_scores",
                f"{item['description']} | `{item['source']}`"
            )
        
        # -----------------------------------------------------------------
        # CONFIG
        # -----------------------------------------------------------------
        with json_tabs[3]:
            st.subheader("⚙️ Konfiguration")
            
            item = all_jsons["config"]["app_config"]
            render_json_with_schema(
                item["data"],
                "app_config",
                "app_config (Feature Flags)",
                f"{item['description']} | `{item['source']}`",
                expanded=True
            )
            
            if "pretest_config" in all_jsons["config"]:
                item = all_jsons["config"]["pretest_config"]
                render_json_with_schema(
                    item["data"],
                    "pretest_config",
                    "pretest_config",
                    f"{item['description']} | `{item['source']}`"
                )
        
        # -----------------------------------------------------------------
        # LOGS
        # -----------------------------------------------------------------
        with json_tabs[4]:
            st.subheader("📊 Debug-Logs")
            
            for key in ["payloads", "llm_calls", "errors", "events"]:
                item = all_jsons["logs"][key]
                count = len(item["data"]) if isinstance(item["data"], list) else 0
                render_json_with_schema(
                    item["data"],
                    f"{key[:-1]}_log_entry" if key != "events" else "event_log_entry",
                    f"{key} ({count})",
                    f"{item['description']} | `{item['source']}`"
                )
        
        # Export-Buttons
        st.markdown("---")
        col1, col2 = st.columns(2)
        
        with col1:
            schema_export = {
                "exported_at": datetime.now().isoformat(),
                "description": "JSON Schemas für Großer Bär",
                "schemas": JSON_SCHEMAS
            }
            st.download_button(
                "📐 Alle Schemas exportieren",
                data=json.dumps(schema_export, indent=2, ensure_ascii=False),
                file_name="grosser_baer_schemas.json",
                mime="application/json",
                use_container_width=True
            )
        
        with col2:
            live_export = {
                "exported_at": datetime.now().isoformat(),
                "session_id": st.session_state.get("session_id"),
                "user_code": st.session_state.get("user_code"),
                "data": {
                    cat: {k: v["data"] for k, v in items.items()}
                    for cat, items in all_jsons.items()
                }
            }
            st.download_button(
                "📊 Alle Live-Daten exportieren",
                data=json.dumps(live_export, indent=2, ensure_ascii=False, default=str),
                file_name=f"session_export_{datetime.now().strftime('%Y%m%d_%H%M')}.json",
                mime="application/json",
                use_container_width=True
            )
    
    # =========================================================================
    # TAB 2: Einstellungen
    # =========================================================================
    with tab_settings:
        st.header("⚙️ Feature Flags & Modi")
        
        col1, col2 = st.columns(2)
        
        with col1:
            st.subheader("Modi")
            
            mock_mode = st.toggle(
                "🎭 Mock-Modus",
                value=get_config("mock_mode", True),
                help="Audio → Text-Input, LLM → Mock-Feedback"
            )
            set_config("mock_mode", mock_mode)
            
            debug_mode = st.toggle(
                "🐛 Debug-Modus", 
                value=get_config("debug_mode", False),
                help="Zeigt erweiterte Infos in der Coach-App"
            )
            set_config("debug_mode", debug_mode)
            
            skip_pretest = st.toggle(
                "⏭️ Pretest überspringen",
                value=get_config("skip_pretest", False),
                help="Für schnelle Tests ohne Pretest"
            )
            set_config("skip_pretest", skip_pretest)
            
            disable_airtable = st.toggle(
                "🚫 Airtable deaktivieren",
                value=get_config("disable_airtable", False),
                help="Keine Daten an Make/Airtable senden"
            )
            set_config("disable_airtable", disable_airtable)
        
        with col2:
            st.subheader("Logging")
            
            log_payloads = st.toggle(
                "📤 Payloads loggen",
                value=get_config("log_payloads", True)
            )
            set_config("log_payloads", log_payloads)
            
            log_llm = st.toggle(
                "🤖 LLM-Calls loggen",
                value=get_config("log_llm_calls", True)
            )
            set_config("log_llm_calls", log_llm)
            
            st.subheader("UI")
            
            show_metrics = st.toggle(
                "📊 Metriken-Tab anzeigen",
                value=get_config("show_metrics_tab", True)
            )
            set_config("show_metrics_tab", show_metrics)
            
            show_llm_tab = st.toggle(
                "🔌 LLM-Input Tab anzeigen",
                value=get_config("show_llm_input_tab", True)
            )
            set_config("show_llm_input_tab", show_llm_tab)
    
    # =========================================================================
    # TAB 3: Session State
    # =========================================================================
    with tab_state:
        st.header("📊 Session State")
        
        col1, col2 = st.columns(2)
        
        with col1:
            st.subheader("User & Session")
            st.metric("User Code", st.session_state.get("user_code", "–"))
            st.metric("Session Count", st.session_state.get("session_count", 0))
            st.metric("Aktuelle Phase", st.session_state.get("phase", "–"))
        
        with col2:
            st.subheader("Pretest Status")
            pretest_done = st.session_state.get("pretest_completed", False)
            st.metric("Pretest", "✅ Ja" if pretest_done else "❌ Nein")
            st.metric("Modul", st.session_state.get("pretest_current_module", 0))
        
        st.markdown("---")
        
        with st.expander("🔍 Alle Session State Keys"):
            state_keys = sorted(st.session_state.keys())
            st.write(f"**{len(state_keys)} Keys**")
            
            selected = st.selectbox("Key inspizieren:", [""] + state_keys)
            if selected:
                val = st.session_state.get(selected)
                st.write(f"**Typ:** `{type(val).__name__}`")
                try:
                    st.json(val)
                except:
                    st.code(str(val)[:2000])
    
    # =========================================================================
    # TAB 4: Logs
    # =========================================================================
    with tab_logs:
        st.header("📝 Logs")
        
        log_type = st.selectbox(
            "Log-Typ:",
            ["payloads", "llm_calls", "errors", "events"]
        )
        
        logs = get_logs(log_type)
        
        if not logs:
            st.info(f"Keine {log_type} geloggt.")
        else:
            st.success(f"{len(logs)} Einträge")
            
            for i, log in enumerate(reversed(logs[-20:])):
                ts = log.get("timestamp", "")[:19]
                label = log.get("endpoint") or log.get("prompt_type") or log.get("error_type") or log.get("event_type") or "–"
                with st.expander(f"{label} – {ts}"):
                    st.json(log)
        
        if logs and st.button(f"🗑️ {log_type} löschen"):
            clear_logs(log_type)
            st.rerun()
    
    # =========================================================================
    # TAB 5: Actions
    # =========================================================================
    with tab_actions:
        st.header("🔧 Quick Actions")
        
        col1, col2 = st.columns(2)
        
        with col1:
            st.subheader("Reset")
            
            if st.button("🔄 Session zurücksetzen", use_container_width=True):
                for key in ["phase", "selected_task_id", "transcript", "feedback_result",
                           "coach_input", "kleiner_baer_result", "audio_bytes",
                           "recording_start", "learner_goal", "learner_context",
                           "reflection_text", "reflection_saved", "session_saved"]:
                    if key in st.session_state:
                        del st.session_state[key]
                st.success("Session zurückgesetzt!")
                st.rerun()
            
            if st.button("🔄 Pretest zurücksetzen", use_container_width=True):
                for key in ["pretest_completed", "pretest_completed_at",
                           "pretest_current_module", "pretest_responses"]:
                    if key in st.session_state:
                        del st.session_state[key]
                st.success("Pretest zurückgesetzt!")
                st.rerun()
            
            if st.button("🗑️ Alle Logs löschen", use_container_width=True):
                clear_logs()
                st.success("Logs gelöscht!")
                st.rerun()
        
        with col2:
            st.subheader("Mock-Generatoren")
            
            if st.button("🎲 Mock-User", use_container_width=True):
                import random
                st.session_state.user_code = f"TEST_{random.randint(1000, 9999)}"
                st.session_state.user_code_confirmed = True
                st.success(f"User: {st.session_state.user_code}")
            
            if st.button("📝 Mock-Pretest", use_container_width=True):
                st.session_state.pretest_completed = True
                st.session_state.pretest_completed_at = datetime.now().isoformat()
                st.session_state.pretest_responses = MOCK_DATA["pretest_responses"].copy()
                st.success("Pretest generiert!")
                st.rerun()
            
            if st.button("🎯 Mock-Session (Feedback)", use_container_width=True):
                success, message = apply_screen_state("phase_feedback", use_mock_data=True)
                st.success(message)
                st.rerun()
        
        st.markdown("---")
        st.page_link("pages/grosser_baer.py", label="← Zurück zur Coach-App", icon="🐻")


# =============================================================================
# MAIN
# =============================================================================

if check_admin_auth():
    render_admin_dashboard()
