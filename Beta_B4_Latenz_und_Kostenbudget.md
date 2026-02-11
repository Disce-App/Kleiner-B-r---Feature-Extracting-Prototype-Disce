
# Beta B4 — Latenz- & Kostenbudget
_Zeitliche und ökonomische Constraints pro Stufe (D1–D7)_

**Status:** Draft v0.1 (MVP-orientiert)  
**Zielgruppe:** Tech/Product, die Pipeline-Owner je Stufe, Biz/Finance (COGS)  

---

## 1) Ziel & Leitplanken

Dieses Dokument definiert **messbare Latenz- und Kostenbudgets** für die End-to-End-Assessment-Pipeline (D1–D7) und übersetzt sie in:

- **SLOs** (p50/p95) für Nutzererlebnis ("interaktiv" vs. "async")
- **Stage-Budgets** (Zeit + Kosten-Treiber) pro Stufe
- **Entscheidungsregeln**: Was wird _synchron_ geliefert, was _asynchron_ nachgeladen?
- **Optimierungshebel**: Parallelisierung, Caching, Batching, Model-Tiers

> Grundprinzip: **Budget ist ein Produkt-Contract**. Wenn ein Modell/Feature das Budget sprengt, muss es entweder optimiert, degradiert oder in den Async-Pfad verschoben werden.

---

## 2) Begriffe (damit wir über dasselbe reden)

- **E2E-Latenz**: Zeit von „Audio-Submit“ bis „Ergebnis im UI verfügbar“.
- **Stage-Latenz**: Zeit zwischen `stage.started_at` und `stage.finished_at` (zzgl. Queue-Time, falls relevant).
- **p50/p95**: Median bzw. 95%-Perzentil (p95 ist UX-relevant, weil die Leute sich daran erinnern).
- **RTF (Real-Time-Factor)**: $$RTF = \frac{compute\_time}{audio\_duration}$$
  - Beispiel: RTF 0,5 bedeutet „2× schneller als Echtzeit“.
- **COGS pro Assessment**: variable Kosten pro Job (Compute, LLM, Storage/IO), ohne Fixkosten/Overhead.

---

## 3) Produkt-SLOs (2-Pfad-Strategie)

Wir definieren **zwei Lieferpfade**:

### 3.1 Interaktiv ("Fast Path")
Für „User wartet im UI“.

- **Ziel:** schnelle, „gut genug“-Rückmeldung
- **SLO-Vorschlag:**
  - p50: „fühlt sich direkt an“
  - p95: „nicht nervig“

**Lieferumfang (typisch):**
- D1 (ASR) + D5 (Textdiagnostik) + D6 (vorläufiges CEFR/Profil) + D7 (kurzes Coaching)
- D2/D3/D4 ggf. nur, wenn Budgets halten oder Audio kurz ist

### 3.2 Async ("Deep Path")
Für „vollständiger Report“, kann nach 10–120 Sekunden nachladen.

- **Ziel:** maximale Qualität/Abdeckung (D2–D4 tief), bessere Erklärbarkeit
- **SLO-Vorschlag:**
  - p95: „kommt sicher, ohne dass UI hängt“

**Lieferumfang:**
- D2 + D3 + D4 in voller Tiefe
- D6 final + D7 ausführlicher Coaching-Plan

---

## 4) Budgetierung: Wie wir Budgets setzen

Wir budgetieren entlang von drei Achsen:

1. **Audio-Dauer-Klassen** (weil Kosten/Latenz stark skalieren)
   - _Kurz_: 5–15s (z.B. Satz/Shadowing)
   - _Mittel_: 20–60s (z.B. Bildbeschreibung)
   - _Lang_: 90–180s (z.B. freies Sprechen)
2. **Pfad**: Interaktiv vs. Async
3. **Stage-Kategorie**:
   - _GPU-lastig_: ASR, ggf. Pronunciation/Prosodie
   - _CPU-lastig_: Alignment, Feature-Extraktion, Statistik
   - _Token-lastig_: LLM-Coaching

> Wichtig: Budgets gelten für **p95 inklusive Queue-Time**. Wenn wir Queueing ausklammern, belügen wir uns freundlich.

---

## 5) Latenzbudgets pro Stufe (Vorschlag)

### 5.1 Baseline-Referenz
In B1 wurde als MVP-Korridor formuliert: **< 10s für 10s Audio** (mit Parallelisierung von D3/D4/D5 nach D2). Das ist unser Startpunkt für die Budgetlogik.

