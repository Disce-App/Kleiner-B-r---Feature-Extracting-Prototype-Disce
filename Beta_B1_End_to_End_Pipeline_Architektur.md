# Beta · B1 – End-to-End-Pipeline & Architektur

> **Beta-Leitfrage:** *Wie werden die sieben Gamma-Bausteine zu einem durchgängigen System verbunden?*
> **B1-Frage:** *Was ist der vollständige Datenfluss von Audio-Input bis Coaching-Output – und welche Architekturentscheidungen bestimmen ihn?*

---

## 1  Systemkontext: Was Disce *ist* und was es *nicht* ist

### 1.1  Abgrenzung

Disce ist **kein** einzelnes ML-Modell, das man mit einer API aufruft. Disce ist eine **kompositorische Diagnostik-Pipeline**: Eine Folge spezialisierter Verarbeitungsschritte, die gemeinsam eine Fähigkeit erzeugen, die keiner der Schritte allein liefern könnte – nämlich ein *erklärbares, mehrdimensionales Sprachprofil mit didaktischem Feedback auf CEFR-Niveau für deutschsprachige Lerner*.

Das Architekturproblem ist nicht "welches Modell nutzen wir?" (das hat Gamma beantwortet), sondern:
- **Wie fließen Daten** von einem Baustein zum nächsten?
- **Was läuft sequenziell**, was parallel?
- **Wo entstehen Engpässe**, wo Fehlerrisiken?
- **Wie wird das System als Ganzes** deploybar, skalierbar, wartbar?

### 1.2  Designprinzipien

| Prinzip | Konsequenz |
|---------|------------|
| **Pipeline-as-DAG** | Der Verarbeitungsfluss ist ein gerichteter azyklischer Graph (DAG), kein linearer Strom. Manche Domänen können parallel laufen. |
| **Explizite Schnittstellen** | Jeder Übergang zwischen Domänen hat einen definierten Vertrag (Input-Schema, Output-Schema, Invarianten). Kein implizites Durchreichen. |
| **Graceful Degradation** | Wenn ein Baustein versagt oder unsichere Ergebnisse liefert, muss die Pipeline kontrolliert degradieren – nicht abstürzen. |
| **Erklärbarkeit > Blackbox** | An jeder Stelle muss nachvollziehbar sein, *warum* ein Score so ist, wie er ist. Kein opakes End-to-End-Modell. |
| **Souveränität** | Kein kritischer Pfad darf von einer externen API abhängen, die jederzeit abgeschaltet werden kann. |

---

## 2  Der DAG: Datenfluss von Audio bis Coaching

### 2.1  Übersichtsgraph

```
                         ┌──────────────┐
                         │   AUDIO-IN   │
                         │  (wav/opus)  │
                         └──────┬───────┘
                                │
                    ┌───────────▼───────────┐
                    │     D1 · ASR          │
                    │  Whisper Large-V3     │
                    │  → Transkript + Timing│
                    └───────────┬───────────┘
                                │
                    ┌───────────▼───────────┐
                    │     D2 · Alignment    │
                    │  MFA + WhisperX       │
                    │  → Phonem-Zeitgrenzen │
                    └───────────┬───────────┘
                                │
              ┌─────────────────┼─────────────────┐
              │                 │                  │
    ┌─────────▼────────┐ ┌─────▼──────┐ ┌────────▼─────────┐
    │  D3 · Pronuncia- │ │ D4 · Proso-│ │  D5 · Text-      │
    │  tion Scoring    │ │ die & Supra│ │  diagnostik (CAF) │
    │  GOP + MDD       │ │ F0, Rhythm │ │  Syntax, Lexik,   │
    │                  │ │            │ │  Morphologie      │
    └─────────┬────────┘ └─────┬──────┘ └────────┬─────────┘
              │                │                  │
              └────────────────┼──────────────────┘
                               │
                    ┌──────────▼───────────┐
                    │   D6 · Diagnostisches│
                    │   Scoring & CEFR     │
                    │   → Radar-Profil     │
                    └──────────┬───────────┘
                               │
                    ┌──────────▼───────────┐
                    │   D7 · Generatives   │
                    │   Coaching           │
                    │   → Feedback + Übung │
                    └──────────────────────┘
```

