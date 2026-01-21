# grosser_baer/session_logger.py
"""
Session-Logging für Großer Bär.
Speichert alle Daten einer Session in strukturiertem JSON-Format.
Optimiert für Forschungsdaten-Export.
"""

import json
import os
from datetime import datetime
from pathlib import Path
from typing import Any
import uuid


# =============================================================================
# KONFIGURATION
# =============================================================================

# Standard-Speicherort (kann überschrieben werden)
DEFAULT_LOG_DIR = Path("session_logs")

# Für Streamlit Cloud: Verwende tmp wenn nötig
CLOUD_LOG_DIR = Path("/tmp/session_logs")


# =============================================================================
# SESSION-DATENSTRUKTUR
# =============================================================================

def create_session_record(
    user_id: str | None = None,
    task_id: str | None = None
) -> dict:
    """
    Erstellt einen neuen Session-Record mit allen Feldern.
    
    Args:
        user_id: Optional, Nutzer-Identifikator (anonymisiert)
        task_id: Optional, ID des gewählten Tasks
    
    Returns:
        Leerer Session-Record als Dict
    """
    return {
        # === Identifikation ===
        "session_id": str(uuid.uuid4()),
        "user_id": user_id or f"anon_{uuid.uuid4().hex[:8]}",
        "created_at": datetime.now().isoformat(),
        "completed_at": None,
        
        # === Task-Kontext ===
        "task": {
            "task_id": task_id,
            "title": None,
            "context": None,
            "register": None,
            "time_seconds": None
        },
        
        # === Phase 1: Plan ===
        "plan": {
            "started_at": None,
            "completed_at": None,
            "meta_prompt_shown": None,
            "user_response": None,  # Falls wir Planungs-Input erfassen
            "preparation_time_seconds": None
        },
        
        # === Phase 2: Perform ===
        "perform": {
            "started_at": None,
            "completed_at": None,
            "duration_seconds": None,
            "audio_file_path": None,
            "monitor_prompts_shown": [],
            
            # STT-Ergebnis
            "transcript": {
                "text": None,
                "word_count": None,
                "confidence": None,  # Von Azure STT
                "language_detected": None
            },
            
            # Prosodie (Azure Pronunciation Assessment)
            "prosody": {
                "speech_rate_wpm": None,
                "pause_ratio": None,
                "filler_count": None,
                "filler_rate": None,
                "pronunciation_score": None,
                "fluency_score": None,
                "raw_azure_response": None  # Für Debugging
            }
        },
        
        # === Phase 3: Feedback ===
        "feedback": {
            "generated_at": None,
            
            # Kleiner Bär Metriken
            "metrics": {
                "cefr_score": None,
                "cefr_label": None,
                "lexical_diversity": None,
                "grammar_accuracy": None,
                "register_match": None,
                "cohesion": None,
                "avg_sentence_length": None,
                "raw_kleiner_baer": None  # Vollständige Analyse
            },
            
            # Claude Feedback
            "narrative": {
                "text": None,
                "model_used": None,
                "prompt_tokens": None,
                "completion_tokens": None,
                "is_mock": False
            }
        },
        
        # === Phase 4: Reflect ===
        "reflect": {
            "started_at": None,
            "completed_at": None,
            "prompts_shown": [],
            "user_responses": {},  # Dict mit prompt_key: response
            "retry_requested": False
        },
        
        # === Meta ===
        "meta": {
            "app_version": "0.1.0",
            "session_complete": False,
            "phases_completed": [],
            "errors": [],
            "notes": None
        }
    }


# =============================================================================
# SESSION LOGGER KLASSE
# =============================================================================

