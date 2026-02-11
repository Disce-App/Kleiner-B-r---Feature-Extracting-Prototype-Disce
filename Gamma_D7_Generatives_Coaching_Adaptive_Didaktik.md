# Gamma · Domäne 7 – Generatives Coaching & Adaptive Didaktik

> **Domänenfrage:** *Diagnostisches Profil (D6) → Was sagt man dem Lerner? Was übt man als Nächstes?*
> **Gamma-Frage:** *Wie verwandeln wir einen Feature-Vektor in didaktisch wirksames, LLM-gestütztes Coaching – sicher, erklärbar und adaptiv?*

---

## 1  Überblick & Abgrenzung

Die Domänen 1–6 **messen**. Domäne 7 **handelt**. Hier wird aus Diagnose → Therapie, aus Profil → Coaching, aus Score → nächster Lernschritt.

| Phase | D1–D6 | D7 |
|---|---|---|
| Funktion | Messen · Analysieren · Bewerten | Erklären · Üben · Motivieren |
| Output | Feature-Vektor + Diagnostisches Profil | Feedback-Text · Übungen · Lernpfad |
| Analogie | Blutbild + Diagnose | Therapieplan + Arztgespräch |
| Kern-Technologie | Signal Processing · NLP · ML | LLM · Prompt Engineering · Spaced Repetition |

### Warum D7 kein Anhängsel ist

Die meisten CAPT-Systeme behandeln Feedback als Nachgedanken: „Du hast 3/5 Punkte. Weiter.“ Das ist, als würde ein Arzt sagen: „Ihr Blutbild ist schlecht. Tschüss.“

**Didaktisch wirksames Feedback** muss drei Fragen beantworten:
1. **Was genau ist das Problem?** (Diagnose → D6 liefert)
2. **Warum ist das ein Problem?** (Erklärung → D7 generiert)
3. **Was kann ich tun, um es zu verbessern?** (Übung → D7 generiert)

Ohne D7 ist Disce ein diagnostisches Instrument. *Mit* D7 wird es ein Coach.

---

## 2  Referenzsysteme: Wie coachen die Großen?

### 2.1  Duolingo Max (GPT-4)

| Feature | Detail |
|---------|--------|
| **Explain My Answer** | LLM erklärt, warum eine Antwort richtig/falsch war – kontextbezogen, in einfacher Sprache |
| **Roleplay** | Szenario-basierte Konversation (z. B. „Bestelle in einem Café“), LLM als Gesprächspartner |
| **Architektur** | Mensch schreibt Szenario-Prompts + initiale Nachricht; GPT-4 generiert Antworten; Human Review der AI-Inhalte |
| **Stärke** | Natürliche, motivierende Interaktion; Skalierung ohne menschliche Tutoren |
| **Schwäche** | Keine Aussprache-Analyse im Roleplay; Feedback bleibt textbasiert; proprietär (OpenAI-Abhängigkeit) |

### 2.2  ELSA Speak

| Feature | Detail |
|---------|--------|
| **Real-Time Corrections** | Sofortfeedback zu Fluency, Intonation, Aussprache, Grammatik, Wortschatz |
| **AI Coach** | Personalisierte Lernpfade basierend auf CEFR-Level-Prognose (A1–C1) |
| **Stärke** | Aussprache-spezifisches Feedback mit Audio-Vergleich |
| **Schwäche** | Nur Englisch; Feedback-Tiefe bei Grammatik/Wortschatz begrenzt |

### 2.3  Praktika (GPT 4.1 / 5.2)

| Feature | Detail |
|---------|--------|
| **Lesson Agent** | Primärer Konversationsagent (GPT 5.2); adaptiert Lektionen basierend auf Lerner-Verhalten und Fortschritt |
| **Architektur** | Multi-Agent: Lesson Agent + Curriculum Agent + Feedback Agent |
| **Stärke** | Echte Konversationsübung mit adaptivem Schwierigkeitsgrad |
| **Schwäche** | Vollständig proprietär; hohe API-Kosten; keine linguistische Tiefendiagnostik |

