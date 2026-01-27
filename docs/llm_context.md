# LLM Context für Disce (Großer Bär + Kleiner Bär)

> **Zweck:** Schnelleinstieg für LLMs, die in diesem Repo Änderungen umsetzen (Refactors, Feature-Erweiterungen, Prompt-/Contract-Änderungen).
> > **Kanonischer Provider (Stand):** OpenAI (Chat + Whisper).
> > **Dokument-Typ:** _Living Doc_ (soll nach größeren Änderungen zusammen mit den generated docs aktualisiert werden).

---

## 0) TL;DR – Was ist dieses Repo?

Dieses Repo enthält zwei eng gekoppelte Teile:

- **Großer Bär (Frontend Coach)**: Streamlit UI für den Speaking-Loop (Aufgabe wählen → aufnehmen/mock → Feedback → Reflexion → optional speichern).
- **Kleiner Bär (Analyse / Feature-Extraction)**: Deterministische Textanalyse (Feature-Extraktion), Hotspots, CEFR-Schätzung und Disce-KPIs.

Wichtig: Obwohl die Begriffe „Großer Bär“ / „Kleiner Bär“ getrennte Rollen beschreiben, liegen beide im selben Repo und sind zur Laufzeit direkt gekoppelt.

---

## 1) Kanonischer LLM-Flow (OpenAI)

### 1.1 Audio → Transkript
- Im Echtmodus wird Audio via OpenAI Whisper transkribiert.
- Im Mock-Modus wird der „gesprochene“ Text manuell eingegeben.

### 1.2 Textanalyse („Kleiner Bär“)
Der UI-Pfad nutzt ein schlankes Interface:

- `disce_core.analyze_text_for_llm(text, context)`

Output (stabiler Contract):
- `metrics_summary`
- `hotspots`
- `cefr` (score + label)
- `disce_metrics`

### 1.3 Coach Input (JSON Contract)
Der LLM bekommt **einen JSON-Block**, der in der UI gebaut wird:

- `pages/grosser_baer.py::build_coach_input(...)`

Dieses Objekt ist der **kanonische Input-Contract** für das Coaching.

### 1.4 Feedback Generation (OpenAI Chat)
Das Coaching-Feedback wird über OpenAI Chat generiert:

- `openai_services.generate_coach_feedback(coach_input)`

Dabei wird `coach_input` als JSON in die User-Message serialisiert (kein separates Prompt-Template als „user prompt“).

---

## 2) Output-Contract: Wie das LLM antworten muss

Die Output-Regeln sind im System Prompt definiert (siehe `grosser_baer/prompts.py`).

### 2.1 Format (muss stabil bleiben)
Antwort ist:
- Deutsch
- **Sie-Form**
- professionell, aber nicht steif

Verwende **genau** diese Überschriften:

- Aufgabenerfüllung
- Struktur & roter Faden
- Ton & Wirkung
- Sprache im Detail
- Fokus fürs nächste Mal

### 2.2 Zentrale Regeln
- **Keine Zahlen nennen** (keine Scores/Prozente/TTR etc.). Zahlen sind interne Hinweise.
- **Max. 2 Fokus-Punkte** unter „Fokus fürs nächste Mal“.
- **Zitiere kurz** aus dem Transkript, um Beobachtungen zu belegen.
- Priorisiere: lieber 1–2 starke Hebel als „alles korrigieren“.

---

## 3) Input-Contract (coach_input) – Schema (v1)

### 3.1 Top-Level Keys

- `user`: Identifikation
- `pretest`: Selbsteinschätzung + Profil + MASQ
- `task_metadata`: Task-Kontext (Situation, Zielregister, Zeitlimit …)
- `session_metadata`: Session-Infos (mode, duration …)
- `learner_planning`: Lernziel & Kontext (User-Text)
- `transcript`: Transkript (String)
- `analysis`: Analyse-Container (Layer 1/2 + CEFR + KPIs + Hotspots)
- `reflection`: Reflexionstext + Timestamp

### 3.2 Detail: `analysis`

- `layer1_deterministic`: `metrics_summary` (aus Kleiner Bär)
- `layer2_azure`: aktuell `None` (Azure ist geplant)
- `cefr`: `{score, label}`
- `home_kpis`: `disce_metrics`
- `hotspots`: Liste annotierter Sätze