### 2.2  DAG-Semantik: Sequenziell, Parallel, Fork-Join

Die Pipeline ist **kein linearer Wasserfall**, sondern ein DAG mit einer zentralen **Fork-Join-Struktur**:

| Phase | Typ | Domänen | Logik |
|-------|-----|---------|-------|
| **Stufe 1** | Sequenziell | D1 → D2 | ASR *muss* vor Alignment abgeschlossen sein. Alignment braucht den Transkriptionstext als Eingabe für Forced Alignment. |
| **Stufe 2** | **Parallel (Fork)** | D3 ‖ D4 ‖ D5 | Drei unabhängige Analysedomänen, die alle denselben Input konsumieren (Audio + Alignment), aber verschiedene Aspekte extrahieren. |
| **Stufe 3** | Sequenziell (Join) | D6 | Aggregiert die Feature-Vektoren aus D3, D4, D5 zu einem Gesamtprofil. Kann erst starten, wenn alle drei vorliegen. |
| **Stufe 4** | Sequenziell | D7 | Generiert Feedback auf Basis des D6-Profils. Streng nach D6. |

**Warum Fork-Join?**

- **Latenzgewinn:** D3, D4 und D5 hängen nicht voneinander ab. Parallele Ausführung spart ca. 40–60 % der Gesamtlatenz gegenüber sequenzieller Verarbeitung dieser drei Stufen.
- **Fehler-Isolation:** Wenn D4 (Prosodie) einen Fehler wirft, können D3 und D5 trotzdem vollständig abschließen. D6 kann ein *partielles* Profil erstellen (Graceful Degradation).
- **Skalierbarkeit:** Die drei parallelen Pfade können auf verschiedene Worker / Prozesse / Container verteilt werden.

### 2.3  Input-Nuancen der Parallelstufe

Die Parallelstufe ist nicht so symmetrisch, wie der Graph suggeriert. Die drei Domänen konsumieren **unterschiedliche Teilmengen** des bisherigen Outputs:

| Domäne | Primärer Input | Sekundärer Input |
|--------|---------------|-----------------|
| **D3** Pronunciation Scoring | Audio + **Phonem-Alignment** (D2) | Transkript (D1) als Referenztext |
| **D4** Prosodie | **Audio (direkt)** + Wort-Alignment (D2) | – |
| **D5** Textdiagnostik | **Transkript-Text** (D1) | – (kein Audio nötig) |

**Kritische Beobachtung:** D5 braucht streng genommen nur das Transkript – kein Alignment, kein Audio. Theoretisch könnte D5 schon nach D1 starten, ohne auf D2 zu warten. In der Praxis warten wir trotzdem auf D2, weil:
1. D5-Ergebnisse ohne Zeitstempel nicht in D6 mit den anderen Dimensionen synchronisiert werden können
2. Der Latenzgewinn minimal ist (D2 läuft typischerweise in < 2s)
3. Ein einheitlicher Fork-Punkt die Architektur einfacher macht

---

## 3  Stufendetail: Was passiert wo?

### 3.1  Stufe 1a – D1: Transkription & ASR

**Baustein (Gamma):** Whisper Large-V3 / V3-Turbo, lokal via faster-whisper

**Input:**
- Audio-Datei (wav, opus, mp3), mono, 16 kHz empfohlen
- Optional: Aufgabenkontext (Prompt-Hint, z.B. "Bildbeschreibung" oder "Nacherzählung")

**Output (Zwischenprodukt, kein Endprodukt):**
```json
{
  "transcript": "Ich gehe gestern in die Schule und habe...",
  "segments": [
    {
      "start": 0.0, "end": 2.34,
      "text": "Ich gehe gestern in die Schule",
      "words": [
        {"word": "Ich", "start": 0.0, "end": 0.28, "confidence": 0.97},
        {"word": "gehe", "start": 0.30, "end": 0.62, "confidence": 0.94}
      ]
    }
  ],
  "language": "de",
  "language_confidence": 0.98,
  "meta": {
    "model": "whisper-large-v3",
    "runtime": "faster-whisper",
    "duration_audio_s": 12.5,
    "duration_processing_s": 1.8
  }
}
```

