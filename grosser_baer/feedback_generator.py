# grosser_baer/feedback_generator.py
"""
Feedback-Generierung für Großer Bär.
Orchestriert Kleiner Bär Analyse + Claude Narratives Feedback.

Pipeline:
    Transkript → Kleiner Bär (Metriken) → Prompt Builder → Claude → Narratives Feedback
"""

import os
from dataclasses import dataclass, field
from datetime import datetime
from typing import Callable

# Lokale Imports
from .prompts import (
    SYSTEM_PROMPT_COACH,
    MOCK_FEEDBACK,
    build_feedback_prompt,
)
from .audio_handler import AudioAnalysisResult, ProsodyResult


# =============================================================================
# DATENKLASSEN
# =============================================================================

@dataclass
class FeedbackResult:
    """Vollständiges Feedback-Ergebnis."""
    
    # Narratives Feedback (von Claude)
    narrative: str
    
    # Metriken (von Kleiner Bär)
    metrics: dict = field(default_factory=dict)
    
    # CEFR-Einschätzung
    cefr_score: float | None = None
    cefr_label: str | None = None
    
    # Hotspots für gezielte Übungen
    hotspots: list = field(default_factory=list)
    
    # Disce-Metriken für Dashboard
    disce_metrics: dict = field(default_factory=dict)
    
    # Meta
    model_used: str | None = None
    prompt_tokens: int | None = None
    completion_tokens: int | None = None
    is_mock: bool = False
    generated_at: str = field(default_factory=lambda: datetime.now().isoformat())
    processing_time_seconds: float | None = None
    
    def to_dict(self) -> dict:
        """Für Session-Logger."""
        return {
            "narrative": self.narrative,
            "metrics": self.metrics,
            "cefr_score": self.cefr_score,
            "cefr_label": self.cefr_label,
            "hotspots": self.hotspots,
            "disce_metrics": self.disce_metrics,
            "model_used": self.model_used,
            "prompt_tokens": self.prompt_tokens,
            "completion_tokens": self.completion_tokens,
            "is_mock": self.is_mock,
            "generated_at": self.generated_at,
        }


# =============================================================================
# KLEINER BÄR INTEGRATION
# =============================================================================

def analyze_with_kleiner_baer(text: str, context: dict | None = None) -> dict:
    """
    Wrapper für disce_core.analyze_text_for_llm().
    Importiert dynamisch um zirkuläre Imports zu vermeiden.
    
    Returns:
        Dict mit: metrics_summary, cefr, hotspots, disce_metrics
    """
    try:
        # Import aus dem Hauptverzeichnis
        import sys
        from pathlib import Path
        
        # Füge Parent-Verzeichnis zum Path (falls nötig)
        parent_dir = Path(__file__).parent.parent
        if str(parent_dir) not in sys.path:
            sys.path.insert(0, str(parent_dir))
        
        from disce_core import analyze_text_for_llm
        
        return analyze_text_for_llm(text, context or {})
        
    except ImportError as e:
        # Fallback: Minimal-Analyse wenn disce_core nicht verfügbar
        print(f"Warning: disce_core nicht verfügbar: {e}")
        return _mock_kleiner_baer_analysis(text)


def _mock_kleiner_baer_analysis(text: str) -> dict:
    """
    Fallback-Analyse wenn disce_core nicht importierbar.
    Für isoliertes Testing des grosser_baer Moduls.
    """
    word_count = len(text.split())
    sentence_count = text.count('.') + text.count('!') + text.count('?')
    sentence_count = max(1, sentence_count)
    
    return {
        "original_text": text,
        "metrics_summary": {
            "text_stats": {
                "num_sentences": sentence_count,
                "num_tokens": word_count,
                "avg_sentence_length": word_count / sentence_count,
            },
            "dims": {
                "lexical_diversity": 0.65,
                "grammar_accuracy": 0.80,
                "cohesion": 0.70,
                "syntactic_complexity": 0.55,
            },
        },
        "cefr": {
            "score": 4.0,
            "label": "B2",
        },
        "hotspots": [],
        "disce_metrics": {
            "level_match": 0.75,
            "prosody_intelligibility": 0.70,
            "sentence_cohesion": 0.70,
            "task_exam_fit": 0.65,
            "goal_progress": 0.50,
        },
    }


