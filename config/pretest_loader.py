"""
Pretest Loader für Großer Bär
Lädt die Pretest-Konfiguration und rendert die Fragen in Streamlit.
"""

import json
from pathlib import Path
from typing import Optional
from datetime import datetime

import streamlit as st


# =============================================================================
# CONFIG LOADER
# =============================================================================

def load_pretest_config(config_path: str = "config/pretest_config.json") -> dict:
    """Lädt die Pretest-Konfiguration aus der JSON-Datei."""
    path = Path(config_path)
    if not path.exists():
        st.error(f"❌ Pretest-Config nicht gefunden: {config_path}")
        return {"modules": []}
    
    with open(path, "r", encoding="utf-8") as f:
        return json.load(f)


def get_enabled_modules(config: dict) -> list:
    """Gibt nur aktivierte Module zurück."""
    return [m for m in config.get("modules", []) if m.get("enabled", False)]


def get_module_by_id(config: dict, module_id: str) -> Optional[dict]:
    """Gibt ein spezifisches Modul nach ID zurück."""
    for module in config.get("modules", []):
        if module.get("id") == module_id:
            return module
    return None


# =============================================================================
# SESSION STATE HELPERS
# =============================================================================

def init_pretest_state():
    """Initialisiert den Pretest-State."""
    if "pretest_responses" not in st.session_state:
        st.session_state.pretest_responses = {}
    
    if "pretest_completed" not in st.session_state:
        st.session_state.pretest_completed = False
    
    if "pretest_completed_at" not in st.session_state:
        st.session_state.pretest_completed_at = None
    
    if "pretest_current_module" not in st.session_state:
        st.session_state.pretest_current_module = 0
    
    if "session_count" not in st.session_state:
        st.session_state.session_count = 0


def save_response(question_id: str, value):
    """Speichert eine Antwort im Session State."""
    st.session_state.pretest_responses[question_id] = {
        "value": value,
        "answered_at": datetime.now().isoformat()
    }


def get_response(question_id: str, default=None):
    """Holt eine gespeicherte Antwort."""
    response = st.session_state.pretest_responses.get(question_id, {})
    return response.get("value", default)


def check_show_condition(question: dict) -> bool:
    """Prüft, ob eine Frage angezeigt werden soll (show_if Logik)."""
    show_if = question.get("show_if")
    if not show_if:
        return True
    
    field = show_if.get("field")
    expected_value = show_if.get("value")
    actual_value = get_response(field)
    
    # Handle Liste von möglichen Werten
    if isinstance(expected_value, list):
        return actual_value in expected_value
    
    return actual_value == expected_value


# =============================================================================
# QUESTION RENDERERS
# =============================================================================

def render_single_select(question: dict, key_prefix: str = "") -> Optional[str]:
    """Rendert eine Single-Select-Frage."""
    options = question.get("options", [])
    
    # Optionen können dict oder string sein
    if options and isinstance(options[0], dict):
        option_labels = [opt["label"] for opt in options]
        option_values = [opt["value"] for opt in options]
    else:
        option_labels = options
        option_values = options
    
    # Vorherige Antwort laden
    previous = get_response(question["id"])
    default_index = 0
    if previous and previous in option_values:
        default_index = option_values.index(previous)
    
    selected_label = st.selectbox(
        question["label"],
        options=option_labels,
        index=default_index,
        help=question.get("description"),
        key=f"{key_prefix}_{question['id']}"
    )
    
    # Label zu Value mappen
    selected_index = option_labels.index(selected_label)
    return option_values[selected_index]


def render_multi_select(question: dict, key_prefix: str = "") -> list:
    """Rendert eine Multi-Select-Frage."""
    options = question.get("options", [])
    
    if options and isinstance(options[0], dict):
        option_labels = [opt["label"] for opt in options]
        option_values = [opt["value"] for opt in options]
    else:
        option_labels = options
        option_values = options
    
    # Vorherige Antworten laden
    previous = get_response(question["id"], [])
    default_labels = [option_labels[option_values.index(v)] for v in previous if v in option_values]
    
    selected_labels = st.multiselect(
        question["label"],
        options=option_labels,
        default=default_labels,
        help=question.get("description"),
        key=f"{key_prefix}_{question['id']}"
    )
    
    # Labels zu Values mappen
    return [option_values[option_labels.index(label)] for label in selected_labels]


