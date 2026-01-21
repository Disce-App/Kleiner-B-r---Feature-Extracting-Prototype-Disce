# grosser_baer/__init__.py
"""
Großer Bär – Speaking Coach Modul für Disce.
Orchestriert Audio → Analyse → Feedback Pipeline.
"""

# Task-Verwaltung
from .task_templates import get_task, get_all_tasks, get_task_choices

# Prompts
from .prompts import build_feedback_prompt, get_meta_prompt, SYSTEM_PROMPT_COACH

# Session-Logging
from .session_logger import SessionLogger

# Audio-Verarbeitung (NEU)
from .audio_handler import (
    AudioProcessor,
    AudioAnalysisResult,
    TranscriptResult,
    ProsodyResult,
    process_speaking_task,
    render_audio_recorder,
)

# Feedback-Generierung (NEU)
from .feedback_generator import (
    FeedbackGenerator,
    FeedbackResult,
    generate_feedback,
    format_feedback_markdown,
)

__all__ = [
    # Tasks
    "get_task",
    "get_all_tasks", 
    "get_task_choices",
    # Prompts
    "build_feedback_prompt",
    "get_meta_prompt",
    "SYSTEM_PROMPT_COACH",
    # Session
    "SessionLogger",
    # Audio
    "AudioProcessor",
    "AudioAnalysisResult",
    "TranscriptResult",
    "ProsodyResult",
    "process_speaking_task",
    "render_audio_recorder",
    # Feedback
    "FeedbackGenerator",
    "FeedbackResult",
    "generate_feedback",
    "format_feedback_markdown",
]
