# Gamma-Inventur — Domäne 1: Transkription & Spracherkennung (ASR)

**Status:** ✅ Recherche abgeschlossen  
**Datum:** 2026-02-11  
**Gamma-Kernfrage:** Welche ASR-Modelle taugen für deutsches Lerner-Audio?

---

## 1. Primärkandidaten (Top-Tier)

### 1.1 OpenAI Whisper Large-V3 / V3-Turbo

| Dimension | Details |
|---|---|
| **Name & Typ** | Whisper Large-V3 / V3-Turbo — Multilinguales ASR-Modell |
| **Quelle** | OpenAI · [github.com/openai/whisper](https://github.com/openai/whisper) · Lizenz: MIT |
| **Architektur** | Transformer Encoder-Decoder, 1,55 Mrd. Parameter |
| **Deutsch-Tauglichkeit** | ~7,4 % WER auf gemischten Benchmarks; Deutsch gehört zu den stärksten Sprachen. Trainiert auf 680.000+ Stunden multilingualer Daten (davon ~13.344 h Deutsch für ASR). |
| **Lerner-Tauglichkeit** | ⚠️ Studie (Korzekwa et al., JASA 2024) zeigt: Whisper performt bei non-nativen Akzenten schlechter als bei nativen. Zusammenhänge zwischen L1-Typologie, L2-Proficiency und WER nachgewiesen. Für L2-Deutsch-Lerner wurde beobachtet, dass Whisper Lerner-Sprache teilweise fälschlicherweise als Englisch erkennt. Whisper neigt dazu, non-native Speech zu „normalisieren" (Auto-Korrektur von Fehlern). |
| **Granularität** | Satz-/Segment-Level; Wort-Timestamps verfügbar |
| **Output-Format** | Text (mit/ohne Punctuation & Capitalization), JSON mit Timestamps, SRT/VTT |
| **Integration** | Python-API, CLI, HuggingFace Transformers, ONNX-Export möglich |
| **Compute** | Large-V3: ~10 GB VRAM (GPU) + 10 GB RAM. Turbo: deutlich leichter durch 4 statt 32 Decoder-Layer |
| **Reife** | Production-Grade |
| **Limitationen** | L2-Akzent-Bias; kein echtes Streaming out-of-the-box; Turbo-Variante schwächer bei Translation |

**Turbo-Variante:**
- 6× schneller als Large-V3 durch Reduktion der Decoder-Schichten (32 → 4)
- Minimaler Genauigkeitsverlust bei Transkription
- Translation-Performance reduziert (Translation-Daten nicht im Fine-Tuning)

---

### 1.2 Fine-tuned Whisper für Deutsch (primeline)

| Dimension | Details |
|---|---|
| **Name & Typ** | `primeline/whisper-large-v3-turbo-german` — Deutsch-optimiertes Whisper-Modell |
| **Quelle** | Florian Zimmermeister / primeLine · [HuggingFace](https://huggingface.co/primeline/whisper-large-v3-turbo-german) · Lizenz: Apache 2.0 |
| **Architektur** | Whisper Large-V3-Turbo, fine-tuned auf deutschem Datenmix |
| **Deutsch-Tauglichkeit** | ✅ **WER 2,628 %** auf deutschem ASR-Mixed-Datensatz — State-of-the-Art für Deutsch |
| **Lerner-Tauglichkeit** | ⚠️ Nicht auf L2-Sprache evaluiert; durch deutsche Optimierung möglicherweise noch stärker normalisierend bei Fehlern |
| **Granularität** | Satz-/Segment-Level; Wort-Timestamps verfügbar |
| **Output-Format** | Text, Timestamps, CTranslate2-kompatibel |
| **Integration** | HuggingFace Transformers, faster-whisper (CTranslate2), Python-API |
| **Compute** | Transkribiert 4 Min. Audio in <1 Sekunde auf RTX 4070 Laptop (GPU, FP16) |
| **Reife** | Production-Grade |
| **Limitationen** | Kein L2-Testing; möglicherweise zu stark auf native Sprecher optimiert |

**CTranslate2 / faster-whisper Variante:**
- Verfügbar als `TheChola/whisper-large-v3-turbo-german-faster-whisper`
- Direkt deploybar mit faster-whisper Framework
- INT8/FP16 Quantisierung konfigurierbar

---

### 1.3 NVIDIA NeMo Canary-1B / Canary-1B-v2

| Dimension | Details |
|---|---|
| **Name & Typ** | Canary-1B / Canary-1B-v2 — Multilinguales Multi-Task ASR+AST Modell |
| **Quelle** | NVIDIA · [HuggingFace](https://huggingface.co/nvidia/canary-1b-v2) · [NeMo Toolkit](https://github.com/NVIDIA-NeMo/NeMo) · Lizenz: NVIDIA-spezifisch (kommerziell prüfen!) |
| **Architektur** | FastConformer Encoder + Transformer Decoder, ~1 Mrd. Parameter |
| **Deutsch-Tauglichkeit** | ✅ Deutsch (de-DE) als Kernsprache; 6,67 % WER (v1) auf HuggingFace Open ASR Leaderboard. Canary-Qwen-2.5B: 5,63 % WER (Leaderboard-Spitze). |
| **Lerner-Tauglichkeit** | ⚠️ Nicht auf L2-Sprache evaluiert |
| **Granularität** | Satz-/Segment-Level; Timestamps via CTC-Hilfsmodell |
| **Output-Format** | Text mit Punctuation & Capitalization; Übersetzung EN↔DE/FR/ES |
| **Integration** | NeMo Toolkit (Python), NVIDIA Riva, HuggingFace; Streaming/Chunked-Inferenz möglich |
| **Compute** | Mind. 6 GB RAM; GPU empfohlen; Canary-1B-Flash optimiert für Speed |
| **Reife** | Production-Grade |
| **Limitationen** | Lizenz nicht Apache/MIT – kommerzielle Nutzung prüfen; NeMo-Ökosystem erforderlich; kein L2-Testing |

**Zusätzliche Varianten:**
- **Canary-1B-Flash:** Optimiert für Inferenz-Speed (32 Encoder + 4 Decoder Layers)
- **Canary-Qwen-2.5B:** Speech-Augmented LLM (SALM), Leaderboard #1 mit 5,63 % WER, aber primär Englisch
- **Canary-1B-v2:** Trainiert auf Granary-Dataset (~1 Mio. Stunden, 25 Sprachen), Noise-Robustness

---

## 2. Alternative Kandidaten

### 2.1 Wav2Vec2 XLSR-53 / XLS-R (German Fine-tunes)

| Dimension | Details |
|---|---|
| **Name & Typ** | Wav2Vec2-basierte ASR-Modelle, fine-tuned für Deutsch |
| **Quelle** | Meta/Facebook AI Research · Diverse Community-Fine-tunes · Lizenz: Apache 2.0 |
| **Architektur** | Self-supervised Pretrained Encoder + CTC Decoder |

**Verfügbare Fine-tunes:**

| Modell | WER | CER | Trainings-Daten |
|---|---|---|---|
| `jonatasgrosman/wav2vec2-large-xlsr-53-german` | 12,06 % | 2,92 % | Common Voice 6.1 |
| `wav2vec2-large-xlsr-53-german-cv9` | 9,48 % | 1,92 % | Common Voice 9.0 |
| `jonatasgrosman/wav2vec2-xls-r-1b-german` | — | — | CV 8.0 + MLS + VoxPopuli + TEDx |
| `facebook/wav2vec2-large-xlsr-53-german` | — | — | Common Voice 6.1 |

**Disce-Einschätzung:** Solide für Forschung und als Baseline, aber Whisper-Varianten überlegen in Accuracy und Ease-of-Use. Wav2Vec2-Embeddings könnten jedoch für Domäne 3 (Aussprache-Scoring) wertvoll sein.

---

### 2.2 Vosk (Offline ASR Toolkit)

| Dimension | Details |
|---|---|
| **Name & Typ** | Vosk — Offline ASR Toolkit |
| **Quelle** | Alpha Cephei · [alphacephei.com/vosk](https://alphacephei.com/vosk/) · Lizenz: Apache 2.0 |
| **Architektur** | Kaldi-basiert (DNN-HMM) |
| **Deutsch-Tauglichkeit** | ✅ Deutsches Modell verfügbar |
| **Lerner-Tauglichkeit** | ⚠️ Nicht evaluiert |
| **Granularität** | Wort-Level |
| **Output-Format** | JSON mit Wort-Timestamps, Konfidenz-Scores |
| **Integration** | Python, Java, C#, Node.js, Swift; Android/iOS SDKs |
| **Compute** | Extrem leichtgewichtig: ~50 MB Modell, läuft auf Raspberry Pi, Smartphone |
| **Reife** | Production-Grade (für embedded/offline Use Cases) |
| **Limitationen** | Deutlich geringere Genauigkeit als Whisper; kein Transformer-basiertes Modell; begrenzte Kontextmodellierung |

**Disce-Einschätzung:** Relevant für Mobile/Edge-Prototyping oder als Fallback bei Offline-Anforderungen, aber nicht als primärer ASR-Layer geeignet.

---

## 3. Emerging / Beobachten

| Modell | Notizen |
|---|---|
| **IBM Granite Speech 3.3 8B** | 5,85 % WER auf Open ASR Leaderboard; unterstützt Deutsch; 8 Mrd. Parameter — sehr groß |
| **Kyutai (Moshi) 2.6B** | Ultra-niedrige Latenz (2,5s Streaming-Start); primär Englisch, Deutsch-Support unklar |
| **Distil-Whisper** | 756M Parameter destilliert aus Whisper Large-V3; 6× schneller, <1% WER-Verlust; primär Englisch-destilliert |

---

## 4. Inferenz-Optimierung (Deployment-Layer)

| Tool | Beschreibung | Speed-Up | Quelle |
|---|---|---|---|
| **faster-whisper** | Whisper-Reimplementation via CTranslate2 | Bis 4× schneller, weniger RAM | [SYSTRAN/faster-whisper](https://github.com/SYSTRAN/faster-whisper) |
| **Distil-Whisper** | Destilliertes Whisper, 756M Parameter | 6× schneller, <1% WER-Verlust | HuggingFace |
| **Whisper-Streaming** | Real-time Streaming mit faster-whisper Backend | Self-adaptive Latency | Community |
| **whisper.cpp** | C/C++ Port von Whisper | CPU-optimiert, Edge-fähig | [ggerganov/whisper.cpp](https://github.com/ggerganov/whisper.cpp) |
| **INT8/FP16 Quantisierung** | Über CTranslate2 konfigurierbar | CPU+GPU effizient | CTranslate2 |

---

## 5. Strategische Empfehlung für Disce

### Primärempfehlung

**`primeline/whisper-large-v3-turbo-german`** via **`faster-whisper`** (CTranslate2)

- ✅ Bestes verfügbares Deutsch-ASR (WER 2,6 %)
- ✅ Apache 2.0 Lizenz (kommerziell nutzbar)
- ✅ Extrem schnelle Inferenz (<1s für 4 Min. Audio)
- ✅ Einfache Integration via Python-API
- ✅ Production-ready

### Architektur-Entscheidung

```
Audio Input (Lerner-Sprache Deutsch)
        │
        ▼
┌─────────────────────────────┐
│  Deployment-Kontext?        │
├──────────┬──────────┬───────┤
│ Server   │ Echtzeit │ Edge  │
│          │          │       │
│ primeline│ Whisper  │ Vosk  │
│ /turbo-  │ Turbo +  │ oder  │
│ german   │ Whisper- │Distil │
│ via      │Streaming │Whisper│
│ faster-  │          │       │
│ whisper  │          │       │
└────┬─────┴────┬─────┴───┬───┘
     │          │         │
     ▼          ▼         ▼
┌─────────────────────────────┐
│  Post-Processing:           │
│  L2-Fehler-Preservation     │
│  Layer                      │
└──────────────┬──────────────┘
               │
               ▼
        → Domäne 2: Alignment
        → Domäne 3: Aussprache
        → Domäne 5: NLP/Fehleranalyse
```

### Kritische Handlungsfelder

1. **L2-Akzent-Bias:** Alle Top-Modelle sind auf native Sprecher optimiert. Der ASR-Layer muss so konfiguriert werden, dass er L2-Fehler **nicht automatisch korrigiert**, sondern möglichst verbatim transkribiert. Whisper neigt zur „Normalisierung" von non-nativer Sprache.

2. **Fine-Tuning-Bedarf:** Mittelfristig muss ein Fine-Tuning auf L2-Lernersprache (Deutsch als Fremdsprache) erfolgen. Dafür werden annotierte L2-Deutsch-Korpora benötigt.

3. **Evaluation-Pipeline:** Vor Produktiveinsatz müssen alle Kandidaten mit echtem Lerner-Audio evaluiert werden (diverse L1-Hintergründe, CEFR A1–C1).

4. **Post-hoc Verification:** Alternativ zum Fine-Tuning kann ein nachgelagerter Verification Layer die ASR-Ausgabe mit dem erwarteten Prompt-Text abgleichen und Abweichungen als potenzielle Lerner-Fehler markieren.

---

## 6. Relevante Forschung

| Paper / Projekt | Relevanz |
|---|---|
| *Evaluating OpenAI's Whisper ASR: Performance analysis across diverse accents and speaker traits* (Korzekwa et al., JASA Express Letters, 2024) | Whisper-Bias bei non-nativen Akzenten; L1/L2-Zusammenhänge |
| *Whisper for L2 speech scoring* (HAL, 2024) | Whisper-Einsatz für L2-Bewertung; Probleme mit Language-Detection bei Lernern |
| *Domain Adversarial Training for German Accented Speech Recognition* (Franzreb & Polzehl, DAGA 2023) | Adversariales Training zur Verbesserung akzentrobuster ASR |
| *A Multi-Dialectal Dataset for German Dialect ASR* (Betthupferl, arXiv 2025) | Evaluations-Dataset für dialektale Robustheit deutscher ASR |
| *Graz Language Database* (IDW, 2024) | Spontansprache-ASR für österreichisches Deutsch; Dialekt-Robustheit |

---

*Nächster Schritt: Domäne 2 — Phonetisches Alignment*