class SessionLogger:
    """
    Verwaltet das Logging einer einzelnen Session.
    
    Usage:
        logger = SessionLogger(user_id="user123", task_id="meeting_update")
        logger.log_plan_start()
        logger.log_transcript("Hallo, ich möchte...")
        logger.log_metrics({...})
        logger.save()
    """
    
    def __init__(
        self,
        user_id: str | None = None,
        task_id: str | None = None,
        log_dir: Path | str | None = None
    ):
        """
        Initialisiert einen neuen SessionLogger.
        
        Args:
            user_id: Nutzer-Identifikator
            task_id: Task-Template ID
            log_dir: Speicherort für Logs
        """
        self.record = create_session_record(user_id, task_id)
        self.log_dir = Path(log_dir) if log_dir else self._get_log_dir()
        self._ensure_log_dir()
    
    def _get_log_dir(self) -> Path:
        """Bestimmt den passenden Log-Ordner."""
        # Prüfe ob wir auf Streamlit Cloud sind
        if os.environ.get("STREAMLIT_RUNTIME"):
            return CLOUD_LOG_DIR
        return DEFAULT_LOG_DIR
    
    def _ensure_log_dir(self):
        """Erstellt Log-Ordner falls nötig."""
        self.log_dir.mkdir(parents=True, exist_ok=True)
    
    @property
    def session_id(self) -> str:
        return self.record["session_id"]
    
    def _now(self) -> str:
        """Aktueller Timestamp als ISO-String."""
        return datetime.now().isoformat()
    
    # -------------------------------------------------------------------------
    # Task-Kontext
    # -------------------------------------------------------------------------
    
    def log_task(self, task: dict):
        """Speichert Task-Informationen."""
        self.record["task"].update({
            "task_id": task.get("id"),
            "title": task.get("title"),
            "context": task.get("context"),
            "register": task.get("register"),
            "time_seconds": task.get("time_seconds")
        })
    
    # -------------------------------------------------------------------------
    # Phase 1: Plan
    # -------------------------------------------------------------------------
    
    def log_plan_start(self, meta_prompt: str | None = None):
        """Markiert Start der Plan-Phase."""
        self.record["plan"]["started_at"] = self._now()
        self.record["plan"]["meta_prompt_shown"] = meta_prompt
        self._add_phase("plan")
    
    def log_plan_complete(self, user_response: str | None = None):
        """Markiert Ende der Plan-Phase."""
        self.record["plan"]["completed_at"] = self._now()
        self.record["plan"]["user_response"] = user_response
        
        # Berechne Vorbereitungszeit
        if self.record["plan"]["started_at"]:
            start = datetime.fromisoformat(self.record["plan"]["started_at"])
            end = datetime.fromisoformat(self.record["plan"]["completed_at"])
            self.record["plan"]["preparation_time_seconds"] = (end - start).total_seconds()
    
    # -------------------------------------------------------------------------
    # Phase 2: Perform
    # -------------------------------------------------------------------------
    
    def log_perform_start(self):
        """Markiert Start der Aufnahme."""
        self.record["perform"]["started_at"] = self._now()
        self._add_phase("perform")
    
    def log_perform_complete(self, audio_file_path: str | None = None):
        """Markiert Ende der Aufnahme."""
        self.record["perform"]["completed_at"] = self._now()
        self.record["perform"]["audio_file_path"] = audio_file_path
        
        # Berechne Aufnahmedauer
        if self.record["perform"]["started_at"]:
            start = datetime.fromisoformat(self.record["perform"]["started_at"])
            end = datetime.fromisoformat(self.record["perform"]["completed_at"])
            self.record["perform"]["duration_seconds"] = (end - start).total_seconds()
    
    def log_monitor_prompt(self, prompt: str):
        """Loggt einen gezeigten Monitor-Prompt."""
        self.record["perform"]["monitor_prompts_shown"].append({
            "prompt": prompt,
            "shown_at": self._now()
        })
    
    def log_transcript(
        self,
        text: str,
        confidence: float | None = None,
        language: str | None = None
    ):
        """Speichert das STT-Transkript."""
        self.record["perform"]["transcript"].update({
            "text": text,
            "word_count": len(text.split()) if text else 0,
            "confidence": confidence,
            "language_detected": language
        })
    
    def log_prosody(
        self,
        speech_rate: float | None = None,
        pause_ratio: float | None = None,
        filler_count: int | None = None,
        pronunciation_score: float | None = None,
        fluency_score: float | None = None,
        raw_response: dict | None = None
    ):
        """Speichert Prosodie-Daten."""
        word_count = self.record["perform"]["transcript"].get("word_count", 0)
        
        self.record["perform"]["prosody"].update({
            "speech_rate_wpm": speech_rate,
            "pause_ratio": pause_ratio,
            "filler_count": filler_count,
            "filler_rate": filler_count / word_count if word_count > 0 and filler_count else None,
            "pronunciation_score": pronunciation_score,
            "fluency_score": fluency_score,
            "raw_azure_response": raw_response
        })
    
    # -------------------------------------------------------------------------
    # Phase 3: Feedback
    # -------------------------------------------------------------------------
    
    def log_metrics(self, kleiner_baer_result: dict):
        """Speichert Kleiner Bär Analyse-Ergebnisse."""
        self.record["feedback"]["generated_at"] = self._now()
        self._add_phase("feedback")
        
        cefr = kleiner_baer_result.get("cefr", {})
        dims = kleiner_baer_result.get("dims", {})
        disce = kleiner_baer_result.get("disce_metrics", {})
        stats = kleiner_baer_result.get("text_stats", {})
        
        self.record["feedback"]["metrics"].update({
            "cefr_score": cefr.get("score"),
            "cefr_label": cefr.get("label"),
            "lexical_diversity": dims.get("lexical_diversity"),
            "grammar_accuracy": dims.get("grammar_accuracy"),
            "register_match": disce.get("level_match"),
            "cohesion": dims.get("cohesion"),
            "avg_sentence_length": stats.get("avg_sentence_length"),
            "raw_kleiner_baer": kleiner_baer_result
        })
    
    def log_narrative_feedback(
        self,
        text: str,
        model: str | None = None,
        prompt_tokens: int | None = None,
        completion_tokens: int | None = None,
        is_mock: bool = False
    ):
        """Speichert das narrative Feedback von Claude."""
        self.record["feedback"]["narrative"].update({
            "text": text,
            "model_used": model,
            "prompt_tokens": prompt_tokens,
            "completion_tokens": completion_tokens,
            "is_mock": is_mock
        })
    
    # -------------------------------------------------------------------------
    # Phase 4: Reflect
    # -------------------------------------------------------------------------
    
    def log_reflect_start(self, prompts: list[str] | None = None):
        """Markiert Start der Reflexions-Phase."""
        self.record["reflect"]["started_at"] = self._now()
        self.record["reflect"]["prompts_shown"] = prompts or []
        self._add_phase("reflect")
    
    def log_reflect_response(self, prompt_key: str, response: str):
        """Speichert eine Reflexions-Antwort."""
        self.record["reflect"]["user_responses"][prompt_key] = {
            "response": response,
            "recorded_at": self._now()
        }
    
    def log_reflect_complete(self, retry_requested: bool = False):
        """Markiert Ende der Reflexions-Phase."""
        self.record["reflect"]["completed_at"] = self._now()
        self.record["reflect"]["retry_requested"] = retry_requested
    
    # -------------------------------------------------------------------------
    # Meta & Utilities
    # -------------------------------------------------------------------------
    
    def _add_phase(self, phase: str):
        """Fügt Phase zur Liste der abgeschlossenen Phasen hinzu."""
        if phase not in self.record["meta"]["phases_completed"]:
            self.record["meta"]["phases_completed"].append(phase)
    
    def log_error(self, error: str, context: str | None = None):
        """Loggt einen Fehler."""
        self.record["meta"]["errors"].append({
            "error": error,
            "context": context,
            "occurred_at": self._now()
        })
    
    def set_complete(self):
        """Markiert Session als vollständig abgeschlossen."""
        self.record["completed_at"] = self._now()
        self.record["meta"]["session_complete"] = True
    
    def add_note(self, note: str):
        """Fügt eine Notiz hinzu."""
        self.record["meta"]["notes"] = note
    
    # -------------------------------------------------------------------------
    # Persistenz
    # -------------------------------------------------------------------------
    
    def get_filename(self) -> str:
        """Generiert Dateinamen für diese Session."""
        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        user_short = self.record["user_id"][:8]
        return f"session_{timestamp}_{user_short}_{self.session_id[:8]}.json"
    
    def save(self) -> Path:
        """
        Speichert die Session als JSON-Datei.
        
        Returns:
            Pfad zur gespeicherten Datei
        """
        filepath = self.log_dir / self.get_filename()
        
        with open(filepath, "w", encoding="utf-8") as f:
            json.dump(self.record, f, ensure_ascii=False, indent=2)
        
        return filepath
    
    def to_dict(self) -> dict:
        """Gibt den aktuellen Record als Dict zurück."""
        return self.record.copy()
    
    def to_json(self) -> str:
        """Gibt den aktuellen Record als JSON-String zurück."""
        return json.dumps(self.record, ensure_ascii=False, indent=2)