# =============================================================================
# CLAUDE API INTEGRATION
# =============================================================================

def get_anthropic_client():
    """
    Erstellt Anthropic Client wenn API-Key vorhanden.
    Returns None wenn nicht konfiguriert.
    """
    api_key = os.environ.get("ANTHROPIC_API_KEY")
    
    if not api_key:
        return None
    
    try:
        from anthropic import Anthropic
        return Anthropic(api_key=api_key)
    except ImportError:
        raise ImportError(
            "anthropic nicht installiert. "
            "Führe aus: pip install anthropic"
        )


def generate_narrative_with_claude(
    prompt: str,
    system_prompt: str = SYSTEM_PROMPT_COACH,
    model: str = "claude-sonnet-4-20250514",
    max_tokens: int = 1024,
    temperature: float = 0.7,
) -> tuple[str, dict]:
    """
    Generiert narratives Feedback mit Claude.
    
    Args:
        prompt: Der formatierte Feedback-Prompt
        system_prompt: System-Prompt für Claude
        model: Claude-Modell
        max_tokens: Maximale Antwortlänge
        temperature: Kreativität (0-1)
        
    Returns:
        Tuple von (feedback_text, usage_dict)
    """
    client = get_anthropic_client()
    
    if not client:
        raise RuntimeError(
            "Anthropic API nicht konfiguriert. "
            "Setze ANTHROPIC_API_KEY Umgebungsvariable."
        )
    
    response = client.messages.create(
        model=model,
        max_tokens=max_tokens,
        temperature=temperature,
        system=system_prompt,
        messages=[
            {"role": "user", "content": prompt}
        ]
    )
    
    # Extrahiere Text
    feedback_text = response.content[0].text
    
    # Usage-Statistiken
    usage = {
        "model": model,
        "prompt_tokens": response.usage.input_tokens,
        "completion_tokens": response.usage.output_tokens,
    }
    
    return feedback_text, usage


def generate_mock_narrative(
    prompt: str | None = None,
    task_id: str | None = None
) -> tuple[str, dict]:
    """
    Mock-Feedback für Testing ohne Claude API.
    
    Returns:
        Tuple von (feedback_text, usage_dict)
    """
    return MOCK_FEEDBACK, {
        "model": "mock",
        "prompt_tokens": 0,
        "completion_tokens": 0,
    }


# =============================================================================
# HAUPTKLASSE: FEEDBACK GENERATOR
# =============================================================================

