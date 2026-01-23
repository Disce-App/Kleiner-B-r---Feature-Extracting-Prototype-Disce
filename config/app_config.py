"""
App Configuration für Großer Bär
Zentrale Verwaltung von Feature-Flags und Debug-Settings.
"""

import streamlit as st
from datetime import datetime
import json


# =============================================================================
# DEFAULT SETTINGS
# =============================================================================

DEFAULT_SETTINGS = {
    # Modi
    "mock_mode": True,              # Mock statt echtem Audio/LLM
    "debug_mode": False,            # Erweiterte Debug-Infos anzeigen
    "skip_pretest": False,          # Pretest überspringen (nur Dev)
    "disable_airtable": False,      # Keine Daten an Make senden
    
    # Logging
    "log_payloads": True,           # Payloads im State speichern
    "log_llm_calls": True,          # LLM In/Out loggen
    
    # UI
    "show_metrics_tab": True,       # Metriken-Tab anzeigen
    "show_llm_input_tab": True,     # LLM-Input Tab anzeigen
}


# =============================================================================
# STATE INITIALIZATION
# =============================================================================

def init_app_config():
    """Initialisiert App-Config im Session State."""
    if "app_config" not in st.session_state:
        st.session_state.app_config = DEFAULT_SETTINGS.copy()
    
    # Logging-Storage
    if "debug_logs" not in st.session_state:
        st.session_state.debug_logs = {
            "payloads": [],         # Liste der gesendeten Payloads
            "llm_calls": [],        # Liste der LLM-Aufrufe
            "errors": [],           # Fehler-Log
            "events": [],           # Allgemeine Events
        }


def get_config(key: str, default=None):
    """Holt einen Config-Wert."""
    init_app_config()
    return st.session_state.app_config.get(key, default)


def set_config(key: str, value):
    """Setzt einen Config-Wert."""
    init_app_config()
    st.session_state.app_config[key] = value


def is_mock_mode() -> bool:
    """Shortcut: Ist Mock-Modus aktiv?"""
    return get_config("mock_mode", True)


def is_debug_mode() -> bool:
    """Shortcut: Ist Debug-Modus aktiv?"""
    return get_config("debug_mode", False)


def should_skip_pretest() -> bool:
    """Shortcut: Soll Pretest übersprungen werden?"""
    return get_config("skip_pretest", False)


def is_airtable_enabled() -> bool:
    """Shortcut: Ist Airtable/Make aktiv?"""
    return not get_config("disable_airtable", False)


# =============================================================================
# LOGGING FUNCTIONS
# =============================================================================

def log_event(event_type: str, message: str, data: dict = None):
    """Loggt ein Event."""
    init_app_config()
    
    log_entry = {
        "timestamp": datetime.now().isoformat(),
        "type": event_type,
        "message": message,
        "data": data
    }
    
    st.session_state.debug_logs["events"].append(log_entry)
    
    # Limit: Nur letzte 50 Events behalten
    if len(st.session_state.debug_logs["events"]) > 50:
        st.session_state.debug_logs["events"] = st.session_state.debug_logs["events"][-50:]


def log_payload(endpoint: str, payload: dict, response: dict = None):
    """Loggt einen gesendeten Payload."""
    init_app_config()
    
    if not get_config("log_payloads", True):
        return
    
    log_entry = {
        "timestamp": datetime.now().isoformat(),
        "endpoint": endpoint,
        "payload": payload,
        "response": response
    }
    
    st.session_state.debug_logs["payloads"].append(log_entry)
    
    # Limit
    if len(st.session_state.debug_logs["payloads"]) > 20:
        st.session_state.debug_logs["payloads"] = st.session_state.debug_logs["payloads"][-20:]


def log_llm_call(prompt_type: str, input_data: dict, output: str = None):
    """Loggt einen LLM-Aufruf."""
    init_app_config()
    
    if not get_config("log_llm_calls", True):
        return
    
    log_entry = {
        "timestamp": datetime.now().isoformat(),
        "prompt_type": prompt_type,
        "input": input_data,
        "output": output[:500] if output else None  # Truncate
    }
    
    st.session_state.debug_logs["llm_calls"].append(log_entry)
    
    # Limit
    if len(st.session_state.debug_logs["llm_calls"]) > 10:
        st.session_state.debug_logs["llm_calls"] = st.session_state.debug_logs["llm_calls"][-10:]


def log_error(error_type: str, message: str, details: dict = None):
    """Loggt einen Fehler."""
    init_app_config()
    
    log_entry = {
        "timestamp": datetime.now().isoformat(),
        "error_type": error_type,
        "message": message,
        "details": details
    }
    
    st.session_state.debug_logs["errors"].append(log_entry)


def get_logs(log_type: str = None) -> list:
    """Holt Logs (alle oder nach Typ)."""
    init_app_config()
    
    if log_type:
        return st.session_state.debug_logs.get(log_type, [])
    
    return st.session_state.debug_logs


def clear_logs(log_type: str = None):
    """Löscht Logs."""
    init_app_config()
    
    if log_type:
        st.session_state.debug_logs[log_type] = []
    else:
        st.session_state.debug_logs = {
            "payloads": [],
            "llm_calls": [],
            "errors": [],
            "events": [],
        }


# =============================================================================
# EXPORT HELPERS
# =============================================================================

def export_state_as_json() -> str:
    """Exportiert relevanten State als JSON."""
    export_data = {
        "exported_at": datetime.now().isoformat(),
        "app_config": st.session_state.get("app_config", {}),
        "user_code": st.session_state.get("user_code"),
        "session_count": st.session_state.get("session_count", 0),
        "pretest_completed": st.session_state.get("pretest_completed", False),
        "pretest_responses": st.session_state.get("pretest_responses", {}),
        "debug_logs": st.session_state.get("debug_logs", {}),
    }
    
    return json.dumps(export_data, indent=2, ensure_ascii=False, default=str)