def render_boolean(question: dict, key_prefix: str = "") -> bool:
    """Rendert eine Ja/Nein-Frage."""
    previous = get_response(question["id"], False)
    
    return st.checkbox(
        question["label"],
        value=previous,
        help=question.get("description"),
        key=f"{key_prefix}_{question['id']}"
    )


def render_text(question: dict, key_prefix: str = "") -> str:
    """Rendert ein Textfeld."""
    previous = get_response(question["id"], "")
    
    return st.text_input(
        question["label"],
        value=previous,
        placeholder=question.get("placeholder", ""),
        help=question.get("description"),
        key=f"{key_prefix}_{question['id']}"
    )


def render_number(question: dict, key_prefix: str = "") -> int:
    """Rendert ein Zahlenfeld."""
    previous = get_response(question["id"], 0)
    
    return st.number_input(
        question["label"],
        min_value=question.get("min", 0),
        max_value=question.get("max", 1000),
        value=previous,
        help=question.get("description"),
        key=f"{key_prefix}_{question['id']}"
    )


def render_likert(question: dict, scale: dict, key_prefix: str = "") -> int:
    """Rendert eine Likert-Skala-Frage."""
    anchors = scale.get("anchors", {})
    previous = get_response(question["id"], 3)  # Default: Mitte
    
    # Radio-Buttons für Likert
    options = list(range(1, 6))
    option_labels = [f"{i} – {anchors.get(str(i), '')}" for i in options]
    
    previous_index = previous - 1 if previous else 2
    
    selected = st.radio(
        question["label"],
        options=option_labels,
        index=previous_index,
        horizontal=True,
        key=f"{key_prefix}_{question['id']}"
    )
    
    # Extrahiere die Zahl
    return int(selected.split(" – ")[0])


# =============================================================================
# MODULE RENDERER
# =============================================================================

def render_module(module: dict, key_prefix: str = "") -> dict:
    """Rendert ein komplettes Modul und gibt die Antworten zurück."""
    responses = {}
    
    st.subheader(module.get("name", "Fragebogen"))
    
    if module.get("description"):
        st.markdown(module["description"])
    
    if module.get("instructions"):
        st.info(module["instructions"])
    
    # Hole Skala für Likert-Fragen
    scale = module.get("scale", {})
    
    for question in module.get("questions", []):
        # Prüfe show_if Bedingung
        if not check_show_condition(question):
            continue
        
        q_type = question.get("type", "text")
        q_id = question["id"]
        
        # Render je nach Typ
        if q_type == "single_select":
            value = render_single_select(question, key_prefix)
        elif q_type == "multi_select":
            value = render_multi_select(question, key_prefix)
        elif q_type == "boolean":
            value = render_boolean(question, key_prefix)
        elif q_type == "text":
            value = render_text(question, key_prefix)
        elif q_type == "number":
            value = render_number(question, key_prefix)
        elif q_type == "likert_5" or scale.get("type") == "likert_5":
            value = render_likert(question, scale, key_prefix)
        else:
            st.warning(f"Unbekannter Fragetyp: {q_type}")
            continue
        
        responses[q_id] = value
        
        # Speichere sofort im State
        save_response(q_id, value)
    
    return responses


# =============================================================================
# MASQ SCORING
# =============================================================================

