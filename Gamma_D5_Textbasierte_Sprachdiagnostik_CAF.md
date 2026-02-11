# Gamma · Domäne 5 – Textbasierte Sprachdiagnostik (CAF+)

> **Domänenfrage:** *Transkript / Schreibtext → Complexity, Accuracy, Fluency auf Textebene*
> **Gamma-Frage:** *Was existiert als Open-Source-Baustein, den wir morgen deployen können?*

---

## 1  Überblick & Abgrenzung

Die Domänen 1–4 operieren auf **Audiosignal-Ebene**: Was wurde gesprochen? Wie klingt es? Wo liegen phonetische oder prosodische Abweichungen?

Domäne 5 wechselt die Ebene: Sobald ein Transkript vorliegt (aus D1) oder ein geschriebener Text eingereicht wird, greifen **linguistische Analyseverfahren** – unabhängig vom Klang. Die zentrale Frage ist nicht mehr „Wie klingt es?", sondern **„Was wird gesagt – und wie komplex, korrekt und flüssig ist die Sprache?"**

| Dimension | Segmental/Prosodisch (D1–D4) | Textbasiert (D5) |
|---|---|---|
| Input | Audio-Signal (Waveform) | Text (Transkript oder Schreibtext) |
| Analyseebene | Phonem, Silbe, Intonationskontur | Wort, Satz, Diskurs |
| Typische Frage | „Klingt /ʃ/ korrekt?" | „Ist die Kasusmarkierung korrekt?" |
| Forschungsrahmen | Phonetik, Akustik | SLA, Korpuslinguistik, NLP |
| Markt-Lücke | Prosodie kaum abgedeckt | Für Deutsch fast nicht existent |

### Das CAF-Framework

CAF (Complexity, Accuracy, Fluency) ist **der** etablierte Rahmen der SLA-Forschung zur Beschreibung von L2-Leistung:

- **Complexity** = Breite und Tiefe der sprachlichen Mittel (syntaktisch + lexikalisch)
- **Accuracy** = Zielsprachliche Korrektheit (Grammatik, Orthographie, Morphologie)
- **Fluency** = Leichtigkeit und Geschwindigkeit der Sprachproduktion (textbasiert: Reparaturen, Wiederholungen, Satzabbrüche; akustisch: → D4)

Wir erweitern das klassische CAF-Triad um ein „+" für **morphologische Komplexität** und **lexikalische Sophistikation** – zwei Dimensionen, die im Deutschen besonders diagnostisch sind.

---

## 2  Die vier Teilprobleme

### 2.1  Syntaktische Komplexität (Complexity – Syntax)

**Was:** Automatische Messung der strukturellen Komplexität auf Satz- und Textebene.

**Warum zentral:** Syntaktische Komplexität ist einer der stärksten Prädiktoren für L2-Proficiency und korreliert zuverlässig mit CEFR-Niveaus. L2-Entwicklung zeigt sich in zwei Phasen: (1) zunehmende Subordination (A1→B1), (2) zunehmende Phrasenelaboration (B2→C1).

**Etablierte Metriken (Lu, 2010; Kyle & Crossley, 2018):**

| Metrik | Abkürzung | Was sie misst | Diagnostisch ab |
|--------|-----------|---------------|-----------------|
| Mean Length of T-unit | MLT | Wörter pro T-unit | A2+ |
| Mean Length of Clause | MLC | Wörter pro Teilsatz | A2+ |
| Clauses per T-unit | C/T | Subordinationsrate | B1+ |
| Dependent Clauses per Clause | DC/C | Anteil subordinierter Strukturen | B1+ |
| Complex Nominals per T-unit | CN/T | Nominalphrasen-Elaboration | B2+ |
| Coordinate Phrases per T-unit | CP/T | Koordination | A2+ |
| Max Dependency Depth | MDD | Tiefste Verschachtelung im Dependenzbaum | B2+ |

**Verfügbare Bausteine:**

