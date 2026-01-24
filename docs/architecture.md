# Systemarchitektur: Disce / Kleiner Bär

> **Zweck:** Technische Übersicht für Entwickler und LLMs  
> **Stand:** Januar 2026

---

## Übersicht

Disce ist ein Sprachcoaching-System für fortgeschrittene Deutschlernende (B2–C2). Die Architektur folgt einem **4-Schichten-Modell** für Diagnostik und Feedback.

```
┌─────────────────────────────────────────────────────────────────────────────┐
│                           BENUTZER-INTERFACE                                 │
│                        (Streamlit: pages/grosser_baer.py)                   │
│  ┌─────────┐  ┌─────────┐  ┌─────────┐  ┌─────────┐  ┌─────────┐           │
│  │ Login   │→ │ Pretest │→ │  Task   │→ │ Record  │→ │Feedback │→ Reflect  │
│  │ (Code)  │  │ (MASQ)  │  │ wählen  │  │(Audio)  │  │  + KPIs │           │
│  └─────────┘  └─────────┘  └─────────┘  └─────────┘  └─────────┘           │
└─────────────────────────────────────────────────────────────────────────────┘
                                      │
                                      ▼
┌─────────────────────────────────────────────────────────────────────────────┐
│                         4-SCHICHTEN-DIAGNOSTIK                               │
│                                                                              │
│  ┌────────────────────────────────────────────────────────────────────────┐ │
│  │ SCHICHT 4: INTERPRETATION                                              │ │
│  │ → CEFR-Aggregation, Home-KPIs, Interventionsempfehlungen              │ │
│  │ → disce_core.py: build_disce_metrics(), estimate_cefr_*()             │ │
│  └────────────────────────────────────────────────────────────────────────┘ │
│                                      ▲                                       │
│  ┌────────────────────────────────────────────────────────────────────────┐ │
│  │ SCHICHT 3: LLM-ANALYSE                                                 │ │
│  │ → Narratives Feedback, Argumentation, Register, Pragmatik             │ │
│  │ → openai_services.py + grosser_baer/prompts.py                        │ │
│  │ → GPT-4o-mini mit SYSTEM_PROMPT_COACH + FEEDBACK_PROMPT_TEMPLATE      │ │
│  └────────────────────────────────────────────────────────────────────────┘ │
│                                      ▲                                       │
│  ┌────────────────────────────────────────────────────────────────────────┐ │
│  │ SCHICHT 2: AZURE SERVICES                                    [GEPLANT] │ │
│  │ → Speech-to-Text, Pronunciation Assessment, Prosody                   │ │
│  │ → Accuracy Score, Fluency Score, Prosody Score                        │ │
│  │ → Status: NICHT IMPLEMENTIERT                                         │ │
│  └────────────────────────────────────────────────────────────────────────┘ │
│                                      ▲                                       │
│  ┌────────────────────────────────────────────────────────────────────────┐ │
│  │ SCHICHT 1: DETERMINISTISCHE ANALYSE                          [AKTIV]  │ │
│  │ → CAF-Metriken, NLP-Features, Lexik, Syntax, Kohäsion                 │ │
│  │ → features_viewer.py (1.865 Zeilen, 35+ Funktionen)                   │ │
│  │ → 100% reproduzierbar: gleicher Input → gleiches Ergebnis            │ │
│  └────────────────────────────────────────────────────────────────────────┘ │
│                                      ▲                                       │
│  ┌────────────────────────────────────────────────────────────────────────┐ │
│  │ ROHDATEN                                                               │ │
│  │ → Audio (Browser) → Whisper → Transkript                              │ │
│  │ → Oder: Mock-Modus (Text-Eingabe direkt)                              │ │
│  └────────────────────────────────────────────────────────────────────────┘ │
└─────────────────────────────────────────────────────────────────────────────┘
                                      │
                                      ▼
┌─────────────────────────────────────────────────────────────────────────────┐
│                           PERSISTENZ                                         │
│  Session-Daten → Make Webhook → Airtable                                    │
│  (user_code, transcript, metrics, feedback, reflection)                     │
└─────────────────────────────────────────────────────────────────────────────┘
```

---

## Schicht 1: Deterministische Analyse (Kleiner Bär)

### Toolstack

| Tool | Zweck | Import |
|------|-------|--------|
| **SoMaJo** | Tokenisierung (CMC-optimiert) | `from somajo import SoMaJo` |
| **HanTa** | POS-Tagging + Lemmatisierung | `from HanTa import HanoverTagger` |
| **spaCy** | Dependency Parsing, Morphologie | `de_core_news_lg` |
| **LanguageTool** | Grammatik-Check | API: `api.languagetool.org` |
| **wordfreq** | Wortfrequenz (Zipf-Score) | `from wordfreq import zipf_frequency` |

### Feature-Gruppen

#### CAF-Trias (Complexity, Accuracy, Fluency)

