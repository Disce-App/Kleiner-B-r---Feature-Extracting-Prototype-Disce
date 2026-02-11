# Gamma-Inventur — Domäne 3: Aussprache-Bewertung (Pronunciation Scoring)

**Status:** ✅ Recherche abgeschlossen  
**Datum:** 2026-02-11  
**Gamma-Kernfrage:** Phonem-Accuracy, Mispronunciation Detection, Goodness of Pronunciation – welche Open-Source-Bausteine existieren für deutsches L2-Audio?

---

## 1. Kernkonzept: Goodness of Pronunciation (GOP)

Der Goldstandard der phonem-basierten Aussprachebewertung ist der **Goodness of Pronunciation (GOP)**-Score, erstmals von Witt & Young (2000) definiert.

### Formel

```
GOP(p) = 1/(t_e - t_s + 1) * log p(p|o)
```

Die Posterior-Wahrscheinlichkeit wird approximiert als:

```
log p(p|o) ≈ log [ p(o|p) / Σ_q p(o|q) ]
```

- **Zähler**: Likelihood aus dem Forced Alignment (kanonische Phonem-Sequenz)
- **Nenner**: Maximum-Likelihood aus einem freien Phone-Loop (Viterbi-Decoding)
- **Ergebnis**: Je negativer der Score, desto weiter weicht die Aussprache vom Zielphon ab

### Kaldi-Implementierung

Die offizielle Kaldi-Implementierung nutzt ein **nnet3 TDNN (no-chain)** Modell, da Chain-Modelle durch ihre HMM-Topologie schlechte GOP-Ergebnisse liefern. Das offizielle Kaldi-Recipe `gop_speechocean762` dient als Baseline-System.

---

## 2. State-of-the-Art Ansätze

### 2.1 Klassischer Pipeline-Ansatz (GOP-basiert)

```
Audio → Feature-Extraktion (MFCC/Fbank) → Akustisches Modell (DNN/TDNN) 
→ Forced Alignment + Phone-Loop Decoding → GOP Score pro Phonem
```

| Dimension | Details |
|---|---|
| **Vorteile** | Interpretierbar, gut verstanden, funktioniert mit Kaldi out-of-the-box |
| **Nachteile** | Stark abhängig von Qualität des Akustik-Modells; Forced Alignment kann bei L2-Speech fehlschlagen; keine kontextuellen Features |
| **Tooling** | Kaldi `gop_speechocean762`, `kaldi-dnn-ali-gop` |

---

### 2.2 GOPT – Transformer auf GOP-Features (ICASSP 2022)