### 5.2 Stage-Budgets (interaktiv) — Audio „mittel“ (z.B. 30–60s)

**Regel:** Interaktiv liefern wir _nicht zwingend_ alle Domänen tief, sondern priorisieren **Text + grobes Level + nutzbares Coaching**.

| Stufe | Rolle im Fast Path | Budget-Idee (p95) | Notizen / Degrade-Option |
|---|---|---:|---|
| D0 Preprocess/Upload | IO + Normalisierung | klein halten | Chunked upload, Audio normalisieren, VAD optional |
| **D1 ASR** | Must-have | **dominant**, aber stabil | Streaming/Chunking, Model-Tier „fast“ |
| D2 Alignment | Optional im Fast Path | niedrig/skip | Wenn D2 zu langsam: skip → D3/D4 nicht möglich |
| D3 Pronunciation | Optional | skip oder „light“ | z.B. nur globale Indikatoren statt phone-level |
| D4 Prosodie | Optional | skip oder „light“ | z.B. nur Sprechtempo + Pausen, kein F0 pro Frame |
| **D5 Textdiagnostik** | Must-have | moderat | CPU/LLM-light je nach Design |
| **D6 Scoring/CEFR** | Must-have | klein | Aggregation + Mapping, keine teuren Modelle |
| **D7 Coaching** | Must-have | token-basiert budgetieren | Kurz-Coaching (Template + kleine LLM) |

> Praktischer Hebel: **D5 kann theoretisch nach D1 starten**; wir lassen D2 im Fast Path optional, damit D5/D6/D7 nicht blockieren.

### 5.3 Stage-Budgets (async) — Audio „mittel“

Async darf teurer/langsamer sein, aber muss **verlässlich** sein.

| Stufe | Rolle im Deep Path | Budget-Idee (p95) | Notizen |
|---|---|---:|---|
| D1 | bereits vorhanden | 0 (reuse) | ASR-Ergebnis wiederverwenden |
| **D2 Alignment** | Must-have | dominant | CPU parallelisieren, cache Lexika, Warm Worker |
| **D3 Pronunciation** | Must-have | dominant | ggf. GPU/CPU je nach Approach |
| **D4 Prosodie** | Must-have | moderat | Feature extraction pipeline optimieren |
| D5 | reuse/refresh | klein | typischerweise reuse |
| **D6 final** | Must-have | klein | Recompute mit mehr Inputs |
| **D7 ausführlich** | Must-have | token-basiert budgetieren | Längerer Prompt, mehr Struktur |

---

## 6) Kostenbudget: Ein operatives Kostenmodell (ohne Provider-Pricing)

Damit wir Kosten steuern können, definieren wir **messbare Cost-Units** statt „€-Schätzungen“, die ohne Provider/Model fix nicht belastbar sind.

### 6.1 Cost Units
Pro Job tracken wir mindestens:

- **GPU-Sekunden** (oder GPU-Minuten) pro Stufe
- **CPU-Sekunden** pro Stufe
- **RAM-GB-Sekunden** (optional, aber bei großen Modellen hilfreich)
- **LLM-Token**:
  - `prompt_tokens`
  - `completion_tokens`
  - `cached_tokens` (falls Prompt-Caching)
- **Storage**:
  - Audio-Bytes gespeichert
  - Feature-Bytes gespeichert
  - Retention-Dauer (Tage)

### 6.2 Stage-spezifische Kostentreiber

| Stufe | Primäre Kostentreiber | Typische Stellhebel |
|---|---|---|
| D1 ASR | GPU-Sekunden, Modellgröße, RTF | Modell-Tier, Quantisierung, Streaming, Batch, VAD |
| D2 Alignment | CPU-Zeit, I/O, Lexika | Worker-Parallelität, Caching, „good-enough“ Alignment |
| D3 Pronunciation | CPU/GPU + Alignment-Qualität | Light vs. full scoring, Sampling, Skip-Rules |
| D4 Prosodie | CPU + Feature-Extraktion | Frame-Rate reduzieren, nur robuste Features |
| D5 Text | CPU/LLM Token | Regelbasiert + kleine Modelle, LLM nur bei Unsicherheit |
| D6 Scoring | CPU klein | Precomputed Features, reines Aggregat |
| D7 Coaching | Token dominant | Template-first, Retrieval begrenzen, Output-Limits |

---

## 7) Konkrete Budget-Mechaniken (die in Code landen sollten)

### 7.1 Timeouts & Deadlines (pro Stufe)
Jede Stage bekommt eine **Deadline** (Wall-Clock), plus eine **Compute-Grenze** (z.B. max GPU-Sekunden).