### Synthese: Was fehlt am Markt?

| Fähigkeit | Duolingo Max | ELSA | Praktika | **Disce (Ziel)** |
|-----------|:---:|:---:|:---:|:---:|
| Aussprache-Feedback (phonetisch) | ✗ | ✓ | ○ | ✓ |
| Grammatik-Erklärung (metalinguistisch) | ✓ | ○ | ✓ | ✓ |
| Prosodie-Feedback | ✗ | ○ | ✗ | ✓ |
| Diagnostisches Profil als Basis | ✗ | ○ | ✗ | ✓ |
| Adaptive Übungsgenerierung | ○ | ✓ | ✓ | ✓ |
| Deutsch als Zielsprache | ✓ | ✗ | ✗ | ✓ |
| Erklärbar (AI Act) | ✗ | ✗ | ✗ | ✓ |

**Disce-Chance:** Kein existierendes System verbindet *tiefe linguistische Diagnostik* (D1–D6) mit *generativem Coaching* (D7) für Deutsch. Das ist die Lücke.

---

## 3  Theoretische Fundierung: Was weiß die SLA-Forschung?

### 3.1  Corrective Feedback (CF) – Die Taxonomie

Die SLA-Forschung unterscheidet sechs Typen korrektiven Feedbacks:

| CF-Typ | Beschreibung | Beispiel (Deutsch) | Effektivität |
|--------|-------------|-------------------|-------------|
| **Recast** | Korrekte Reformulierung ohne expliziten Hinweis | L: „Ich habe gegeht.“ → T: „Ah, du bist gegangen.“ | Mittel (oft überhört) |
| **Explicit Correction** | Direkte Korrektur mit Markierung | „Nicht ‘gegeht’ – das Partizip ist ‘gegangen’.“ | Hoch für einfache Fehler |
| **Metalinguistic Feedback** | Grammatische Erklärung | „‘Gehen’ ist ein starkes Verb. Starke Verben ändern den Stammvokal im Partizip.“ | Hoch für regelhafte Fehler |
| **Elicitation** | Aufforderung zur Selbstkorrektur | „Wie heißt das Partizip von ‘gehen’?“ | Hoch (aktive Verarbeitung) |
| **Repetition** | Wiederholung des Fehlers mit Betonung | „Du hast ge-GEHT?“ | Kontextabhängig |
| **Clarification Request** | Verständnisfrage | „Wie meinst du das? Kannst du das nochmal sagen?“ | Niedrig für Formfehler |

**Für Disce relevant:** Die Forschung zeigt, dass **Prompts** (Elicitation, Metalinguistic Feedback) langfristig wirksamer sind als **Reformulations** (Recasts), weil sie den Lerner zur aktiven Verarbeitung zwingen. Ein LLM kann alle Typen generieren – die Frage ist, *wann welcher Typ angemessen ist*.

### 3.2  Scaffolding & Zone of Proximal Development (ZPD)

| Prinzip | Implikation für Disce |
|---------|----------------------|
| **ZPD (Vygotsky)** | Feedback und Übungen müssen im „Lernbaren“ liegen – nicht zu leicht (Langeweile), nicht zu schwer (Frustration) |
| **i+1 (Krashen)** | Input sollte eine Stufe über dem aktuellen Niveau liegen |
| **Focus on Form (Long)** | Aufmerksamkeit auf sprachliche Form *im kommunikativen Kontext* lenken – nicht isolierte Grammatikübungen |
| **Noticing Hypothesis (Schmidt)** | Lerner müssen Fehler *bewusst wahrnehmen*, bevor sie sie korrigieren können |

**Operative Konsequenz:** Disce muss das diagnostische Profil (D6) nutzen, um **den richtigen Schwierigkeitsgrad** und **den richtigen Feedback-Typ** zu wählen.

### 3.3  Feedback-Timing

| Timing | Beschreibung | Einsatz |
|--------|-------------|---------|
| **Immediate** | Sofort nach der Äußerung | Aussprache-Drills, isolierte Übungen |
| **Delayed** | Nach Abschluss einer Aufgabe | Kommunikative Übungen, Roleplay |
| **Aggregated** | Nach einer Lerneinheit/Session | Diagnostisches Profil, Fortschrittsreport |