| Tool | Funktion | Lizenz | Stärke | Schwäche |
|------|----------|--------|--------|----------|
| **spaCy** (`de_core_news_lg` / `de_dep_news_trf`) | Tokenisierung, POS-Tagging, Dependency Parsing, NER, Lemmatisierung | MIT | Industrie-Standard; schnell; Transformer-Modell verfügbar; trainiert auf UD German GSD/HDT; aktive Community | Accuracy auf L2-Text ggf. geringer als auf Zeitungstext |
| **Stanza** (Stanford NLP) | Tokenisierung, MWT-Expansion, POS, Morphologie, Dependency Parsing, NER | Apache-2.0 | Top-Accuracy auf UD CoNLL 2018; für 70+ Sprachen; Python-nativ | Langsamer als spaCy; keine Pipeline-Erweiterbarkeit wie spaCy |
| **L2SCA / NeoSCA** | 14 Indizes syntaktischer Komplexität (MLT, MLC, C/T, DC/C, CN/T, …) | GPL-3 (NeoSCA) | Direkte Implementierung der Lu (2010)-Metriken; Python-nativ (NeoSCA); kein Java nötig | Nur für **Englisch** validiert – deutsche Adaption fehlt |
| **TAASSC** (Kyle) | Syntaktische Sophistikation + Komplexität (Subordination, Phrasenelaboration, Frequenz syntaktischer Muster) | Open Source | Umfassendster Analyzer; nutzt spaCy-Dependency-Parses; 4 Perspektiven auf Syntaxkomplexität | Nur für **Englisch** – nutzt COCA-Frequenzen; keine deutsche Version |

**Problem für Deutsch:** L2SCA, TAASSC und NeoSCA sind alle **für Englisch gebaut**. Die Metriken (T-units, Clauses, etc.) sind theoretisch sprachunabhängig, aber die Implementierungen nutzen englische Tregex-Pattern oder spaCy-en-Modelle. Für Deutsch müssen die Pattern auf deutsche Dependenzrelationen (UD-Schema) adaptiert werden.

**Empfehlung für Disce:** spaCy `de_dep_news_trf` als NLP-Backbone + eigene Reimplementierung der Lu-Metriken auf deutschen UD-Dependenzbäumen. Die Metriken selbst (MLT, MLC, C/T, DC/C, CN/T) lassen sich **regelbasiert** aus dem Parse-Baum ableiten.

---

### 2.2  Lexikalische Komplexität (Complexity – Lexikon)

**Was:** Messung von Wortschatzbreite (Diversity), Wortschatztiefe (Sophistication) und lexikalischer Dichte.

**Warum zentral:** Lexikalische Entwicklung korreliert stark mit CEFR-Stufen. Ein A2-Lerner verwendet hauptsächlich hochfrequente Wörter; ein C1-Lerner greift auf seltene, fachsprachliche und abstrakte Wörter zurück.

**Etablierte Metriken:**

| Kategorie | Metrik | Was sie misst | Anmerkung |
|-----------|--------|---------------|-----------|
| **Diversität** | TTR (Type-Token Ratio) | Verhältnis verschiedener Wörter zu Gesamtwörtern | ⚠️ Textlängen-abhängig – nur zum Vergleich gleich langer Texte |
| **Diversität** | MTLD (McCarthy & Jarvis) | Textlängen-stabiles Diversitätsmaß | Gold-Standard; stabil ab ~100 Token |
| **Diversität** | MATTR (Moving-Average TTR) | Gleitendes Fenster über Text | Robust; konfigurierbar |
| **Diversität** | HD-D (Hypergeometric D) | Stichprobenbasierte Diversität | Mathematisch robust |
| **Sophistikation** | LFP (Lexical Frequency Profile) | Anteil des Wortschatzes in Frequenzbändern (Top-1000, 2000, …) | Braucht sprachspezifische Frequenzlisten |
| **Sophistikation** | Mittlere Wortfrequenz | Durchschnittliche Korpusfrequenz der verwendeten Wörter | Niedrigere Frequenz = höheres Niveau |
| **Dichte** | Lexical Density | Inhaltswörter / Gesamtwörter | Misst informative Dichte |

**Verfügbare Bausteine:**