**Kompositionsentscheidungen (Beta-Ebene):**
- **Warum nicht nur Whisper-Zeitstempel nutzen?** Whisper liefert Wort-Zeitstempel, aber keine Phonem-Zeitstempel. Für D3 (GOP) brauchen wir Phonem-Alignment → deshalb existiert D2 als eigenständige Stufe.
- **Warum Whisper-Wortgrenzen trotzdem behalten?** Sie dienen als *Initialisierung* für MFA in D2 (bessere Convergence) und als Fallback, falls MFA divergiert.
- **Confidence-Weiterleitung:** Wort-Konfidenzwerte aus D1 werden an D6 durchgereicht. Ein Wort mit Confidence < 0.5 wird im Scoring als "ASR-unsicher" markiert – sein GOP-Score hat reduziertes Gewicht.

### 3.2  Stufe 1b – D2: Phonetisches Alignment

**Baustein (Gamma):** MFA (Montreal Forced Aligner) mit L2-adaptiertem Acoustic Model + WebMAUS als Verification Layer

**Input:**
- Audio (identisch mit D1-Input)
- Transkript-Text aus D1
- Pronunciation Dictionary (deutsch, IPA-basiert, mit Variantenformen)

**Output:**
```json
{
  "words": [
    {
      "word": "Ich",
      "start": 0.01, "end": 0.27,
      "phones": [
        {"phone": "ɪ", "start": 0.01, "end": 0.09},
        {"phone": "ç", "start": 0.09, "end": 0.27}
      ]
    },
    {
      "word": "gehe",
      "start": 0.30, "end": 0.61,
      "phones": [
        {"phone": "ɡ", "start": 0.30, "end": 0.38},
        {"phone": "eː", "start": 0.38, "end": 0.52},
        {"phone": "ə", "start": 0.52, "end": 0.61}
      ]
    }
  ],
  "alignment_confidence": 0.91,
  "meta": {
    "aligner": "MFA-2.2",
    "acoustic_model": "german_mfa_l2_adapted",
    "dictionary": "disce_de_ipa_v2",
    "verification": "webmaus_local"
  }
}
```

**Kompositionsentscheidungen:**
- **Dual-Stack:** MFA als primärer Aligner, WebMAUS als Verifikation. Bei Abweichung > 30 ms auf Phonem-Ebene wird ein Flag gesetzt. Dieses Flag propagiert an D3 als Unsicherheitssignal.
- **Pronunciation Dictionary als Kompositonsschicht:** Das Dictionary ist weder rein D1 noch rein D2 – es ist eine *Querschnittsressource*. Es enthält kanonische Formen **und** erwartbare L2-Varianten (z.B. /ç/ → [ʃ] für arabische L1). Diese Varianten ermöglichen, dass MFA nicht bei Lerner-Aussprache divergiert, und dass D3 zwischen "falsch" und "akzeptable Variante" unterscheiden kann.
- **TextGrid → JSON-Transformation:** MFA produziert Praat TextGrids. Diese werden inline in das kanonische JSON-Format transformiert, damit alle nachgelagerten Domänen ein einheitliches Format konsumieren.

### 3.3  Stufe 2 – Der Fork: D3 ‖ D4 ‖ D5

#### D3 · Pronunciation Scoring

**Input:** Audio + Phonem-Alignment (D2) + Transkript (D1)
**Gamma-Bausteine:** Kaldi-DNN-Ali-GOP, CTC-basierter GOP (wav2vec2), artikulatorisches MDD (wav2vec2 Speech Attribute Detection)

**Verarbeitung (3-Phasen-Architektur aus Gamma D3):**
1. **Phase 1 – GOP:** Für jedes Phonem-Segment (aus D2) wird ein Goodness of Pronunciation Score berechnet
2. **Phase 2 – MDD:** Mispronunciation Detection & Diagnosis identifiziert *was* statt des Zielphonems produziert wurde
3. **Phase 3 – Artikulatorische Analyse:** Speech Attribute Detection ordnet Fehler artikulatorischen Merkmalen zu (Manner, Place, Voicing)

