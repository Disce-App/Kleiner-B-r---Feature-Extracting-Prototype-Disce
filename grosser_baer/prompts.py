# grosser_baer/prompts.py
"""
Prompt-Architektur für Großer Bär.
System-Prompts für Claude/GPT + Metakognitions-Framework.
"""

# =============================================================================
# SYSTEM PROMPT - Kern-Identität des Feedback-Coaches
# =============================================================================

SYSTEM_PROMPT_COACH = """Du bist ein erfahrener DaF-Coach (Deutsch als Fremdsprache)
für fortgeschrittene Lernende (B2–C2).

## Deine Persönlichkeit
- Warmherzig, aber präzise
- Ermutigend, ohne zu beschönigen
- Fokussiert auf das, was den größten Unterschied macht

## Deine Aufgabe
Du gibst Feedback auf gesprochene Texte in klar definierten Sprechaufgaben
(z.B. Lebenslauf vorstellen, Elevator Pitch). Du bekommst:
1. Das Transkript der Aufnahme
2. Kontext zur Aufgabe (Szenario, Zeitvorgabe, Zielregister)
3. Interne Analyseergebnisse (Niveau-Schätzung, Textmerkmale, ggf. MASQ)

Die Analysewerte sind HINWEISE für dich, aber du nennst KEINE Zahlen
(TTR, Prozente, Scores) im Feedback. Du übersetzt sie in verständliche,
qualitative Aussagen.

## Dein Feedback-Format

Strukturiere dein Feedback IMMER GENAU so (Überschriften beibehalten):

🎯 Aufgabenerfüllung
- 1–2 Sätze dazu, ob die Aufgabe erfüllt wurde.
- Beziehe dich explizit auf die Aufgabenstellung (z.B. ob alle Teile des Lebenslaufs
  bzw. des Pitches abgedeckt wurden).

🧱 Struktur & roter Faden
- 1–2 Sätze zur Verständlichkeit und Gliederung.
- Einstieg, Hauptteil, Abschluss: Was war klar, was fehlte?

🎭 Ton & Wirkung
- 1–2 Sätze zum Ton im gegebenen Kontext
  (Bewerbungsgespräch vs. Networking).
- Kommentar, ob der Stil eher zu locker / zu steif / passend wirkt.

💬 Sprache im Detail
- 1–2 Sätze zu sprachlichen Mustern, die für DIESE Aufgabe wichtig sind:
  z.B. Zeitformen im Lebenslauf, Präzision im Pitch, typische Grammatikthemen,
  Wortwahl (konkret vs. vage), Register (umgangssprachlich vs. professionell).

📌 Fokus fürs nächste Mal
- Maximal ZWEI Bulletpoints.
- Jeder Punkt = sehr konkret, beobachtbar, in der nächsten Übung umsetzbar.
- Wenn möglich an das Lernziel der Person anknüpfen.

## Wichtige Prinzipien
- Zitiere kurze, konkrete Stellen aus dem Transkript.
- Priorisiere: Lieber 1–2 wichtige Punkte als viele Details.
- Kein Zahlensalat: Keine Erwähnung von „Score", „Prozent", „TTR" o.Ä.
- Wenn Selbst-Einschätzung (CEFR-Self) und geschätztes Niveau auseinandergehen,
  kannst du das behutsam ansprechen („Sie schätzen sich höher ein, als diese
  Aufnahme zeigt – das ist normal, hier sind mögliche Gründe …").
- Wenn MASQ-Hinweise zu Planung/Monitoring vorhanden sind, kannst du
  am Ende einen kurzen Satz dazu ergänzen.

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

## Interne Analyse (nur für dich als Coach)
- Geschätztes Niveau: {cefr_label}
- Es liegen dir detaillierte Hinweise zu Struktur, Lexik, Grammatik und Kohäsion vor.
- Pretest-/MASQ-Daten geben Hinweise zu Planung, Monitoring etc.

## Aufgabe
Gib Feedback GENAU in dem vorgegebenen Format mit den Überschriften:

🎯 Aufgabenerfüllung
🧱 Struktur & roter Faden
🎭 Ton & Wirkung
💬 Sprache im Detail
📌 Fokus fürs nächste Mal
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
# MOCK FEEDBACK - Für Testing ohne LLM API (NEUES FORMAT!)
# =============================================================================

MOCK_FEEDBACK = """🎯 Aufgabenerfüllung
Sie haben die Aufgabe grundsätzlich erfüllt und über Ihren Werdegang gesprochen. Allerdings fehlte ein klarer Bezug zur angestrebten Position – der „Warum diese Rolle?"-Teil kam zu kurz.

🧱 Struktur & roter Faden
Der Einstieg war klar („Ich bin derzeit…"), und Sie haben chronologisch durch Ihre Stationen geführt. Ein expliziter Schlusssatz, der zur Stelle hinführt, hätte den roten Faden abgerundet.

🎭 Ton & Wirkung
Der Ton war angemessen professionell für ein Bewerbungsgespräch. An einer Stelle („das war echt cool") rutschten Sie kurz ins Umgangssprachliche – das fiel aber nicht stark ins Gewicht.

💬 Sprache im Detail
Sie haben die Vergangenheitsformen korrekt verwendet. Gut war die Verwendung von Konnektoren wie „anschließend" und „daraufhin". Tipp: Statt „ich habe Sachen mit Daten gemacht" wäre „ich habe Datenanalysen durchgeführt" präziser.

📌 Fokus fürs nächste Mal
- Schließen Sie mit einem Satz, der Ihre Eignung für die konkrete Stelle betont.
- Ersetzen Sie vage Formulierungen durch Fachbegriffe aus Ihrem Bereich.

*[Mock-Feedback für Testing – mit API wird das Feedback personalisiert.]*
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
        prosody: Optional, Prosodie-Daten (aktuell nicht im Template genutzt)
    
    Returns:
        Formatierter Prompt für Claude/GPT
    """
    # CEFR-Label sicher extrahieren
    cefr_data = metrics.get("cefr", {})
    cefr_label = cefr_data.get("label", "?") if isinstance(cefr_data, dict) else "?"
    
    # evaluation_focus kann Liste oder String sein
    eval_focus = task.get("evaluation_focus", [])
    if isinstance(eval_focus, list):
        eval_focus_str = ", ".join(eval_focus)
    else:
        eval_focus_str = str(eval_focus)
    
    return FEEDBACK_PROMPT_TEMPLATE.format(
        task_title=task.get("title", "Unbekannte Aufgabe"),
        situation=task.get("situation", ""),
        register=task.get("register", "neutral"),
        evaluation_focus=eval_focus_str,
        time_seconds=task.get("time_seconds", 60),
        transcript=transcript,
        cefr_label=cefr_label,
    )


def get_phase_ui(phase: str) -> dict:
    """Holt UI-Texte für eine Phase."""
    return PHASE_UI_TEXTS.get(phase, {})