| Tool | Funktion | Lizenz | Stärke |
|------|----------|--------|--------|
| **TAALED** | TTR, Root TTR, MTLD, MATTR, HD-D, Maas | BSD-3 | Python-nativ; berechnet alle modernen Diversitätsmaße; textlängen-stabile Indizes |
| **lexicalrichness** (Python) | TTR, MTLD, MATTR, HD-D, Yule's K, Herdan's C | MIT | Minimale Dependency; einfache API |
| **DeReWo** (IDS Mannheim) | Korpusbasierte Frequenzlisten für Deutsch | Frei verfügbar | 4 Mio. Wortformen mit Frequenzklassen; aus dem Deutschen Referenzkorpus (DeReKo) |
| **Leipzig Corpora Collection** | Wortfrequenzlisten für 200+ Sprachen | CC-BY | Deutsch: bis 1 Mio. Sätze aus Nachrichtentexten; Kookurenzen, Frequenzen |
| **DWDS** (Berlin-Brandenburgische Akademie) | Deutsches Wortinformationssystem; Frequenzen, Wortverlaufskurven | Frei für Forschung | Historische + aktuelle Frequenzen; API verfügbar |

**Empfehlung für Disce:** TAALED für Diversitätsmetriken (MTLD, MATTR, HD-D) + DeReWo-Frequenzlisten für Sophistikation (LFP für Deutsch). Beide erfordern lemmatisierte Inputtexte → spaCy-Lemmatizer als Vorverarbeitung.

---

### 2.3  Accuracy (Grammatische Korrektheit)

**Was:** Automatische Erkennung und optional Korrektur grammatischer, orthographischer und morphologischer Fehler.

**Warum besonders herausfordernd im Deutschen:**
- **Kasussystem:** 4 Kasus × 3 Genus × 2 Numeri = komplexe Artikelmorphologie (der/die/das/den/dem/des/…)
- **Verbstellung:** V2 im Hauptsatz, Verbletzt im Nebensatz, Verbklammer bei Modalverben/Perfekt
- **Adjektivdeklination:** Starke/schwache/gemischte Flexion abhängig von Determiner
- **Genus:** Nicht vorhersagbar – muss lexikalisch gelernt werden
- → L2-Lerner machen systematische Fehler, die weit über Orthographie hinausgehen

**Verfügbare Bausteine:**

| Tool | Methode | Lizenz | Stärke | Schwäche |
|------|---------|--------|--------|----------|
| **LanguageTool** | Regelbasiert + n-gram + neuronales Backend | LGPL-2.1 (Core) | >5.000 Regeln für Deutsch; Genus, Kasus, Kongruenz, Kommasetzung; self-hostable (Java); API verfügbar | Optimiert für L1-Sprecher, nicht für L2-Fehler; komplexe L2-Fehler (z. B. Verbstellung) werden oft nicht erkannt |
| **GECToR** (Grammarly) | Sequence Tagging (BERT + Token-Transformationen) | MIT | Schnell (kein Seq2Seq-Decoding); SOTA auf BEA-2019 (Englisch) | Nur für **Englisch** trainiert; deutsches Finetuning bräuchte annotierte Daten |
| **MultiGEC-2025 Modelle** | LLM-basierte GEC; Shared Task mit Falko-MERLIN Daten für Deutsch | Varies | Erster multilingualer GEC Shared Task mit deutschem Track; nutzt Falko-MERLIN-Korpus | Noch keine veröffentlichten fertigen Modelle für Production-Use |
| **ERRANT (multilingual)** | Error Annotation Toolkit – aligniert Original ↔ Korrektur und labelt Fehlertypen | MIT | De-facto-Standard für GEC-Evaluation; neue multilingual-Version unterstützt Deutsch (via Stanza) | Evaluationstool, nicht Korrekturtool – braucht korrigierte Version als Input |
| **LLMs (Llama, Mistral, etc.)** | Prompt-basierte Fehlerkorrektur | Varies | Flexibel; kann auch Erklärungen generieren; mehrsprachig | Hohe Latenz; nicht deterministisch; Halluzinationsgefahr; teuer bei Scale |

**Deutsche Learner-Korpora (für Training/Evaluation):**

| Korpus | Inhalt | Verfügbarkeit |
|--------|--------|---------------|
| **MERLIN** | 2.290 geschriebene Lernertext (DaF/DaZ); A1–C1; CEFR-annotiert; Fehlerannotation | Frei verfügbar (ANNIS) |
| **Falko** | Fehlerannotierter Lernerkorpus Deutsch (FU Berlin); Essays + Zusammenfassungen | Frei verfügbar |
| **Falko-MERLIN GED/GEC** | Merged Dataset für Shared Tasks; train/dev/test-Splits | Frei verfügbar |