**Output:**
```json
{
  "phone_scores": [
    {
      "phone_target": "ç", "phone_produced": "ʃ",
      "gop_score": -3.2,
      "mdd_label": "substitution",
      "articulatory_detail": {
        "place_error": true, "place_target": "palatal", "place_produced": "postalveolar",
        "manner_error": false,
        "voicing_error": false
      },
      "time_ref": {"start": 0.09, "end": 0.27}
    }
  ],
  "word_scores": [
    {"word": "Ich", "pronunciation_score": 0.62, "flags": ["substitution:ç→ʃ"]}
  ],
  "utterance_score": 0.78,
  "meta": {"gop_backend": "kaldi_dnn_ali", "mdd_backend": "wav2vec2_ctc"}
}
```

#### D4 · Prosodie & Suprasegmentalia

**Input:** Audio + Wort-Alignment (D2, Wortebene reicht)
**Gamma-Bausteine:** Parselmouth (Praat-Wrapper), librosa, OpenSMILE; perspektivisch wav2vec2-basierte Prosodie-Embeddings

**Verarbeitung:**
1. **F0-Tracking:** Grundfrequenz-Kontur über die gesamte Äußerung
2. **Rhythmusmetriken:** PVI (Pairwise Variability Index), %V, ΔC – Rhythmus-Indikatoren
3. **Sprechrate & Pausen:** Silben/Sekunde, Pausenlängen, Pausenverteilung
4. **Intonationsanalyse:** Vergleich der F0-Kontur mit erwartbaren Muster (Frage vs. Aussage)

**Output:**
```json
{
  "f0_contour": {"values": [120, 125, ...], "times": [0.0, 0.01, ...]},
  "rhythm": {
    "pvi_vocalic": 52.3,
    "pvi_consonantal": 48.1,
    "percent_v": 0.44,
    "speech_rate_syl_per_s": 3.2
  },
  "pauses": [
    {"start": 2.34, "end": 3.10, "duration": 0.76, "type": "filled", "filler": "ähm"}
  ],
  "fluency": {
    "articulation_rate": 4.1,
    "mean_length_of_run": 5.3,
    "pause_frequency": 0.18
  },
  "meta": {"f0_method": "parselmouth_cc", "sample_rate": 16000}
}
```

#### D5 · Textbasierte Sprachdiagnostik (CAF+)

**Input:** Transkript-Text (D1), optional Wort-Zeitstempel
**Gamma-Bausteine:** spaCy (de_dep_news_trf), LanguageTool, language_tool_python, lexikalische Frequenzlisten

**Verarbeitung:**
1. **Complexity (C):** Syntaktische Komplexität – T-Units, Subordinationsindex, Satzlänge, Dependenz-Tiefe
2. **Accuracy (A):** Grammatische Korrektheit via GEC (LanguageTool), Fehlerklassifikation (Kasus, Genus, Kongruenz, Wortstellung)
3. **Fluency (F):** Hier textbasiert: Reparaturen, Wortwiederholungen, Abbrüche (ergänzt D4-Audio-Fluency)
4. **Lexik (L+):** Type-Token-Ratio, lexikalische Diversität (MTLD, HD-D), Frequenzband-Verteilung

**Output:**
```json
{
  "complexity": {
    "mls": 8.3,
    "subordination_index": 1.4,
    "max_dependency_depth": 5
  },
  "accuracy": {
    "error_rate": 0.12,
    "errors": [
      {
        "type": "tense", "subtype": "present_for_past",
        "surface": "gehe", "correction": "ging",
        "position": {"word_idx": 1, "start": 0.30, "end": 0.62}
      }
    ]
  },
  "fluency_text": {
    "repairs": 1, "repetitions": 0, "false_starts": 0
  },
  "lexical": {
    "ttr": 0.72, "mtld": 48.5, "hd_d": 0.81,
    "frequency_bands": {"A1": 0.45, "A2": 0.25, "B1": 0.20, "B2": 0.08, "C1": 0.02}
  },
  "meta": {"nlp_model": "de_dep_news_trf", "gec_engine": "languagetool_6.4"}
}
```