class FeedbackGenerator:
    """
    Orchestriert die komplette Feedback-Pipeline.
    
    Usage:
        generator = FeedbackGenerator(use_mock=True)
        
        result = generator.generate(
            transcript="Ich möchte kurz zusammenfassen...",
            task=get_task("meeting_update"),
            prosody=prosody_result
        )
        
        print(result.narrative)
        print(result.cefr_label)
    """
    
    def __init__(
        self,
        use_mock: bool | None = None,
        model: str = "claude-sonnet-4-20250514",
        temperature: float = 0.7,
    ):
        """
        Args:
            use_mock: True = immer Mock, False = immer Claude, None = Auto
            model: Claude-Modell für Feedback
            temperature: Kreativität der Antworten
        """
        self.model = model
        self.temperature = temperature
        
        # Auto-detect Mock-Modus
        if use_mock is None:
            self.use_mock = get_anthropic_client() is None
        else:
            self.use_mock = use_mock
    
    def generate(
        self,
        transcript: str,
        task: dict,
        prosody: ProsodyResult | dict | None = None,
        context: dict | None = None,
    ) -> FeedbackResult:
        """
        Generiert vollständiges Feedback für eine Speaking-Aufnahme.
        
        Args:
            transcript: STT-Transkript des gesprochenen Texts
            task: Task-Template aus task_templates.py
            prosody: Prosodie-Daten (optional)
            context: Zusätzlicher Kontext für Analyse
            
        Returns:
            FeedbackResult mit Narrativ, Metriken, CEFR, Hotspots
        """
        start_time = datetime.now()
        
        # 1. Kleiner Bär Analyse
        analysis = analyze_with_kleiner_baer(transcript, context)
        
        # 2. Prosodie-Dict vorbereiten
        if isinstance(prosody, ProsodyResult):
            prosody_dict = prosody.to_dict()
        elif isinstance(prosody, dict):
            prosody_dict = prosody
        else:
            prosody_dict = {}
        
        # 3. Feedback-Prompt bauen
        prompt = build_feedback_prompt(
            task=task,
            transcript=transcript,
            metrics=analysis,
            prosody=prosody_dict
        )
        
        # 4. Narratives Feedback generieren
        if self.use_mock:
            narrative, usage = generate_mock_narrative(
                prompt=prompt,
                task_id=task.get("id")
            )
        else:
            narrative, usage = generate_narrative_with_claude(
                prompt=prompt,
                model=self.model,
                temperature=self.temperature
            )
        
        # 5. Ergebnis zusammenbauen
        processing_time = (datetime.now() - start_time).total_seconds()
        
        cefr = analysis.get("cefr", {})
        
        return FeedbackResult(
            narrative=narrative,
            metrics=analysis.get("metrics_summary", {}),
            cefr_score=cefr.get("score"),
            cefr_label=cefr.get("label"),
            hotspots=analysis.get("hotspots", []),
            disce_metrics=analysis.get("disce_metrics", {}),
            model_used=usage.get("model"),
            prompt_tokens=usage.get("prompt_tokens"),
            completion_tokens=usage.get("completion_tokens"),
            is_mock=self.use_mock,
            processing_time_seconds=processing_time
        )
    
    def generate_from_audio_result(
        self,
        audio_result: AudioAnalysisResult,
        task: dict,
        context: dict | None = None,
    ) -> FeedbackResult:
        """
        Convenience-Methode: Generiert Feedback direkt aus AudioAnalysisResult.
        
        Usage:
            from grosser_baer.audio_handler import process_speaking_task
            
            audio_result = process_speaking_task(audio_bytes, task_id="meeting_update")
            feedback = generator.generate_from_audio_result(audio_result, task)
        """
        return self.generate(
            transcript=audio_result.transcript.text,
            task=task,
            prosody=audio_result.prosody,
            context=context
        )


# =============================================================================
# CONVENIENCE FUNCTIONS
# =============================================================================

def generate_feedback(
    transcript: str,
    task: dict,
    prosody: ProsodyResult | dict | None = None,
    use_mock: bool | None = None,
) -> FeedbackResult:
    """
    High-Level-Funktion für schnelle Feedback-Generierung.
    
    Args:
        transcript: Der gesprochene Text
        task: Task-Template
        prosody: Prosodie-Daten (optional)
        use_mock: Mock-Modus erzwingen
        
    Returns:
        FeedbackResult
        
    Usage:
        from grosser_baer.task_templates import get_task
        from grosser_baer.feedback_generator import generate_feedback
        
        task = get_task("meeting_update")
        result = generate_feedback(
            transcript="Ich möchte den aktuellen Stand zusammenfassen...",
            task=task,
            use_mock=True
        )
        
        print(result.narrative)
    """
    generator = FeedbackGenerator(use_mock=use_mock)
    return generator.generate(transcript, task, prosody)