**Empfehlung:** Aussprache-Feedback → immediate. Grammatik/Wortschatz-Feedback in Konversation → delayed. Profil-Update → aggregated.

---

## 4  Disce Coaching-Architektur: Die Feedback-Pipeline

```
+---------------------------------------------------------------------+
|              D7 - Generatives Coaching - Pipeline                    |
|                                                                      |
|  INPUT: Diagnostisches Profil (D6) + Lernermodell + Aufgabentyp     |
|         |                                                            |
|         v                                                            |
|  +-----------------------------------------------------------+      |
|  |  MODUL A - Feedback-Routing                                |      |
|  |  Welche Dimension? Welcher Feedback-Typ? Welches Timing?   |      |
|  |  Regelbasierter Router auf Basis des Profils               |      |
|  +--------------------+--------------------------------------+      |
|                       |                                              |
|         +-------------+-------------+                                |
|         v             v             v                                |
|  +-----------+  +-----------+  +-------------+                       |
|  | MODUL B   |  | MODUL C   |  | MODUL D     |                       |
|  | Feedback- |  | Uebungs-  |  | Konversation|                       |
|  | Generier. |  | Generator |  | & Roleplay  |                       |
|  | (LLM)    |  | (LLM+Tmpl)|  | (LLM)       |                       |
|  +-----+-----+  +-----+-----+  +------+------+                       |
|        |              |               |                               |
|        v              v               v                               |
|  +-----------------------------------------------------------+      |
|  |  MODUL E - Guardrails & Validierung                        |      |
|  |  Faktencheck - Grammatik-Regelcheck - Tonalitaet           |      |
|  +--------------------+--------------------------------------+      |
|                       v                                              |
|  +-----------------------------------------------------------+      |
|  |  MODUL F - Spaced Repetition & Lernpfad                    |      |
|  |  Error-Tracking - Wiederholungsplanung - Fortschritt       |      |
|  +-----------------------------------------------------------+      |
|                                                                      |
|  OUTPUT: Feedback-Text - Uebung - Lernpfad-Update                   |
+---------------------------------------------------------------------+
```

---

### 4.1  Modul A: Feedback-Routing

Der Router entscheidet auf Basis des diagnostischen Profils, **was** der Lerner als Nächstes braucht:

```python
def route_feedback(profile, task_type):
    # 1. Schwaechste Dimension identifizieren
    weakest = min(profile.dimensions, key=lambda d: d.score)

    # 2. Feedback-Typ waehlen (abhaengig von Dimension + Niveau)
    if weakest.dimension == "Aussprache":
        if weakest.score < 30:
            return FeedbackStrategy(
                type="explicit_correction",
                modality="audio_comparison",
                exercise="minimal_pair_drill",
                timing="immediate"
            )
        else:
            return FeedbackStrategy(
                type="metalinguistic",
                modality="text + audio",
                exercise="sentence_reading",
                timing="immediate"
            )

    elif weakest.dimension == "Grammatik":
        if task_type == "conversation":
            return FeedbackStrategy(
                type="recast",
                modality="text",
                exercise="targeted_cloze",
                timing="delayed"
            )
        else:
            return FeedbackStrategy(
                type="metalinguistic",
                modality="text",
                exercise="rule_explanation + transformation",
                timing="immediate"
            )

    elif weakest.dimension == "Wortschatz":
        return FeedbackStrategy(
            type="elicitation",
            modality="text",
            exercise="context_vocabulary",
            timing="delayed"
        )
```

**Prinzip:** Der Router ist **regelbasiert** (kein LLM), weil didaktische Entscheidungen reproduzierbar und auditierbar sein müssen. Das LLM kommt erst bei der *Generierung* des Feedbacks zum Einsatz.

### 4.2  Modul B: Feedback-Generierung (LLM-gestützt)

**Architektur: RAG + Structured Output**

