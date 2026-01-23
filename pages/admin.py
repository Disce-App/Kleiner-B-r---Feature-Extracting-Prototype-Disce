"""
🛠️ Admin Dashboard für Großer Bär
Debugging, Logging und Konfiguration.
"""

import streamlit as st
import json
from datetime import datetime

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
                "id": "demographics",
                "title": "Über dich",
                "questions": [
                    {
                        "id": "native_language",
                        "type": "text",
                        "label": "Was ist deine Muttersprache?",
                        "required": True
                    }
                ]
            },
            {
                "id": "cefr_self",
                "title": "Selbsteinschätzung",
                "questions": ["..."]
            },
            {
                "id": "masq",
                "title": "Lernstrategien (MASQ)",
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
    "pretest_responses": {
        "cefr_overall": {
            "value": "B2",
            "answered_at": "2026-01-23T14:30:00"
        },
        "cefr_speaking": {
            "value": "B1",
            "answered_at": "2026-01-23T14:30:15"
        },
        "native_language": {
            "value": "Englisch",
            "answered_at": "2026-01-23T14:29:00"
        },
        "learning_duration": {
            "value": 24,
            "answered_at": "2026-01-23T14:29:30"
        },
        "learning_context": {
            "value": "Universität + Selbststudium",
            "answered_at": "2026-01-23T14:29:45"
        },
        "masq_scores": {
            "factors": {
                "PE": {"mean": 3.8, "sum": 19, "items": 5},
                "PS": {"mean": 3.5, "sum": 14, "items": 4},
                "PK": {"mean": 3.2, "sum": 16, "items": 5},
                "DA": {"mean": 3.6, "sum": 18, "items": 5},
                "MT": {"mean": 2.8, "sum": 14, "items": 5}
            },
            "total": 81,
            "level": "medium",
            "level_label": "Durchschnittliche metakognitive Bewusstheit"
        }
    },
    
    "masq_scores": {
        "factors": {
            "PE": {
                "mean": 3.8,
                "sum": 19,
                "items": 5,
                "_description": "Planning & Evaluation – Planung und Selbstbewertung"
            },
            "PS": {
                "mean": 3.5,
                "sum": 14,
                "items": 4,
                "_description": "Problem-Solving – Problemlösestrategien"
            },
            "PK": {
                "mean": 3.2,
                "sum": 16,
                "items": 5,
                "_description": "Person Knowledge – Wissen über eigenes Lernen"
            },
            "DA": {
                "mean": 3.6,
                "sum": 18,
                "items": 5,
                "_description": "Directed Attention – Fokussierte Aufmerksamkeit"
            },
            "MT": {
                "mean": 2.8,
                "sum": 14,
                "items": 5,
                "_description": "Mental Translation – Mentale Übersetzung (niedrig = besser)"
            }
        },
        "total": 81,
        "level": "medium",
        "level_label": "Durchschnittliche metakognitive Bewusstheit"
    },
    
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
            "cefr_self_speaking": "B1",
            "masq_level": "medium",
            "masq_factors": {
                "PE": 3.8,
                "PS": 3.5,
                "PK": 3.2,
                "DA": 3.6,
                "MT": 2.8
            }
        },
        "task_metadata": {
            "task_id": "meeting_update",
            "situation": "Du bist in einem Team-Meeting und sollst ein kurzes Projekt-Update geben.",
            "task": "Fasse den aktuellen Stand zusammen und benenne die nächsten Schritte.",
            "target_level": "B2",
            "target_register": "beruflich-formell",
            "time_limit_seconds": 90
        },
        "session_metadata": {
            "session_id": "550e8400-e29b-41d4-a716-446655440000",
            "session_number": 3,
            "mode": "speaking",
            "started_at": "2026-01-23T15:00:00",
            "ended_at": "2026-01-23T15:01:45",
            "duration_seconds": 105
        },
        "learner_planning": {
            "goal": "Ich möchte flüssiger sprechen ohne lange Pausen",
            "context": "Ich habe nächste Woche ein echtes Meeting mit meinem Chef",
            "submitted_at": "2026-01-23T15:00:00"
        },
        "transcript": "Guten Tag, ich möchte kurz den aktuellen Projektstand zusammenfassen. Wir haben in der letzten Woche gute Fortschritte gemacht. Die wichtigsten Meilensteine wurden erreicht. Als nächstes werden wir uns auf die Testphase konzentrieren.",
        "analysis": {
            "layer1_deterministic": {
                "word_count": 35,
                "sentence_count": 4,
                "avg_sentence_length": 8.75,
                "filler_count": 0,
                "vocabulary_diversity": 0.85
            },
            "layer2_azure": None,
            "cefr": {
                "label": "B1",
                "score": 0.65,
                "confidence": 0.78
            },
            "home_kpis": {
                "level_match": 0.70,
                "prosody_intelligibility": 0.80,
                "sentence_cohesion": 0.75,
                "task_exam_fit": 0.85,
                "goal_progress": 0.60
            },
            "hotspots": [
                {"type": "filler", "text": "ähm", "position": 12, "severity": "low"},
                {"type": "pause", "duration_ms": 1200, "position": 25, "severity": "medium"}
            ]
        },
        "reflection": {
            "text": "Ich war am Anfang nervös, aber dann wurde es besser. Nächstes Mal möchte ich weniger Pausen machen.",
            "submitted_at": "2026-01-23T15:02:30"
        }
    },
    
    "current_task": {
        "id": "meeting_update",
        "situation": "Du bist in einem Team-Meeting und sollst ein kurzes Projekt-Update geben.",
        "task": "Fasse den aktuellen Stand zusammen und benenne die nächsten Schritte.",
        "level": "B2",
        "register": "beruflich-formell",
        "time_seconds": 90,
        "example_phrases": [
            "Ich möchte kurz zusammenfassen...",
            "Der aktuelle Stand ist...",
            "Als nächstes werden wir..."
        ],
        "meta_prompts": {
            "plan": "Überlege dir eine klare Struktur: Rückblick → Aktueller Stand → Ausblick",
            "reflect": "War deine Struktur klar? Hast du alle drei Teile abgedeckt?"
        }
    },
    
    "session_metadata": {
        "session_id": "550e8400-e29b-41d4-a716-446655440000",
        "user_code": "ABC123",
        "session_count": 3,
        "phase": "feedback",
        "recording_start": "2026-01-23T15:00:00",
        "learner_goal": "Ich möchte flüssiger sprechen",
        "learner_context": "Meeting mit Chef nächste Woche",
        "reflection_text": "Es lief besser als erwartet",
        "transcript": "Guten Tag, ich möchte kurz..."
    },
    
    # =========================================================================
    # ANALYSE (Kleiner Bär Output)
    # =========================================================================
    "kleiner_baer_result": {
        "metrics_summary": {
            "word_count": 35,
            "sentence_count": 4,
            "avg_sentence_length": 8.75,
            "type_token_ratio": 0.85,
            "lexical_density": 0.52,
            "filler_count": 2,
            "filler_ratio": 0.057,
            "connector_count": 3,
            "modal_verb_count": 1,
            "subjunctive_count": 0,
            "formal_markers": ["möchte", "zusammenfassen"],
            "informal_markers": []
        },
        "cefr": {
            "label": "B1",
            "score": 0.65,
            "confidence": 0.78,
            "indicators": {
                "vocabulary": "B1",
                "syntax": "B1-B2",
                "coherence": "B1"
            }
        },
        "disce_metrics": {
            "level_match": 0.70,
            "prosody_intelligibility": 0.80,
            "sentence_cohesion": 0.75,
            "task_exam_fit": 0.85,
            "goal_progress": 0.60
        },
        "hotspots": [
            {
                "type": "filler",
                "text": "ähm",
                "position": 12,
                "context": "...und ähm wir haben...",
                "severity": "low",
                "suggestion": "Pause statt Füllwort"
            },
            {
                "type": "pause",
                "duration_ms": 1200,
                "position": 25,
                "severity": "medium",
                "suggestion": "Kürzere Denkpausen durch bessere Vorbereitung"
            },
            {
                "type": "register_mismatch",
                "text": "halt",
                "expected": "beruflich-formell",
                "found": "umgangssprachlich",
                "severity": "medium"
            }
        ],
        "register_analysis": {
            "target": "beruflich-formell",
            "detected": "neutral-formell",
            "match_score": 0.70,
            "formal_features": 3,
            "informal_features": 1
        }
    },
    
    "cefr_estimation": {
        "label": "B1",
        "score": 0.65,
        "confidence": 0.78,
        "method": "rule_based_v1",
        "indicators": {
            "vocabulary_range": "B1",
            "grammatical_accuracy": "B1",
            "syntactic_complexity": "B1-B2",
            "coherence_cohesion": "B1",
            "task_achievement": "B2"
        },
        "comparison_to_self_assessment": {
            "self_reported": "B1",
            "estimated": "B1",
            "delta": 0
        }
    },
    
    "disce_metrics": {
        "level_match": {
            "value": 0.70,
            "description": "Wie gut passt das Niveau zur Zielaufgabe?",
            "target": "B2",
            "estimated": "B1"
        },
        "prosody_intelligibility": {
            "value": 0.80,
            "description": "Verständlichkeit und Sprechfluss",
            "components": {
                "speech_rate_wpm": 125,
                "pause_ratio": 0.15,
                "filler_ratio": 0.057
            }
        },
        "sentence_cohesion": {
            "value": 0.75,
            "description": "Zusammenhang zwischen Sätzen",
            "connectors_used": 3,
            "logical_flow": "adequate"
        },
        "task_exam_fit": {
            "value": 0.85,
            "description": "Erfüllung der Aufgabenstellung",
            "task_elements_covered": ["summary", "next_steps"],
            "missing": []
        },
        "goal_progress": {
            "value": 0.60,
            "description": "Fortschritt bezogen auf Lernziel",
            "learner_goal": "flüssiger sprechen",
            "evidence": "noch einige Pausen"
        }
    },
    
    "hotspots": [
        {
            "id": 1,
            "type": "filler",
            "text": "ähm",
            "position": {"start": 45, "end": 48},
            "context": "...Projektstand ähm zusammenfassen...",
            "severity": "low",
            "category": "fluency",
            "suggestion": "Kurze Pause statt Füllwort",
            "learnable": True
        },
        {
            "id": 2,
            "type": "pause",
            "duration_ms": 1200,
            "position": {"start": 120, "end": 120},
            "context": "...Meilensteine wurden [1.2s] erreicht...",
            "severity": "medium",
            "category": "fluency",
            "suggestion": "Satz im Kopf vorbereiten vor dem Sprechen"
        },
        {
            "id": 3,
            "type": "register_mismatch",
            "text": "halt",
            "position": {"start": 85, "end": 89},
            "context": "...wir haben halt...",
            "severity": "medium",
            "category": "register",
            "expected_register": "beruflich-formell",
            "found_register": "umgangssprachlich",
            "suggestion": "→ 'also' oder 'demnach' im beruflichen Kontext"
        }
    ],
    
    # =========================================================================
    # LOGS
    # =========================================================================
    "payload_log_entry": {
        "timestamp": "2026-01-23T15:03:00",
        "endpoint": "make_webhook",
        "payload": {
            "session_id": "550e8400-...",
            "user_code": "ABC123",
            "transcript": "...",
            "cefr_label": "B1"
        },
        "response": {
            "status_code": 200,
            "message": "accepted"
        }
    },
    
    "llm_call_log_entry": {
        "timestamp": "2026-01-23T15:02:00",
        "prompt_type": "gpt_coach",
        "model": "gpt-4o-mini",
        "input": {
            "coach_input": "{ ... siehe coach_input Schema ... }"
        },
        "output": "## Feedback zu deiner Übung\n\n**Was gut war:**\n- Klare Struktur...",
        "tokens_used": {
            "prompt": 850,
            "completion": 320,
            "total": 1170
        },
        "duration_ms": 2340
    },
    
    "error_log_entry": {
        "timestamp": "2026-01-23T15:02:15",
        "error_type": "whisper",
        "message": "Audio file too short",
        "details": {
            "audio_length_ms": 500,
            "min_required_ms": 1000
        },
        "stack_trace": "..."
    },
    
    "event_log_entry": {
        "timestamp": "2026-01-23T14:55:00",
        "event_type": "auth",
        "message": "User eingeloggt",
        "details": {
            "user_code": "ABC123",
            "method": "manual"
        }
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
    return hints.get(schema_key, "→ Nutze den Mock-Generator unter 'Actions'")


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
    st.caption("Debugging, Logging und Konfiguration für Großer Bär")
    
    # Tabs
    tab1, tab2, tab3, tab4, tab5 = st.tabs([
        "📋 JSON Viewer",
        "⚙️ Einstellungen",
        "📊 Session State",
        "📝 Logs",
        "🔧 Actions"
    ])
    
    # =========================================================================
    # TAB 1: JSON VIEWER (NEU: Hauptfokus)
    # =========================================================================
    with tab1:
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
        # SESSION & COACH (wichtigste JSONs zuerst)
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
                expanded=True  # Standardmäßig offen
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
        # ANALYSE (Kleiner Bär)
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
            # Schema-Export
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
            # Live-Daten Export
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
    with tab2:
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
    with tab3:
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
    with tab4:
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
    with tab5:
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
                st.session_state.pretest_responses = JSON_SCHEMAS["pretest_responses"].copy()
                st.success("Pretest generiert!")
                st.rerun()
            
            if st.button("🎯 Mock-Session", use_container_width=True):
                import uuid
                st.session_state.phase = "feedback"
                st.session_state.session_id = str(uuid.uuid4())
                st.session_state.selected_task_id = "meeting_update"
                st.session_state.learner_goal = "Flüssiger sprechen"
                st.session_state.transcript = "Guten Tag, ich möchte den Projektstand zusammenfassen..."
                st.session_state.coach_input = JSON_SCHEMAS["coach_input"].copy()
                st.session_state.kleiner_baer_result = JSON_SCHEMAS["kleiner_baer_result"].copy()
                st.success("Session generiert!")
                st.rerun()
        
        st.markdown("---")
        st.page_link("pages/grosser_baer.py", label="← Zurück zur Coach-App", icon="🐻")


# =============================================================================
# MAIN
# =============================================================================

if check_admin_auth():
    render_admin_dashboard()
