# Gamma · Domäne 4 – Prosodie & Suprasegmentalia

> **Domänenfrage:** *Gesprochenes → Intonation, Betonung, Rhythmus, Sprechrate, Pausen*
> **Gamma-Frage:** *Was existiert als Open-Source-Baustein, den wir morgen deployen können?*

---

## 1  Überblick & Abgrenzung

Die Domänen 1–3 liefern *segmentale* Informationen: Welche Wörter und Phoneme wurden gesprochen, wo liegen sie zeitlich, und wie nah ist jedes einzelne Phonem an der Referenz?  
Domäne 4 operiert auf einer anderen Ebene – der **suprasegmentalen**:

| Merkmal | Segmental (D1–D3) | Suprasegmental (D4) |
|---|---|---|
| Granularität | Phonem / Wort | Silbe → Äußerung → Diskurs |
| Akustische Korrelate | Spektrale Form, Formanten | F0, Energie, Dauer, Pausen |
| Diagnostische Rolle | „Hat der Lerner /ʃ/ statt /s/ produziert?" | „Klingt der Satz wie eine Frage? Liegt der Wortakzent richtig?" |
| Markt-Lücke | Gut abgedeckt (GOP, MDD) | Kaum adressiert – die meisten CAPT-Systeme ignorieren Prosodie |

Prosodie ist der Bereich, den die **systematische CAPT-Forschung als größte Lücke** identifiziert: Meta-Analysen zeigen, dass ASR-basierte Systeme segmentale Genauigkeit verbessern, suprasegmentale jedoch kaum (Ngo, Chen & Lai, 2024). Für uns ist das eine Chance.

---

## 2  Die vier Teilprobleme

Prosodie ist kein einzelnes Problem, sondern zerfällt in vier miteinander verwobene Schichten:

### 2.1  Pitch-Tracking (F0-Extraktion)

**Was:** Frame-weise Schätzung der Grundfrequenz (F0) aus dem Audiosignal.

**Warum zentral:** F0 ist der akustische Primärträger von Intonation (Satzmelodie), lexikalem Stress und emotionalem Ausdruck.

**Verfügbare Bausteine:**

| Tool | Methode | Lizenz | Stärke | Schwäche |
|------|---------|--------|--------|----------|
| **Praat / Parselmouth** | Autokorrelation (klassischer DSP) | GPL-2 | Gold-Standard in der Phonetik; volle Python-API via Parselmouth; F0, Intensity, Formanten, HNR, MFCC in einem Paket | Heuristik-basiert; kann bei verrauschtem L2-Audio fehlerhafte F0-Konturen erzeugen |
| **librosa.pyin** | Probabilistic YIN (DSP + HMM) | ISC | Leichtgewichtig; nativ in Python; Viterbi-Decodierung für zeitliche Glättung | Weniger robust als neuronale Tracker bei starkem Noise |
| **CREPE** | CNN auf Roh-Waveform | MIT | Höchste Pitch-Accuracy (stand 2018 ICASSP); vortrainiertes Modell sofort einsatzbereit; 360-Bin Auflösung | Kein Periodizitäts-Signal out-of-the-box; rein monophon |
| **PENN** | Erweiterte CREPE-Architektur + Viterbi-Decoder | MIT | Cross-Domain-Transfer; liefert Pitch + Periodicity gemeinsam; verschiedene Decoder-Modi (argmax, pyin, viterbi) | Neueres Projekt, kleinere Community |
| **openSMILE (eGeMAPS)** | Regelbasierter Featureset-Extraktor | Forschungslizenz (nicht kommerziell!) | 88 statische Features inkl. F0, Jitter, Shimmer, HNR, Loudness – alles in einem Vektor; wissenschaftlich breit validiert | ⚠️ **Nicht frei für kommerzielle Nutzung** → nur als Benchmark/Referenz brauchbar |

**Empfehlung für Disce:** CREPE/PENN für neuronales Pitch-Tracking + Parselmouth für klassische Features (Intensity, HNR, Formanten) als Komplementärschicht. Beide MIT/GPL-lizenziert und kommerziell nutzbar.