```
+----------------+    +---------------------+    +----------------+
| Diagnostisches |---->| Prompt-Template     |---->| LLM            |
| Profil (D6)    |    | + Fehlerkontext     |    | (Structured    |
|                |    | + Grammatik-KB (RAG)|    |  Output/JSON)  |
+----------------+    +---------------------+    +--------+-------+
                                                          |
                                                          v
                                                  +----------------+
                                                  | Validierung    |
                                                  | (Modul E)      |
                                                  +----------------+
```

**Warum RAG?** Ein reines LLM halluziniert Grammatikregeln. „Der Dativ ist der dritte Fall“ ist harmlos; „nach ‘weil’ steht immer der Konjunktiv“ ist falsch und schädlich. Deshalb: LLM generiert **mit angereichertem Kontext** aus einer kuratierten Grammatik-Wissensbasis.

**Prompt-Template (Beispiel: Grammatik-Feedback)**

```
SYSTEM:
Du bist ein DaF-Sprachcoach. Dein Lerner ist auf Niveau {cefr_level}.
Erklaere Fehler klar, ermutigend und altersgerecht.
Verwende die folgende Grammatikregel als Basis:
---
{grammar_rule_from_kb}
---
Antworte im JSON-Format:
{
  "error_type": "...",
  "what_went_wrong": "...",
  "why_it_matters": "...",
  "correct_form": "...",
  "rule_summary": "...",
  "example_correct": "...",
  "encouragement": "..."
}

USER:
Der Lerner hat gesagt: "{learner_utterance}"
Erkannter Fehler: {error_from_d5}
Fehlertyp: {error_type}
Fehlerkontext: {error_context}
```

**Beispiel-Output:**

```json
{
  "error_type": "Kasusmarkierung (Akkusativ statt Dativ)",
  "what_went_wrong": "Du hast gesagt 'Ich helfe den Mann', aber nach 'helfen' braucht man den Dativ, nicht den Akkusativ.",
  "why_it_matters": "Im Deutschen bestimmt das Verb, welchen Fall das Objekt bekommt. Das ist anders als in vielen anderen Sprachen.",
  "correct_form": "Ich helfe dem Mann.",
  "rule_summary": "'Helfen' gehoert zu den Verben mit Dativ-Objekt. Andere Beispiele: danken, folgen, gratulieren.",
  "example_correct": "Ich danke dem Lehrer. Sie folgt dem Weg.",
  "encouragement": "Der Rest deines Satzes war super - die Wortstellung und der Wortschatz stimmen perfekt!"
}
```

### 4.3  Modul C: Übungsgenerator

Basierend auf dem erkannten Fehlermuster generiert das System **gezielte Übungen**:

| Fehlertyp | Übungstyp | Generierungsmethode |
|-----------|-----------|-------------------|
| **Phonem-Substitution** (z.B. /c\u0327/ -> /\u0283/) | Minimal-Pair-Drill | Template: Wortpaare aus phonetischer DB; TTS fuer Audiomodell |
| **Prosodie** (flache Intonation) | Satzimitations-Übung | Modellsatz (TTS) -> Lerner imitiert -> Vergleich (D4) |
| **Kasusmarkierung** | Lückentext (Cloze) | LLM generiert Sätze mit Lücke am Fehlerort; Distraktoren = typische Fehlformen |
| **Wortschatz** (frequenter Bereich) | Kontextuelle Zuordnung | LLM generiert Sätze mit Zielwort in verschiedenen Kontexten |
| **Syntax** (Nebensatzstellung) | Satztransformation | Template: Hauptsatz -> Nebensatz umformen; LLM variiert Inhalt |
| **Morphologie** (Verb-Konjugation) | Konjugationstabelle + Lückentext | Template + LLM fuer kontextualisierte Sätze |

**Übungsgenerierung: Template + LLM Hybrid**

