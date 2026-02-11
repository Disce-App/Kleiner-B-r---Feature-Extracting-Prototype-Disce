# Gamma-Recherche: Domäne 2 – Phonetisches Alignment & Segmentierung

> **Leitfrage:** *Wort- und phonemgenaue Zuordnung zum Audiosignal – welche Open-Source-Bausteine existieren, die wir morgen deployen können?*

---

## 1. Primärer Kandidat: Montreal Forced Aligner (MFA)

| Dimension | Details |
|---|---|
| **Name & Typ** | Montreal Forced Aligner (MFA) 3.x |
| **Quelle** | McGill University – [github.com/MontrealCorpusTools/Montreal-Forced-Aligner](https://github.com/MontrealCorpusTools/Montreal-Forced-Aligner) · Lizenz: MIT |
| **Architektur** | Kaldi-basiert (GMM-HMM): Monophone → Triphone → Speaker-Adapted Triphone. Iteratives Training mit MFCC-Features + fMLLR Speaker Adaptation |
| **Deutsch-Tauglichkeit** | ✅ Pretrained German Acoustic Model + German MFA Dictionary verfügbar via `mfa model download` |
| **Lerner-Tauglichkeit** | ⚠️ Auf native Sprecher trainiert. L2-Akzente führen zu Alignment-Degradation (siehe Forschung unten). Adapter/Retraining auf L2-Daten möglich |
| **Granularität** | **Wort-Level + Phonem-Level** – direkte Modellierung von Wörtern als Phonem-Sequenzen |
| **Output-Format** | Praat TextGrid (Wort-Tier + Phonem-Tier mit exakten Zeitstempeln) |
| **G2P** | Integriertes Grapheme-to-Phoneme (Pynini-basiert). Kann OOV-Wörter automatisch phonetisieren |
| **Compute** | CPU-fähig, moderate Anforderungen. Parallelisierung über Kaldi |
| **Reife** | Production-Grade für Forschung. Aktive Weiterentwicklung (v3.x). De-facto-Standard in Corpus Phonetics |
| **Limitationen** | Benötigt Pronunciation Dictionary; G2P-Qualität variiert; L2-Sprache ist systematisch schlechter alignt; Installation via Conda kann tricky sein |

**Disce-Einschätzung:** MFA ist der **primäre Alignment-Kandidat** für Disce. Es liefert sowohl Wort- als auch Phonem-Zeitstempel, die direkt in Domäne 3 (Pronunciation Scoring via GOP) und Domäne 4 (Prosodie via Praat) einfließen. Die GMM-HMM-Architektur ist für Forced Alignment nachweislich genauer als End-to-End-Modelle.

**Benchmark-Referenz:** In einer direkten Vergleichsstudie (Chodroff et al., 2024, Interspeech/arXiv) auf TIMIT und Buckeye übertraf MFA sowohl WhisperX als auch MMS in der Alignment-Genauigkeit auf Wort- und Phonem-Ebene. Die Studie zeigt: klassische GMM-HMM-Modelle sind für Forced Alignment weiterhin State-of-the-Art.

---

## 2. Sekundäre Kandidaten

### 2.1 WhisperX (wav2vec2-basiertes Alignment)

| Dimension | Details |
|---|---|
| **Name & Typ** | WhisperX – Whisper + wav2vec2 Forced Alignment |
| **Quelle** | Max Bain (University of Oxford) – [github.com/m-bain/whisperX](https://github.com/m-bain/whisperX) · Lizenz: BSD-4 |
| **Architektur** | Pipeline: Whisper (ASR) → VAD (pyannote) → wav2vec2.0 (CTC Forced Alignment) → Speaker Diarization |
| **Deutsch-Tauglichkeit** | ✅ Deutsch unterstützt via `jonatasgrosman/wav2vec2-large-xlsr-53-german` oder ähnliche HuggingFace-Modelle (`--language de`) |
| **Lerner-Tauglichkeit** | ⚠️ wav2vec2-Modelle auf native Sprecher trainiert. Gleiche L2-Problematik wie MFA |
| **Granularität** | **Wort-Level** (primär). Phonem-Level nur indirekt über wav2vec2-Alignments |
| **Output-Format** | JSON/SRT mit Wort-Zeitstempeln, optional Character-Level |
| **Compute** | GPU empfohlen (wav2vec2 + Whisper). Batch-Inference möglich |
| **Reife** | Weit verbreitet, aber primär als ASR-Postprocessing konzipiert, nicht als phonetisches Präzisionswerkzeug |
| **Limitationen** | Alignment-Genauigkeit hinter MFA (benchmark-belegt). Wörter ohne Dictionary-Zeichen (Zahlen, Sonderzeichen) werden nicht alignt. Keine native Phonem-Segmentierung |

**Disce-Einschätzung:** WhisperX ist **nicht der primäre Aligner**, aber strategisch wertvoll als **schnelle Wort-Level-Alignment-Schicht** in der Echtzeit-Pipeline (z.B. für Fluency-Metriken wie Pausenanalyse, Sprechrate). Die Integration mit dem Whisper-ASR-Output aus Domäne 1 ist nahtlos. Für phonetische Präzision (GOP, Mispronunciation Detection) reicht WhisperX allein nicht.

---

### 2.2 WebMAUS / BAS Web Services (Uni München)

| Dimension | Details |
|---|---|
| **Name & Typ** | WebMAUS (Munich Automatic Segmentation System) |
| **Quelle** | Bavarian Archive for Speech Signals (BAS), LMU München – [bas.uni-muenchen.de](https://www.bas.uni-muenchen.de/Bas/BasMAUS.html) · Lizenz: Frei für Forschung, API-Nutzung |
| **Architektur** | Hybrid: HMM + probabilistische Ausspracheregel-Modelle. Statistisch abgeleitete Aussprache-Varianten aus deutschen Korpora |
| **Deutsch-Tauglichkeit** | ✅✅ **Exzellent** – originär für Deutsch entwickelt. Unterstützt auch schweizerdeutsche Dialekte. 25+ Sprachen insgesamt |
| **Lerner-Tauglichkeit** | ⚠️ Auf native Sprecher optimiert, aber probabilistisches Aussprachemodell könnte mit L2-Varianten besser umgehen als rein lexikonbasierte Systeme |
| **Granularität** | **Wort-Level + Phonem-Level** (SAMPA/IPA). Optional: Silbenstruktur |
| **Output-Format** | Praat TextGrid, BAS Partitur Format (BPF), Emu |
| **Varianten** | WebMAUS Basic (Text + Audio), WebMAUS General (BPF + Audio), WebMAUS MINNI (nur Audio, keine Transkription nötig!) |
| **Compute** | Cloud-basiert (Web-Service) oder lokale Installation möglich |
| **Reife** | Production-Grade. 20+ Jahre Entwicklung. In Evaluierungen für Schweizer Parlamentssprache beste Boundary-Precision unter allen Alignern |
| **Limitationen** | Cloud-Variante = Datenschutz-Problem für Disce (Audio an externen Server). Lokale Installation aufwendiger. API-Rate-Limits |

**Disce-Einschätzung:** WebMAUS ist **die Referenz für deutsches Phonem-Alignment** und liefert die höchste Qualität für native deutsche Sprache. Für Disce problematisch: Die Cloud-Variante verletzt das Souveränitätsprinzip (Audio-Daten verlassen die EU-Infrastruktur nicht kontrolliert). Eine **lokale MAUS-Installation** auf dem eigenen EU-GPU-Cluster wäre ideal, ist aber aufwendiger als MFA. WebMAUS MINNI (alignment ohne Text) könnte als Verification-Layer interessant sein.

---

### 2.3 torchaudio CTC Forced Alignment (MMS_FA / Wav2Vec2FABundle)

| Dimension | Details |
|---|---|
| **Name & Typ** | torchaudio Forced Alignment API + MMS_FA Pipeline |
| **Quelle** | PyTorch / Meta – [pytorch.org/audio](https://docs.pytorch.org/audio/stable/tutorials/forced_alignment_tutorial.html) · Lizenz: BSD |
| **Architektur** | wav2vec2.0-basiertes CTC-Alignment. `MMS_FA` Bundle: multilinguales Alignment-Modell (1.130 Sprachen, trainiert auf 31K Stunden) |
| **Deutsch-Tauglichkeit** | ✅ Deutsch inkludiert im multilingualen MMS_FA-Modell |
| **Lerner-Tauglichkeit** | ⚠️ Multilinguales Training könnte bei L2-Sprechern robuster sein als monolinguale Modelle (Hypothese, nicht validiert) |
| **Granularität** | **Character-Level** (Buchstaben-Alignment). Phonem-Level nur über Mapping |
| **Output-Format** | Python Tensors (Frame-Level Scores + Alignment-Pfade). Custom Post-Processing nötig |
| **Compute** | GPU-optimiert. Effiziente GPU-basierte Alignment-Implementierung |
| **Reife** | Stabil als API, aber torchaudio geht in Maintenance-Phase (ab v2.8). Migration zu TorchCodec angekündigt |
| **Limitationen** | Character-Level ≠ Phonem-Level (für Deutsche Sprache mit nicht-transparenter Orthographie problematisch). Weniger phonetische Granularität als MFA/WebMAUS. Maintenance-Phase |

**Disce-Einschätzung:** Strategisch als **Fallback/Ergänzung** relevant, besonders wegen des multilingualen MMS-Modells. Für Disce weniger geeignet als Primärlösung, da Character-Level-Alignment nicht direkt Phonem-Boundaries liefert. Könnte aber für schnelles "grobes" Alignment in der Echtzeit-Pipeline nützlich sein. Achtung: torchaudio Maintenance-Phase beobachten.

---

### 2.4 Kaldi-DNN-Ali-GOP (Forced Alignment + GOP)

| Dimension | Details |
|---|---|
| **Name & Typ** | kaldi-dnn-ali-gop – Forced Alignment & Goodness of Pronunciation |
| **Quelle** | [github.com/tbright17/kaldi-dnn-ali-gop](https://github.com/tbright17/kaldi-dnn-ali-gop) · Lizenz: Apache 2.0 |
| **Architektur** | Kaldi nnet3 (DNN-HMM). Kombiniert Forced Alignment mit GOP-Berechnung in einem Schritt |
| **Deutsch-Tauglichkeit** | ⚠️ Kein deutsches Modell mitgeliefert. Training mit deutschem Acoustic Model nötig |
| **Lerner-Tauglichkeit** | ✅ Explizit für L2-Pronunciation-Evaluation entwickelt. Phoneme Confusion Matrix auf Frame- und Segment-Level |
| **Granularität** | **Phonem-Level** + GOP-Scores pro Phonem |
| **Output-Format** | TextGrid (Alignment) + GOP-Textdatei |
| **Compute** | CPU (Kaldi-Inference ist CPU-basiert) |
| **Reife** | Research-Grade. Funktional, aber wenig Maintenance |
| **Limitationen** | Kaldi-Abhängigkeit (komplexe Installation). Kein Deutsch out-of-the-box. Wenig aktive Weiterentwicklung |

**Disce-Einschätzung:** **Brücke zwischen Domäne 2 und Domäne 3.** Dieses Tool liefert Alignment + Pronunciation Scoring in einem Durchlauf. Wenn Disce ein eigenes deutsches Kaldi-Modell trainiert (mit L2-Daten), wird dieses Tool zum Kern der Aussprache-Pipeline. Kurz- bis mittelfristig jedoch hoher Integrationsaufwand.

---

### 2.5 SPPAS (Automatic Phonetic Annotation)

| Dimension | Details |
|---|---|
| **Name & Typ** | SPPAS – Automatic Annotation and Analysis of Speech |
| **Quelle** | Brigitte Bigi, LPL Aix-en-Provence – [sppas.org](https://sppas.org) · Lizenz: AGPL v3 |
| **Architektur** | Dictionary-basierte Phonetisierung + Julius Engine (Grammar-based HMM) |
| **Deutsch-Tauglichkeit** | ⚠️ Nicht primär für Deutsch. Fokus auf Französisch, Englisch, Chinesisch u.a. |
| **Granularität** | Wort → Phonem → Silben-Segmentierung |
| **Reife** | Stabil, akademisch breit genutzt |
| **Limitationen** | Kein Deutsch-Modell out-of-the-box. Julius-Engine weniger genau als Kaldi/MFA. AGPL-Lizenz problematisch für kommerzielle Nutzung |

**Disce-Einschätzung:** Nicht empfohlen als primäres Tool. AGPL-Lizenz und fehlende Deutsch-Unterstützung disqualifizieren SPPAS für Disce.

---

### 2.6 Gentle (Kaldi TDNN-basiert)

| Dimension | Details |
|---|---|
| **Name & Typ** | Gentle – Robust yet Lenient Forced Aligner |
| **Quelle** | [github.com/strob/gentle](https://github.com/strob/gentle) · Lizenz: MIT |
| **Architektur** | Kaldi TDNN (Time-Delay Neural Network), trainiert auf Fisher English (ASpIRE Recipe) |
| **Deutsch-Tauglichkeit** | ❌ Nur Englisch |
| **Reife** | Stabil, Docker-ready, aber wenig aktive Weiterentwicklung |
| **Limitationen** | Nur Englisch. Kein Phonem-Level-Output |

**Disce-Einschätzung:** Nicht relevant für Disce (kein Deutsch).

---

## 3. Emerging / Beobachten

### 3.1 Meta MMS Alignment Model

Meta hat im Rahmen des MMS-Projekts ein **multilinguales Alignment-Modell** (31K Stunden, 1.130 Sprachen) open-sourced, zusammen mit einem effizienten GPU-basierten Forced-Alignment-Algorithmus. Dieses Modell ist über `fairseq` verfügbar und wird auch in `torchaudio.pipelines.MMS_FA` genutzt.

**Disce-Relevanz:** Langfristig interessant als multilingualer Alignment-Backbone. Aktuell jedoch: Character-Level (nicht Phonem-Level), und die Granularität reicht für phonetische Diagnostik nicht aus. Beobachten für zukünftige Versionen.

### 3.2 Deep-Learning-basierte Aligner (Trainable)

Neuere Ansätze trainieren End-to-End-Alignment-Modelle auf manuell annotierten Daten (z.B. für Kind-Sprache oder L2-Sprache). Diese zeigen vielversprechende Ergebnisse, sind aber noch forschungsnah und benötigen annotierte Trainingsdaten.

**Disce-Relevanz:** Wenn Disce eigene annotierte L2-Deutsch-Alignment-Daten sammelt (ab MVP), könnte ein trainierter Aligner mittelfristig die MFA-Lösung ergänzen oder ablösen.

---

## 4. Architektur-Entscheidungsbaum

```
Audio + Transkript (aus Domäne 1)
       │
       ├─── Deployment-Kontext?
       │
  Server/Batch          Echtzeit/Streaming
       │                      │
   MFA 3.x              WhisperX
  (Phonem +             (Wort-Level
   Wort-Level)           schnell)
       │                      │
       │              ┌───────┴────────┐
       │              │                │
       │         Wort-Timing      Pausen-
       │         für Fluency      Analyse
       │                          Filler
       │
  ┌────┴─────┐
  │          │
Phonem-    Wort-
Timestamps  Timestamps
  │          │
  ▼          ▼
Domäne 3:  Domäne 4:
GOP /      Prosodie
Aussprache (Praat/
           Parselmouth)
```

---

## 5. L2-Alignment: Das zentrale Problem

### Warum ist Forced Alignment bei L2-Sprechern problematisch?

Alle Alignment-Tools sind auf **native Sprachmodelle** trainiert. L2-Sprecher erzeugen systematische Abweichungen:

1. **Phonem-Substitutionen:** L1-Transfer führt zu Lauten, die im deutschen Phonem-Inventar nicht existieren (z.B. türkische Sprecher: /ø/ → /o/, arabische Sprecher: /ç/ → /ʃ/)
2. **Epenthese/Tilgung:** Einschub oder Wegfall von Lauten, die das Alignment-Modell nicht erwartet
3. **Prosodie-Abweichungen:** Unerwartete Betonungsmuster, die die HMM-State-Transitions stören
4. **Coarticulation-Muster:** Andere Koartikulation als in nativen Trainingsdaten

### Empirische Evidenz (Studie: ScienceDirect, 2024)

Eine Studie mit dem MFA auf L2-Englisch-Sprechern (9 L1-Hintergründe) zeigte:
- Signifikant höhere Boundary-Fehler bei L2 vs. L1
- Fehler korrelieren mit Akzentstärke und L1-Distanz
- Besonders problematisch: Konsonanten-Cluster, die in der L1 nicht existieren

### Disce-Strategie für L2-Alignment

| Phase | Ansatz |
|---|---|
| **MVP (sofort)** | MFA mit nativem German Model. Akzeptiere höhere Fehlerrate bei L2. Post-hoc Verification: Alignment-Konfidenz berechnen, niedrige Konfidenz flaggen |
| **Phase 1 (nach 1.000+ Sessions)** | MFA Speaker Adaptation (`mfa adapt`) mit gesammelten L2-Daten. Evaluation gegen manuelle Annotationen |
| **Phase 2 (nach 5.000+ Sessions)** | Training eines L2-spezifischen Acoustic Models. Optional: Multi-L1 Modelle (Türkisch-L1, Arabisch-L1, etc.) |
| **Langfristig** | Eigener Deep-Learning-Aligner, trainiert auf Disce-Annotationsdaten |

---

## 6. Relevante Forschung

| Paper / Projekt | Relevanz |
|---|---|
| *Tradition or Innovation: A Comparison of Modern ASR Methods for Forced Alignment* (Chodroff et al., arXiv 2024) | Direkter Vergleich MFA vs. WhisperX vs. MMS. MFA gewinnt auf Wort- und Phonem-Level |
| *Analysis of forced aligner performance on L2 English speech* (ScienceDirect, 2024) | Empirische Evaluation von MFA auf L2-Sprechern. Zeigt systematische Degradation und L1-spezifische Fehlerprofile |
| *How Does Alignment Error Affect Automated Pronunciation Scoring in Children's Speech?* (Interspeech 2024) | Zeigt direkten Impact von Alignment-Fehlern auf GOP-Scores. Relevant für Disce Domäne 3 |
| *CTC-Segmentation of Large Corpora for German End-to-End Speech Recognition* (Kürzinger et al.) | Grundlage des torchaudio CTC-Alignment-Tutorials. Deutsch-spezifisch |
| *Scaling Speech Technology to 1,000+ Languages* (Pratap et al., 2023) | Meta MMS Paper. Beschreibt das multilinguale Alignment-Modell |
| *Phonological Level wav2vec2-based Mispronunciation Detection* (arXiv, 2023) | Verbindung von wav2vec2-Alignment und Mispronunciation Detection. Brücke D2→D3 |
| *Evaluation of Three Automatic Alignment Tools for the Processing of Non-native French* (ResearchGate, 2025) | Evaluation von Alignment-Tools auf L2-Sprache (Französisch). Methodik übertragbar |
| *Strunk, Schiel, Seifart (2014): Untrained Forced Alignment with WebMAUS* | Zeigt, dass WebMAUS auch ohne sprachspezifisches Training akzeptable Ergebnisse liefert |

---

## 7. Tool-Empfehlung für Disce

### Primärstack (MVP → Phase 1)

| Schicht | Tool | Zweck |
|---|---|---|
| **Phonem-Alignment** | MFA 3.x (German Model) | Phonem- und Wort-Zeitstempel für Pronunciation Scoring (→ Domäne 3) |
| **Schnell-Alignment** | WhisperX (wav2vec2) | Wort-Zeitstempel für Fluency-Metriken (→ Domäne 4) |
| **Verification** | Alignment-Konfidenz-Scores | Niedrige Konfidenz → manuelle Überprüfung / Datensammlung |

### Langfrist-Vision (Phase 2+)

| Schicht | Tool | Zweck |
|---|---|---|
| **Phonem-Alignment** | MFA mit L2-adaptiertem Acoustic Model | Höhere Genauigkeit bei Lerner-Sprache |
| **GOP** | Kaldi-DNN-Ali-GOP mit deutschem Modell | Integriertes Alignment + Pronunciation Scoring |
| **Verification** | WebMAUS (lokal) | Zweitmeinung / Qualitätssicherung |

---

## 8. Integration in die Disce-Pipeline

```
┌─────────────────────────────────────────────────────┐
│ Domäne 1: Whisper ASR                                │
│ Output: Transkript + Wort-Zeitstempel (grob)         │
└──────────────┬──────────────────────────────────────┘
               │
               ▼
┌─────────────────────────────────────────────────────┐
│ Domäne 2: Phonetisches Alignment                     │
│                                                       │
│  ┌──────────┐    ┌──────────────┐                    │
│  │ WhisperX │    │  MFA 3.x     │                    │
│  │ (schnell) │    │ (präzise)    │                    │
│  │ Wort-Level│    │ Phonem-Level │                    │
│  └────┬─────┘    └──────┬───────┘                    │
│       │                 │                             │
│       │    ┌────────────┘                             │
│       │    │                                          │
│       ▼    ▼                                          │
│  ┌─────────────────┐                                 │
│  │ Alignment-       │                                 │
│  │ Confidence-      │                                 │
│  │ Score            │                                 │
│  └────────┬────────┘                                 │
│           │                                           │
└───────────┼───────────────────────────────────────────┘
            │
     ┌──────┴──────┐
     │             │
     ▼             ▼
┌─────────┐  ┌──────────┐
│ Domäne 3│  │ Domäne 4 │
│ GOP /   │  │ Prosodie │
│Aussprache│  │ Praat    │
└─────────┘  └──────────┘
```

---

## 9. Kritische Handlungsfelder

1. **L2-Adaptation ist nicht optional:** Ohne Anpassung des Acoustic Models an Lerner-Sprache werden Alignment-Fehler systematisch die GOP-Scores in Domäne 3 verfälschen. Die Studie (Interspeech 2024) zeigt: Alignment-Fehler propagieren direkt in Pronunciation Scores.

2. **Pronunciation Dictionary für DaF/DaZ:** Das Standard-MFA-Dictionary für Deutsch enthält nur kanonische Aussprachevarianten. Für L2-Diagnostik brauchen wir ein **erweitertes Dictionary mit typischen L2-Aussprachevarianten** (z.B. /ç/ → [ʃ] als akzeptierte Variante für L1-Arabisch).

3. **Alignment-Evaluation-Pipeline:** Vor Produktiveinsatz müssen alle Alignment-Tools mit echtem Lerner-Audio evaluiert werden. Manuelle Annotation eines Gold-Standard-Korpus (50-100 Utterances, diverse L1-Hintergründe) ist essentiell.

4. **WebMAUS-Souveränität:** WebMAUS Cloud-API ist datenschutzrechtlich problematisch. Lokale Installation prüfen oder als Offline-Evaluation-Tool nutzen (nicht in Echtzeit-Pipeline).

5. **Dual-Alignment-Strategie:** WhisperX für Echtzeit-Fluency, MFA für Batch-Phonetik. Beide Pfade müssen aufeinander abgestimmt sein (konsistente Zeitachse).

---

*Nächster Schritt: Domäne 3 – Aussprache-Bewertung (Pronunciation Scoring)*