**Empfehlung für Disce:** LanguageTool (self-hosted) als regelbasierter MVP für Accuracy-Messung. Parallel: Falko-MERLIN als Trainingsgrundlage für ein deutsches GECToR-Modell evaluieren. Langfristig: eigenes Error-Detection-Modell, das L2-typische Fehlerklassen (Genus, Kasus, Verbstellung) gezielt erkennt.

---

### 2.4  Morphologische Komplexität (das Deutsche „+"")

**Was:** Analyse der Nutzung und Korrektheit morphologischer Mittel – ein Bereich, der im klassischen CAF-Framework (das primär für Englisch entwickelt wurde) zu kurz kommt.

**Warum ein eigenes Teilproblem im Deutschen:**
Deutsch ist morphologisch **signifikant reicher** als Englisch:

| Phänomen | Englisch | Deutsch |
|----------|----------|---------|
| Kasus | – (nur Pronomen) | 4 Kasus auf Artikel, Adjektiv, Pronomen |
| Genus | – (natural gender) | 3 Genus (grammatisch, nicht vorhersagbar) |
| Adjektivdeklination | – (unveränderlich) | 48 Formen (3 Deklinationsklassen × 4 Kasus × 2 Numeri × Genus) |
| Verbmorphologie | 3–4 Formen (go/goes/went/gone) | 6+ Formen pro Tempus + Konjunktiv I/II |
| Komposita | Selten, mit Leerzeichen | Produktiv, zusammengeschrieben (Donaudampfschifffahrtsgesellschaft) |
| Wortstellung | SVO (fest) | V2 + Verbletzt + Verbklammer (flexibel, aber regelgeleitet) |

**Messbare Indikatoren:**

| Indikator | Was er zeigt | Berechnung |
|-----------|-------------|------------|
| Morphological Richness | Wie viele verschiedene Flexionsformen nutzt der Lerner? | Unique morphologische Tags / Gesamttokens (via spaCy `morph`) |
| Case Accuracy | Korrektheit der Kasusmarkierung | Regelbasiert: Verb/Präposition → erwarteter Kasus → Abgleich mit produziertem Kasus |
| Gender Consistency | Kongruenz von Artikel, Adjektiv, Nomen im Genus | Regelbasiert über Dependency-Parse + Lexikon |
| Verb Morphology Index | Tempus-/Modusvielfalt (Präsens, Perfekt, Präteritum, Konjunktiv) | Zählung der verwendeten Tempus-/Modus-Tags |
| Compound Awareness | Korrekte Kompositabildung vs. Getrenntschreibung | Lexikon-Lookup + Dekomposition (z. B. CharSplit) |

**Verfügbare Bausteine:**

| Tool | Funktion | Lizenz |
|------|----------|--------|
| **spaCy `morph`** | Morphologische Features pro Token (Case, Gender, Number, Tense, Mood, …) nach UD-Schema | MIT |
| **Stanza** | Gleiche morphologische Features; höchste Accuracy auf UD-Benchmarks | Apache-2.0 |
| **DEMorphy** | Deutsches morphologisches Analyse-Tool; generiert alle möglichen Lesarten eines Worts | MIT |
| **CharSplit** | Kompositazerlegung für Deutsch (neuronales Modell) | MIT |

**Empfehlung für Disce:** spaCy-Morphologie-Tags als Basis → eigene regelbasierte Analyzer für Case Accuracy, Gender Consistency und Verb Morphology Index. Das sind Metriken, die **kein existierendes Tool liefert** – und die für DaF/DaZ hochdiagnostisch sind.

---

## 3  NLP-Backbone: spaCy vs. Stanza

Beide Tools kommen für die zentrale Textverarbeitung in Frage. Entscheidungsmatrix:

| Kriterium | spaCy | Stanza |
|-----------|-------|--------|
| Geschwindigkeit | ⚡ Schnell (Cython-optimiert) | 🐢 Langsamer (reines PyTorch) |
| Accuracy (UD Deutsch) | Sehr gut (de_dep_news_trf) | Leicht höher auf CoNLL 2018 |
| Erweiterbarkeit | Exzellent (Custom Components, Pipes) | Begrenzt |
| Morphologie | UD-Features via `morph` Attribut | UD-Features (gleicher Standard) |
| Dependency Labels | UD v2 | UD v2 |
| Integration | spaCy-Ökosystem (Prodigy, etc.) | CoreNLP-Bridge (Java) |
| Lizenz | MIT | Apache-2.0 |
| Community | Sehr groß (Explosion AI) | Groß (Stanford NLP Group) |
| L2-Text-Robustheit | Nicht speziell getestet | Nicht speziell getestet |

**Empfehlung:** spaCy als primäres NLP-Backbone (schneller, erweiterbarer, MIT-lizenziert). Stanza als Cross-Validation-Tool bei kritischen Parse-Entscheidungen.

---

## 4  Readability & CEFR-Indikation

**Was:** Automatische Einschätzung des Textniveaus – nicht als definitive CEFR-Zuweisung, sondern als Feature-Input.

| Tool / Metrik | Funktion | Lizenz | Anmerkung |
|---------------|----------|--------|-----------|
| **textstat** (Python) | Flesch Reading Ease, Flesch-Kincaid, LIX, ARI, Coleman-Liau, Gunning Fog | MIT | Mehrere Formeln; LIX funktioniert gut für Deutsch (skandinavischer Ursprung) |
| **LIX-Formel** | (Wörter/Sätze) + 100×(lange Wörter/Wörter) | – | Sprachunabhängiger als Flesch; validiert für skandinavische + deutsche Texte |
| **Complexity-Contour-Ansatz** | RNN/BERT auf CAF-Features → CEFR-Level-Klassifikation | Forschung | Accuracy ~60–70% über 6 CEFR-Stufen; besser als Textmittelwerte allein |
| **MERLIN-basiertes Benchmarking** | Vergleich der Feature-Verteilungen mit MERLIN-CEFR-Annotierten Texten | – | Kein Modell nötig: statistische Verteilungsvergleiche (z. B. z-Scores) |

**Empfehlung für Disce:** LIX + eigene Feature-Verteilungen (MLT, MTLD, Error Rate, Morphological Richness) → Vergleich mit MERLIN-Referenzwerten pro CEFR-Stufe. Kein Black-Box-Classifier, sondern **interpretierbare Profile**.

---

## 5  Zusammenfassung: Was Gamma liefert

```
┌─────────────────────────────────────────────────────────────────────────┐
│                   Domäne 5 · Gamma-Bausteine                           │
│                                                                         │
│  ┌──────────────┐    ┌──────────────┐    ┌──────────────┐              │
│  │    spaCy      │    │ LanguageTool │    │   TAALED     │              │
│  │  de_dep_trf   │    │  (self-host) │    │  Diversity   │              │
│  │  POS + Dep +  │    │  5.000+ dt.  │    │  MTLD, MATTR │              │
│  │  Morph + Lemma│    │  Regeln      │    │  HD-D        │              │
│  └──────┬───────┘    └──────┬───────┘    └──────┬───────┘              │
│         │                   │                   │                       │
│         ▼                   ▼                   ▼                       │
│  ┌────────────────────────────────────────────────────────┐            │
│  │   Text-Input: Transkript (D1) oder Schreibtext         │            │
│  └──────────────────────┬─────────────────────────────────┘            │
│                         │                                               │
│                         ▼                                               │
│  ┌────────────────────────────────────────────────────────┐            │
│  │  Regelbasierte Feature-Berechnung:                      │            │
│  │                                                          │            │
│  │  COMPLEXITY                                              │            │
│  │  • Syntaktisch: MLT, MLC, C/T, DC/C, CN/T, MDD         │            │
│  │  • Lexikalisch: MTLD, MATTR, HD-D, LFP (DeReWo)        │            │
│  │  • Morphologisch: Morph. Richness, Tempusvielfalt       │            │
│  │                                                          │            │
│  │  ACCURACY                                                │            │
│  │  • LanguageTool Error Count + Error Categories           │            │
│  │  • Error-Free T-units / Total T-units                    │            │
│  │  • Case/Gender Accuracy (regelbasiert)                   │            │
│  │                                                          │            │
│  │  FLUENCY (textbasiert)                                   │            │
│  │  • Reparaturen, Wiederholungen, Satzabbrüche             │            │
│  │  • (Akustische Fluency → D4)                             │            │
│  │                                                          │            │
│  │  READABILITY                                             │            │
│  │  • LIX, Flesch (dt.), Wortlänge, Satzlänge              │            │
│  │  • Feature-Profil vs. MERLIN-CEFR-Verteilungen           │            │
│  └────────────────────────────────────────────────────────┘            │
└─────────────────────────────────────────────────────────────────────────┘
```