```python
def generate_cloze_exercise(error_type, learner_level, context):
    template = EXERCISE_TEMPLATES[error_type]  # Regelbasiert

    prompt = f"""
    Erstelle 5 Lueckensaetze zum Thema '{error_type}'
    fuer Niveau {learner_level}.
    Kontext des Fehlers: {context}
    Format: JSON-Array mit Feldern:
      sentence, gap_position, correct_answer, distractors[3]
    Die Distraktoren sollen typische Lernerfehler widerspiegeln.
    """

    raw_exercises = llm.generate(prompt, output_format="json")
    validated = validate_exercises(raw_exercises, template.rules)
    return validated
```

### 4.4  Modul D: Konversation & Roleplay

**Ziel:** Freie Sprachproduktion in kontrolliertem Rahmen – der Lerner *übt* sprechen, das System *diagnostiziert* dabei (D1–D6) und gibt *nach* der Konversation gezieltes Feedback.

| Aspekt | Design-Entscheidung |
|--------|-------------------|
| **Szenario-Design** | Kuratierte Szenarien (Arztbesuch, Wohnungssuche, Vorstellungsgespraech), abgestimmt auf CEFR-Stufe |
| **LLM-Rolle** | Gespraechspartner mit klarer Persona + didaktischem Auftrag |
| **Feedback-Timing** | **Delayed** – nicht waehrend der Konversation unterbrechen (Focus on Form: Kommunikation hat Vorrang) |
| **Diagnose** | Jede Lerner-Aeusserung durchlaeuft D1–D6 im Hintergrund; Fehler werden gesammelt, nicht sofort angezeigt |
| **Post-Conversation-Report** | Nach dem Gespraech: „Du hast 3x den Dativ nach Wechselpraepositionen verwechselt. Hier sind Beispiele...“ |

**Prompt-Architektur fuer Roleplay:**

```
SYSTEM:
Du bist {persona} in einem {szenario}.
Der Lerner ist auf Niveau {cefr_level}.
Sprich natuerlich, aber:
- Verwende Vokabular auf Niveau {cefr_level} bis {cefr_level+1}
- Stelle Fragen, die den Lerner zum Sprechen motivieren
- Wenn der Lerner etwas nicht versteht, vereinfache
- Korrigiere NICHT waehrend des Gespraechs
- Beende das Gespraech nach ca. {n_turns} Turns natuerlich
```

### 4.5  Modul E: Guardrails & Validierung

**Das kritischste Modul.** Ein LLM, das falsche Grammatikregeln lehrt, ist schlimmer als kein LLM.

| Risiko | Mitigation | Implementierung |
|--------|-----------|----------------|
| **Halluzinierte Grammatikregel** | RAG mit kuratierter Grammatik-KB; Regelcheck gegen Referenz | Grammatik-KB (z.B. canoonet, Duden-API, eigene DB); Output-Validierung gegen bekannte Regeln |
| **Falsches Beispiel** | Syntaktische Validierung des korrekten Beispielsatzes | LanguageTool-Check auf den generierten Beispielsatz |
| **Unangemessener Ton** | Tonalitaets-Check; Persona-Constraints im System-Prompt | Sentiment-Filter; explizite Prompt-Anweisungen |
| **Inkonsistenz mit D6-Diagnose** | Feedback muss auf tatsaechliche Fehler referenzieren | Input-Validierung: Feedback wird nur fuer Features generiert, die D1–D6 tatsaechlich gemessen haben |
| **Zu komplexe Erklaerung fuer Niveau** | Sprachkomplexitaet des Feedbacks an Lerner-Niveau anpassen | Readability-Check; Niveau-spezifische Prompt-Templates |

**Validierungspipeline:**

```python
def validate_feedback(feedback_json, diagnostic_profile, grammar_kb):
    checks = []

    # 1. Stimmt der Fehlertyp mit D6 ueberein?
    checks.append(
        feedback_json["error_type"] in diagnostic_profile.detected_errors
    )

    # 2. Ist der "korrekte" Satz tatsaechlich korrekt?
    lt_result = language_tool.check(feedback_json["correct_form"])
    checks.append(len(lt_result.errors) == 0)

    # 3. Ist die Regel in der KB vorhanden?
    checks.append(
        grammar_kb.contains_rule(feedback_json["rule_summary"])
    )

    # 4. Ist die Sprache niveau-angemessen?
    checks.append(
        readability_score(feedback_json["what_went_wrong"])
        <= MAX_READABILITY[diagnostic_profile.cefr_level]
    )

    if all(checks):
        return feedback_json
    else:
        return fallback_template_feedback(diagnostic_profile)
```