# =============================================================================
# EXPORT-UTILITIES (für Admin-Dashboard später)
# =============================================================================

def load_session(filepath: Path | str) -> dict:
    """Lädt eine einzelne Session aus JSON."""
    with open(filepath, "r", encoding="utf-8") as f:
        return json.load(f)


def load_all_sessions(log_dir: Path | str | None = None) -> list[dict]:
    """
    Lädt alle Sessions aus dem Log-Ordner.
    
    Returns:
        Liste aller Session-Records
    """
    log_dir = Path(log_dir) if log_dir else DEFAULT_LOG_DIR
    
    if not log_dir.exists():
        return []
    
    sessions = []
    for filepath in log_dir.glob("session_*.json"):
        try:
            sessions.append(load_session(filepath))
        except (json.JSONDecodeError, IOError) as e:
            print(f"Fehler beim Laden von {filepath}: {e}")
    
    # Sortiere nach Erstellungsdatum
    sessions.sort(key=lambda s: s.get("created_at", ""), reverse=True)
    return sessions


def export_sessions_csv(
    sessions: list[dict],
    output_path: Path | str
) -> Path:
    """
    Exportiert Sessions als CSV für Analyse.
    Flacht die Struktur ab für tabellarische Ansicht.
    
    Returns:
        Pfad zur CSV-Datei
    """
    import csv
    
    output_path = Path(output_path)
    
    # Definiere Spalten für Export
    fieldnames = [
        "session_id",
        "user_id",
        "created_at",
        "completed_at",
        "session_complete",
        "task_id",
        "task_title",
        "task_context",
        "preparation_time_seconds",
        "recording_duration_seconds",
        "transcript_text",
        "transcript_word_count",
        "cefr_score",
        "cefr_label",
        "lexical_diversity",
        "grammar_accuracy",
        "register_match",
        "cohesion",
        "speech_rate_wpm",
        "filler_rate",
        "feedback_is_mock",
        "retry_requested"
    ]
    
    rows = []
    for s in sessions:
        rows.append({
            "session_id": s.get("session_id"),
            "user_id": s.get("user_id"),
            "created_at": s.get("created_at"),
            "completed_at": s.get("completed_at"),
            "session_complete": s.get("meta", {}).get("session_complete"),
            "task_id": s.get("task", {}).get("task_id"),
            "task_title": s.get("task", {}).get("title"),
            "task_context": s.get("task", {}).get("context"),
            "preparation_time_seconds": s.get("plan", {}).get("preparation_time_seconds"),
            "recording_duration_seconds": s.get("perform", {}).get("duration_seconds"),
            "transcript_text": s.get("perform", {}).get("transcript", {}).get("text"),
            "transcript_word_count": s.get("perform", {}).get("transcript", {}).get("word_count"),
            "cefr_score": s.get("feedback", {}).get("metrics", {}).get("cefr_score"),
            "cefr_label": s.get("feedback", {}).get("metrics", {}).get("cefr_label"),
            "lexical_diversity": s.get("feedback", {}).get("metrics", {}).get("lexical_diversity"),
            "grammar_accuracy": s.get("feedback", {}).get("metrics", {}).get("grammar_accuracy"),
            "register_match": s.get("feedback", {}).get("metrics", {}).get("register_match"),
            "cohesion": s.get("feedback", {}).get("metrics", {}).get("cohesion"),
            "speech_rate_wpm": s.get("perform", {}).get("prosody", {}).get("speech_rate_wpm"),
            "filler_rate": s.get("perform", {}).get("prosody", {}).get("filler_rate"),
            "feedback_is_mock": s.get("feedback", {}).get("narrative", {}).get("is_mock"),
            "retry_requested": s.get("reflect", {}).get("retry_requested")
        })
    
    with open(output_path, "w", encoding="utf-8", newline="") as f:
        writer = csv.DictWriter(f, fieldnames=fieldnames)
        writer.writeheader()
        writer.writerows(rows)
    
    return output_path


