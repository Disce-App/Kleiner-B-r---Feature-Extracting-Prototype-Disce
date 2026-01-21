# grosser_baer/prompts.py
"""
Prompt-Architektur für Großer Bär.
System-Prompts für Claude + Metakognitions-Framework.
"""

# =============================================================================
# SYSTEM PROMPT - Kern-Identität des Feedback-Coaches
# =============================================================================

SYSTEM_PROMPT_COACH = """Du bist ein erfahrener DaF-Coach (Deutsch als Fremdsprache) für fortgeschrittene Lernende (B2-C2).

## Deine Persönlichkeit
- Warmherzig, aber präzise
- Ermutigend, ohne zu beschönigen
- Fokussiert auf das, was den größten Unterschied macht

## Deine Aufgabe
Du gibst Feedback auf gesprochene Texte. Du bekommst:
1. Das Transkript der Aufnahme
2. Metriken aus der automatischen Analyse
3. Den Kontext (welche Aufgabe, welches Szenario)

## Dein Feedback-Format
Strukturiere dein Feedback IMMER so:

### ✓ Das ist gelungen
[Eine konkrete Stärke mit Beispiel aus dem Text]

### → Fokus für nächstes Mal
[1-2 priorisierte Verbesserungspunkte, konkret und umsetzbar]

### 💡 Mini-Übung
[Eine kleine, sofort umsetzbare Übung oder ein Revisionsvorschlag]

## Wichtige Prinzipien
- Zitiere immer konkrete Stellen aus dem Text
- Priorisiere: Was hat den größten Impact für dieses Szenario?
- Vermeide Überforderung: Maximal 2 Fokuspunkte
- Beachte das Register: Formell/informell je nach Situation
- Verbinde Feedback mit dem Lernziel des Tasks

## Ton
Schreibe auf Deutsch, in Sie-Form, professionell aber nicht steif.
"""


# =============================================================================
# FEEDBACK PROMPT TEMPLATE - Wird mit Daten gefüllt
# =============================================================================

FEEDBACK_PROMPT_TEMPLATE = """## Kontext
**Aufgabe:** {task_title}
**Szenario:** {situation}
**Erwartetes Register:** {register}
**Bewertungsfokus:** {evaluation_focus}
**Zeitvorgabe:** {time_seconds} Sekunden

## Transkript der Aufnahme
{transcript}

## Analyse-Metriken
- CEFR-Niveau: {cefr_label} (Score: {cefr_score:.1f})
- Lexikalische Diversität: {lexical_diversity:.0%}
- Grammatik-Genauigkeit: {grammar_accuracy:.0%}
- Register-Match: {register_match:.0%}
- Satzlänge (Durchschnitt): {avg_sentence_length:.1f} Wörter
- Kohäsion: {cohesion:.0%}

## Prosodie (falls verfügbar)
- Sprechgeschwindigkeit: {speech_rate} WPM
- Pausen-Verhältnis: {pause_ratio:.0%}
- Füllwort-Rate: {filler_rate:.0%}

## Aufgabe
Gib strukturiertes Feedback gemäß deinem Format.
Beachte besonders: {evaluation_focus}
"""


# =============================================================================
# METAKOGNITIONS-PROMPTS - Plan / Monitor / Reflect
# =============================================================================

METACOGNITION_PROMPTS = {
    "plan": {
        "generic": "Bevor Sie beginnen: Was sind die 2-3 wichtigsten Punkte, die Sie kommunizieren wollen?",
        "structure": "Wie werden Sie Ihre Antwort strukturieren?",
        "register": "Welchen Ton wollen Sie treffen – eher formell oder kollegial?",
        "goal": "Was wäre für Sie ein erfolgreiches Ergebnis dieser Übung?"
    },
    
    "monitor": {
        "generic": "Achten Sie auf klare Struktur und passenden Ton.",
        "time": "Sie haben noch {remaining_seconds} Sekunden.",
        "halfway": "Halbzeit – haben Sie Ihre Hauptpunkte genannt?",
        "structure": "Denken Sie an Einleitung, Hauptteil, Schluss.",
        "register": "Achten Sie auf die passende Anrede und Höflichkeitsform."
    },
    
    "reflect": {
        "generic": "Was hat gut funktioniert? Was würden Sie anders machen?",
        "content": "Haben Sie alle wichtigen Punkte abgedeckt?",
        "structure": "War Ihre Struktur klar erkennbar?",
        "register": "Passte Ihr Ton zur Situation?",
        "improvement": "Wenn Sie es nochmal machen könnten – was würden Sie ändern?",
        "learning": "Was nehmen Sie aus dieser Übung mit?"
    }
}


# =============================================================================
# PHASE-SPEZIFISCHE UI-TEXTE
# =============================================================================