**Fallback-Prinzip:** Wenn die Validierung fehlschlaegt -> Template-basiertes Feedback (weniger natuerlich, aber korrekt) statt halluziniertem LLM-Feedback.

### 4.6  Modul F: Spaced Repetition & Lernpfad

**Fehler-Tracking ueber Sessions hinweg:**

| Komponente | Beschreibung | Tool |
|-----------|-------------|------|
| **Error Log** | Jeder erkannte Fehler wird mit Typ, Kontext, Zeitpunkt gespeichert | PostgreSQL / SQLite |
| **Error Decay Model** | Wie schnell vergisst der Lerner eine Korrektur? -> Wiederholungsintervall | FSRS (Free Spaced Repetition Scheduler, Open Source, MIT) |
| **Lernpfad-Priorisierung** | Welche Fehlertypen zuerst ueben? -> Schwaechste Dimension x Haeufigkeit x Lernbarkeit | Regelbasierter Algorithmus |
| **Fortschritts-Tracking** | Profil-Entwicklung ueber Zeit -> Motivationsvisualisierung | Zeitreihe der Dimensionsscores (D6) |

**FSRS vs. SM-2:**

| Algorithmus | Beschreibung | Vorteil |
|-------------|-------------|---------|
| SM-2 (Anki) | Klassischer Spaced-Repetition-Algorithmus | Einfach, bewaehrt |
| **FSRS** | Moderner, datengetriebener SR-Algorithmus; optimiert Intervalle basierend auf tatsaechlichem Lerner-Verhalten | Bessere Vorhersage; Open Source (MIT); scikit-learn-kompatibel |

---

## 5  Feedback-Typen nach Dimension

| Dimension (D6) | Primaerer Feedback-Typ | Uebungsformat | Beispiel |
|-----------------|----------------------|-------------|---------|
| **Aussprache** | Explicit Correction + Audio-Vergleich | Minimal-Pair-Drill; Nachsprechen | "Hoer den Unterschied: *Kirche* vs. *Kirsche*. Jetzt du!" |
| **Prosodie** | Modell-Imitation | Satzimitation mit F0-Vergleich | "Hoer zu: 'Kommst du MIT?' (steigende Intonation). Sprich nach." |
| **Fluency** | Ermutigung + Chunk-Training | Wiederholtes Lesen; Phrase-Drills | "Lies diesen Absatz dreimal. Versuche, die markierten Chunks fluessig zu sprechen." |
| **Syntaktische Komplexitaet** | Elicitation + Modell | Satzkombination; Nebensatzbildung | "Verbinde die Saetze: 'Es regnet.' + 'Ich bleibe zu Hause.' -> 'Weil es regnet, ...'" |
| **Wortschatz** | Kontextualisierung | Lueckentext; Synonym-Zuordnung | "Welches Wort passt? 'Der Arzt hat mir ein ___ verschrieben.' (Rezept / Rechnung / Regal)" |
| **Grammatische Korrektheit** | Metalinguistic Feedback | Regel + Transformation + Cloze | "Nach Wechselpraepositionen steht der Dativ bei 'wo?' und der Akkusativ bei 'wohin?'" |
| **Morphologie** | Explicit + Tabelle | Konjugations-/Deklinationsuebung | "Fuelle die Tabelle aus: ich gehe, du ___, er/sie ___, wir ___" |

---

## 6  Technische Bausteine

