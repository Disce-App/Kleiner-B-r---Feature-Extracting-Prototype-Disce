# Systemarchitektur: Disce (Großer Bär + Kleiner Bär)

> **Zweck:** Technische Übersicht für Entwickler:innen und Agents (LLMs/Coding-Agents), die am Repo arbeiten.
> > **Stand:** 2026-01-27
> > **Wichtig (Evolving Architecture):** Diese Architektur ist **ein Prototyp in aktiver Entwicklung**. > Teile sind bewusst pragmatisch/heuristisch umgesetzt (z.B. KPIs, Logging-Payload), und **Strukturen können sich noch ändern**.

---

## 0) Orientierung: Was ist in diesem Repo?

Das Repo ist ein **kombiniertes** System aus:

- **Großer Bär (Frontend Coach)**: Streamlit UI, Speaking-Loop, Session-State, LLM-Call, Persistenz (Make/Airtable).
- **Kleiner Bär (Analyse)**: deterministische Textanalyse, Hotspots, CEFR-Schätzung, Disce-KPIs.

Repo-Struktur (high-level): `pages/`, `grosser_baer/`, `config/`, `docs/`, plus Root-Module (`disce_core.py`, `features_viewer.py`, `openai_services.py`, `app.py`).

---

## 1) Leitprinzipien

1. **Loop statt Feature-Sammlung**: Der Kern ist der Speaking-Loop: Aufgabe → (Audio oder Mock) → Analyse → Feedback → Reflexion → optional speichern.
2. **Contracts > Impl-Details**: Entscheidend sind stabile Schnittstellen (z.B. `analyze_text_for_llm` und `coach_input`).
3. **Layering**: Analyse ist als Schichten-Modell gedacht (deterministisch → Azure geplant → LLM → Interpretation/Anzeige).
4. **Ehrliche Doku**: Alles, was „geplant“ ist, wird als geplant markiert; nichts wird „schön geredet“.

---

## 2) Runtime-Komponenten (Wer macht was?)

### 2.1 UI / Orchestrierung (Großer Bär)

**Datei:** `pages/grosser_baer.py`

- Steuert den Phasen-Flow über `st.session_state.phase` mit mindestens: `select`, `record`, `feedback`.
- Baut den LLM-Input via `build_coach_input(...)`.
- Triggert Persistenz via `send_session_to_airtable()`.

### 2.2 Deterministische Analyse (Kleiner Bär)

**Datei:** `disce_core.py`

- Bietet das stabile Interface `analyze_text_for_llm(text, context)`.
- Baut `metrics_summary` via `build_metrics_summary(...)`.
- Identifiziert `hotspots` via `select_hotspots(...)`.

**Features/Extraktion:** `features_viewer.py`

- Enthält die zugrundeliegenden Feature-Funktionen (Tokenisierung, POS, Syntax, Lexik, Kohäsion, …).

### 2.3 LLM-Services (kanonisch: OpenAI)

**Datei:** `openai_services.py`

- **Whisper** für Transkription (`whisper-1`).
- **Chat** für Coach-Feedback (`gpt-4o-mini`).

Wichtig: Der Chat-Call serialisiert `coach_input` als JSON in die User-Message.

### 2.4 Persistenz / Integrationen

- Make Webhook → Airtable (flacher Payload in `send_session_to_airtable()`).
- Airtable kann per Config deaktiviert sein.

---

## 3) Der kanonische Datenfluss (End-to-End)

### 3.1 Phasen im UI

1. **Select**: Nutzer wählt Task + setzt Lernziel/optional Kontext.
2. **Record**: Audioaufnahme (Echtmodus) oder Texteingabe (Mock).
3. **Feedback**:
   - Transcript bestimmen
   - Kleiner Bär Analyse
   - Coach-Input bauen
   - LLM Feedback generieren (OpenAI)
   - Ergebnisse anzeigen (Feedback/Transkript/Metriken/optional LLM-Input)
4. **Reflexion + Save**:
   - Reflexion erfassen, in `coach_input` ergänzen
   - optional: per Make/Airtable speichern

### 3.2 Zentrale Contracts

#### Contract A: `analyze_text_for_llm(text, context) -> dict`
Dieses Interface ist der **stabile Output** der deterministischen Analyse für andere Systeme.

Rückgabe enthält u.a.:
- `metrics_summary`
- `hotspots`
- `cefr: {score, label}`
- `disce_metrics`

#### Contract B: `coach_input` (LLM Input)
`coach_input` ist der **kanonische Input-Contract** für den Coach-LLM.