- Wenn Deadline erreicht:
  - Fast Path: **degrade/skip** und Ergebnis trotzdem liefern
  - Async: **retry** (mit Backoff) oder in „degraded final“ übergehen

### 7.2 Token-Budgets (D7)
Setzt hart:

- `max_prompt_tokens`
- `max_completion_tokens`
- „Stop“-Regeln (z.B. nach N Bulletpoints)

Und soft:

- Prompt-Compression, falls Inputs groß (z.B. nur Top-5 Findings, nicht alles)

### 7.3 Adaptive Compute (Tiering)
Ein einfaches, robustes Tiering:

- **Tier 0 (ultra-fast)**: kurze Audios, schwaches Netz, Demo-Modus
- **Tier 1 (MVP default)**: normal
- **Tier 2 (deep)**: nur async oder nur für paying users

Tiering kann getriggert werden durch:

- Audio-Dauer
- Queue-Auslastung
- User-Segment (free vs paid)
- „Need for detail“ (z.B. Lernmodus vs Prüfungssimulation)

### 7.4 Caching (wo es wirklich hilft)
- **D1**: selten sinnvoll „job-cache“ (Audio ist neu), aber:
  - Modell warm halten
  - Feature caches (z.B. Mel-Spectrogram) nur, wenn es mehrere Downstream-Consumer gibt
- **D2**: Lexikon/Phonem-Mapping cache
- **D7**: Prompt-Template cache, ggf. „policy + rubric“ als system cache

---

## 8) Kapazitätsplanung (Quick & Dirty, aber nützlich)

Wir brauchen **eine Zahl**, ab wann wir „Queueing-Latenz“ als Hauptproblem haben.

### 8.1 Little’s Law als Faustregel
Wenn
- $$\lambda$$ = Jobs pro Sekunde (Arrival Rate)
- $$W$$ = durchschnittliche Zeit im System (inkl. Queue)
- $$L$$ = durchschnittliche Jobs im System

Dann $$L = \lambda \cdot W$$.

Für die Praxis:

- Pro Worker mit mittlerer Service-Time $$S$$ (ohne Queue)
- Bei Ziel-Auslastung $$\rho$$ (z.B. 0,6–0,8)

grob:  
$$workers \approx \frac{\lambda \cdot S}{\rho}$$

> Wir sollten pro Stage getrennt rechnen (GPU-Pool für D1, CPU-Pool für D2/D5/D6, Token-Pool/D7).

---

## 9) Observability: Was wir messen müssen (sonst ist Budget ein Wunschzettel)

**Pro Job und pro Stage** im Envelope/Tracing:

- `queue_time_ms`
- `compute_time_ms`
- `io_time_ms`
- `retries`
- `degradation_flags`
- `input_sizes` (audio_sec, tokens_in, tokens_out)

Und als Dashboards:

- p50/p95 E2E Fast Path
- p50/p95 pro Stage
- GPU-Utilization, CPU-Load
- Token/Job (D7)
- % Jobs mit Degrade/Skip

---

## 10) Budget-Checkliste (MVP)

1. **Fast-Path SLO** festlegen (p95) und als „Release Gate“ nutzen
2. Für jede Stage:
   - Deadline + max Cost Units
   - Degrade-Strategie (skip vs light)
3. **D7 Token-Budget** fixieren (max completion)
4. **Async-Report** sauber nachladen (UI/Backend Contract)
5. Performance-Regression-Tests:
   - 10s, 30s, 60s Audios
   - p95 darf nicht > X% steigen pro Release

---

## Anhang A — Vorschlag: Budget-Matrix als Tabelle im Repo

Lege im Repo eine `budgets.yaml` an (konfigurierbar pro Environment):

```yaml
fast_path:
  audio_sec_max: 60
  e2e_p95_ms: 12000
  stages:
    d1_asr:
      deadline_ms: 6000
      max_gpu_sec: 8
    d5_text:
      deadline_ms: 2500
      max_cpu_sec: 4
    d7_coaching:
      deadline_ms: 2500
      max_prompt_tokens: 2500
      max_completion_tokens: 350
async_path:
  e2e_p95_ms: 120000
  stages:
    d2_alignment:
      deadline_ms: 45000
    d3_pronunciation:
      deadline_ms: 45000
    d4_prosody:
      deadline_ms: 30000
    d7_coaching:
      max_completion_tokens: 900
```

Wichtig: Zahlen sind **Platzhalter** – sie müssen empirisch kalibriert werden.