def calculate_masq_scores(responses: dict, scoring_config: dict) -> dict:
    """Berechnet die MASQ-Scores basierend auf den Antworten."""
    factors = scoring_config.get("factors", {})
    
    factor_scores = {}
    
    for factor_name, question_ids in factors.items():
        values = []
        for q_id in question_ids:
            value = responses.get(q_id)
            if value is not None:
                values.append(value)
        
        if values:
            factor_scores[factor_name] = {
                "mean": sum(values) / len(values),
                "sum": sum(values),
                "items": len(values)
            }
    
    # Gesamtscore: (PE + PS + PK + DA) - MT
    total = 0
    for factor in ["PE", "PS", "PK", "DA"]:
        if factor in factor_scores:
            total += factor_scores[factor]["sum"]
    
    if "MT" in factor_scores:
        total -= factor_scores["MT"]["sum"]
    
    # Interpretation
    interpretation_config = scoring_config.get("interpretation", {})
    level = "medium"
    if total >= interpretation_config.get("high", {}).get("min", 70):
        level = "high"
    elif total < interpretation_config.get("low", {}).get("max", 45):
        level = "low"
    
    return {
        "factors": factor_scores,
        "total": total,
        "level": level,
        "level_label": interpretation_config.get(level, {}).get("label", level)
    }


# =============================================================================
# MAIN PRETEST FLOW
# =============================================================================

def should_show_pretest(config: dict) -> bool:
    """Prüft, ob der Pretest angezeigt werden soll."""
    # Wenn noch nie abgeschlossen
    if not st.session_state.get("pretest_completed", False):
        return True
    
    # Prüfe Level-Recheck
    level_recheck = get_module_by_id(config, "level_recheck")
    if level_recheck and level_recheck.get("enabled"):
        frequency_n = level_recheck.get("frequency_n", 5)
        session_count = st.session_state.get("session_count", 0)
        
        if session_count > 0 and session_count % frequency_n == 0:
            # Nur Level-Recheck, nicht den ganzen Pretest
            st.session_state.pretest_show_recheck = True
            return False  # Kein voller Pretest, aber Recheck
    
    return False


def render_pretest(config: dict) -> bool:
    """
    Rendert den kompletten Pretest.
    Gibt True zurück, wenn abgeschlossen.
    """
    init_pretest_state()
    
    enabled_modules = [m for m in get_enabled_modules(config) 
                       if m.get("frequency") == "once_per_user"]
    
    if not enabled_modules:
        return True
    
    st.title("📋 Bevor wir starten...")
    st.markdown(
        "Bitte beantworte diese Fragen, damit wir dein Feedback besser auf dich "
        "abstimmen können. Das dauert nur 2-3 Minuten."
    )
    
    # Progress Bar
    if config.get("settings", {}).get("show_progress_bar", True):
        current = st.session_state.pretest_current_module
        total = len(enabled_modules)
        st.progress((current) / total, text=f"Modul {current + 1} von {total}")
    
    st.markdown("---")
    
    # Aktuelles Modul
    current_index = st.session_state.pretest_current_module
    
    if current_index >= len(enabled_modules):
        # Alle Module abgeschlossen
        st.session_state.pretest_completed = True
        st.session_state.pretest_completed_at = datetime.now().isoformat()
        return True
    
    current_module = enabled_modules[current_index]
    
    # Modul rendern
    with st.form(key=f"pretest_form_{current_module['id']}"):
        responses = render_module(current_module, key_prefix="pretest")
        
        col1, col2, col3 = st.columns([1, 1, 1])
        
        with col1:
            if current_index > 0:
                back = st.form_submit_button("← Zurück")
            else:
                back = False
        
        with col3:
            if current_index < len(enabled_modules) - 1:
                next_btn = st.form_submit_button("Weiter →", type="primary")
            else:
                next_btn = st.form_submit_button("✅ Abschließen", type="primary")
        
        if back:
            st.session_state.pretest_current_module -= 1
            st.rerun()
        
        if next_btn:
            # Validierung: Pflichtfelder prüfen
            missing = []
            for q in current_module.get("questions", []):
                if q.get("required", False) and check_show_condition(q):
                    value = responses.get(q["id"])
                    if value is None or value == "" or value == []:
                        missing.append(q["label"])
            
            if missing:
                st.error(f"Bitte beantworte: {', '.join(missing[:2])}...")
            else:
                # MASQ-Scores berechnen wenn MASQ-Modul
                if current_module["id"] == "masq_short":
                    scoring = current_module.get("scoring", {})
                    masq_scores = calculate_masq_scores(
                        st.session_state.pretest_responses, 
                        scoring
                    )
                    st.session_state.pretest_responses["masq_scores"] = masq_scores
                
                st.session_state.pretest_current_module += 1
                st.rerun()
    
    return False