### 3.4  Stufe 3 – Der Join: D6 Diagnostisches Scoring

**Input:** Feature-Vektoren aus D3, D4, D5 (alle drei müssen vorliegen – oder explizit als fehlend markiert sein)
**Gamma-Bausteine:** Ordinal Regression (CORAL/CORN), regelbasiertes Schwellenmodell, Referenzdaten (MERLIN-Korpus-Statistiken)

**Verarbeitung (5-Schichten-Modell aus Gamma D6):**
1. **Schicht 1 – Feature-Normalisierung:** Alle D3/D4/D5-Scores werden auf vergleichbare Skalen gebracht
2. **Schicht 2 – Dimensionsscore:** Pro Dimension (Aussprache, Prosodie, Grammatik, Lexik, Fluency) wird ein Score berechnet
3. **Schicht 3 – Profilbildung:** Die fünf Dimensionsscores bilden ein Radar-Profil
4. **Schicht 4 – CEFR-Indikation:** Regelbasiertes + ML-gestütztes Mapping auf CEFR-Stufe (A1–C1)
5. **Schicht 5 – Konfidenz & Auditierung:** Jeder Score trägt ein Konfidenzintervall und ist rückverfolgbar

**Output:**
```json
{
  "profile": {
    "pronunciation": {"score": 62, "cefr_indication": "A2+", "confidence": 0.78},
    "prosody":       {"score": 55, "cefr_indication": "A2",  "confidence": 0.65},
    "grammar":       {"score": 48, "cefr_indication": "A2",  "confidence": 0.82},
    "lexical":       {"score": 71, "cefr_indication": "B1",  "confidence": 0.80},
    "fluency":       {"score": 58, "cefr_indication": "A2+", "confidence": 0.72}
  },
  "cefr_overall": {"level": "A2", "sublevel": "A2+", "confidence": 0.74},
  "weakest_dimension": "grammar",
  "priority_targets": [
    {"dimension": "grammar", "specific": "Kasusmarkierung Akkusativ/Dativ", "source": "D5_errors"},
    {"dimension": "pronunciation", "specific": "Palatalfrikativ /ç/", "source": "D3_mdd"}
  ],
  "meta": {
    "scoring_model": "ordinal_regression_v1",
    "reference_corpus": "merlin_de_stats_v3",
    "degraded_dimensions": []
  }
}
```

### 3.5  Stufe 4 – D7: Generatives Coaching

**Input:** Diagnostisches Profil aus D6 + Aufgabenkontext + Lerner-Historie (falls vorhanden)
**Gamma-Bausteine:** LLM (lokal: Mistral/Llama oder API: GPT-4o), Prompt-Templates, Übungsgenerator, Guardrails

**Verarbeitung:**
1. **Feedback-Generierung:** LLM erhält das D6-Profil als strukturierten Prompt-Kontext und generiert natürlichsprachliches Feedback
2. **Übungsauswahl/-generierung:** Basierend auf `priority_targets` wird eine passende Übung ausgewählt oder generiert
3. **Guardrails:** Output wird auf didaktische Plausibilität, Tonalität und Sicherheit geprüft

**Output (Endprodukt an den Lerner):**
```json
{
  "feedback": {
    "summary": "Du hast einen guten Wortschatz – das ist deine Stärke! ...",
    "dimension_feedback": [
      {
        "dimension": "grammar",
        "message": "Achte auf die Zeitformen: Du hast 'gehe' statt 'ging' gesagt...",
        "severity": "focus_area"
      }
    ]
  },
  "exercise": {
    "type": "fill_in_the_blank",
    "topic": "Präteritum",
    "items": [
      {"prompt": "Gestern ___ ich in die Schule.", "target": "ging", "distractors": ["gehe", "gehen"]}
    ]
  },
  "meta": {
    "llm_model": "mistral-7b-instruct",
    "prompt_template": "coaching_v2_de",
    "guardrail_passed": true
  }
}
```

---

## 4  Architekturmuster: Wie wird der DAG ausgeführt?

### 4.1  Deployment-Topologie

