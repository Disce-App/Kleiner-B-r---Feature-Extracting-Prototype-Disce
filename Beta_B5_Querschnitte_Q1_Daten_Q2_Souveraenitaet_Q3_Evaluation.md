
# Beta B5 — Querschnitte
_Q1 Daten · Q2 Souveränität · Q3 Evaluation_

**Status:** Draft v0.1 (MVP-orientiert)  
**Zielgruppe:** Tech/Product, Data/ML, Security/Compliance, QA/Research  

---

## 0) Zweck dieses Dokuments

B5 bündelt **pipeline-übergreifende** Entscheidungen und Standards, die in jedem Modul (D1–D7) „mitlaufen“ müssen:

- **Q1 Daten:** Welche Daten entstehen wo, wie werden sie versioniert, gespeichert, anonymisiert, gelöscht und wiederverwendet?
- **Q2 Souveränität:** Wie stellen wir Daten‑, Modell‑ und Anbieter-Souveränität sicher (Compliance, Lock-in, Residency, Auditability)?
- **Q3 Evaluation:** Wie messen wir Qualität _pro Stufe_ und _end-to-end_, wie bauen wir Goldsets, und wie verhindern wir Regressionen?

> Leitidee: Wenn wir diese Querschnitte nicht sauber definieren, werden Latenz, Kosten, Qualität und Compliance „zufällig“.

---

## Q1 — Daten (Lifecycle, Verträge, Qualität)

### Q1.1 Datenklassen (was ist „was“?)

Wir unterscheiden mindestens vier Datenklassen, weil daraus direkte Pflichten folgen (Retention, Zugriff, Export, Löschung):

1. **Rohdaten (Raw)**
   - Audio (Original), ggf. Video
   - User-Input-Text (Prompts/Antworten)
2. **Abgeleitete Daten (Derived)**
   - ASR-Transkript, Tokenisierung
   - Alignment, Phonem-/Silben-Events
   - Prosodie-Features (F0, Energy, Pausen, Tempo)
   - Textfeatures (Lexical diversity, Syntax, Errors etc.)
3. **Ergebnisdaten (Outputs)**
   - Scores / CEFR-Mapping / Rubrics
   - Feedback/Coaching-Text, Übungsplan
4. **Telemetry & Audit (Meta)**
   - Stage-Latenzen, Queue Times, Degradation Flags
   - Model/Version-Hashes, Config-Snapshots

**Prinzip:** _Raw ist am sensibelsten_, Derived ist oft re-identifizierbar, Outputs sind häufig „personenbezogene Leistungsdaten“.

---

### Q1.2 Datenfluss pro Job (Artefakte & Abhängigkeiten)

Pro Assessment-Run entstehen Artefakte entlang D1–D7. Das Minimum, das wir konsistent benötigen:

- `audio.original` (oder Referenz auf Object Storage)
- `asr.transcript.v1`
- `text.features.vX`
- `scoring.profile.vX`
- `coaching.fast.v1` (Fast Path)
- optional deep:
  - `alignment.vX`, `pronunciation.events.vX`, `prosody.features.vX`, `coaching.deep.v1`

**Ablage-Regel:** Artefakte sind **immutable** (append-only). Korrekturen erzeugen neue Versionen.

---

### Q1.3 Schemas & Verträge (damit Teams parallel arbeiten können)

#### (a) Envelope/Trace als „Single Source of Truth“
Jeder Job hat eine einheitliche Hülle (Envelope), die Stage-Ergebnisse, Status, Metriken und Artefakte referenziert.  
Damit kann das UI jederzeit _partial results_ anzeigen.

**Minimalfelder (Vorschlag):**
- Identitäten: `assessment_id`, `user_id` (oder pseudonym), `tenant_id`
- Kontext: `language`, `task_type`, `audio_sec`, `created_at`
- Stage-Statusliste: pro Stage `status`, `started_at`, `finished_at`, `error_code`
- Artefakte: pro Stage `artifact_refs[]` inkl. `schema_version`
- Budgets: `deadline_ms`, `tier`, `degradation_flags[]`

> Implementation: Envelope als JSON, versioniert (`envelope_schema_version`).

#### (b) Datenformate
- Audio: PCM/WAV intern normalisiert (z.B. 16kHz mono), Original optional separat
- Text: UTF‑8, explizite `language_tag` (BCP‑47)
- Features: Parquet/Arrow (batch/analytics) oder JSON (MVP) – aber **immer schema-versioned**

---

### Q1.4 Retention & Löschung (produkt- und compliance-tauglich)

