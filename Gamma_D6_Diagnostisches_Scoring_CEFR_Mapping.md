# Gamma · Domäne 6 – Diagnostisches Scoring & CEFR-Mapping

> **Domänenfrage:** *Feature-Vektor (D1–D5) → interpretierbare Bewertung → CEFR-Verortung*
> **Gamma-Frage:** *Welche Scoring-Architektur können wir aufbauen – und wo liegt die Grenze des Möglichen ohne eigene annotierte Daten?*

---

## 1  Überblick & Abgrenzung

Die Domänen 1–5 liefern **Rohmaterial**: Phonem-Scores, Prosodie-Konturen, Fluency-Metriken, Komplexitäts-Indizes, Fehlertypen. Domäne 6 stellt die entscheidende Frage: **Was bedeutet das alles zusammen?**

| Phase | Domänen 1–5 | Domäne 6 |
|---|---|---|
| Output | Feature-Vektor (30–80 Einzelwerte) | Diagnostisches Profil + CEFR-Verortung |
| Analogie | Blutbild (einzelne Laborwerte) | Ärztliche Diagnose (Was bedeuten die Werte zusammen?) |
| Herausforderung | Feature-Extraktion (technisch) | Feature-Integration & Interpretation (methodisch) |

### Warum das ein eigenes Problem ist