| Tool | Funktion | Lizenz | Einsatz in D7 |
|------|----------|--------|---------------|
| **LLM (API)** | Feedback-Generierung, Uebungserstellung, Roleplay | Variabel (OpenAI / Anthropic / Open Source) | Module B, C, D |
| **Open-Source LLMs** | Llama 3, Mistral Nemo (12B) – fuer Deutsch gut geeignet; lokale Inferenz moeglich | Apache 2.0 / MIT | Fallback; Datenschutz-Option; Kostenreduktion |
| **Grammatik-KB** | Kuratierte deutsche Grammatikregeln als RAG-Quelle | Eigene Erstellung | Modul B, E (Halluzinationsschutz) |
| **LanguageTool** | Validierung generierter Beispielsaetze auf Korrektheit | LGPL | Modul E |
| **FSRS** | Spaced Repetition Scheduling | MIT | Modul F |
| **TTS (Coqui / VITS)** | Audio-Generierung fuer Modellsaetze, Minimal Pairs | MPL-2.0 / Apache | Module B, C (Audio-Feedback) |
| **Jinja2 / Prompt-Templates** | Strukturierte Prompt-Verwaltung | BSD-3 | Alle Module |

---

## 7  LLM-Strategie: Build vs. Buy

| Option | Pro | Contra | Empfehlung |
|--------|-----|--------|-----------|
| **OpenAI API (GPT-4o)** | Beste Qualitaet; schnell integrierbar | Kosten (~$15/1M Tokens); Datenschutz (US-Server); Vendor Lock-in | MVP-Start (schnellstes Time-to-Market) |
| **Anthropic API (Claude)** | Hohe Qualitaet; guter Deutsch-Support; EU-Server verfuegbar | Kosten; API-Abhaengigkeit | Alternative zu OpenAI |
| **Open Source (Mistral Nemo 12B)** | Lokale Inferenz; kein Vendor Lock-in; Datenschutz | Qualitaet etwas niedriger; Infrastruktur-Aufwand | Mittelfristig: eigene Instanz fuer Kostenkontrolle |
| **Fine-Tuned Open Source** | Optimiert fuer DaF-Feedback; hoechste Kontrolle | Fine-Tuning braucht Daten + Expertise | Langfristig (Beta/Scale-Phase) |

**Gamma-Empfehlung:** Start mit API (GPT-4o oder Claude) -> Parallel Open-Source-Evaluation (Mistral Nemo) -> Mittelfristig Migration auf Self-Hosted fuer Kostenreduktion und Datenschutz.

---

## 8  AI Act Compliance

Sprachbewertung im Bildungsbereich faellt unter **Hochrisiko-KI** (Annex III, Punkt 3 des EU AI Act).

| Anforderung | Disce-Implementierung |
|-------------|----------------------|
| **Transparenz** | Lerner sieht: "KI-generiertes Feedback, basierend auf deinem Sprachprofil." Kein verstecktes Scoring. |
| **Erklaerbarkeit** | Feedback referenziert immer die gemessenen Features: "Dein Pausenanteil (38%) liegt ueber dem B1-Durchschnitt (25%)." |
| **Menschliche Aufsicht** | Lehrkraft kann Feedback einsehen, ueberschreiben, kommentieren. System trifft keine autonomen Bewertungsentscheidungen fuer Zertifizierungen. |
| **Risikomanagement** | Guardrails (Modul E); Fallback auf Template-Feedback bei Validierungsfehlern. |
| **Datenqualitaet** | Referenzdaten (D6) transparent dokumentiert; Lerner-Daten DSGVO-konform gespeichert. |

---

## 9  Zusammenfassung: Was Gamma liefert

