# grosser_baer/task_templates.py
"""
Berufliche Speaking-Szenarien für Großer Bär.
Jedes Template definiert Kontext, Aufgabe, Zeitrahmen und Bewertungsfokus.
"""

TASK_TEMPLATES = {
    "cv_self_presentation": {
        "id": "cv_self_presentation",
        "title": "Lebenslauf vorstellen im Bewerbungsgespräch",
        "context": "Business",
        "cefr_target": "B2-C1",
        "icon": "💼",
        "situation": (
            "Sie sind in einem Bewerbungsgespräch. "
            "Die Personalerin sagt: „Erzählen Sie doch bitte kurz etwas über sich "
            "und Ihren bisherigen Werdegang.“"
        ),
        "task": (
            "Stellen Sie sich und Ihren beruflichen Werdegang in ca. 60–90 Sekunden vor. "
            "Wählen Sie die wichtigsten Stationen aus und führen Sie zu der Rolle hin, "
            "für die Sie sich bewerben."
        ),
        "time_seconds": 90,
        "evaluation_focus": [
            "Aufgabenerfüllung (Werdegang + aktuelles Profil klar?)",
            "Struktur & roter Faden",
            "Ton & Wirkung im Bewerbungskontext",
            "Klarheit der Sprache (Zeitformen, Präzision)",
        ],
        "register": "formell-professionell",
        "example_phrases": [
            "Ich bin derzeit …",
            "Mein fachlicher Schwerpunkt liegt auf …",
            "Für diese Position bringe ich besonders … mit.",
        ],
        "meta_prompts": {
            "plan": (
                "Überlegen Sie vor dem Sprechen: "
                "1) Kurzprofil, 2) 2–3 relevante Stationen, "
                "3) aktueller Stand, 4) warum diese Rolle."
            ),
            "monitor": "Achten Sie auf klare Übergänge zwischen den Stationen.",
            "reflect": "Ist klar geworden, wer Sie sind und warum Sie zu dieser Stelle passen?",
        },
    },

    "elevator_self_pitch": {
        "id": "elevator_self_pitch",
        "title": "Elevator Pitch: Ich als Profi",
        "context": "Business",
        "cefr_target": "B2-C1",
        "icon": "🚀",
        "situation": (
            "Sie treffen auf einer Veranstaltung eine Person, die für Ihre Karriere wichtig "
            "sein könnte. Sie haben ca. 45–60 Sekunden, um einen starken ersten Eindruck "
            "zu machen."
        ),
        "task": (
            "Stellen Sie sich in 45–60 Sekunden so vor, dass klar wird, "
            "wer Sie beruflich sind, wofür Sie stehen und was andere mit Ihnen "
            "in Verbindung bringen sollen."
        ),
        "time_seconds": 60,
        "evaluation_focus": [
            "Aufgabenerfüllung (Wer sind Sie, wofür stehen Sie?)",
            "Struktur (starker Einstieg, klarer Abschluss)",
            "Ton & Wirkung (Energie, Klarheit, Merkbarkeit)",
            "Konkret statt vage (klare Beispiele statt Buzzwords)",
        ],
        "register": "professionell-kollegial",
        "example_phrases": [
            "Ich arbeite an der Schnittstelle von …",
            "Besonders spannend finde ich …",
            "Wenn Sie mehr über … hören wollen, erzähle ich Ihnen gern mehr.",
        ],
        "meta_prompts": {
            "plan": (
                "Überlegen Sie: 1) Wer sind Sie beruflich? 2) Wofür stehen Sie? "
                "3) Welches Beispiel passt dazu? 4) Wie schließen Sie ab?"
            ),
            "monitor": "Achten Sie darauf, nicht in einen kompletten Lebenslauf abzurutschen.",
            "reflect": "Bleibt ein klarer Eindruck von Ihnen hängen?",
        },
    },
}


def get_task(task_id: str) -> dict | None:
    """Einzelnes Task-Template abrufen."""
    return TASK_TEMPLATES.get(task_id)


def get_all_tasks() -> dict:
    """Alle Task-Templates abrufen."""
    return TASK_TEMPLATES


def get_tasks_by_context(context: str) -> list[dict]:
    """Tasks nach Kontext filtern (Business, Academic, Social)."""
    return [t for t in TASK_TEMPLATES.values() if context.lower() in t["context"].lower()]


def get_task_choices() -> list[tuple[str, str]]:
    """Für Streamlit-Dropdown: Liste von (display_name, id)."""
    return [(f"{t['icon']} {t['title']}", t["id"]) for t in TASK_TEMPLATES.values()]