Die Disce-Pipeline ist kein Monolith und kein Microservice-Schwarm. Sie ist ein **modularer Monolith mit internem DAG-Scheduler** – die pragmatische Mitte für ein Startup:

| Architekturmuster | Bewertung für Disce |
|---|---|
| **Monolith** | ❌ Zu starr. Modelle haben unterschiedliche Ressourcenanforderungen (GPU vs. CPU). |
| **Microservices** | ❌ Zu komplex für ein 2–3-Personen-Team. Netzwerk-Overhead, Service-Discovery, Tracing – alles Overhead. |
| **Modularer Monolith** | ✅ Ein Deployment-Artefakt, intern sauber modularisiert. Domänen als Python-Module mit klaren Interfaces. |
| **Task Queue (Celery/Redis)** | ✅ Für den Fork-Join in Stufe 2. Drei parallele Tasks, ein Join-Callback. Leichtgewichtig. |

### 4.2  Technologiestack (Empfehlung)

```
┌─────────────────────────────────────────────────────────┐
│                    API-Gateway                          │
│               FastAPI + Uvicorn (async)                 │
│         Endpunkte: /assess, /status, /profile           │
├─────────────────────────────────────────────────────────┤
│                  DAG-Orchestrierung                     │
│          Celery + Redis (Task Queue + Broker)           │
│    Task-Graph: D1 → D2 → [D3 ‖ D4 ‖ D5] → D6 → D7    │
├──────────┬──────────┬──────────┬────────────────────────┤
│  Worker  │  Worker  │  Worker  │       Worker           │
│  D1+D2   │ D3 (GPU) │ D4 (CPU) │  D5 (CPU) / D6 / D7  │
│  (GPU)   │          │          │                        │
├──────────┴──────────┴──────────┴────────────────────────┤
│               Shared State / Cache                      │
│          Redis (Zwischenergebnisse, Session)             │
├─────────────────────────────────────────────────────────┤
│              Persistenz (optional)                       │
│         PostgreSQL (Lerner-Profile, Historie)            │
└─────────────────────────────────────────────────────────┘
```

### 4.3  Request-Lifecycle

Der vollständige Lebenszyklus eines Assessment-Requests:

```
1. Client sendet Audio + Aufgabenkontext an POST /assess
2. FastAPI validiert Input, erzeugt Job-ID, gibt 202 Accepted zurück
3. Celery-Chain wird gestartet:
   a) Task D1_transcribe(audio) → result_d1
   b) Task D2_align(audio, result_d1) → result_d2
   c) Celery-Group (parallel):
      - Task D3_pronunciation(audio, result_d2, result_d1)
      - Task D4_prosody(audio, result_d2)
      - Task D5_text_diagnostics(result_d1)
   d) Chord-Callback: D6_score(result_d3, result_d4, result_d5)
   e) Task D7_coach(result_d6, context)
4. Ergebnis wird in Redis gecacht + optional in PostgreSQL persistiert
5. Client pollt GET /status/{job_id} oder erhält Webhook-Callback
6. Client ruft GET /profile/{job_id} ab → vollständiges Ergebnis
```

### 4.4  Celery-DAG in Code (Sketch)

```python
from celery import chain, group, chord

def run_assessment(audio_path: str, context: dict) -> str:
    """Startet die vollständige Assessment-Pipeline als Celery-DAG."""
    
    pipeline = chain(
        # Stufe 1: Sequenziell
        d1_transcribe.s(audio_path),
        d2_align.s(audio_path),
        
        # Stufe 2: Fork-Join via Chord
        # chord = group (parallel) + callback (join)
        chord(
            group(
                d3_pronunciation.s(audio_path),
                d4_prosody.s(audio_path),
                d5_text_diagnostics.s(),
            ),
            d6_score.s()  # wird aufgerufen, wenn alle 3 fertig
        ),
        
        # Stufe 3: Coaching
        d7_coach.s(context)
    )
    
    result = pipeline.apply_async()
    return result.id
```

> **Anmerkung:** In der realen Implementierung werden die Zwischenergebnisse über Redis geteilt (nicht als Celery-Argumente, da Audio-Daten zu groß). Die `.s(audio_path)`-Signatur ist vereinfacht – tatsächlich wird eine Job-ID übergeben, und jeder Worker liest seine Inputs aus dem Shared State.