```
+----------------------------------------------------------------------+
|                   Domaene 7 - Gamma-Bausteine                         |
|                                                                       |
|  INPUT: Diagnostisches Profil (D6) + Fehlerlog + Lernermodell        |
|                                                                       |
|  +----------------------------------------------------------+       |
|  |  A. Feedback-Router (regelbasiert)                        |       |
|  |     Dimension x Niveau x Aufgabentyp -> Strategie         |       |
|  +----------------------------------------------------------+       |
|  |  B. Feedback-Generierung (LLM + RAG + Grammatik-KB)      |       |
|  |     Structured Output -> Validierung -> Fallback           |       |
|  +----------------------------------------------------------+       |
|  |  C. Uebungsgenerator (LLM + Templates)                   |       |
|  |     Fehlertyp -> gezielte Uebung (Cloze, Drill, ...)      |       |
|  +----------------------------------------------------------+       |
|  |  D. Konversation & Roleplay (LLM)                        |       |
|  |     Szenario-basiert - Delayed Feedback                    |       |
|  +----------------------------------------------------------+       |
|  |  E. Guardrails (LanguageTool + KB-Check + Readability)    |       |
|  |     Halluzinationsschutz - Validierung - Fallback          |       |
|  +----------------------------------------------------------+       |
|  |  F. Spaced Repetition (FSRS)                             |       |
|  |     Error Tracking - Wiederholungsplanung - Lernpfad       |       |
|  +----------------------------------------------------------+       |
|                                                                       |
|  OUTPUT: Feedback - Uebungen - Lernpfad - Fortschritt               |
|          korrekt - erklaerbar - adaptiv - AI-Act-konform             |
+----------------------------------------------------------------------+
```

---

## 10  Limitationen auf Gamma-Ebene

| # | Limitation | Konsequenz |
|---|-----------|------------|
| 1 | **LLM-Kosten.** Jede Feedback-Generierung kostet Tokens. Bei 1.000 Lernern x 10 Feedbacks/Tag x 500 Tokens = 5M Tokens/Tag -> ~$75/Tag (GPT-4o). | Muss in Unit Economics eingepreist werden. Open-Source-Migration senkt Kosten langfristig. |
| 2 | **Halluzinationsrisiko.** Trotz RAG + Guardrails kann ein LLM falsche Erklaerungen generieren – insbesondere bei seltenen Grammatikphaenomenen. | Kuratierte Grammatik-KB muss umfassend sein; Template-Fallback als Sicherheitsnetz; Human-in-the-Loop fuer neue Fehlertypen. |
| 3 | **Keine TTS-Bewertung.** TTS-generierte Modellsaetze koennen selbst Aussprachefehler enthalten oder unnatuerlich klingen. | TTS-Qualitaet muss evaluiert werden; fuer kritische Minimal-Pair-Drills: aufgenommene Stimmen (professionelle Sprecher) bevorzugt. |
| 4 | **Uebungswirksamkeit nicht validiert.** Ob die generierten Uebungen tatsaechlich zu Lernfortschritt fuehren, ist im MVP nicht empirisch belegt. | A/B-Tests in der Beta-Phase; didaktische Evaluation mit DaF-Lehrkraeften. |
| 5 | **Roleplay-Steuerung.** LLMs in freier Konversation koennen off-topic gehen, unpassende Themen ansprechen oder das Niveau verfehlen. | Strenge System-Prompts; Turn-Limit; Post-hoc-Review der Konversationsverlaeufe. |
| 6 | **Personalisierungstiefe.** Ohne ausreichende Lerner-Historie (erste Sessions) ist das Coaching generisch. | Cold-Start-Strategie: Einstufungstest (D6) + erste 3–5 Sessions als Kalibrierungsphase. |

---

## 11  Moat-Vorschau

> **Warum ist "ChatGPT, hilf mir Deutsch lernen" kein Konkurrenzprodukt?**

Ein nacktes LLM hat:
- Keine Aussprachediagnostik (hoert den Lerner nicht)
- Keine Prosodiemessung (sieht keine F0-Kontur)
- Keine systematische Fehleranalyse (erfindet Fehler oder uebersieht sie)
- Kein Lernermodell (vergisst alles nach dem Chat)
- Keine Spaced Repetition (wiederholt nichts gezielt)
- Keine Validierung (halluziniert Grammatikregeln)

**Disce = Diagnostik (D1–D6) + Coaching (D7)** – das LLM ist *ein Baustein* in einer Pipeline, nicht die Pipeline selbst. Die Integration von **tiefem linguistischem Wissen** (Features) mit **generativer Kommunikationsfaehigkeit** (LLM) unter **didaktischer Kontrolle** (Router + Guardrails) – das ist der Coaching-Moat.
