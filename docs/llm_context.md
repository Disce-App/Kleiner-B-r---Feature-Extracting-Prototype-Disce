# LLM Context für Disce / Kleiner Bär

> **Zweck:** Schnelleinstieg für Claude, Goose oder andere LLMs, die mit diesem Repo arbeiten.  
> **Stand:** Januar 2026  
> **Maintainer:** [Dein Name]

---

## Was ist das hier?

**Disce** ist ein Sprachcoaching-System für fortgeschrittene Deutschlernende (B2–C2).

Das System besteht aus zwei Hauptmodulen:

| Modul | Rolle | Hauptdateien |
|-------|-------|--------------|
| **Großer Bär** | Speaking Coach – UI, Feedback-Loop, Session-Management | `pages/grosser_baer.py`, `grosser_baer/*.py` |
| **Kleiner Bär** | Feature-Extraktion – NLP, CAF-Metriken, CEFR-Schätzung | `features_viewer.py`, `disce_core.py` |

**Kern-Idee:** User spricht/schreibt → Kleiner Bär extrahiert Metriken → LLM generiert narratives Feedback → User reflektiert.

---

## Aktueller Stand (Januar 2026)

### ✅ Funktioniert produktiv
- **Deterministische Analyse (Schicht 1):** 30+ NLP-Features (SoMaJo, HanTa, spaCy, LanguageTool, wordfreq)
- **CEFR-Schätzung:** Regelbasiert aus 8 Dimensionen
- **LLM-Feedback:** GPT-4o-mini mit strukturiertem Prompt
- **Session-Logging:** Airtable via Make Webhook
- **Streamlit-UI:** Vollständiger Flow (Login → Pretest → Task → Aufnahme → Feedback → Reflexion)

### 🔧 Funktioniert bedingt
- **Audio-Aufnahme:** Browser-Mikrofon via `audio_recorder_streamlit`
- **Transkription:** OpenAI Whisper (wenn API-Key vorhanden), sonst Mock-Modus

### ❌ Noch nicht implementiert
- **Azure Speech-to-Text:** Vorbereitet in Architektur, Code fehlt
- **Azure Pronunciation Assessment:** Geplant für Prosodie-Analyse
- **Schicht 2 (Azure Services):** Komplett ausstehend

### ⚠️ Bekanntes Tech Debt
- `features_viewer.py` hat 1.865 Zeilen → sollte aufgeteilt werden
- 4 von 5 Home-KPIs sind Hardcoded-Defaults (nur `sentence_cohesion` ist echt)
- Demo-Dateien im Root-Verzeichnis → sollten in `/experiments/` verschoben werden
- "Neuer Ordner" existiert leer im Repo

---

## Wo finde ich was?

### Dokumentation
| Datei | Inhalt |
|-------|--------|
| `docs/architecture.md` | Systemarchitektur, Datenfluss, 4 Schichten |
| `docs/llm_context.md` | **Diese Datei** – Schnelleinstieg |
| `docs/generated/repo_map.md` | Auto-generierte Dateistruktur |
| `docs/generated/modules.md` | Auto-generierte Modul-Übersicht |
| `docs/generated/integrations.md` | Erkannte externe Services |

### Code-Einstiegspunkte
| Was | Wo |
|-----|-----|
| **Streamlit Entry** | `app.py` |
| **Speaking Coach UI** | `pages/grosser_baer.py` |
| **Feature-Extraktion** | `features_viewer.py` |
| **Features → UI Bridge** | `disce_core.py` |
| **LLM Prompts** | `grosser_baer/prompts.py` |
| **Task-Templates** | `grosser_baer/task_templates.py` |
| **OpenAI Services** | `openai_services.py` |
| **Pretest/MASQ** | `config/pretest_loader.py`, `config/pretest_config.json` |

### Datenfluss (vereinfacht)
```
User Input (Audio/Text)
       ↓
[Whisper] → Transkript
       ↓
[features_viewer.py] → 30+ NLP-Features
       ↓
[disce_core.py] → Aggregation (8 Dimensionen, CEFR, KPIs, Hotspots)
       ↓
[grosser_baer.py] → build_coach_input() → JSON-Block
       ↓
[openai_services.py] → GPT-4o-mini mit SYSTEM_PROMPT_COACH
       ↓
Feedback-Anzeige + Reflexion + Airtable-Logging
```

---

## Für LLMs: Do's and Don'ts

### ✅ Do's
- **Kleine Schritte:** Änderungen fokussiert und testbar halten
- **Metriken nutzen:** Das System ist datenbasiert – Feedback sollte auf echten Features basieren
- **Docs aktualisieren:** Nach strukturellen Änderungen `python generate_docs.py` ausführen
- **Kontext beachten:** Pretest-Daten (CEFR-Selbsteinschätzung, MASQ) fließen ins Coaching ein
- **Schichten respektieren:** Deterministisch (Schicht 1) → Azure (Schicht 2) → LLM (Schicht 3) → Interpretation (Schicht 4)

### ❌ Don'ts
- **Nicht `features_viewer.py` komplett umschreiben** ohne vorherigen Refactoring-Plan
- **Keine neuen Integrationen** ohne Eintrag in Docs
- **Keine Magic Numbers** – Schwellenwerte dokumentieren oder in Config auslagern
- **Nicht Azure/Whisper voraussetzen** – Mock-Modus muss immer funktionieren

---

## Typische Aufgaben für LLMs

### 1. Feature hinzufügen
1. Funktion in `features_viewer.py` implementieren
2. In `analyze_all()` aufrufen
3. In `compute_dimension_scores()` einbinden (falls relevant für Dimensionen)
4. In `build_metrics_summary()` für LLM-Output aufnehmen

### 2. Neuen Task-Typ erstellen
1. Template in `grosser_baer/task_templates.py` hinzufügen
2. Evaluation-Focus und Meta-Prompts definieren
3. Ggf. spezifische Prompt-Anpassungen in `prompts.py`

### 3. CEFR-Schätzung verbessern
- Schwellenwerte in `estimate_cefr_score_from_dims()` anpassen
- Gewichtungen der Dimensionen in `compute_dimension_scores()` prüfen

### 4. Azure-Integration bauen
- Ziel: `layer2_azure` in `coach_input["analysis"]` befüllen
- Pronunciation Assessment Scores integrieren
- Prosodie-Daten (Pitch, Tempo) extrahieren

---

## Schnellstart: Lokale Entwicklung

```bash
# Repo klonen / updaten
cd /pfad/zu/Kleiner-Baer
git pull origin main

# Virtuelle Umgebung (falls nicht vorhanden)
python -m venv venv
source venv/bin/activate  # oder venv\Scripts\activate auf Windows

# Dependencies
pip install -r requirements.txt
python -m spacy download de_core_news_lg

# Streamlit starten
streamlit run app.py

# Generated Docs aktualisieren
python generate_docs.py
```

---

## Kontakt / Fragen

Bei Unklarheiten:
1. Prüfe `docs/architecture.md` für Systemverständnis
2. Prüfe `docs/generated/modules.md` für Code-Struktur
3. Frage den Maintainer

---

*Zuletzt aktualisiert: 2026-01-24*