---

### 2.2  Pausen- und Sprechratenmessung (Fluency-Temporalia)

**Was:** Erkennung von Sprechphasen vs. Stille; Berechnung temporaler Fluency-Metriken.

**Warum zentral:** Sprechrate korreliert hoch mit L2-Proficiency. Pausen-Muster (Ort, Dauer, Häufigkeit) unterscheiden zuverlässig zwischen Niveaustufen und sind ein Kernbestandteil jeder CEFR-Fluency-Bewertung.

**Fluency-Metriken (aus der L2-Forschung):**

| Metrik | Definition | Diagnostische Aussage |
|--------|-----------|----------------------|
| Speech Rate (SR) | Silben / Gesamtzeit (inkl. Pausen) | Globales Fluency-Maß; korreliert stark mit Proficiency |
| Articulation Rate (AR) | Silben / reine Sprechzeit (ohne Pausen) | Artikulationsgeschwindigkeit unabhängig von Planung |
| Mean Length of Run (MLR) | Mittlere Silbenzahl zwischen zwei Pausen | Sprachplanungskapazität; steigt mit Niveau |
| Silent Pause Rate | Stille Pausen / Zeit | Breakdown Fluency |
| Filled Pause Rate | „äh", „ähm" / Zeit | Hesitation; L2-typisch |
| Phonation Time Ratio | Sprechzeit / Gesamtzeit | Kompaktheit der Produktion |

**Verfügbare Bausteine:**

| Tool | Methode | Lizenz | Stärke |
|------|---------|--------|--------|
| **Silero VAD** | Neuronales VAD (PyTorch) | MIT | Enterprise-Grade Qualität; >6000 Sprachen im Training; 8kHz + 16kHz; <1 ms/Frame auf CPU; liefert Sprech-Timestamps direkt |
| **WebRTC VAD** | GMM-basiert (klassisch) | BSD-3 | Ultra-leichtgewichtig; aber veraltend – viele False Positives |
| **Whisper-Timestamps** | Nebenprodukt der ASR (D1) | MIT | Wort-/Segment-Timestamps aus der Transkription selbst → gratis mitgeliefert |
| **Praat-Skripte (De Jong & Wempe)** | Intensitätsschwellen + Silbendetektion | GPL | Validiert für L2-Fluency-Forschung; misst SR, Pausen, filled pauses automatisch |

**Empfehlung für Disce:** Silero VAD als primäres Pausenerkennungs-Tool + Whisper-Timestamps als Cross-Check. Daraus lassen sich alle obigen Fluency-Metriken berechnen – rein regelbasiert, ohne weiteres ML.

---

### 2.3  Rhythmus-Metriken

**Was:** Quantifizierung des Sprechrhythmus als Verhältnis vokalischer und konsonantischer Intervall-Dauern.

**Warum zentral:** Deutsch ist eine **stress-timed** Sprache (wie Englisch, Niederländisch). L2-Lerner aus syllable-timed Sprachen (Türkisch, Spanisch, Französisch) oder mora-timed Sprachen (Japanisch) übertragen ihren L1-Rhythmus – das ist akustisch messbar und diagnostisch relevant.

**Etablierte Metriken (Grabe & Low, 2002; Ramus et al., 1999):**

| Metrik | Was sie misst |
|--------|--------------|
| **%V** | Anteil vokalischer Intervalle an der Gesamtdauer |
| **ΔC / ΔV** | Standardabweichung konsonantischer / vokalischer Intervalldauern |
| **VarcoC / VarcoV** | Ratenormalisierte Variabilität (Varco = ΔX / mean × 100) |
| **nPVI-V** | Normalized Pairwise Variability Index (vokalisch) – misst aufeinanderfolgende Dauer-Unterschiede |
| **rPVI-C** | Raw PVI (konsonantisch) |

Deutsch zeigt typischerweise hohe nPVI-V und hohe rPVI-C Werte – ein L2-Lerner, dessen Werte signifikant niedriger liegen, produziert einen zu „flachen" Rhythmus.