def quick_analyze(text: str) -> dict:
    """
    Schnelle Kleiner-Bär-Analyse ohne Feedback-Generierung.
    Nützlich für Testing und Debugging.
    
    Returns:
        Dict mit CEFR, Dims, Hotspots
    """
    return analyze_with_kleiner_baer(text)


# =============================================================================
# BATCH PROCESSING (für Admin/Forschung)
# =============================================================================

def batch_generate_feedback(
    items: list[dict],
    use_mock: bool = True,
    progress_callback: Callable[[int, int], None] | None = None,
) -> list[FeedbackResult]:
    """
    Generiert Feedback für mehrere Sessions.
    
    Args:
        items: Liste von Dicts mit {transcript, task, prosody}
        use_mock: Mock-Modus (empfohlen für Batch)
        progress_callback: Wird mit (current, total) aufgerufen
        
    Returns:
        Liste von FeedbackResults
        
    Usage:
        items = [
            {"transcript": "...", "task": get_task("meeting_update")},
            {"transcript": "...", "task": get_task("phone_complaint")},
        ]
        
        results = batch_generate_feedback(items, use_mock=True)
    """
    generator = FeedbackGenerator(use_mock=use_mock)
    results = []
    
    total = len(items)
    for i, item in enumerate(items):
        result = generator.generate(
            transcript=item["transcript"],
            task=item["task"],
            prosody=item.get("prosody"),
            context=item.get("context")
        )
        results.append(result)
        
        if progress_callback:
            progress_callback(i + 1, total)
    
    return results


# =============================================================================
# FEEDBACK FORMATTER (für verschiedene Output-Formate)
# =============================================================================

def format_feedback_markdown(result: FeedbackResult) -> str:
    """
    Formatiert Feedback als Markdown für Streamlit.
    """
    lines = [
        f"## Feedback",
        f"",
        f"**CEFR-Niveau:** {result.cefr_label} (Score: {result.cefr_score:.1f})" if result.cefr_score else "",
        f"",
        result.narrative,
    ]
    
    # Hotspots hinzufügen wenn vorhanden
    if result.hotspots:
        lines.extend([
            "",
            "---",
            "### 🔍 Interessante Stellen",
            ""
        ])
        for i, hotspot in enumerate(result.hotspots[:3], 1):
            reasons = ", ".join(hotspot.get("reasons", []))
            text = hotspot.get("sentence_text", "")[:100]
            lines.append(f"{i}. *\"{text}...\"* – {reasons}")
    
    return "\n".join(lines)


def format_feedback_json(result: FeedbackResult) -> dict:
    """
    Formatiert Feedback als JSON-kompatibles Dict.
    Für API-Responses oder Export.
    """
    return {
        "feedback": {
            "narrative": result.narrative,
            "cefr": {
                "score": result.cefr_score,
                "label": result.cefr_label,
            },
        },
        "analysis": {
            "metrics": result.metrics,
            "hotspots": result.hotspots,
            "disce_metrics": result.disce_metrics,
        },
        "meta": {
            "model": result.model_used,
            "is_mock": result.is_mock,
            "generated_at": result.generated_at,
            "processing_time_seconds": result.processing_time_seconds,
        }
    }


def format_feedback_plain(result: FeedbackResult) -> str:
    """
    Formatiert Feedback als Plain Text (für Export/Email).
    Entfernt Markdown-Formatierung.
    """
    import re
    
    text = result.narrative
    
    # Markdown entfernen
    text = re.sub(r'\*\*(.+?)\*\*', r'\1', text)  # Bold
    text = re.sub(r'\*(.+?)\*', r'\1', text)      # Italic
    text = re.sub(r'###?\s*', '', text)           # Headers
    text = re.sub(r'[✓→💡🔍]', '-', text)         # Emojis zu Dashes
    
    header = f"CEFR-Niveau: {result.cefr_label}\n\n" if result.cefr_label else ""
    
    return header + text