Top-Level:
- `user`, `pretest`, `task_metadata`, `session_metadata`, `learner_planning`, `transcript`, `analysis`, `reflection`

`analysis` enthält:
- `layer1_deterministic`: `metrics_summary`
- `layer2_azure`: aktuell `None` (Azure geplant)
- `cefr`, `home_kpis`, `hotspots`

---

## 4) Analyse-Schichten (Status: aktiv vs geplant)

### Schicht 1: Deterministische Analyse (aktiv)

**Ziel:** Reproduzierbare Metriken aus Text/Transkript (gleicher Input → gleiches Ergebnis).

**Pipeline (vereinfacht):**
- Tokenisierung/POS/Syntax/Lexik/Kohäsion → Dimensions-Scores → CEFR score/label → Summary + Hotspots

**Outputs:**
- `metrics_summary` (LLM-freundliches, aber numerisches Summary)
- `hotspots` (annotierte Sätze)
- `disce_metrics` (5 KPIs)

### Schicht 2: Azure Services (geplant)

**Ziel:** tiefere Audio-/Prosodie-/Pronunciation-Analyse (Wort-Timestamps, Prosody, Pronunciation Assessment).

**Contract-Position:**
- `coach_input["analysis"]["layer2_azure"]` ist aktuell `None` und soll später ein strukturiertes Objekt werden.

### Schicht 3: LLM-Analyse / Coaching (aktiv, kanonisch: OpenAI)

**Ziel:** Narrative Coaching-Rückmeldung, die die deterministischen Signale in didaktisch sinnvolles Feedback übersetzt.

- System-Prompt definiert Format/Regeln (keine Zahlen ausgeben, max 2 Fokus-Punkte, Sie-Form).
- `coach_input` wird als JSON übergeben.

### Schicht 4: Interpretation / Anzeige / Aggregation (teilweise aktiv)

**Ziel:** Zusammenfassung für UI und Persistenz.

Aktuell u.a.:
- Anzeige von CEFR + Disce-Dimensionen
- Auswahl und Anzeige von Hotspots
- Export/Logging-Format (Make/Airtable Payload)

Hinweis: Diese Schicht ist im Prototyp teilweise „UI-getrieben“ und kann sich bei Produktreife noch stärker zu einem separaten Aggregationsmodul entwickeln.

---

## 5) Persistenz & Observability

### 5.1 Make → Airtable

- Die UI baut einen **flachen Payload** (Top-Level Felder) für den Make Webhook.
- Enthält u.a. Transcript, Reflection, CEFR, `disce_metrics` (als JSON), sowie ausgewählte Pretest/MASQ-Felder.

### 5.2 Lokale Logs

Es existiert außerdem ein JSON-Session-Logger (`grosser_baer/session_logger.py`) als strukturierte, exportfreundliche Speicherung.

---

## 6) Run Modes & Config

### 6.1 Mock vs Echt

- Mock-Modus: Texteingabe statt Audio, Mock-Feedback-Pfad.
- Echt-Modus: Audio → Whisper → GPT-Feedback.

### 6.2 `mode` Feld

Im aktuellen UI werden mindestens diese Mode-Werte genutzt:
- `mock_speaking`
- `speaking`

Der Mode fließt in `coach_input.session_metadata.mode` und wird zusätzlich als Kontext an `analyze_text_for_llm()` übergeben.

---

## 7) Known Issues / Tech Debt (bewusst dokumentiert)

1. **Task Feldnamen drift**: UI nutzt teils `task.get("level")`, Tasks definieren aber `cefr_target`. Das kann zu stillen `None`-Werten in `coach_input` führen.
2. **Heuristische KPIs**: Einige KPIs sind aktuell heuristisch bzw. context-defaulted (bis Azure/weiteres Scoring ergänzt wird).
3. **Evolving Architecture**: Mehrere Teile (Azure Layer 2, Metrik-Definitionen, Persistenzschema) sind bewusst noch im Fluss.

---

## 8) Roadmap (kurz) – was sich wahrscheinlich ändern wird

### 8.1 Azure Layer 2 einführen
- `layer2_azure` wird von `None` zu einem strukturierten Objekt.
- Prosody-/Pronunciation-Features sollen in UI + Coach-Input auftauchen.

### 8.2 Contract-Stabilität erhöhen
Empfehlung (wenn ihr das einführen wollt):
- `schema_version` im `coach_input` ergänzen
- Breaking Changes nur mit Version-Bump

---

*Zuletzt aktualisiert: 2026-01-27*