Die meisten CAPT-Systeme stoppen nach der Feature-Extraktion oder springen direkt zu einem **Black-Box-Score** (1–5 Sterne, „B1"). Beides ist für Disce unzureichend:

- **Feature ohne Kontext** sind für Lehrkräfte und Lerner wertlos: „Dein GOP-Score für /ʃ/ ist 2.3" sagt niemandem etwas.
- **Ein einzelner Score** ist diagnostisch wertlos: Er verbirgt, *warum* jemand auf einem bestimmten Niveau eingestuft wird und *wo* die Hebel für Verbesserung liegen.
- **CEFR-Mapping ohne Transparenz** ist in Europa regulatorisch heikel: Der AI Act verlangt Erklärbarkeit bei KI-basierten Bewertungen im Bildungsbereich.

Disce braucht einen Mittelweg: **interpretierbare, mehrdimensionale Profile**, die sich *optional* zu CEFR-Stufen verdichten lassen.

---

## 2  Referenzsysteme: Wie machen es die Großen?

Bevor wir unsere Architektur definieren, lohnt sich ein Blick auf die etablierten automatisierten Scoring-Systeme:

### 2.1  ETS SpeechRater (TOEFL iBT)

| Aspekt | Detail |
|--------|--------|
| Einsatz | Operationell seit 2019 im TOEFL iBT Speaking |
| Dimensionen | **Delivery** (Fluency + Pronunciation), **Language Use** (Vocabulary + Grammar), **Topic Development** (Content + Coherence) |
| Features | ~30 Dimensionen: Speech Rate, Pause-Metriken, Chunk Length, Pronunciation Score, Vocabulary Diversity, Grammar Error Rate, Content Vectors, … |
| Scoring | Multiple lineare Regression auf Human Scores → einzelner Score (0–4) pro Dimension + Gesamtscore |
| Stärke | Höchste Korrelation mit Human Raters (r ≈ 0.85); 30 interpretierbare Dimensionen |
| Schwäche | Proprietär; nur Englisch; nur Read-Aloud + Monolog-Tasks |

### 2.2  Pearson Versant

| Aspekt | Detail |
|--------|--------|
| Einsatz | Versant English Test + Versant Pro |
| Subscores | **Sentence Mastery**, **Vocabulary**, **Fluency**, **Pronunciation** |
| Methode | HMM-basiertes Forced Alignment + statistische Modelle |
| Stärke | 4 klar getrennte Subscores; schnelle automatische Bewertung |
| Schwäche | Proprietär; fokussiert auf kurze, kontrollierte Aufgaben |

### 2.3  Duolingo English Test (DET)

| Aspekt | Detail |
|--------|--------|
| Einsatz | Akzeptiert an >5.000 Institutionen |
| Subscores | **Literacy**, **Comprehension**, **Conversation**, **Production** + 6 neue Component Subscores |
| Methode | IRT-basiertes adaptives Testen + ML-Scoring |
| Stärke | Mehrdimensionalität explizit kommuniziert: „One number can't fully capture someone's proficiency" |
| Schwäche | Proprietär; gemischte Aufgabentypen (nicht nur Speaking) |

### Synthese: Was die Großen gemeinsam haben

1. **Mehrdimensionalität:** Kein System liefert nur einen einzigen Score.
2. **Interpretierbare Subdimensionen:** Delivery/Language Use/Content (ETS), Sentence Mastery/Vocabulary/Fluency/Pronunciation (Versant).
3. **Lineare oder schwach-nichtlineare Modelle:** Regression oder IRT – keine Deep-Learning-Black-Boxes für den finalen Score.
4. **Feature-Engineering > End-to-End:** Alle nutzen handcraftete Features, nicht raw audio → score.

---

## 3  Disce Scoring-Architektur: Das 5-Schichten-Modell

Wir definieren fünf Schichten der Informationsverdichtung – von Rohfeatures bis zur CEFR-Verortung:

```
┌─────────────────────────────────────────────────────────────────────┐
│  SCHICHT 5 · CEFR-Verortung                                        │
│  Optional: A1 → C2 (mit Konfidenz + Caveat)                        │
│  "Profil entspricht am ehesten B1, mit B2-Anteilen in Lexik"       │
├─────────────────────────────────────────────────────────────────────┤
│  SCHICHT 4 · Diagnostisches Profil (Radar-Chart)                   │
│  5–7 Dimensionen, je 0–100 (normreferenziert)                      │
│  Aussprache · Prosodie · Fluency · Syntaxkomplexität ·             │
│  Wortschatz · Grammatische Korrektheit · Morphologie               │
├─────────────────────────────────────────────────────────────────────┤
│  SCHICHT 3 · Dimensionsscores                                      │
│  Pro Dimension: gewichtete Aggregation der Subfeatures              │
│  z. B. Aussprache = f(GOP_mean, GOP_worst5, MDD_rate, …)           │
├─────────────────────────────────────────────────────────────────────┤
│  SCHICHT 2 · Normalisierte Features                                │
│  z-Scores relativ zu CEFR-Referenzverteilungen                     │
│  z. B. Speech_Rate_z = (SR_lerner - μ_B1) / σ_B1                  │
├─────────────────────────────────────────────────────────────────────┤
│  SCHICHT 1 · Rohfeatures (D1–D5)                                   │
│  ~40–80 Einzelwerte pro Lerneräußerung                              │
│  GOP-Scores, F0-Konturen, Pausen, MLT, MTLD, Error Count, …       │
└─────────────────────────────────────────────────────────────────────┘
```

### 3.1  Schicht 1: Rohfeatures (Input aus D1–D5)

Der Feature-Vektor, den wir aus den vorherigen Domänen gewinnen:

| Domäne | Feature-Beispiele | Typ | Anzahl (ca.) |
|--------|------------------|-----|-------------|
| D1 (ASR) | WER, CER, OOV-Rate | Kontinuierlich | 3–5 |
| D2 (Alignment) | Phone-Dauern, Alignment-Confidence | Kontinuierlich | 5–10 |
| D3 (Pronunciation) | GOP_mean, GOP_std, GOP_worst5%, MDD-Phoneme, Substitution-Patterns | Kontinuierlich + Kategorisch | 10–15 |
| D4 (Prosodie) | Speech Rate, MLR, Pause Ratio, nPVI-V, rPVI-C, F0-Range, F0-Slope, Stress Accuracy | Kontinuierlich | 10–15 |
| D5 (Text/CAF+) | MLT, MLC, C/T, DC/C, MTLD, MATTR, LFP-Bänder, Error Count, Error Types, Morph. Richness | Kontinuierlich + Kategorisch | 15–25 |
| **Gesamt** | | | **~45–70** |

### 3.2  Schicht 2: Normalisierung

**Problem:** Rohwerte sind nicht vergleichbar. Ein GOP-Score von 2.3 und ein MTLD von 45 existieren auf völlig verschiedenen Skalen. Schlimmer: Ein Speech Rate von 3.5 Silben/s kann für einen A2-Lerner hervorragend und für einen C1-Lerner besorgniserregend sein.

**Lösung: Referenzbasierte z-Normalisierung**

Für jedes Feature $$x_i$$ und jede CEFR-Stufe $$L$$ berechnen wir:

$$z_{i,L} = \frac{x_i - \mu_{i,L}}{\sigma_{i,L}}$$

wobei $$\mu_{i,L}$$ und $$\sigma_{i,L}$$ der Mittelwert und die Standardabweichung des Features $$i$$ in der Referenzpopulation der Stufe $$L$$ sind.

**Woher kommen die Referenzverteilungen?**

| Quelle | Verfügbarkeit | Abdeckung | Limitation |
|--------|---------------|-----------|------------|
| **MERLIN-Korpus** | Frei (ANNIS) | A1–C1, geschriebene Texte, DaF/DaZ | Nur Text → nur D5-Features; keine Audio-Features |
| **SpeechOcean762** | Frei | L2-Englisch; Phone/Word/Utterance-Scores | Nur Englisch; nur Aussprache |
| **Eigene Erhebung** | Noch nicht vorhanden | – | → Kritische Beta-Aufgabe |
| **Bootstrapping mit Goethe-Prüfungen** | Theoretisch möglich | A1–C2 Audio + Text | Rechtliche Klärung nötig |

**Gamma-Realität:** Für D5-Features (Text) können wir MERLIN als Referenz nutzen. Für D3/D4-Features (Audio) haben wir **keine deutschen Referenzverteilungen** – das ist die zentrale Datenlücke.

**Empfehlung:** MVP startet mit **nicht-normreferenziertem Scoring** (absolute Schwellenwerte aus der Literatur, z. B. „Speech Rate < 2.5 Syl/s → niedrige Fluency") und wechselt zu z-Scores, sobald eigene Referenzdaten vorliegen.

### 3.3  Schicht 3: Dimensionsscores

Aggregation der normalisierten Features zu **5–7 interpretierbaren Dimensionen**, die direkt auf CEFR-Kompetenzskalen abbildbar sind:

| Dimension | CEFR-Skala | Input-Features (Auswahl) | Aggregation |
|-----------|------------|-------------------------|-------------|
| **Aussprache** | Phonological Control | GOP_mean, GOP_worst5%, MDD_rate, Substitution_count | Gewichteter Durchschnitt |
| **Prosodie & Intonation** | Phonological Control (erweitert, CEFR 2020) | F0_range, Stress_accuracy, nPVI_V, Intonation_contour_match | Gewichteter Durchschnitt |
| **Fluency** | Spoken Fluency | Speech_rate, MLR, Pause_ratio, Filled_pause_rate, Phonation_time_ratio | Gewichteter Durchschnitt |
| **Syntaktische Komplexität** | General Linguistic Range | MLT, C/T, DC/C, CN/T, MDD_syntax | Gewichteter Durchschnitt |
| **Wortschatz** | Vocabulary Range | MTLD, MATTR, LFP_band1_ratio, Mean_word_frequency | Gewichteter Durchschnitt |
| **Grammatische Korrektheit** | Grammatical Accuracy | Error_free_Tunits_ratio, Case_accuracy, Gender_consistency, LT_error_rate | Gewichteter Durchschnitt |
| **Morphologische Kontrolle** | (Deutsch-spezifisch, kein direktes CEFR-Pendant) | Morph_richness, Verb_morph_index, Compound_awareness | Gewichteter Durchschnitt |

**Gewichtung:** Initialgewichte aus der SLA-Literatur (welche Features korrelieren am stärksten mit Proficiency?). Langfristig: datengetrieben (Ridge/Lasso-Regression auf annotierten Daten).

### 3.4  Schicht 4: Diagnostisches Profil

**Das Kernprodukt von D6** – kein einzelner Score, sondern ein **mehrdimensionales Profil**, das zeigt:

- **Wo steht der Lerner** in jeder Dimension (relativ zur Referenzgruppe)?
- **Wo liegen Stärken und Schwächen** (Asymmetrien im Profil)?
- **Was ist der nächste Entwicklungsschritt** (schwächste Dimension = höchster Hebel)?

**Visualisierung: Radar-/Spider-Chart**

```
                    Aussprache
                       100
                        │
                   80 ──┤
                  ╱     │     ╲
       Morpho-  ╱  60 ──┤      ╲  Prosodie
       logie   ╱   ╱    │   ╲   ╲
              ╱   ╱ 40 ─┤    ╲   ╲
             ╱   ╱  ╱    │  ╲  ╲   ╲
            ╱   ╱  ╱ 20 ─┤   ╲  ╲   ╲
           ╱   ╱  ╱      │    ╲  ╲   ╲
    Gramm. ────────────────────────── Fluency
    Korrekt.╲   ╲  ╲     │    ╱  ╱   ╱
             ╲   ╲  ╲    │   ╱  ╱   ╱
              ╲   ╲  ╲   │  ╱  ╱   ╱
               ╲   ╲     │     ╱
                ╲        │    ╱
                  Wort-  │  Syntax-
                  schatz │  komplexität

    ── Lerner-Profil     ── B1-Referenz
```

**Interpretation für Lehrkraft:** „Der Lerner hat eine solide Aussprache (75/100) und guten Wortschatz (68/100), aber die grammatische Korrektheit (32/100) und Prosodie (38/100) liegen deutlich unter dem B1-Referenzprofil. Empfehlung: Fokus auf Kasusmarkierung und Satzintonation."

### 3.5  Schicht 5: CEFR-Verortung (optional)

**Warum optional?** Drei Gründe:

1. **CEFR-Stufen sind Bündel-Urteile**, die holistisch vergeben werden. Ein automatisches System, das einzelne Features misst, kann Indikatoren liefern, aber keine rechtsgültige CEFR-Einstufung ersetzen.
2. **CEFR-Profile sind nicht monoton.** Ein Lerner kann B2-Wortschatz, aber A2-Morphologie haben – das ist die Regel, nicht die Ausnahme.
3. **Der AI Act** verlangt für Bildungs-KI (Hochrisiko-Kategorie) Transparenz über Limitationen.

**Operationalisierung:**

| Ansatz | Methode | Interpretierbarkeit | Accuracy (Literatur) |
|--------|---------|--------------------|--------------------|
| **Schwellenwert-basiert** | Pro Dimension: Feature-Werte → CEFR-Band via literaturbasierte Cut-Scores | ⭐⭐⭐⭐⭐ Voll erklärbar | Niedrig (~40–50% über 6 Stufen) |
| **Ordinal Regression** | Feature-Vektor → Cumulative Link Model → P(≥A2), P(≥B1), … | ⭐⭐⭐⭐ Koeffizienten interpretierbar | Mittel (~55–65%) |
| **Random Forest / Gradient Boosting** | Feature-Vektor → Klassifikation + SHAP-Erklärungen | ⭐⭐⭐ Mit SHAP erklärbar | Hoch (~60–70%) |
| **Ordinal-aware Cross-Entropy** | Neuronales Modell mit Kernel-gewichteter ordinaler Loss-Funktion | ⭐⭐ Weniger transparent | Höchste (~65–75%) |
| **LLM-Prompt** | „Auf welchem CEFR-Niveau ist dieser Lerner?" | ⭐ Black Box | Variabel; nicht reproduzierbar |

**Empfehlung für Disce (Gamma):**

Zwei Pfade parallel:

1. **MVP (regelbasiert):** Schwellenwert-basierte CEFR-Indikation pro Dimension. Output: „Aussprache: B1-Bereich, Grammatik: A2-Bereich." Kein Gesamt-CEFR-Level.
2. **Beta-Vorbereitung:** Feature-Vektor → Ordinal Regression (mord-Library, scikit-learn-kompatibel) trainiert auf MERLIN (D5-Features) + eigenen annotierten Daten (D3/D4-Features, sobald verfügbar).

---

## 4  CEFR-Deskriptoren als Scoring-Anker

Die CEFR-Skalen des Companion Volume (2020) liefern die **qualitativen Anker**, an denen wir unsere quantitativen Features verankern:

### 4.1  Phonological Control (CEFR 2020)

| Stufe | Deskriptor | Operationalisierbare Features |
|-------|-----------|-------------------------------|
| A1 | „Pronunciation of a very limited repertoire of learnt words and phrases can be understood with some effort by interlocutors used to dealing with speakers of the language group." | GOP_mean < Schwelle; hohe MDD-Rate; eingeschränktes Phoneminventar |
| A2 | „Pronunciation is generally clear enough to be understood, but conversational partners will need to ask for repetition from time to time." | GOP_mean steigt; einige persistente Substitutionen; Intelligibility-Threshold |
| B1 | „Pronunciation is clearly intelligible even if a foreign accent is sometimes evident and occasional mispronunciations occur." | GOP_mean > Schwelle; wenige systematische Substitutionen; Prosodie noch L1-beeinflusst |
| B2 | „Has a clear, natural pronunciation and intonation." | Hoher GOP_mean; gute Stress Accuracy; natürliche F0-Konturen; nPVI-V im L1-Bereich |
| C1 | „Can vary intonation and place sentence stress correctly in order to express finer shades of meaning." | Exzellenter GOP; kontextadäquate Intonationsvariation; Fokus-Akzent korrekt |
| C2 | „Can employ the full range of phonological features … so that the finer points of their message are clear and precise." | Near-native in allen suprasegmentalen Dimensionen |

### 4.2  Weitere relevante Skalen

| CEFR-Skala | Disce-Dimension | Primäre Features |
|------------|----------------|-----------------|
| Spoken Fluency | Fluency | Speech Rate, MLR, Pause Ratio |
| General Linguistic Range | Syntaktische Komplexität | MLT, C/T, DC/C |
| Vocabulary Range | Wortschatz | MTLD, LFP, Mean Word Frequency |
| Grammatical Accuracy | Grammatische Korrektheit | Error-Free T-units, Case/Gender Accuracy |
| Vocabulary Control | Wortschatz (Korrektheit) | Lexical Error Rate, Word Choice Accuracy |

---

## 5  Technische Bausteine

| Tool | Funktion | Lizenz | Einsatz in D6 |
|------|----------|--------|---------------|
| **scikit-learn** | Regression, Klassifikation, Feature Selection | BSD-3 | Ordinal Regression (via Wrappers), Random Forest, Feature Importance |
| **mord** | Ordinal Regression (Cumulative Link Models) | BSD-3 | CEFR-Level-Prediction mit ordinalem Charakter der Stufen |
| **SHAP** | Feature-Attribution / Explainability | MIT | „Warum wurde dieser Lerner als B1 eingestuft?" → Feature-Beiträge pro Prediction |
| **matplotlib / plotly** | Radar-Charts, Profil-Visualisierung | BSD / MIT | Diagnostisches Profil-Dashboard |
| **pandas / numpy** | Feature-Engineering, Normalisierung, Aggregation | BSD-3 | Schichten 1–3 der Scoring-Pipeline |

---

## 6  Zusammenfassung: Was Gamma liefert

```
┌──────────────────────────────────────────────────────────────────────┐
│                   Domäne 6 · Gamma-Bausteine                        │
│                                                                      │
│  INPUT: Feature-Vektor aus D1–D5 (~45–70 Features)                  │
│         │                                                            │
│         ▼                                                            │
│  ┌────────────────────────────────────────────────┐                  │
│  │  Schicht 2: Normalisierung                     │                  │
│  │  • Absolute Schwellenwerte (Literatur)  [MVP]   │                  │
│  │  • z-Scores vs. Referenz  [wenn Daten da]       │                  │
│  └────────────────────┬───────────────────────────┘                  │
│                       ▼                                              │
│  ┌────────────────────────────────────────────────┐                  │
│  │  Schicht 3: Dimensionsscores (5–7 Dimensionen) │                  │
│  │  Gewichtete Aggregation (initial: Literatur)    │                  │
│  └────────────────────┬───────────────────────────┘                  │
│                       ▼                                              │
│  ┌────────────────────────────────────────────────┐                  │
│  │  Schicht 4: Diagnostisches Profil              │                  │
│  │  Radar-Chart · Stärken/Schwächen · Empfehlung  │                  │
│  └────────────────────┬───────────────────────────┘                  │
│                       ▼                                              │
│  ┌────────────────────────────────────────────────┐                  │
│  │  Schicht 5: CEFR-Indikation (optional)         │                  │
│  │  Pro Dimension: "B1-Bereich" (mit Konfidenz)    │                  │
│  │  Kein Gesamt-Level im MVP                       │                  │
│  └────────────────────────────────────────────────┘                  │
│                                                                      │
│  OUTPUT: Diagnostisches Profil + CEFR-Indikation                    │
│          interpretierbar · reproduzierbar · auditierbar              │
└──────────────────────────────────────────────────────────────────────┘
```

---

## 7  Limitationen auf Gamma-Ebene

| # | Limitation | Konsequenz |
|---|-----------|------------|
| 1 | **Keine deutschen Audio-Referenzverteilungen.** Für D3/D4-Features (GOP, Prosodie) existieren keine CEFR-annotierten Referenzdaten für DaF. | CEFR-Mapping für Audio-Features ist im MVP *indikativ*, nicht *normreferenziert*. Eigene Datenerhebung = kritische Beta-Aufgabe. |
| 2 | **MERLIN nur für Text.** Die einzige CEFR-annotierte deutsche Referenz (MERLIN) enthält nur geschriebene Texte → nur D5-Features abdeckbar. | Audio-Dimensionen (D3/D4) bleiben im MVP ohne Referenzverankerung. |
| 3 | **Feature-Gewichtungen sind nicht empirisch validiert.** Welche Features für DaF am stärksten mit Proficiency korrelieren, ist nicht systematisch untersucht. | Initialgewichte aus der (primär englischen) SLA-Literatur; Validierung mit eigenen Daten nötig. |
| 4 | **Kein High-Stakes-Anspruch.** Das System kann und soll keine zertifizierende Prüfung ersetzen (TestDaF, Goethe-Zertifikat). | Klare Kommunikation: „diagnostische Orientierung", nicht „zertifizierte Einstufung". |
| 5 | **CEFR-Stufen sind keine natürlichen Klassen.** Die Übergänge A2→B1→B2 sind fließend; die 6 Stufen sind konventionelle Abstufungen, keine empirisch scharfen Grenzen. | Ordinal Regression ist methodisch korrekt (behandelt CEFR als ordinal, nicht nominal); trotzdem: Klassifikationsgenauigkeit wird nie 100% erreichen. |
| 6 | **Ungleiche Profil-Dimensionen.** Lerner können in Aussprache B2 und in Grammatik A2 sein. Ein einzelner CEFR-Level ist dann irreführend. | Deshalb: Profil-basiertes Scoring als Primäroutput; Gesamt-Level nur als optionale Zusammenfassung mit Caveat. |

---

## 8  Moat-Vorschau

> **Warum ist „ein Score" kein Produkt – und was ist es stattdessen?**

Die Marktlogik sagt: Lerner wollen **einen klaren Score**. Die didaktische Realität sagt: Ein Score ohne Erklärung ist nutzlos, und ein Score ohne Handlungsempfehlung ist frustrierend.

**Was die Konkurrenz liefert:**
- Duolingo DET: 4 Subscores, aber **nicht diagnostisch** (Literacy/Comprehension/Conversation/Production sind Skill-Bündel, keine linguistischen Dimensionen).
- ELSA Speak: Pronunciation Score + Fluency Score, aber **keine syntaktische oder lexikalische Analyse**.
- Babbel/Busuu: Keine automatische Bewertung jenseits von Multiple-Choice-Korrektheit.

**Was Disce liefert:**
Ein **7-dimensionales diagnostisches Profil**, das:
1. Für den **Lerner** sichtbar macht, wo die größte Hebelwirkung liegt.
2. Für die **Lehrkraft** zeigt, welche linguistischen Teilkompetenzen gezielt gefördert werden müssen.
3. Für den **Kursanbieter** ermöglicht, Lerner in homogene Fördergruppen zu clustern.
4. Für die **Regulatorik** (AI Act) transparent und erklärbar bleibt.

Die Kombination aus **interpretierbar** (regelbasiert + SHAP) und **mehrdimensional** (7 Dimensionen statt 1 Score) ist der Scoring-Moat.
