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
    # TAB 1: Einstellungen
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
        
        st.markdown("---")
        
        # Aktuelle Config anzeigen
        with st.expander("📋 Aktuelle Config (JSON)"):
            st.json(st.session_state.get("app_config", {}))
    
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
            st.metric("Aktuelle Phase", st.session_state.get("current_phase", "–"))
        
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
                    "user_reflection", "feedback_result", "coach_input"
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
            
            if st.button("💥 ALLES zurücksetzen", type="secondary", use_container_width=True):
                for key in list(st.session_state.keys()):
                    if key != "admin_authenticated":
                        del st.session_state[key]
                st.success("Kompletter State gelöscht!")
                st.rerun()
        
        with col2:
            st.subheader("Export")
            
            if st.button("📥 State als JSON exportieren", use_container_width=True):
                json_export = export_state_as_json()
                st.download_button(
                    "⬇️ JSON herunterladen",
                    data=json_export,
                    file_name=f"grosser_baer_state_{datetime.now().strftime('%Y%m%d_%H%M')}.json",
                    mime="application/json"
                )
            
            st.subheader("Test-Daten")
            
            if st.button("🎲 Mock-User generieren", use_container_width=True):
                import random
                st.session_state.user_code = f"TEST_{random.randint(1000, 9999)}"
                st.session_state.session_count = random.randint(0, 10)
                st.success(f"Mock-User erstellt: {st.session_state.user_code}")
        
        st.markdown("---")
        
        # Config anzeigen
        if PRETEST_AVAILABLE:
            with st.expander("📋 Pretest-Config anzeigen"):
                try:
                    config = load_pretest_config()
                    st.json(config)
                except Exception as e:
                    st.error(f"Fehler beim Laden: {e}")


# =============================================================================
# MAIN
# =============================================================================

if check_admin_auth():
    render_admin_dashboard()