Wir brauchen eine klare Matrix:

| Datentyp | Zweck | Standard-Retention | Löschtrigger | Besonderheiten |
|---|---|---:|---|---|
| Raw Audio | Rekonstruktion, ggf. Support | kurz | User delete / policy | stärkste Verschlüsselung |
| Derived Features | Recompute vermeiden | mittel | User delete / policy | ggf. re-identifizierbar |
| Outputs (Scores/Feedback) | Lernverlauf | länger | User delete / policy | Leistungsdaten |
| Telemetry | Betrieb/QA | mittel | policy | minimieren & aggregieren |

**MVP-Rule of Thumb:**
- Default: Raw kurz halten, Derived nur wenn Nutzen klar, Outputs für Lernverlauf.
- Alles: **Löschung muss kaskadieren** (Raw → Derived → Outputs/History, wo nötig).

---

### Q1.5 Zugriff, Rechte, Multi-Tenancy

- Prinzip: **Least privilege**
- Trennung: Tenant-Scopes erzwingen (Row-Level Security / separate Buckets)
- Zugriff auf Raw Audio stark begrenzen (Support nur mit Ticket/Reason)
- „Research Mode“ nur mit explizitem Consent + Pseudonymisierung

---

### Q1.6 Datenqualität (DQ) & Sicherheitschecks in der Pipeline

**Automatische Checks (MVP):**
- Audio: Sample rate/Channels ok, Clipping-Rate, SNR grob, Dauer innerhalb Policy
- ASR: Empty transcript detection, language mismatch, confidence floor
- Features: NaN/Inf, Out-of-range (z.B. F0), fehlende Segmente
- Outputs: Score-range checks, „explainability snippets“ vorhanden

**Wenn Check fehlschlägt:**
- setze `degradation_flag` und liefer „safe“ Output (keine Halluzination, keine falsche Sicherheit)

---

## Q2 — Souveränität (Daten, Modelle, Anbieter)

### Q2.1 Was meinen wir mit „Souveränität“?

Souveränität heißt für uns:

1. **Data sovereignty**: Kontrolle über Speicherort, Zugriff, Verschlüsselung, Löschung, Export.
2. **Model sovereignty**: Fähigkeit, Modelle/Provider zu wechseln, ohne Produkt neu zu bauen.
3. **Operational sovereignty**: Auditability, reproduzierbare Runs, Notfallpläne.

---

### Q2.2 Data Residency & Verschlüsselung

**MVP-Minimum:**
- At-rest: Verschlüsselung (Object Storage + DB)
- In-transit: TLS überall
- Schlüsselmanagement: klarer Owner, Rotation, Trennung zwischen Environments

**Residency-Entscheidung (früh klären):**
- Wo liegen Raw/Derived/Outputs?
- Welche Teile dürfen externe Provider sehen (z.B. LLM prompt)?

---

### Q2.3 Provider & Lock-in (Design gegen Abhängigkeit)

**Technische Leitplanken:**
- Abstraktionslayer pro Capability:
  - ASR Provider Interface
  - LLM/Coach Interface
  - Embeddings/Retrieval Interface
- Konfigurierbare „Model IDs“ (kein Hardcoding)
- Logs speichern **Model-Versionen** + **Prompt-Versionen**

**Strategie:**
- _Dual-run_ möglich machen (A/B oder shadow inference), um Providerwechsel zu testen.

---

### Q2.4 Prompt-/Policy-Souveränität (D7)

- Prompts sind **Code**: versionieren, reviewen, changelog
- Sicherheitslayer:
  - Output-Constraints (Format, Länge)
  - Content policies (keine medizinischen/diagnostischen Aussagen, wenn nicht erlaubt)
  - PII-Redaction in Prompts (wo möglich)

---

### Q2.5 Reproduzierbarkeit & Audit Trails

Pro Run speichern wir:
- Input-Hashes (Audio hash, transcript hash)
- Modell-/Code-Versionen (git sha), Config snapshot
- Stage-Metriken & Degradation

Ziel: „Warum bekam User A gestern anderes Feedback als heute?“ muss beantwortbar sein.

---

### Q2.6 Risiko-Register (leichtgewichtig)

| Risiko | Impact | Early signal | Mitigation |
|---|---|---|---|
| Provider outage (ASR/LLM) | UX down | error-rate, latency spike | fallback tier, queue, graceful degrade |
| Data breach | existenziell | audit anomalies | encryption, access controls, monitoring |
| Model drift | Qualität sinkt | eval delta | continuous eval, canary |
| Lock-in | Kosten/Speed | switching cost | abstraction layer, dual-run |