def get_session_summary_stats(sessions: list[dict]) -> dict:
    """
    Berechnet zusammenfassende Statistiken über alle Sessions.
    Nützlich für Admin-Dashboard.
    """
    if not sessions:
        return {"total_sessions": 0}
    
    complete = [s for s in sessions if s.get("meta", {}).get("session_complete")]
    
    cefr_scores = [
        s.get("feedback", {}).get("metrics", {}).get("cefr_score")
        for s in complete
        if s.get("feedback", {}).get("metrics", {}).get("cefr_score") is not None
    ]
    
    return {
        "total_sessions": len(sessions),
        "complete_sessions": len(complete),
        "completion_rate": len(complete) / len(sessions) if sessions else 0,
        "unique_users": len(set(s.get("user_id") for s in sessions)),
        "avg_cefr_score": sum(cefr_scores) / len(cefr_scores) if cefr_scores else None,
        "retry_rate": sum(
            1 for s in complete 
            if s.get("reflect", {}).get("retry_requested")
        ) / len(complete) if complete else 0,
        "tasks_distribution": _count_tasks(sessions)
    }


def _count_tasks(sessions: list[dict]) -> dict:
    """Zählt wie oft jeder Task verwendet wurde."""
    counts = {}
    for s in sessions:
        task_id = s.get("task", {}).get("task_id")
        if task_id:
            counts[task_id] = counts.get(task_id, 0) + 1
    return counts