**Berechnung:** Alle Metriken lassen sich **rein regelbasiert** aus den Phone-Level-Timestamps (Domäne 2: MFA-Alignment) ableiten. Kein eigenes ML-Modell nötig – nur saubere Segmentierung.

**Empfehlung für Disce:** Rhythmusmetriken als downstream-Feature der MFA-Alignment-Pipeline (D2) implementieren. Input = phone-level TextGrid → Output = nPVI-V, rPVI-C, %V, VarcoC, VarcoV pro Äußerung.

---

### 2.4  Wort- und Satzakzent (Stress Detection)

**Was:** Erkennung, ob der Lerner die richtige Silbe betont (Wortakzent) und die richtigen Wörter im Satz hervorhebt (Satzakzent / Fokus).

**Warum speziell schwierig im Deutschen:**
- Wortakzent im Deutschen ist **nicht positionsfest** (anders als z. B. Französisch: letzte Silbe, oder Polnisch: vorletzte Silbe). Die betonte Silbe hängt von Morphologie, Präfixen und Lehnwort-Status ab.
- Beispiele: **ˈum**fahren (= umlenken) vs. um**ˈfah**ren (= überfahren); **ˈAn**fang vs. Stu**ˈdent** vs. Uni**ver**si**ˈtät**.
- Satzakzent markiert Fokus und Informationsstruktur – falsche Akzentsetzung kann die pragmatische Bedeutung verändern.

**Akustische Korrelate von Stress:**
- Erhöhte **F0** (Pitch)
- Erhöhte **Energie** (Intensity/Loudness)
- Verlängerte **Dauer** der betonten Silbe
- Vollere **Vokalqualität** (weniger Schwa-Reduktion)

**Verfügbare Ansätze:**

| Ansatz | Methode | Status |
|--------|---------|--------|
| **Regelbasiert** | F0-Peak + Energie-Peak + Dauer an Silben-Positionen → Vergleich mit lexikalischer Stress-Annotation (Lexikon) | Sofort umsetzbar mit Parselmouth + MFA + Aussprachelexikon |
| **Multi-Distribution DNN** (Li et al., 2018) | Silbenbasierte prosodische Features → DNN → Stress/No-Stress | Forschungsprototyp; nicht direkt als Paket verfügbar |
| **wav2vec 2.0 Probing** | SSL-Embeddings enthalten implizit Stress-Information (nachgewiesen via Probing-Experiments) | Nutzbar über finegetuntes wav2vec2 → aber kein fertiges Stress-Detection-Modell für Deutsch |
| **Sequence-to-Sequence** (Ruan et al., 2019) | Transformer-basiert: Audio → Phonemsequenz mit Stress-Markern | Nur für Englisch trainiert; kein deutsches Pendant |

**Empfehlung für Disce:** Regelbasierter Ansatz als MVP: MFA-Alignment liefert Silbengrenzen → Parselmouth extrahiert F0/Energie/Dauer pro Silbe → Vergleich mit Soll-Stress aus dem Lexikon (z. B. IPA-Lexikon oder CELEX/BAS). Langfristig: eigenes Modell auf deutschen L2-Daten finetunen.

---

## 3  Übergreifende Toolkits

Einige Frameworks bündeln mehrere der obigen Teilprobleme:

| Toolkit | Abdeckung | Lizenz | Einordnung |
|---------|-----------|--------|-----------|
| **Parselmouth** (Python-Wrapper für Praat) | F0, Intensity, Formanten, HNR, Jitter, Shimmer, Spectrogramme | GPL-2 | Phonetik-Goldstandard; Jadoul et al. (2018); voll integrierbar in Python-Pipelines |
| **SpeechBrain** | Feature-Extraktion, Emotion Recognition, Speaker Verification, ASR | Apache-2.0 | PyTorch-basiert; eher Toolkit-Ebene als fertige Prosodie-Pipeline |
| **openSMILE** | 88 eGeMAPS-Features (F0, Jitter, Shimmer, HNR, Loudness, Spectral Flux, …) | ⚠️ Forschungslizenz | Wissenschaftlicher Benchmark; **nicht kommerziell nutzbar** |