---

## 5  Latenz-Analyse: Wo bleibt die Zeit?

### 5.1  Geschätzte Latenz pro Stufe (10s Audio, GPU: RTX 3090 oder vergleichbar)

| Stufe | Domäne | Geschätzte Latenz | Hardware | Begründung |
|-------|--------|-------------------|----------|------------|
| 1a | D1 ASR | ~1,5–2,5 s | GPU | faster-whisper large-v3, ~6x Realtime |
| 1b | D2 Alignment | ~1,5–3,0 s | CPU/GPU | MFA: CPU-heavy, aber parallelisierbar; WebMAUS-Verifikation addiert ~0,5s |
| 2 | D3 Pronunciation | ~1,0–2,0 s | GPU | GOP über alle Phoneme + MDD |
| 2 | D4 Prosodie | ~0,3–0,8 s | CPU | Parselmouth/librosa – rein CPU, schnell |
| 2 | D5 Text | ~0,5–1,5 s | CPU | spaCy-Transformer + LanguageTool |
| 3 | D6 Scoring | ~0,1–0,3 s | CPU | Numerische Aggregation, trivial schnell |
| 4 | D7 Coaching | ~1,0–3,0 s | GPU/API | LLM-Inferenz, abhängig von Modellgröße |

### 5.2  Gesamtlatenz

**Sequenziell (worst case):** ~6–13 s
**Mit Parallelisierung (Stufe 2):** ~4,5–9,5 s (D3 als längster Pfad in Stufe 2)
**Zielkorridor MVP:** < 10 s für 10 s Audio

**Latenz-Waterfall:**
```
Zeit →  0s        2s        4s        6s        8s       10s
        ├─ D1 ────┤
                  ├─ D2 ────┤
                            ├─ D3 ─────┤
                            ├─ D4 ─┤   │  (parallel)
                            ├─ D5 ──┤  │
                                       ├─ D6 ┤
                                             ├─ D7 ────┤
```

### 5.3  Latenz-Optimierungen (post-MVP)

| Optimierung | Geschätzter Gewinn | Komplexität |
|-------------|-------------------|-------------|
| **Streaming-ASR** (D1 startet, bevor Audio fertig ist) | -30–50 % D1-Latenz | Hoch |
| **D5 parallel zu D2** (Text-Diagnostik braucht kein Alignment) | -0,5–1,0 s | Niedrig |
| **GPU-Batching** (D1 + D3 auf selber GPU, sequenziell aber warm) | -0,5 s Overhead | Mittel |
| **LLM-Caching** (häufige Feedback-Patterns vorberechnen) | -50–80 % D7-Latenz für Wiederholungsfälle | Niedrig |
| **Distil-Whisper** statt Large-V3 | -50 % D1-Latenz, +5 % WER-Risiko | Niedrig |

---

## 6  Datenformate: Das kanonische Zwischenformat

### 6.1  Designentscheidung: Ein gemeinsames Envelope

Alle Domänen schreiben ihre Ergebnisse in ein gemeinsames **Assessment-Envelope**, das als JSON-Dokument durch die Pipeline wandert:

```json
{
  "job_id": "uuid-v4",
  "audio_ref": "s3://disce-audio/{job_id}.wav",
  "created_at": "2026-02-11T14:30:00Z",
  "task_context": {
    "task_type": "picture_description",
    "expected_level": "A2-B1",
    "prompt_text": "Beschreiben Sie das Bild."
  },
  "stages": {
    "d1_asr": { "status": "completed", "result": { ... }, "meta": { ... } },
    "d2_alignment": { "status": "completed", "result": { ... }, "meta": { ... } },
    "d3_pronunciation": { "status": "completed", "result": { ... }, "meta": { ... } },
    "d4_prosody": { "status": "completed", "result": { ... }, "meta": { ... } },
    "d5_text": { "status": "completed", "result": { ... }, "meta": { ... } },
    "d6_scoring": { "status": "completed", "result": { ... }, "meta": { ... } },
    "d7_coaching": { "status": "completed", "result": { ... }, "meta": { ... } }
  },
  "pipeline_meta": {
    "pipeline_version": "0.1.0",
    "total_duration_s": 7.3,
    "degraded_stages": []
  }
}
```