| Gruppe | Features | Funktionen |
|--------|----------|------------|
| **Complexity** | Satzlänge, Nebensätze, Einbettungstiefe, komplexe NPs | `sentence_lengths()`, `estimated_subclauses()`, `complex_nps_per_sentence()`, `vorfeld_lengths()` |
| **Accuracy** | Grammatikfehler pro 100 Wörter, Fehlertypen | `check_grammar_with_languagetool()` |
| **Fluency** | (Bei Audio: WPM, Pausen, Filler) | *Aktuell via Azure geplant* |

#### Lexikalische Features

| Feature | Beschreibung | Funktion |
|---------|--------------|----------|
| TTR / MATTR | Type-Token-Ratio (Moving Average) | `moving_average_ttr()` |
| Zipf-Frequenz | Durchschnittliche Wortfrequenz | `word_frequency_features()` |
| Seltene Wörter | Wörter mit Zipf < 3.0 | `get_rare_words_list()` |

#### Syntaktische Features

| Feature | Beschreibung | Funktion |
|---------|--------------|----------|
| Dependency-Tiefe | Max/Mean Baumtiefe | `dependency_tree_features()` |
| Satztypen | Relativ-/Konditional-/Finalsätze | `clause_type_features()` |

#### Stilistische Features

| Feature | Beschreibung | Funktion |
|---------|--------------|----------|
| Passiv | Vorgangs-/Zustands-/Modalpassiv | `passive_voice_features()` |
| Modalpartikeln | ja, doch, halt, eben, wohl, ... | `modal_particle_features()` |
| Pronomen | ich/wir/man/Sie-Verteilung | `pronoun_stats()` |
| Modus | Indikativ/Konjunktiv I/II | `verb_mood_features()` |

#### Kohäsion

| Feature | Beschreibung | Funktion |
|---------|--------------|----------|
| Konnektoren | Anzahl + Typen (via DiMLex-basiert) | `cohesion_features()` |
| Satz-Overlap | Lexikalische Überlappung | `sentence_overlap()` |

### Output: 8 Dimensionen

`compute_dimension_scores()` aggregiert alle Features zu 8 normalisierten Dimensionen (0–1):

```python
{
    "lexical_diversity": 0.72,    # TTR + Frequenz
    "syntactic_complexity": 0.65, # Nebensätze + Tiefe
    "grammar_accuracy": 0.88,     # LanguageTool
    "cohesion": 0.70,             # Konnektoren + Overlap
    "style_variation": 0.55,      # Passiv + Modalpartikeln
    "formality": 0.80,            # Pronomen + Register-Marker
    "morphological_control": 0.75,# Modus + Tempus
    "fluency": 0.60               # (Placeholder ohne Audio)
}
```

### CEFR-Schätzung

`estimate_cefr_score_from_dims()` berechnet einen Score (0–1), der zu Labels gemappt wird:

| Score | Label |
|-------|-------|
| < 0.40 | B1 |
| 0.40–0.55 | B2 |
| 0.55–0.70 | B2+ |
| 0.70–0.82 | C1 |
| 0.82–0.92 | C1+ |
| > 0.92 | C2 |

---

## Schicht 3: LLM-Analyse

### Prompt-Architektur

```
┌─────────────────────────────────────────────────────────────────┐
│                    SYSTEM_PROMPT_COACH                          │
│  - Persönlichkeit: warmherzig, präzise, fokussiert              │
│  - Format: "Das ist gelungen" → "Fokus fürs nächste Mal" →     │
│            "Mini-Übung"                                         │
│  - Prinzipien: konkrete Zitate, max 2 Fokuspunkte, Register    │
└─────────────────────────────────────────────────────────────────┘
                              +
┌─────────────────────────────────────────────────────────────────┐
│                 FEEDBACK_PROMPT_TEMPLATE                         │
│  - Kontext: Task, Situation, Register, Zeitvorgabe              │
│  - Transkript: User-Text                                        │
│  - Metriken: CEFR, Lexik, Grammatik, Kohäsion, ...             │
│  - Prosodie: (wenn Azure aktiv)                                 │
└─────────────────────────────────────────────────────────────────┘
```

### Metakognitions-Framework

Für jede Phase gibt es Prompts in `METACOGNITION_PROMPTS`:

| Phase | Zweck | Beispiel |
|-------|-------|----------|
| **Plan** | Vor der Übung | "Was sind die 2-3 wichtigsten Punkte?" |
| **Monitor** | Während der Übung | "Halbzeit – haben Sie Ihre Hauptpunkte genannt?" |
| **Reflect** | Nach der Übung | "Was würden Sie anders machen?" |

---

## Datenfluss: Eine Session