### 3.3 Empfehlungen für Contract-Stabilität (Engineering)
- `schema_version` ergänzen (z.B. `"coach_input/v1"`)
- Breaking Changes vermeiden (lieber neue Keys additiv hinzufügen)

---

## 4) Pretest Contract

### 4.1 `pretest.self_assessment`
- `cefr_overall`
- `cefr_speaking`
- `has_official_cert`
- `official_cert_type`

### 4.2 `pretest.learner_profile`
- `learning_duration_months`
- `learning_context` (Liste)
- `native_language`
- `other_languages`

### 4.3 `pretest.masq`
MASQ wird als strukturiertes Objekt übergeben (inkl. `factors`, `total`, `level`, `level_label`).

---

## 5) Kleiner Bär: `metrics_summary` (Inhalt)

`metrics_summary` ist ein **stabiler Sub-Contract**: Er wird in `disce_core.build_metrics_summary(...)` gebaut und in `analyze_text_for_llm()` durchgereicht.

**Wichtig:**
- Der Coach bekommt hier typischerweise viele numerische Signale.
- Im Output dürfen diese Zahlen nicht erscheinen (nur qualitative Übersetzung).

Wenn du `metrics_summary` erweitern willst:
- Änderungen in `disce_core.build_metrics_summary(...)` machen,
- anschließend `analyze_text_for_llm()` weiter stabil halten.

---

## 6) Hotspots Contract

`hotspots` ist eine Liste von annotierten Satz-Objekten (kein reines String-Array).

Wenn du das Schema ändern willst, ändere konsistent:
- `disce_core.select_hotspots(...)`
- alle Consumer (UI/LLM/logging)

---

## 7) Task Templates (Großer Bär)

Tasks sind in `grosser_baer/task_templates.py` definiert.

Typische Felder:
- `id`, `title`, `context`, `cefr_target`, `situation`, `task`, `time_seconds`, `evaluation_focus`, `register`, `example_phrases`, `meta_prompts`.

### Known issue (bitte vor Änderungen beachten)
In der UI werden teils Task-Feldnamen wie `level` erwartet, während Templates z.B. `cefr_target` nutzen.

Empfehlung: Vor größeren Änderungen Feldnamen harmonisieren, sonst entstehen leise `None`-Werte im `coach_input`.

---

## 8) Modi (run modes)

Im UI gibt es (mindestens) diese Modes:
- `mock_speaking`
- `speaking`

Der Mode fließt in `coach_input.session_metadata.mode` und wird auch als Kontext an `analyze_text_for_llm()` übergeben.

---

## 9) Logging / Persistenz (Make → Airtable)

Die UI kann Session-Daten über einen Make Webhook senden (flacher Payload).

Im Payload sind u.a. enthalten:
- Task-Metadaten, Transcript, Reflection
- CEFR-Label/Score
- `disce_metrics` als JSON
- Pretest-Felder inkl. MASQ-Factor-Means

Airtable kann per Config deaktiviert sein; dann wird das Senden übersprungen.

---

## 10) Für LLMs: Do’s / Don’ts im Repo

### ✅ Do
- Arbeite entlang des kanonischen Contracts (`coach_input`, `analyze_text_for_llm`).
- Halte Änderungen additiv/backwards-compatible (neue Keys statt bestehende umzubenennen), außer du machst einen bewussten Breaking Change.
- Nach strukturellen Änderungen: `python generate_docs.py` laufen lassen und `docs/generated/*` committen.

### ❌ Don’t
- Keine unkoordinierten Änderungen am `coach_input` Schema (das ist euer API-Contract).
- Keine Vermischung von „interne Metriken“ und „User-facing Feedback“: Output soll qualitativ sein.

---

## 11) Geplante Erweiterung: Azure (Layer 2)

Azure ist als nächster Schritt geplant, um Prosodie/Pronunciation tiefer auszuwerten.

Ziel: `coach_input["analysis"]["layer2_azure"]` wird von `None` zu einem strukturierten Objekt.

Empfehlung: Sobald Azure ergänzt wird, bitte auch:
- `schema_version` im `coach_input` einführen,
- klare Subschemas (z.B. `pronunciation`, `prosody`, `word_level`).

---

*Zuletzt aktualisiert: 2026-01-27*