| Dimension | Details |
|---|---|
| **Name & Typ** | GOPT – Goodness Of Pronunciation Feature-Based Transformer |
| **Quelle** | Yuan Gong et al. (MIT & PAII) · [github.com/YuanGongND/gopt](https://github.com/YuanGongND/gopt) · Lizenz: MIT |
| **Architektur** | Kaldi GOP-Features → Transformer Encoder → Multi-Head Regression |
| **Besonderheit** | Erstes Modell, das **multi-aspekt** (Accuracy, Fluency, Prosody) und **multi-granular** (Phonem, Wort, Satz) gleichzeitig bewertet |
| **Benchmark (SpeechOcean762)** | Phonem-PCC: 0.612 · Wort-PCC: 0.549 · Satz-PCC: 0.742 — jeweils SotA zum Zeitpunkt der Veröffentlichung |
| **Pipeline** | Kaldi GOP-Features extrahieren → GOPT-Modell → Multi-Aspekt Scores |
| **Reproduzierbarkeit** | Kaldi-Zwischenoutputs werden mitgeliefert → Reproduktion ohne Kaldi möglich (1-Click oder Google Colab) |
| **Limitationen** | Kaldi-Abhängigkeit für Feature-Extraktion; nur Englisch trainiert; kein Deutsch out-of-the-box |

**Disce-Einschätzung:** GOPT ist die **architektonische Blaupause** für Disces Multi-Aspekt-Scoring. Die Transformer-Architektur auf GOP-Features ist direkt übertragbar, wenn ein deutsches Akustik-Modell für die GOP-Berechnung vorliegt.

---

### 2.3 SSL-basierte Ansätze (wav2vec2 / HuBERT)

| Dimension | Details |
|---|---|
| **Ansatz** | Self-Supervised Learning (SSL) Modelle, fine-tuned auf L2-Pronunciation-Assessment |
| **Architektur** | wav2vec2.0 oder HuBERT → CTC Fine-Tuning auf L2-Daten → Layer-wise Embeddings → Scoring Head |
| **Deutsch-Tauglichkeit** | ✅ wav2vec2-XLSR-53 und XLS-R sind multilingual (inkl. Deutsch) |
| **Performance** | Übertrifft klassische GOP-Baselines auf Speechocean762 und KESL-Datensätzen |
| **Vorteile** | Kein explizites Forced Alignment nötig; robuster bei akzentierter Sprache; weniger Daten für Fine-Tuning nötig dank SSL Pre-Training |
| **Nachteile** | Weniger interpretierbar als GOP; GPU-intensiver; noch keine standardisierte Pipeline |

**Disce-Einschätzung:** SSL-basierte Pronunciation Assessment ist der **zukunftsweisende Ansatz** und wird mittelfristig die klassischen GOP-Methoden ablösen. Für Disce besonders attraktiv, weil die multilingualen Modelle (XLSR/XLS-R) bereits Deutsch-Repräsentationen enthalten und das Fine-Tuning auf eigene L2-Daten mit relativ wenig Daten möglich ist.

---

### 2.4 Mispronunciation Detection & Diagnosis (MDD)

#### Phonem-Level MDD

| Dimension | Details |
|---|---|
| **Ansatz** | wav2vec2 + CTC für End-to-End Phonem-Erkennung, Vergleich mit kanonischer Transkription |
| **Performance** | State-of-the-Art MDD auf L2-Englisch-Korpora |
| **Limitationen** | Erkennt nur *welches* Phonem falsch ist, nicht *wie* es falsch ist |

#### Artikulatorisches MDD (Speech-Attribute-basiert)

| Dimension | Details |
|---|---|
| **Ansatz** | wav2vec2 als Backbone → Speech Attribute Detection (Manner + Place of Articulation) → Abweichungsanalyse |
| **Quelle** | arXiv 2311.07037 |
| **Vorteile** | Erkennt nicht nur Fehler, sondern gibt detaillierte artikulatorische Beschreibung (z.B. „Zunge zu weit vorn", „Stimmhaftigkeit fehlt") |
| **Performance** | Signifikant niedrigere FAR, FRR und DER als phonem-basiertes MDD |
| **Deutsch-Relevanz** | Besonders wertvoll für DaF-Diagnostik: L1-spezifische artikulatorische Transferfehler können systematisch beschrieben werden |

**Disce-Einschätzung:** Artikulatorisches MDD ist der **Differenzierungshebel** für Disce. Kein kommerzieller Anbieter (auch nicht Azure) bietet artikulatorische Fehlerdiagnose. Wenn Disce „Der Laut /ç/ wurde als [ʃ] realisiert – die Zungenposition ist zu weit hinten" sagen kann, ist das ein Alleinstellungsmerkmal.

---

### 2.5 Unified CAPT: JAM (Joint APA + MDD, 2024/2025)

| Dimension | Details |
|---|---|
| **Name & Typ** | JAM – Joint neural model for APA and MDD |
| **Quelle** | APSIPA ASC 2024 (IEEE) |
| **Architektur** | End-to-End Modell mit paralleler Pronunciation Modeling Architecture |
| **Besonderheit** | Vereint APA (Automatic Pronunciation Assessment) und MDD in einer Architektur |
| **Innovation** | Nutzt EMA (Electromagnetic Articulography) Features für feinere artikulatorische Cues |
| **Benchmark** | Evaluiert auf SpeechOcean762 |
| **Reife** | Forschung (2024). Noch kein öffentliches Repo bekannt |

**Disce-Einschätzung:** JAM zeigt die Richtung: **Assessment + Diagnose müssen zusammenwachsen**. Disces Alpha-Capability sollte genau das sein: ein integriertes System, das gleichzeitig bewertet und diagnostiziert.

---

### 2.6 Align-Free / Segmentation-Free GOP

| Dimension | Details |
|---|---|
| **Ansatz** | GOP-Berechnung ohne explizites Forced Alignment |
| **Varianten** | GOP-SA (Self-Aligned): CTC-Aktivierungen als Segmente · GOP-SF (Segmentation-Free): GOP-Definition unabhängig von Segmentierung |
| **CTC-basiert** | Nutzt `wav2vec2-xlsr-53-espeak-cv-ft` (HuggingFace) als multilinguales Phonem-Modell |
| **Vorteile** | Eliminiert die Fehlerquelle Forced Alignment; robuster bei stark abweichender L2-Aussprache |
| **Quelle** | arXiv 2506.12067 (2025) |

**Disce-Einschätzung:** Hochrelevant für Disce, weil es die **größte Schwachstelle der klassischen Pipeline** (Alignment-Fehler bei L2-Sprechern propagieren in GOP-Scores) adressiert. Mittelfristig sollte Disce auf Align-Free GOP migrieren.

---

### 2.7 Universeller Phonem-Recognizer: Allosaurus

| Dimension | Details |
|---|---|
| **Name & Typ** | Allosaurus – Universal Phone Recognition |
| **Quelle** | Xinjian Li et al. (CMU) · [github.com/xinjli/allosaurus](https://github.com/xinjli/allosaurus) · Lizenz: Apache 2.0 |
| **Architektur** | Multilingualer Allophone-System, trainiert auf 2000+ Sprachen |
| **Deutsch-Tauglichkeit** | ✅ Deutsch als eine der unterstützten Sprachen |
| **Pronunciation Assessment** | Wird in der Deutsch-spezifischen CAPT-Studie (Mehta et al., HCII 2025) eingesetzt: Siamese Model + Allosaurus → 74% Accuracy auf Deutsch-L2 |
| **Output** | Phonem-Sequenz (IPA) mit Zeitstempeln |
| **Vorteile** | Kein sprachspezifisches Training nötig; erkennt Phones, die im Zielinventar nicht existieren (L1-Transfer-Phones!) |
| **Limitationen** | Accuracy unter sprachspezifischen Modellen; kein Fine-Tuning auf L2-Deutsch verfügbar |

**Disce-Einschätzung:** Allosaurus ist der **schnellste Weg zu einem funktionierenden Pronunciation Assessment für Deutsch** im MVP. Die Kombination mit einem Siamese Network für den Vergleich Lerner vs. Referenz ist direkt einsetzbar. Langfristig wird ein fine-tuned wav2vec2 genauer sein.

---

### 2.8 Deutsch-spezifisches CAPT-System (HCII 2025)

| Dimension | Details |
|---|---|
| **Titel** | AI-Based Pronunciation Assessment and Grammatical Error Correction with Feedback for the German Language |
| **Quelle** | Mehta, Roth, Munteanu, Chandna (2025) · HCII 2025, Springer LNCS Vol. 15820 |
| **Architektur** | Modul 1: Siamese Network + Allosaurus → Pronunciation Assessment (74% Accuracy) · Modul 2: mT5 → Grammatikkorrektur |
| **Deutsch-Tauglichkeit** | ✅✅ Explizit für Deutsch-L2 entwickelt |
| **Feedback** | Detailliertes Feedback zu Phonem-Mismatches und Ähnlichkeiten |
| **Reife** | Forschungsprototyp (2025) |

**Disce-Einschätzung:** Das **direktrelevanteste Paper** für Disce. Zeigt, dass ein funktionierendes Deutsch-CAPT-System mit Open-Source-Komponenten (Allosaurus + Siamese) machbar ist. Die 74% Accuracy ist ein realistischer Startpunkt für ein MVP.

---

## 3. Benchmark: SpeechOcean762

| Eigenschaft | Detail |
|---|---|
| **Utterances** | 5.000 englische Sätze |
| **Sprecher** | 250 nicht-muttersprachliche (L1: Mandarin) |
| **Demografie** | 50% Kinder, 50% Erwachsene |
| **Annotationen** | 5 Experten pro Utterance, unabhängig |
| **Granularitäten** | Phonem, Wort, Satz |
| **Aspekte** | Accuracy, Stress, Fluency, Completeness, Prosody |
| **Lizenz** | CC BY 4.0 (auch kommerziell) |
| **Download** | [OpenSLR 101](https://www.openslr.org/101/) (520 MB) |
| **Kaldi-Recipe** | `egs/gop_speechocean762` |

**⚠️ Kritisch für Disce:** Es gibt **kein SpeechOcean762-Äquivalent für Deutsch**. Alle Benchmarks und Baselines sind auf Englisch. Disces eigener annotierter Deutsch-L2-Korpus wird zum strategischen Asset.

---

## 4. Konkrete Open-Source-Bausteine

| Komponente | Tool/Repo | Sprache | Lizenz | Reife |
|---|---|---|---|---|
| **GOP (klassisch)** | Kaldi `gop_speechocean762` | EN (anpassbar) | Apache 2.0 | Production |
| **GOP + Forced Alignment** | `kaldi-dnn-ali-gop` (tbright17) | EN (Librispeech AM) | Apache 2.0 | Research |
| **Multi-Aspekt Scoring** | GOPT (YuanGongND) | EN | MIT | Research+ |
| **CTC-basierter GOP** | `wav2vec2-xlsr-53-espeak-cv-ft` | Multilingual | MIT | Research+ |
| **Universeller Phonem-Recognizer** | Allosaurus (xinjli) | 2000+ Sprachen | Apache 2.0 | Research+ |
| **SSL Pronunciation Assessment** | wav2vec2 / HuBERT Fine-Tuning | Multilingual | Apache/MIT | Research |
| **Benchmark-Daten** | SpeechOcean762 | EN (L1 Mandarin) | CC BY 4.0 | Standard |

---

## 5. Vergleich: Azure Pronunciation Assessment vs. Disce Open-Source Stack

| Dimension | Azure Pronunciation Assessment | Disce Open-Source Stack |
|---|---|---|
| **Granularität** | Phonem, Wort, Satz | Phonem, Wort, Satz (via GOPT) |
| **Aspekte** | Accuracy, Fluency, Completeness, Prosody | Accuracy, Fluency, Prosody + artikulatorische Diagnose |
| **Deutsch** | ✅ Out-of-the-box | ⚠️ Muss aufgebaut werden |
| **L2-Optimierung** | Unbekannt (Black Box) | Volle Kontrolle, Fine-Tuning möglich |
| **Artikulatorisches Feedback** | ❌ Nicht verfügbar | ✅ Über Speech-Attribute MDD |
| **Souveränität** | ❌ Azure-Cloud, US-Datenverarbeitung | ✅ Self-hosted, EU-Infrastruktur |
| **Kosten** | Pay-per-use ($1/1000 Bewertungen) | Einmalig Compute (GPU) |
| **Vendor Lock-in** | ✅ Hoch | ❌ Keiner |
| **Time-to-Market** | Sofort | 2-4 Monate für MVP |
| **Content Assessment** | Retired ab SDK 1.46.0 (→ OpenAI) | Über Domäne 5 (NLP) abdeckbar |

---

## 6. Strategische Empfehlung für Disce

### Phase 1 — MVP (sofort umsetzbar)

**Allosaurus + Edit-Distance Scoring**

```
Audio → Allosaurus → Erkannte Phonem-Sequenz (IPA)
Prompt-Text → G2P (MFA Dictionary) → Kanonische Phonem-Sequenz (IPA)
→ Edit Distance (Substitution/Insertion/Deletion) → Phonem-Level Score
→ Aggregation → Wort-Level & Satz-Level Scores
```

Alternativ: `wav2vec2-xlsr-53-espeak-cv-ft` für CTC-basierte GOP-Scores ohne Kaldi-Dependency.

### Phase 2 — Verbesserung (nach 1.000+ annotierte Sessions)

**Fine-tuned wav2vec2-XLSR + GOPT-Style Transformer**

```
Audio → wav2vec2-XLSR (fine-tuned auf Deutsch-L2) → CTC GOP-Scores
→ GOPT-Transformer → Multi-Aspekt, Multi-Granular Scores
   (Accuracy, Fluency, Prosody × Phonem, Wort, Satz)
```

### Phase 3 — Differenzierung (strategischer Moat)

**Artikulatorisches MDD + L1-spezifische Fehlermodelle**

```
Audio → wav2vec2 → Speech Attribute Detection
   (Manner of Articulation, Place of Articulation, Voicing, Nasality)
→ Vergleich mit Ziel-Attributen → Artikulatorische Fehlerdiagnose
→ L1-spezifisches Feedback-Template
   (z.B. "Arabisch-L1: /ç/ → [ʃ] — Zungenposition zu weit hinten")
```

### Architektur-Entscheidungsbaum

```
Audio + Prompt-Text
       │
       ├──── Phase 1 (MVP)
       │     │
       │     ├── Allosaurus → Phonem-Erkennung
       │     │       │
       │     │       ▼
       │     │   Edit Distance vs. kanonische Phoneme
       │     │       │
       │     │       ▼
       │     └── Phonem/Wort/Satz-Scores
       │
       ├──── Phase 2
       │     │
       │     ├── wav2vec2-XLSR (fine-tuned) → CTC-GOP
       │     │       │
       │     │       ▼
       │     │   GOPT-Transformer
       │     │       │
       │     │       ▼
       │     └── Multi-Aspekt Scores
       │
       └──── Phase 3
             │
             ├── wav2vec2 → Speech Attributes
             │       │
             │       ▼
             │   Artikulatorische Diagnose
             │       │
             │       ▼
             └── L1-spezifisches Feedback
```

---

## 7. Kritische Handlungsfelder

1. **Deutsch-L2-Korpus aufbauen:** Ohne annotierten Deutsch-L2-Korpus (analog SpeechOcean762) gibt es keine Möglichkeit, Pronunciation Scoring für Deutsch zu evaluieren oder zu trainieren. Empfehlung: Ab MVP opt-in Datensammlung mit Expert-Annotation starten. Ziel: 500-1.000 Utterances mit Phonem-Level Annotation.

2. **L1-spezifische Fehlermodelle:** Verschiedene L1-Hintergründe erzeugen systematisch verschiedene Fehler. Separate Fehlermodelle für die häufigsten L1-Gruppen (Türkisch, Arabisch, Polnisch, Ukrainisch, Englisch) erhöhen Diagnose-Genauigkeit drastisch.

3. **Alignment-Fehler → Scoring-Fehler:** Wie in Domäne 2 dokumentiert, propagieren Alignment-Fehler direkt in GOP-Scores. Align-Free GOP (CTC-basiert) ist daher mittelfristig zwingend.

4. **Kein Azure-Lock-in nötig:** Die Kombination aus Allosaurus + CTC-GOP + GOPT-Transformer + Artikulatorischem MDD übertrifft Azure Pronunciation Assessment in der Diagnosetiefe – bei voller Datensouveränität.

5. **Artikulatorisches MDD als Moat:** Kein kommerzieller Anbieter bietet artikulatorische Fehlerdiagnose. Wenn Disce das als erstes für Deutsch implementiert, ist das ein verteidigbarer Wettbewerbsvorteil.

---

## 8. Relevante Forschung

| Paper / Projekt | Relevanz |
|---|---|
| *Transformer-Based Multi-Aspect Multi-Granularity Non-native English Speaker Pronunciation Assessment* (Gong et al., ICASSP 2022) | GOPT – Architektur-Blaupause für Multi-Aspekt Scoring |
| *Phonological Level wav2vec2-based Mispronunciation Detection and Diagnosis* (arXiv 2311.07037, 2023) | Speech-Attribute-basiertes MDD; wav2vec2 als Backbone; übertrifft phonem-basiertes MDD |
| *SSL-based Pronunciation Assessment* (arXiv 2204.03863, 2022) | wav2vec2 + HuBERT Fine-Tuning für Pronunciation Assessment; übertrifft GOP-Baselines |
| *JAM: Joint Multi-granularity Pronunciation Assessment and MDD* (APSIPA ASC 2024) | Unified APA+MDD Architektur; nutzt EMA-Features |
| *Evaluating Logit-Based GOP Scores for Mispronunciation Detection* (arXiv 2506.12067, 2025) | Align-Free GOP; CTC-basierte GOP-Varianten (GOP-SA, GOP-SF) |
| *AI-Based Pronunciation Assessment and Grammatical Error Correction with Feedback for the German Language* (Mehta et al., HCII 2025) | Direkt relevant: Deutsch-CAPT mit Allosaurus + Siamese Network (74% Accuracy) |
| *Automatic Pronunciation Error Detection and Feedback* (DFKI / Saarland, 2015) | L2-Fehlertypen (Substitution, Distortion); HMM-Klassifikator; 98.4% Recall, 94.6% Precision auf Phonem-Level |
| *The ISLE Corpus of Non-native Spoken English* (Menzel et al.) | Annotierter L2-Korpus (IT/DE Sprecher → EN); Phonem-Level Fehler-Annotation |
| *Universal Phone Recognition with a Multilingual Allophone System* (Li et al., ICASSP 2020) | Allosaurus – universeller Phonem-Recognizer für 2000+ Sprachen |
| *SpeechOcean762* (Zhang et al., Interspeech 2021) | Standard-Benchmark für Pronunciation Scoring |

---

*Nächster Schritt: Domäne 4 – Prosodie-Analyse (Pitch, Intensity, Rhythm)*
