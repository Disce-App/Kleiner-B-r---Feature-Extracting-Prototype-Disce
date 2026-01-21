# grosser_baer/task_templates.py
"""
Berufliche Speaking-Szenarien für Großer Bär.
Jedes Template definiert Kontext, Aufgabe, Zeitrahmen und Bewertungsfokus.
"""

TASK_TEMPLATES = {
    "meeting_update": {
        "id": "meeting_update",
        "title": "Projekt-Update im Meeting",
        "context": "Business",
        "cefr_target": "B2-C1",
        "icon": "📊",
        "situation": (
            "Sie sind in einem Team-Meeting mit 5 Kolleg:innen. "
            "Ihre Projektleiterin bittet Sie, ein kurzes Update zum aktuellen "
            "Stand Ihres Teilprojekts zu geben."
        ),
        "task": (
            "Geben Sie ein strukturiertes Update: "
            "(1) Was wurde erreicht? "
            "(2) Wo stehen Sie gerade? "
            "(3) Was sind die nächsten Schritte?"
        ),
        "time_seconds": 90,
        "evaluation_focus": ["struktur", "fachsprache", "präzision"],
        "register": "formell-kollegial",
        "example_phrases": [
            "Ich möchte kurz den aktuellen Stand zusammenfassen...",
            "Was die nächsten Schritte betrifft...",
            "Hier sehe ich noch Klärungsbedarf bei..."
        ],
        "meta_prompts": {
            "plan": "Was sind die 3 wichtigsten Punkte, die Sie kommunizieren wollen?",
            "monitor": "Achten Sie auf klare Übergänge zwischen den drei Teilen.",
            "reflect": "Haben Sie alle drei Aspekte abgedeckt? Was würden Sie präziser formulieren?"
        }
    },
    
    "phone_complaint": {
        "id": "phone_complaint",
        "title": "Telefonische Reklamation",
        "context": "Business",
        "cefr_target": "B2",
        "icon": "📞",
        "situation": (
            "Sie haben ein Produkt online bestellt, das beschädigt angekommen ist. "
            "Sie rufen beim Kundenservice an, um das Problem zu klären und eine Lösung zu finden."
        ),
        "task": (
            "Schildern Sie das Problem höflich aber bestimmt. "
            "Erklären Sie, was passiert ist, und formulieren Sie klar, "
            "welche Lösung Sie sich wünschen."
        ),
        "time_seconds": 60,
        "evaluation_focus": ["höflichkeit", "bestimmtheit", "klarheit"],
        "register": "formell-höflich",
        "example_phrases": [
            "Ich rufe an, weil ich leider ein Problem mit meiner Bestellung habe.",
            "Ich würde mir wünschen, dass...",
            "Wäre es möglich, dass Sie...?"
        ],
        "meta_prompts": {
            "plan": "Wie können Sie bestimmt UND höflich zugleich sein?",
            "monitor": "Achten Sie auf Konjunktiv II für höfliche Bitten.",
            "reflect": "War Ihr Ton angemessen? Haben Sie Ihre Erwartung klar formuliert?"
        }
    },
    
    "job_interview_strength": {
        "id": "job_interview_strength",
        "title": "Vorstellungsgespräch: Stärken",
        "context": "Business",
        "cefr_target": "B2-C1",
        "icon": "💼",
        "situation": (
            "Sie sind in einem Vorstellungsgespräch für eine Position, "
            "die Sie sehr interessiert. Die Personalerin fragt: "
            "'Was würden Sie als Ihre größte Stärke bezeichnen?'"
        ),
        "task": (
            "Beantworten Sie die Frage überzeugend: "
            "Nennen Sie eine Stärke, belegen Sie sie mit einem konkreten Beispiel, "
            "und erklären Sie, wie diese Stärke für die Stelle relevant ist."
        ),
        "time_seconds": 90,
        "evaluation_focus": ["überzeugungskraft", "konkretheit", "selbstpräsentation"],
        "register": "formell-professionell",
        "example_phrases": [
            "Eine meiner größten Stärken ist...",
            "Das hat sich zum Beispiel gezeigt, als ich...",
            "Ich denke, das ist besonders relevant für diese Position, weil..."
        ],
        "meta_prompts": {
            "plan": "Welches konkrete Beispiel werden Sie nennen?",
            "monitor": "Verbinden Sie die Stärke mit der ausgeschriebenen Stelle.",
            "reflect": "War Ihr Beispiel spezifisch genug? Klang es authentisch?"
        }
    },
    
    "explain_technical": {
        "id": "explain_technical",
        "title": "Fachliches Konzept erklären",
        "context": "Academic/Business",
        "cefr_target": "C1",
        "icon": "🎓",
        "situation": (
            "Ein:e Kolleg:in aus einer anderen Abteilung fragt Sie, "
            "ob Sie ein Konzept aus Ihrem Fachgebiet kurz erklären können. "
            "Die Person hat keinen fachlichen Hintergrund."
        ),
        "task": (
            "Erklären Sie ein Konzept aus Ihrem Berufs- oder Studienfeld "
            "so, dass jemand ohne Vorwissen es verstehen kann. "
            "Nutzen Sie ein Beispiel oder eine Analogie."
        ),
        "time_seconds": 120,
        "evaluation_focus": ["verständlichkeit", "struktur", "adressatengerecht"],
        "register": "neutral-erklärend",
        "example_phrases": [
            "Im Grunde kann man sich das so vorstellen wie...",
            "Das bedeutet konkret, dass...",
            "Ein einfaches Beispiel wäre..."
        ],
        "meta_prompts": {
            "plan": "Welche Analogie oder welches Beispiel hilft beim Verstehen?",
            "monitor": "Vermeiden Sie Fachbegriffe oder erklären Sie sie direkt.",
            "reflect": "Hätte jemand ohne Vorwissen das verstanden?"
        }
    },
    
    "small_talk_network": {
        "id": "small_talk_network",
        "title": "Smalltalk beim Networking",
        "context": "Social/Business",
        "cefr_target": "B2",
        "icon": "🤝",
        "situation": (
            "Sie sind auf einer Branchenveranstaltung und kommen mit einer "
            "Person ins Gespräch, die Sie interessant finden. "
            "Sie möchten einen guten ersten Eindruck machen."
        ),
        "task": (
            "Führen Sie einen kurzen Smalltalk: "
            "Stellen Sie sich vor, zeigen Sie Interesse an der anderen Person, "
            "und finden Sie einen natürlichen Gesprächsabschluss."
        ),
        "time_seconds": 60,
        "evaluation_focus": ["natürlichkeit", "gesprächsführung", "höflichkeit"],
        "register": "informell-höflich",
        "example_phrases": [
            "Wie hat Ihnen der Vortrag gefallen?",
            "Das klingt wirklich interessant! Wie sind Sie dazu gekommen?",
            "Es war sehr nett, Sie kennenzulernen. Vielleicht sieht man sich ja später noch."
        ],
        "meta_prompts": {
            "plan": "Wie können Sie echtes Interesse zeigen, ohne aufdringlich zu wirken?",
            "monitor": "Stellen Sie offene Fragen, nicht nur Ja/Nein-Fragen.",
            "reflect": "Wirkte das Gespräch natürlich? War der Abschluss elegant?"
        }
    }
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
    return [(f"{t['icon']} {t['title']}", t['id']) for t in TASK_TEMPLATES.values()]