---

## 4  Zusammenfassung: Was Gamma liefert

```
┌───────────────────────────────────────────────────────────────────┐
│                  Domäne 4 · Gamma-Bausteine                      │
│                                                                   │
│  ┌─────────────┐  ┌─────────────┐  ┌─────────────┐              │
│  │  CREPE/PENN  │  │ Parselmouth │  │  Silero VAD │              │
│  │  Pitch (F0)  │  │  Intensity  │  │   Pausen    │              │
│  │  Periodicity │  │  HNR, Form. │  │  Timestamps │              │
│  └──────┬──────┘  └──────┬──────┘  └──────┬──────┘              │
│         │                │                │                       │
│         ▼                ▼                ▼                       │
│  ┌────────────────────────────────────────────┐                  │
│  │     Rohsignale: F0-Kontur, Energie-Kontur, │                  │
│  │     Pausen-Intervalle, Phone-Dauern (MFA)  │                  │
│  └──────────────────┬─────────────────────────┘                  │
│                     │                                             │
│                     ▼                                             │
│  ┌────────────────────────────────────────────┐                  │
│  │  Regelbasierte Feature-Berechnung:         │                  │
│  │  • Speech Rate, MLR, Pause Ratio           │                  │
│  │  • nPVI-V, rPVI-C, %V, VarcoV/C           │                  │
│  │  • F0-Range, F0-Slope, Stress-Ratio        │                  │
│  └────────────────────────────────────────────┘                  │
└───────────────────────────────────────────────────────────────────┘
```

---

## 5  Limitationen auf Gamma-Ebene

| # | Limitation | Konsequenz |
|---|-----------|------------|
| 1 | **Kein fertiges Prosodie-Scoring-Modell für Deutsch.** GOPT und 3M-Modelle existieren nur für Englisch (trainiert auf SpeechOcean762). | Wir können Rohfeatures extrahieren, aber nicht „Prosodie-Score: 3.8/5" liefern – dafür brauchen wir eigene annotierte Daten + Modell (→ Beta). |
| 2 | **Keine Reference-Prosodie.** Anders als bei GOP (wo das Lexikon den Soll-Laut definiert) gibt es für Intonation und Rhythmus keine einzelne „richtige" Kontur. | Wir brauchen L1-Referenzverteilungen, nicht einzelne Referenzwerte (→ Beta). |
| 3 | **Sprechervariation bei F0.** Männer ≈ 80–160 Hz, Frauen ≈ 160–300 Hz, Kinder ≈ 250–400 Hz. Absolute F0-Werte sind diagnostisch wertlos. | Alle F0-basierten Features müssen sprechernormalisiert werden (z. B. Semitöne relativ zum Median). |
| 4 | **openSMILE-Lizenz.** Das mächtigste Feature-Set (eGeMAPS) ist kommerziell nicht nutzbar. | Wir müssen die relevanten Features mit Parselmouth + eigenen Skripten replizieren. |
| 5 | **Stress-Detection = ungelöst für DaF.** Es gibt kein trainiertes Modell für deutsche Wortakzent-Erkennung bei L2-Sprechern. | MVP: regelbasierter Ansatz mit Lexikon-Lookup; langfristig: eigenes Modell. |

---

## 6  Moat-Vorschau

> **Warum messen die meisten EdTech-Produkte Prosodie gar nicht – und warum wir schon?**

Prosodie wird ignoriert, weil sie **drei Probleme gleichzeitig** aufwirft, die kein einzelnes Tool löst:
1. Man braucht **Alignment auf Silbenebene** (D2) als Input.
2. Man braucht **sprechernormalisierte F0/Energie-Features** statt absoluter Werte.
3. Man braucht **L1-Referenzverteilungen**, nicht eine einzige Referenz.

Wer nur einen Cloud-API-Call (Azure, Google) macht, bekommt keines dieser drei Dinge. Wer die gesamte Pipeline D1→D2→D3→D4 kontrolliert, kann Prosodie bewerten – und das tun wir.