PHASE_UI_TEXTS = {
    "plan": {
        "title": "📋 Phase 1: Vorbereitung",
        "instruction": "Nehmen Sie sich einen Moment, um Ihre Antwort zu planen.",
        "cta": "Ich bin bereit – Aufnahme starten"
    },
    
    "perform": {
        "title": "🎙️ Phase 2: Aufnahme",
        "instruction": "Sprechen Sie jetzt. Die Aufnahme läuft.",
        "cta": "Aufnahme beenden"
    },
    
    "feedback": {
        "title": "📊 Phase 3: Feedback",
        "instruction": "Hier ist Ihr Feedback.",
        "cta": "Weiter zur Reflexion"
    },
    
    "reflect": {
        "title": "💭 Phase 4: Reflexion",
        "instruction": "Reflektieren Sie kurz über Ihre Leistung.",
        "cta_retry": "Nochmal versuchen",
        "cta_next": "Neue Aufgabe wählen",
        "cta_finish": "Session beenden"
    }
}


# =============================================================================
# MOCK FEEDBACK - Für Testing ohne Claude API
# =============================================================================

MOCK_FEEDBACK = """### ✓ Das ist gelungen
Sie haben eine klare Struktur verwendet und Ihre Hauptpunkte verständlich präsentiert. Besonders gut war der Einstieg mit der direkten Kontextualisierung.

### → Fokus für nächstes Mal
1. **Präzisere Fachbegriffe:** Statt "das Ding mit den Daten" könnten Sie "die Datenanalyse" oder "der Datensatz" verwenden.
2. **Übergänge:** Zwischen Ihren Punkten könnten Signalwörter wie "Darüber hinaus" oder "Was den nächsten Punkt betrifft" helfen.

### 💡 Mini-Übung
Nehmen Sie Ihren ersten Satz und formulieren Sie ihn in drei Varianten: einmal neutral, einmal formeller, einmal direkter. Das schärft Ihr Registerbewusstsein.

*[Dies ist Mock-Feedback für Testing. Mit Claude API wird das Feedback personalisiert.]*
"""


# =============================================================================
# HELPER FUNCTIONS
# =============================================================================

def get_meta_prompt(phase: str, prompt_type: str = "generic", **kwargs) -> str:
    """
    Holt den passenden Metakognitions-Prompt.
    
    Args:
        phase: "plan", "monitor", oder "reflect"
        prompt_type: Spezifischer Typ oder "generic"
        **kwargs: Für Formatierung (z.B. remaining_seconds)
    
    Returns:
        Formatierter Prompt-String
    """
    prompts = METACOGNITION_PROMPTS.get(phase, {})
    prompt = prompts.get(prompt_type, prompts.get("generic", ""))
    
    if kwargs:
        try:
            prompt = prompt.format(**kwargs)
        except KeyError:
            pass
    
    return prompt


def build_feedback_prompt(
    task: dict,
    transcript: str,
    metrics: dict,
    prosody: dict | None = None
) -> str:
    """
    Baut den vollständigen Feedback-Prompt aus Task, Transkript und Metriken.
    
    Args:
        task: Task-Template aus task_templates.py
        transcript: STT-Transkript
        metrics: Metriken aus Kleiner Bär
        prosody: Optional, Prosodie-Daten aus Azure
    
    Returns:
        Formatierter Prompt für Claude
    """
    # Defaults für fehlende Prosodie-Daten
    prosody = prosody or {}
    
    return FEEDBACK_PROMPT_TEMPLATE.format(
        task_title=task.get("title", "Unbekannte Aufgabe"),
        situation=task.get("situation", ""),
        register=task.get("register", "neutral"),
        evaluation_focus=", ".join(task.get("evaluation_focus", [])),
        time_seconds=task.get("time_seconds", 60),
        transcript=transcript,
        cefr_label=metrics.get("cefr", {}).get("label", "?"),
        cefr_score=metrics.get("cefr", {}).get("score", 0),
        lexical_diversity=metrics.get("metrics_summary", {}).get("dims", {}).get("lexical_diversity", 0),
        grammar_accuracy=metrics.get("dims", {}).get("grammar_accuracy", 0),
        register_match=metrics.get("disce_metrics", {}).get("level_match", 0),
        avg_sentence_length=metrics.get("text_stats", {}).get("avg_sentence_length", 0),
        cohesion=metrics.get("dims", {}).get("cohesion", 0),
        speech_rate=prosody.get("speech_rate", "N/A"),
        pause_ratio=prosody.get("pause_ratio", 0),
        filler_rate=prosody.get("filler_rate", 0)
    )


def get_phase_ui(phase: str) -> dict:
    """Holt UI-Texte für eine Phase."""
    return PHASE_UI_TEXTS.get(phase, {})
