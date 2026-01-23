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
# AUTH CHECK (einfacher Passwortschutz)
# =============================================================================

def check_admin_auth() -> bool:
    """Einfacher Passwortschutz für Admin-Bereich."""
    
    # Prüfe ob schon authentifiziert
    if st.session_state.get("admin_authenticated", False):
        return True
    
    st.title("🔐 Admin-Zugang")
    st.markdown("Bitte Passwort eingeben, um auf das Admin-Dashboard zuzugreifen.")
    
    # Passwort aus Secrets oder Fallback
    try:
        correct_password = st.secrets.get("ADMIN_PASSWORD", "disce2026")
    except:
        correct_password = "disce2026"  # Fallback für lokale Entwicklung
    
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
# JSON VIEWER HELPER
# =============================================================================

def render_json_viewer(data, title: str, description: str = "", expanded: bool = False):
    """Rendert einen JSON-Block in einem Expander mit Copy-Funktion."""
    with st.expander(title, expanded=expanded):
        if description:
            st.caption(description)
        
        if data is None:
            st.info("Keine Daten vorhanden")
        elif isinstance(data, (dict, list)):
            # Zeige als formatiertes JSON
            st.json(data)
            
            # Copy-Button (JSON als String)
            try:
                json_str = json.dumps(data, indent=2, ensure_ascii=False, default=str)
                st.download_button(
                    "📋 Als JSON herunterladen",
                    data=json_str,
                    file_name=f"{title.replace(' ', '_').lower()}.json",
                    mime="application/json",
                    key=f"download_{title}_{id(data)}"
                )
            except Exception as e:
                st.warning(f"JSON-Export fehlgeschlagen: {e}")
        else:
            st.code(str(data))


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
    # 1. KONFIGURATION (Input-JSONs)
    # =========================================================================
    
    # App-Config (Feature Flags)
    jsons["config"]["app_config"] = {
        "data": st.session_state.get("app_config", DEFAULT_SETTINGS),
        "description": "Aktuelle App-Einstellungen (Mock-Modus, Debug, etc.)",
        "source": "session_state.app_config"
    }
    
    # Pretest-Config (aus Datei)
    if PRETEST_AVAILABLE:
        try:
            pretest_config = load_pretest_config()
            jsons["config"]["pretest_config"] = {
                "data": pretest_config,
                "description": "Pretest-Konfiguration (Module, Fragen, Scoring)",
                "source": "config/pretest_config.json"
            }
        except Exception as e:
            jsons["config"]["pretest_config"] = {
                "data": {"error": str(e)},
                "description": "Fehler beim Laden",
                "source": "config/pretest_config.json"
            }
    
    # =========================================================================
    # 2. PRETEST-DATEN (User-Input)
    # =========================================================================
    
    # Pretest-Antworten
    jsons["pretest"]["pretest_responses"] = {
        "data": st.session_state.get("pretest_responses", {}),
        "description": "Alle Pretest-Antworten des aktuellen Users",
        "source": "session_state.pretest_responses"
    }
    
    # MASQ-Scores (berechnet)
    masq_scores = st.session_state.get("pretest_responses", {}).get("masq_scores", {})
    jsons["pretest"]["masq_scores"] = {
        "data": masq_scores,
        "description": "Berechnete MASQ-Scores (Planning, Problem-Solving, etc.)",
        "source": "session_state.pretest_responses.masq_scores"
    }
    
    # =========================================================================
    # 3. SESSION-DATEN (Aktuelle Übung)
    # =========================================================================
    
    # Coach-Input (das was ans LLM geht)
    jsons["session"]["coach_input"] = {
        "data": st.session_state.get("coach_input", {}),
        "description": "JSON-Block der an die LLM-Coach-API gesendet wird",
        "source": "session_state.coach_input"
    }
    
    # Task-Metadaten
    task_id = st.session_state.get("selected_task_id")
    if task_id:
        try:
            from grosser_baer import get_task
            task_data = get_task(task_id)
            jsons["session"]["current_task"] = {
                "data": task_data,
                "description": f"Aktuelle Aufgabe: {task_id}",
                "source": "grosser_baer.get_task()"
            }
        except:
            jsons["session"]["current_task"] = {
                "data": {"task_id": task_id},
                "description": "Task-ID vorhanden, Details nicht geladen",
                "source": "session_state.selected_task_id"
            }
    
    # Session-Metadaten
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
            "transcript": st.session_state.get("transcript", "")[:500] + "..." if st.session_state.get("transcript", "") and len(st.session_state.get("transcript", "")) > 500 else st.session_state.get("transcript", ""),
        },
        "description": "Metadaten der aktuellen Session",
        "source": "session_state (diverse Keys)"
    }
    
    # =========================================================================
    # 4. ANALYSE-DATEN (Kleiner Bär Output)
    # =========================================================================
    
    # Kleiner Bär Result
    jsons["analysis"]["kleiner_baer_result"] = {
        "data": st.session_state.get("kleiner_baer_result", {}),
        "description": "Vollständige Analyse von Kleiner Bär (Textmetriken, CEFR, KPIs)",
        "source": "session_state.kleiner_baer_result"
    }
    
    # CEFR-Schätzung (extrahiert)
    kb_result = st.session_state.get("kleiner_baer_result", {})
    jsons["analysis"]["cefr_estimation"] = {
        "data": kb_result.get("cefr", {}),
        "description": "CEFR-Level-Schätzung aus der Textanalyse",
        "source": "kleiner_baer_result.cefr"
    }
    
    # Disce-Metriken (extrahiert)
    jsons["analysis"]["disce_metrics"] = {
        "data": kb_result.get("disce_metrics", {}),
        "description": "Disce-KPIs (Register, Kohäsion, Task-Fit, etc.)",
        "source": "kleiner_baer_result.disce_metrics"
    }
    
    # Hotspots
    jsons["analysis"]["hotspots"] = {
        "data": kb_result.get("hotspots", []),
        "description": "Erkannte Problemstellen (Füllwörter, Pausen, etc.)",
        "source": "kleiner_baer_result.hotspots"
    }
    
    # =========================================================================
    # 5. LOGS
    # =========================================================================
    
    debug_logs = st.session_state.get("debug_logs", {})
    
    jsons["logs"]["payloads"] = {
        "data": debug_logs.get("payloads", []),
        "description": "Gesendete Payloads an Make/Airtable",
        "source": "debug_logs.payloads"
    }
    
    jsons["logs"]["llm_calls"] = {
        "data": debug_logs.get("llm_calls", []),
        "description": "LLM-Aufrufe (Input/Output)",
        "source": "debug_logs.llm_calls"
    }
    
    jsons["logs"]["errors"] = {
        "data": debug_logs.get("errors", []),
        "description": "Fehler-Log",
        "source": "debug_logs.errors"
    }
    
    jsons["logs"]["events"] = {
        "data": debug_logs.get("events", []),
        "description": "Event-Log (Login, Session-Start, etc.)",
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
        "⚙️ Einstellungen",
        "📊 Session State",
        "📤 Payloads",
        "🤖 LLM Calls",
        "🔧 Actions"
    ])
    
    # =========================================================================
    # TAB 1: Einstellungen + JSON Viewer
    # =========================================================================
    with tab1:
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
        
        # =====================================================================
        # NEU: ALLE JSONs ANZEIGEN
        # =====================================================================
        st.markdown("---")
        st.header("📋 Alle JSONs")
        st.caption("Übersicht aller Konfigurationen, Daten und Logs in JSON-Format")
        
        all_jsons = get_all_jsons()
        
        # Kategorie-Tabs für bessere Übersicht
        json_tab1, json_tab2, json_tab3, json_tab4, json_tab5 = st.tabs([
            "⚙️ Config",
            "📝 Pretest",
            "🎯 Session",
            "🔬 Analyse",
            "📊 Logs"
        ])
        
        with json_tab1:
            st.subheader("Konfigurationsdateien")
            for key, item in all_jsons["config"].items():
                render_json_viewer(
                    item["data"],
                    f"📄 {key}",
                    f"{item['description']} | Quelle: `{item['source']}`"
                )
        
        with json_tab2:
            st.subheader("Pretest-Daten")
            for key, item in all_jsons["pretest"].items():
                render_json_viewer(
                    item["data"],
                    f"📝 {key}",
                    f"{item['description']} | Quelle: `{item['source']}`"
                )
        
        with json_tab3:
            st.subheader("Session-Daten")
            for key, item in all_jsons["session"].items():
                # Coach-Input standardmäßig aufgeklappt (wichtigstes JSON)
                expanded = (key == "coach_input")
                render_json_viewer(
                    item["data"],
                    f"🎯 {key}",
                    f"{item['description']} | Quelle: `{item['source']}`",
                    expanded=expanded
                )
        
        with json_tab4:
            st.subheader("Analyse-Daten (Kleiner Bär)")
            for key, item in all_jsons["analysis"].items():
                render_json_viewer(
                    item["data"],
                    f"🔬 {key}",
                    f"{item['description']} | Quelle: `{item['source']}`"
                )
        
        with json_tab5:
            st.subheader("Debug-Logs")
            for key, item in all_jsons["logs"].items():
                count = len(item["data"]) if isinstance(item["data"], list) else 0
                render_json_viewer(
                    item["data"],
                    f"📊 {key} ({count} Einträge)",
                    f"{item['description']} | Quelle: `{item['source']}`"
                )
        
        # Download ALL JSONs
        st.markdown("---")
        col1, col2 = st.columns(2)
        with col1:
            if st.button("📥 Alle JSONs als ZIP herunterladen", use_container_width=True):
                st.info("Feature kommt bald – nutze vorerst die einzelnen Download-Buttons")
        
        with col2:
            # Kompletter State-Export
            full_export = {
                "exported_at": datetime.now().isoformat(),
                "all_jsons": {
                    category: {
                        key: item["data"] 
                        for key, item in items.items()
                    }
                    for category, items in all_jsons.items()
                }
            }
            st.download_button(
                "📦 Kompletten State exportieren",
                data=json.dumps(full_export, indent=2, ensure_ascii=False, default=str),
                file_name=f"grosser_baer_full_export_{datetime.now().strftime('%Y%m%d_%H%M')}.json",
                mime="application/json",
                use_container_width=True
            )
    
    # =========================================================================
    # TAB 2: Session State Viewer
    # =========================================================================
    with tab2:
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
            st.metric("Pretest abgeschlossen", "✅ Ja" if pretest_done else "❌ Nein")
            st.metric("Pretest-Modul", st.session_state.get("pretest_current_module", 0))
            
            completed_at = st.session_state.get("pretest_completed_at")
            if completed_at:
                st.caption(f"Abgeschlossen: {completed_at}")
        
        st.markdown("---")
        
        # Pretest-Antworten
        with st.expander("📝 Pretest-Antworten"):
            responses = st.session_state.get("pretest_responses", {})
            if responses:
                st.json(responses)
            else:
                st.info("Noch keine Pretest-Antworten vorhanden.")
        
        # Vollständiger State (nur Keys)
        with st.expander("🔍 Alle Session State Keys"):
            state_keys = list(st.session_state.keys())
            st.write(f"**{len(state_keys)} Keys:**")
            st.code("\n".join(sorted(state_keys)))
        
        # Einzelne Keys inspizieren
        with st.expander("🔬 Key inspizieren"):
            if state_keys := list(st.session_state.keys()):
                selected_key = st.selectbox("Key auswählen", sorted(state_keys))
                if selected_key:
                    value = st.session_state.get(selected_key)
                    st.write(f"**Typ:** `{type(value).__name__}`")
                    try:
                        st.json(value)
                    except:
                        st.code(str(value)[:2000])
    
    # =========================================================================
    # TAB 3: Payload Inspector
    # =========================================================================
    with tab3:
        st.header("📤 Payload Inspector")
        
        payloads = get_logs("payloads")
        
        if not payloads:
            st.info("Noch keine Payloads geloggt.")
            st.caption("Payloads werden gespeichert, wenn Daten an Make/Airtable gesendet werden.")
        else:
            st.success(f"{len(payloads)} Payload(s) geloggt")
            
            for i, log in enumerate(reversed(payloads)):
                with st.expander(f"📤 {log.get('endpoint', 'Unknown')} – {log.get('timestamp', '')[:19]}"):
                    st.subheader("Request Payload")
                    st.json(log.get("payload", {}))
                    
                    if log.get("response"):
                        st.subheader("Response")
                        st.json(log.get("response"))
            
            if st.button("🗑️ Payloads löschen"):
                clear_logs("payloads")
                st.rerun()
    
    # =========================================================================
    # TAB 4: LLM Calls
    # =========================================================================
    with tab4:
        st.header("🤖 LLM Call Log")
        
        llm_calls = get_logs("llm_calls")
        
        if not llm_calls:
            st.info("Noch keine LLM-Calls geloggt.")
        else:
            st.success(f"{len(llm_calls)} LLM-Call(s) geloggt")
            
            for log in reversed(llm_calls):
                with st.expander(f"🤖 {log.get('prompt_type', 'Unknown')} – {log.get('timestamp', '')[:19]}"):
                    st.subheader("Input")
                    st.json(log.get("input", {}))
                    
                    if log.get("output"):
                        st.subheader("Output (truncated)")
                        st.text(log.get("output"))
            
            if st.button("🗑️ LLM Logs löschen"):
                clear_logs("llm_calls")
                st.rerun()
        
        # Errors
        st.markdown("---")
        st.subheader("❌ Fehler-Log")
        
        errors = get_logs("errors")
        if errors:
            for err in reversed(errors[-10:]):
                st.error(f"**{err.get('error_type')}:** {err.get('message')}")
                if err.get("details"):
                    with st.expander("Details"):
                        st.json(err.get("details"))
        else:
            st.success("Keine Fehler geloggt 🎉")
    
    # =========================================================================
    # TAB 5: Quick Actions
    # =========================================================================
    with tab5:
        st.header("🔧 Quick Actions")
        
        col1, col2 = st.columns(2)
        
        with col1:
            st.subheader("Reset-Aktionen")
            
            if st.button("🔄 Session zurücksetzen", use_container_width=True):
                keys_to_reset = [
                    "current_phase", "selected_task", "transcript",
                    "user_reflection", "feedback_result", "coach_input",
                    "kleiner_baer_result", "phase", "selected_task_id",
                    "audio_bytes", "recording_start", "learner_goal",
                    "learner_context", "reflection_text", "reflection_saved",
                    "session_saved", "transcript_text"
                ]
                for key in keys_to_reset:
                    if key in st.session_state:
                        del st.session_state[key]
                st.success("Session zurückgesetzt!")
                st.rerun()
            
            if st.button("🔄 Pretest zurücksetzen", use_container_width=True):
                keys_to_reset = [
                    "pretest_completed", "pretest_completed_at",
                    "pretest_current_module", "pretest_responses"
                ]
                for key in keys_to_reset:
                    if key in st.session_state:
                        del st.session_state[key]
                st.success("Pretest zurückgesetzt!")
                st.rerun()
            
            if st.button("🗑️ Alle Logs löschen", use_container_width=True):
                clear_logs()
                st.success("Logs gelöscht!")
                st.rerun()
            
            if st.button("💥 ALLES zurücksetzen", type="secondary", use_container_width=True):
                for key in list(st.session_state.keys()):
                    if key != "admin_authenticated":
                        del st.session_state[key]
                st.success("Kompletter State gelöscht!")
                st.rerun()
        
        with col2:
            st.subheader("Export")
            
            json_export = export_state_as_json()
            st.download_button(
                "📥 State als JSON exportieren",
                data=json_export,
                file_name=f"grosser_baer_state_{datetime.now().strftime('%Y%m%d_%H%M')}.json",
                mime="application/json",
                use_container_width=True
            )
            
            st.subheader("Test-Daten")
            
            if st.button("🎲 Mock-User generieren", use_container_width=True):
                import random
                st.session_state.user_code = f"TEST_{random.randint(1000, 9999)}"
                st.session_state.user_code_confirmed = True
                st.session_state.session_count = random.randint(0, 10)
                st.success(f"Mock-User erstellt: {st.session_state.user_code}")
            
            if st.button("📝 Mock-Pretest generieren", use_container_width=True):
                st.session_state.pretest_completed = True
                st.session_state.pretest_completed_at = datetime.now().isoformat()
                st.session_state.pretest_responses = {
                    "cefr_overall": {"value": "B2", "answered_at": datetime.now().isoformat()},
                    "cefr_speaking": {"value": "B1", "answered_at": datetime.now().isoformat()},
                    "learning_duration": {"value": 24, "answered_at": datetime.now().isoformat()},
                    "native_language": {"value": "Englisch", "answered_at": datetime.now().isoformat()},
                    "masq_scores": {
                        "factors": {
                            "PE": {"mean": 3.8, "sum": 19, "items": 5},
                            "PS": {"mean": 3.5, "sum": 14, "items": 4},
                            "PK": {"mean": 3.2, "sum": 16, "items": 5},
                            "DA": {"mean": 3.6, "sum": 18, "items": 5},
                            "MT": {"mean": 2.8, "sum": 14, "items": 5},
                        },
                        "total": 53,
                        "level": "medium",
                        "level_label": "Durchschnittliche metakognitive Bewusstheit"
                    }
                }
                st.success("Mock-Pretest generiert!")
                st.rerun()
            
            if st.button("🎯 Mock-Session generieren", use_container_width=True):
                import uuid
                st.session_state.phase = "feedback"
                st.session_state.session_id = str(uuid.uuid4())
                st.session_state.selected_task_id = "meeting_update"
                st.session_state.transcript = "Guten Tag, ich möchte kurz den aktuellen Projektstand zusammenfassen. Wir haben in der letzten Woche gute Fortschritte gemacht."
                st.session_state.learner_goal = "Ich möchte flüssiger sprechen"
                st.session_state.recording_start = datetime.now()
                st.session_state.coach_input = {
                    "user": {"code": st.session_state.get("user_code", "TEST"), "is_anonymous": False},
                    "task_metadata": {"task_id": "meeting_update", "situation": "Projekt-Meeting"},
                    "transcript": st.session_state.transcript,
                    "session_metadata": {"mode": "mock", "duration_seconds": 45}
                }
                st.session_state.kleiner_baer_result = {
                    "cefr": {"label": "B1", "score": 0.65},
                    "disce_metrics": {
                        "level_match": 0.7,
                        "prosody_intelligibility": 0.8,
                        "sentence_cohesion": 0.75,
                        "task_exam_fit": 0.85,
                        "goal_progress": 0.6
                    },
                    "hotspots": [{"type": "filler", "text": "ähm", "position": 12}]
                }
                st.success("Mock-Session generiert!")
                st.rerun()
        
        st.markdown("---")
        
        # Navigation zurück zur App
        st.subheader("🔗 Navigation")
        st.page_link("pages/grosser_baer.py", label="← Zurück zur Coach-App", icon="🐻")


# =============================================================================
# MAIN
# =============================================================================

if check_admin_auth():
    render_admin_dashboard()