def render_level_recheck(config: dict):
    """Rendert den Level-Recheck nach N Sessions."""
    level_recheck = get_module_by_id(config, "level_recheck")
    
    if not level_recheck:
        return
    
    st.info("🔄 **Kurzer Check:** Hat sich dein Niveau verändert?")
    
    with st.form("level_recheck_form"):
        responses = render_module(level_recheck, key_prefix="recheck")
        
        if st.form_submit_button("Bestätigen", type="primary"):
            st.session_state.pretest_show_recheck = False
            st.rerun()


# =============================================================================
# EXPORT HELPERS
# =============================================================================

def get_pretest_data_for_airtable() -> dict:
    """Bereitet die Pretest-Daten für Airtable auf."""
    responses = st.session_state.get("pretest_responses", {})
    
    # Flache Struktur für Airtable
    # WICHTIG: Keine None-Werte! Airtable braucht echte Defaults.
    data = {
        "pretest_completed": st.session_state.get("pretest_completed", False),
        "pretest_completed_at": st.session_state.get("pretest_completed_at") or "",  # FIX: None → ""
    }
    
    # CEFR-Felder – mit expliziten Fallbacks für None
    data["cefr_self_overall"] = get_response("cefr_overall") or ""  # FIX
    data["cefr_self_speaking"] = get_response("cefr_speaking") or ""  # FIX
    data["has_official_cert"] = get_response("has_official_cert", False) or False
    data["official_cert_type"] = get_response("official_cert_type", "") or ""
    data["learning_duration_months"] = get_response("learning_duration_months", 0) or 0
    data["learning_context"] = ",".join(get_response("learning_context", []) or [])
    data["native_language"] = get_response("native_language", "") or ""
    data["other_languages"] = get_response("other_languages", "") or ""
    
    # MASQ-Scores – IMMER mit Defaults initialisieren (FIX)
    data["masq_total"] = 0
    data["masq_level"] = ""
    data["masq_pe_mean"] = 0.0
    data["masq_ps_mean"] = 0.0
    data["masq_pk_mean"] = 0.0
    data["masq_mt_mean"] = 0.0
    data["masq_da_mean"] = 0.0
    
    # Überschreibe mit echten Werten wenn vorhanden
    masq = responses.get("masq_scores", {})
    if masq:
        data["masq_total"] = masq.get("total", 0) or 0
        data["masq_level"] = masq.get("level", "") or ""
        
        factors = masq.get("factors", {})
        for factor in ["PE", "PS", "PK", "MT", "DA"]:
            if factor in factors:
                mean_value = factors[factor].get("mean", 0)
                data[f"masq_{factor.lower()}_mean"] = float(mean_value) if mean_value else 0.0
    
    return data


def get_pretest_data_for_coach_input() -> dict:
    """Bereitet die Pretest-Daten für den Coach-Input auf."""
    return {
        "self_assessment": {
            "cefr_overall": get_response("cefr_overall"),
            "cefr_speaking": get_response("cefr_speaking"),
            "has_official_cert": get_response("has_official_cert", False),
            "official_cert_type": get_response("official_cert_type"),
        },
        "learner_profile": {
            "learning_duration_months": get_response("learning_duration_months"),
            "learning_context": get_response("learning_context", []),
            "native_language": get_response("native_language"),
            "other_languages": get_response("other_languages"),
        },
        "masq": st.session_state.get("pretest_responses", {}).get("masq_scores", {}),
    }