---

## Q3 — Evaluation (Qualität pro Stufe & E2E)

### Q3.1 Evaluationspyramide

Wir evaluieren auf drei Ebenen:

1. **Unit/Stage Metrics** (D1–D7 jeweils)
2. **System Metrics** (E2E Profile/CEFR & Feedbackqualität)
3. **Product Metrics** (Lernerfolg, Retention, NPS, „time-to-insight“)

---

### Q3.2 Stage-Metriken (Vorschläge)

#### D1 ASR
- WER/CER (je Sprache/Task)
- segment coverage (wie viel Audio wurde transkribiert)
- confidence calibration

#### D2 Alignment
- boundary error (ms) gegen manuelle Alignments
- coverage: Anteil aligned tokens

#### D3 Pronunciation
- Korrelation zu menschlichen Ratings (Spearman/Pearson)
- Klassifikationsgüte (z.B. „problematisch vs ok“) inkl. precision/recall
- fairness slices (Akzente, L1 Gruppen), vorsichtig interpretieren

#### D4 Prosodie
- Stabilität/Robustheit (Noise sensitivity)
- agreement zu annotierten Prosodie-Kategorien (falls vorhanden)

#### D5 Textdiagnostik
- Feature validity (z.B. Korrelation zu CEFR Labels)
- error detection quality (precision/recall) für bestimmte Fehlertypen

#### D6 Scoring/CEFR
- Accuracy/MAE gegen Labels (ordinal)
- Confusion matrix pro Level
- Calibration/Confidence

#### D7 Coaching
- Human preference (pairwise)
- Rubric scoring: correctness, specificity, actionability, tone
- Safety metrics: policy violations, hallucination rate

---

### Q3.3 Goldsets & Datenstrategie (ohne Overkill)

**MVP-Goldset v1** (klein, aber repräsentativ):
- pro Sprache × Task-Type × Level (A1–C1) ein Mindestkontingent
- je Sample:
  - Audio
  - Referenztranskript (wenn möglich)
  - CEFR/Score Label (mind. 2 Rater)
  - Coaching-Rubric Rating (kurz)

**Annotation-Guidelines:**
- klare Rubrics, Beispiele, „edge cases“
- Inter-rater reliability tracken (Cohen’s kappa / Krippendorff’s alpha)

---

### Q3.4 Regression-Tests & Release Gates

Jedes Release muss:

- E2E-Latenz Budgets halten (Fast Path) – sonst Feature in Async oder Tier2
- Stage-Qualität nicht signifikant verschlechtern (z.B. WER delta < X)
- Token-Budget D7 nicht sprengen (p95 prompt+completion)

**Artefakt:** `eval_report.md` pro Release, automatisch generiert.

---

### Q3.5 Online Monitoring (nach Go-Live)

- Drift detection:
  - audio length distribution
  - language distribution
  - ASR confidence shifts
- Silent failures:
  - empty transcripts
  - extreme scores
  - spike in degradation flags

---

## 4) „MVP Done“-Definition für B5

### Q1 Daten — Done
- Schema-Versionierung definiert
- Retention & Löschkaskade dokumentiert
- Zugriff/Scopes (Tenant, Support) umgesetzt

### Q2 Souveränität — Done
- Provider-Abstraktionen vorhanden (ASR, LLM)
- Audit fields & reproducibility minimal implementiert
- Residency-Entscheidung dokumentiert

### Q3 Evaluation — Done
- Goldset v1 existiert
- Automated regression pipeline (nightly + pre-merge) läuft
- Dashboard für p95 latency + quality deltas

---

## Anhang A — Checkliste (Copy/Paste)

### Daten (Q1)
- [ ] Welche Artefakte speichern wir wirklich? (und warum?)
- [ ] Für jedes Artefakt: schema_version + owner + retention + delete strategy
- [ ] Pseudonymisierung/Consent flags im Envelope
- [ ] Export/Deletion getestet (E2E)

### Souveränität (Q2)
- [ ] Provider austauschbar (kein Hardcoding)
- [ ] Keys/Encryption/Roles dokumentiert
- [ ] Audit trail pro Run vorhanden
- [ ] Incident plan (outage, breach) skizziert

### Evaluation (Q3)
- [ ] Goldset repräsentativ (Slices)
- [ ] Stage metrics implementiert
- [ ] Release gates definiert
- [ ] „Human in the loop“ für D7 Rubric mindestens stichprobenartig