---

## 6  Limitationen auf Gamma-Ebene

| # | Limitation | Konsequenz |
|---|-----------|------------|
| 1 | **Alle existierenden CAF-Analyzer (L2SCA, TAASSC, TAALES) sind für Englisch.** Es gibt kein fertiges Tool, das syntaktische Komplexität für Deutsch berechnet. | Wir müssen die Metriken auf deutschen UD-Parses selbst reimplementieren – konzeptuell bekannt, aber Entwicklungsaufwand (→ Beta). |
| 2 | **GEC für Deutsch ist ungelöst.** LanguageTool erkennt L1-Fehler gut, aber L2-typische Fehler (Verbstellung, Kasusselektion nach Wechselpräpositionen) schlecht. | LanguageTool als Baseline + eigenes Finetuning auf Falko-MERLIN (→ Beta). |
| 3 | **NLP-Modelle sind auf Standarddeutsch trainiert.** L2-Text enthält nicht-standardsprachliche Konstruktionen, die Parser verwirren können. | Parse-Accuracy auf L2-Text muss empirisch geprüft werden; ggf. Finetuning auf MERLIN-Texten. |
| 4 | **T-unit-Segmentierung ist im Deutschen nicht trivial.** V2/Verbletzt-Alternation und Verbklammern machen die Clause-Erkennung komplexer als im Englischen. | Eigene Heuristiken nötig, die deutsche Satzstruktur berücksichtigen. |
| 5 | **Lexikalische Frequenzlisten für DaF fehlen.** DeReWo basiert auf L1-Zeitungstext; es gibt kein DaF-spezifisches Frequenzband-System (analog zu AWL für Englisch). | DeReWo als Approximation; langfristig: DaF-spezifische Wortlisten (→ Alpha). |
| 6 | **Kein Ground Truth für Feature-CEFR-Korrelationen im Deutschen.** Welche MLT-/MTLD-Werte typisch für B1 vs. B2 sind, ist nicht systematisch untersucht. | MERLIN-Korpus als Annäherung; eigene Erhebung nötig (→ Beta/Alpha). |

---

## 7  Moat-Vorschau

> **Warum ist regelbasierte Linguistik kein Rückschritt, sondern ein Vorsprung?**

Die meisten EdTech-Produkte, die „Schreiben bewerten", tun eines von zwei Dingen:
1. **LLM-Prompt:** „Bewerte diesen Text auf B1-Niveau" → Black-Box-Antwort, nicht erklärbar, nicht reproduzierbar.
2. **Oberflächenmetriken:** Wortanzahl, Satzlänge, Rechtschreibfehler → zu grob für diagnostische Aussagen.

Was **keiner** tut (und wir schon):
- **Syntaktische Komplexität auf Deutsch** messen (MLT, DC/C, CN/T aus UD-Parses)
- **Morphologische Korrektheit** gezielt evaluieren (Genus, Kasus, Adjektivdeklination)
- **Lexikalische Sophistikation** gegen deutsche Frequenzlisten messen (DeReWo-LFP)
- **Alle Features interpretierbar** und pro CEFR-Dimension zuordenbar

Die Kombination aus **regelbasierter linguistischer Analyse** (erklärbar, deterministisch, auditierbar) mit **modernem NLP** (spaCy-Transformer für robustes Parsing) ist kein Rückschritt hinter LLMs – sie ist die Voraussetzung dafür, dass Diagnostik **nachvollziehbar** bleibt. Ein Sprachlehrer will nicht „Der Text ist B1" hören – er will wissen, **warum**: weil die Subordinationsrate niedrig ist, die Kasusmarkierung in 40% der Fälle fehlerhaft und der Wortschatz auf die Top-2000 beschränkt.