### 6.2  Warum ein Envelope?

| Vorteil | Erklärung |
|---------|-----------|
| **Auditierbarkeit** | Jede Entscheidung ist rückverfolgbar: Warum hat D6 den Score 48 für Grammatik vergeben? → D5-Fehler nachschlagen → D1-Transkript prüfen. |
| **Partielle Ergebnisse** | Wenn D4 fehlschlägt, sind D3 und D5 trotzdem im Envelope. D6 kann ein partielles Profil erstellen. |
| **Replay** | Das vollständige Envelope kann für Debugging, Evaluation oder Re-Scoring erneut durch einzelne Stufen geschickt werden. |
| **Versionierung** | `pipeline_version` ermöglicht A/B-Tests verschiedener Modellversionen. |

---

## 7  Systemgrenzen & offene Fragen für B2–B5

### 7.1  Was B1 *nicht* spezifiziert (und warum)

| Thema | Gehört in | Warum nicht hier? |
|-------|-----------|-------------------|
| Exakte JSON-Schemata mit Validation Rules | **B2** (Schnittstellenverträge) | B1 zeigt *was* fließt, B2 spezifiziert *wie genau* |
| Was passiert bei ASR-Fehler in D1? | **B3** (Fehlerpropagation) | B1 zeigt den Happy Path, B3 den Unhappy Path |
| GPU-Sizing, Cloud-Kosten, Skalierung auf 1.000 User | **B4** (Latenz & Kosten) | B1 schätzt Latenz, B4 rechnet durch |
| DSGVO, AI Act, Datenhaltung | **B5** (Querschnitte) | B1 zeigt die technische Architektur, B5 die regulatorische |

### 7.2  Architekturentscheidungen, die in B2–B5 zu treffen sind

1. **Streaming vs. Batch** (B4): Soll D1 schon anfangen, während der Lerner noch spricht? Und wenn ja: Wie ändert sich der DAG?
2. **Audio-Retention** (B5): Wie lange wird das Audio gespeichert? DSGVO-Löschfristen vs. Bedarf für Modellverbesserung.
3. **Fehler-Taxonomie** (B3): Welche Fehlerklassen gibt es? (ASR-Fehler, Alignment-Divergenz, Scoring-Ausreißer, LLM-Halluzination)
4. **Session-Kontext** (B2): Wie wird Lerner-Historie über mehrere Assessments hinweg geführt? Ist das Teil des Envelope oder ein separater Store?

---

## 8  Zusammenfassung: Der Disce-Kern in einem Satz

**Disce ist ein Fork-Join-DAG aus sieben spezialisierten Sprachdiagnostik-Domänen, der als modularer Monolith mit Celery-Orchestrierung deployed wird und in < 10 Sekunden ein erklärbares, mehrdimensionales CEFR-Profil mit generativem Coaching aus einer einzelnen Audio-Aufnahme erzeugt.**

---

## Referenzen & Gamma-Grundlagen

| Gamma-Dokument | In B1 referenziert für |
|---|---|
| **D1** Transkription & ASR | Whisper-Auswahl, Confidence-Weiterleitung |
| **D2** Phonetisches Alignment | MFA-Dual-Stack, TextGrid→JSON, L2-Dictionary |
| **D3** Pronunciation Scoring | 3-Phasen-Architektur (GOP → MDD → Artikulatorisch) |
| **D4** Prosodie & Suprasegmentalia | Parselmouth-Features, Rhythmusmetriken |
| **D5** Textbasierte Diagnostik | spaCy + LanguageTool, CAF-Dimensionen |
| **D6** Diagnostisches Scoring | 5-Schichten-Modell, Radar-Profil, CEFR-Mapping |
| **D7** Generatives Coaching | LLM-Feedback-Pipeline, Guardrails, Übungsgenerierung |

---

*Nächstes Dokument: **B2 – Schnittstellenverträge & Datenformate** → Exakte Spezifikation der Domänenübergänge*