```
1. LOGIN
   └→ user_code → session_state

2. PRETEST (einmalig pro User)
   └→ CEFR-Selbsteinschätzung, MASQ-Scores → session_state.pretest_responses

3. TASK WÄHLEN
   └→ task_id, learner_goal, learner_context → session_state

4. AUFNAHME
   ├→ [Mock-Modus] Text-Eingabe → transcript
   └→ [Echt-Modus] audio_recorder → Whisper → transcript

5. ANALYSE (Kleiner Bär)
   └→ analyze_text_for_llm(transcript, context)
      ├→ tokenize_and_split()          # SoMaJo
      ├→ pos_tag_sentences()           # HanTa
      ├→ analyze_all()                 # 30+ Features
      ├→ compute_dimension_scores()    # 8 Dimensionen
      ├→ estimate_cefr_*()             # CEFR-Label
      ├→ build_metrics_summary()       # LLM-freundlich
      ├→ build_disce_metrics()         # 5 Home-KPIs
      └→ select_hotspots()             # Übungs-Sätze

6. COACH-INPUT BAUEN
   └→ build_coach_input()
      {
        user, pretest, task_metadata, session_metadata,
        learner_planning, transcript,
        analysis: { layer1_deterministic, layer2_azure, cefr, home_kpis, hotspots },
        reflection
      }

7. LLM-FEEDBACK
   ├→ [Mock-Modus] MOCK_FEEDBACK (statisch)
   └→ [Echt-Modus] generate_coach_feedback(coach_input)
      └→ GPT-4o-mini mit SYSTEM_PROMPT_COACH + FEEDBACK_PROMPT_TEMPLATE

8. ANZEIGE
   └→ Tabs: Feedback | Transkript | Metriken | (LLM-Input)

9. REFLEXION
   └→ reflection_text → update_coach_input_with_reflection()

10. SPEICHERN
    └→ send_session_to_airtable() → Make Webhook → Airtable
```

---

## Modul-Übersicht

### Kernmodule

| Datei | Zeilen | Verantwortung |
|-------|--------|---------------|
| `features_viewer.py` | 1.865 | **Kleiner Bär:** Alle NLP-Features |
| `disce_core.py` | 499 | Bridge: Features → Dimensionen → CEFR → KPIs |
| `pages/grosser_baer.py` | 1.258 | **Großer Bär:** Speaking Coach UI |
| `openai_services.py` | 148 | Whisper + GPT-4o-mini |
| `grosser_baer/prompts.py` | ~150 | System-Prompt + Templates |

### Unterstützende Module

| Datei | Verantwortung |
|-------|---------------|
| `grosser_baer/task_templates.py` | Sprechaufgaben-Definitionen |
| `grosser_baer/audio_handler.py` | Audio-Verarbeitung (Mock + echt) |
| `grosser_baer/feedback_generator.py` | Feedback-Logik (Mock) |
| `grosser_baer/session_logger.py` | Logging-Utilities |
| `config/app_config.py` | Zentrale Konfiguration |
| `config/pretest_loader.py` | Pretest-UI + Datenverarbeitung |

---

## Externe Abhängigkeiten

| Service | Zweck | Status |
|---------|-------|--------|
| **OpenAI API** | Whisper (STT) + GPT-4o-mini (Feedback) | ✅ Aktiv |
| **LanguageTool API** | Grammatik-Check | ✅ Aktiv |
| **Make.com** | Webhook-Orchestrierung | ✅ Aktiv |
| **Airtable** | Session-Persistenz | ✅ Aktiv |
| **Azure Speech** | Pronunciation + Prosody | ❌ Geplant |

---

## Geplante Erweiterungen

### Schicht 2: Azure Services

```python
# Ziel-Struktur in coach_input["analysis"]["layer2_azure"]
{
    "pronunciation": {
        "accuracy_score": 0.85,
        "fluency_score": 0.78,
        "completeness_score": 0.92,
        "prosody_score": 0.70
    },
    "word_level": [...],  # Pro-Wort-Scores
    "phoneme_level": [...] # Phonem-Details
}
```

### Weitere Module (Phase 2)

- `metaphor_and_frame_map` – Konzeptuelle Metaphern
- `audience_reaction_simulation` – Leserreaktionen simulieren
- `stress_response_analysis` – Tonveränderung unter Druck

---

## Konventionen

### Naming
- **Dateien:** `snake_case.py`
- **Klassen:** `PascalCase`
- **Funktionen:** `snake_case`, Verb zuerst (`get_*`, `build_*`, `analyze_*`)
- **Konstanten:** `SCREAMING_SNAKE_CASE`

### Feature-Funktionen
- Input: `tagged_sentences` (Liste von Sätzen, jeder Satz = Liste von `(word, lemma, pos)` Tuples)
- Output: Dict mit benannten Werten
- Fehlerbehandlung: Nicht crashen, Defaults zurückgeben

### Dimensions-Scores
- Immer normalisiert auf 0–1
- `clamp01()` verwenden
- Dokumentieren, welche Features eingehen

---

*Zuletzt aktualisiert: 2026-01-24*
