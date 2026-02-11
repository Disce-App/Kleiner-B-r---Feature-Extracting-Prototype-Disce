# German-Disce-Speech-Suite — Tech Vision & Strategy

> **Leitfrage des gesamten Dokuments:**
> *Wieso kann niemand sonst tun, was wir tun?*

---

## 0 — North Star

**Alles, was ein modernes, KI-basiertes E-Learning-Produkt für Sprachdiagnostik und Sprachförderung brauchen könnte, ist bei Disce in-house vorhanden und eigens entwickelt.**

Kein einzelner Baustein ist einzigartig. Die Einzigartigkeit entsteht durch die *Komposition*: die Art, wie wir existierende Open-Source-Fundamente zu einer durchgängigen, erklärbaren, souveränen Pipeline verbinden — optimiert auf eine Domäne, die kein großer Player priorisiert: **deutschsprachige Sprachdiagnostik auf CEFR-Niveau, von der Phonemebene bis zum didaktischen Feedback.**

---

## 1 — Die Matrix: Sieben Domänen × Drei Ebenen

### Lesehinweis

| Ebene | Name | Frage |
|-------|------|-------|
| **Gamma** | Fundament | Was existiert als Open-Source-Baustein, den wir morgen deployen können? |
| **Beta** | Komposition | Welche Techniken / Methoden / Architekturen verbinden diese Bausteine? |
| **Alpha** | Ziel-Capability | Was entsteht daraus als Disce-eigene Fähigkeit, die niemand sonst so hat? |

---

### ① Transkription & Erkennung

*Gesprochenes → Text + Timing + Konfidenz*

#### Gamma — Fundament
- [ ] …

#### Beta — Komposition
- [ ] …

#### Alpha — Ziel-Capability
- [ ] …

#### Moat-Beitrag
> *Warum reicht „einfach Whisper nutzen" nicht?*
> …

---

### ② Phonetisches Alignment & Segmentierung

*Wort- und phonemgenaue Zuordnung zum Audiosignal*

#### Gamma — Fundament
- [ ] …

#### Beta — Komposition
- [ ] …

#### Alpha — Ziel-Capability
- [ ] …

#### Moat-Beitrag
> *Warum ist Alignment die unsichtbare Schlüsselschicht?*
> …

---

### ③ Aussprache-Bewertung (Pronunciation Scoring)

*Phonem-Accuracy, Mispronunciation Detection, Goodness of Pronunciation*

#### Gamma — Fundament
- [ ] …

#### Beta — Komposition
- [ ] …

#### Alpha — Ziel-Capability
- [ ] …

#### Moat-Beitrag
> *Warum ist ein deutscher Pronunciation Scorer kein Commodity?*
> …

---

### ④ Prosodie & Suprasegmentalia

*Intonation, Betonung, Rhythmus, Sprechrate, Pausen*

#### Gamma — Fundament
- [ ] …

#### Beta — Komposition
- [ ] …

#### Alpha — Ziel-Capability
- [ ] …

#### Moat-Beitrag
> *Warum messen die meisten EdTech-Produkte Prosodie gar nicht — und warum wir schon?*
> …

---

### ⑤ Textbasierte Sprachdiagnostik (CAF+)

*Complexity, Accuracy, Fluency — auf Transkript-/Schreibtextebene*

#### Gamma — Fundament
- [ ] …

#### Beta — Komposition
- [ ] …

#### Alpha — Ziel-Capability
- [ ] …

#### Moat-Beitrag
> *Warum ist regelbasierte Linguistik kein Rückschritt, sondern ein Vorsprung?*
> …

---

### ⑥ Diagnostisches Scoring & CEFR-Mapping

*Integration aller Signale → Lernerprofil → Niveaustufe → Evidenzkette*

#### Gamma — Fundament
- [ ] …

#### Beta — Komposition
- [ ] …

#### Alpha — Ziel-Capability
- [ ] …

#### Moat-Beitrag
> *Warum ist ein CEFR-Score ohne Evidenzkette wertlos — und warum liefern wir beides?*
> …

---

### ⑦ Generatives Coaching & Feedback

*Didaktisch situiertes, erklärbares, adaptives Feedback*

#### Gamma — Fundament
- [ ] …

#### Beta — Komposition
- [ ] …

#### Alpha — Ziel-Capability
- [ ] …

#### Moat-Beitrag
> *Warum ist „GPT sagt dir, was du falsch machst" kein Produkt?*
> …

---

## 2 — Querschnitte

### Q1 — Datenstrategie & Teacher→Student-Logik

> *Warum wird unser Produkt mit jedem Nutzer besser — und warum kann ein Wettbewerber das nicht nachmachen, selbst wenn er unseren Code hätte?*

- [ ] Session-als-Trainingsmaterial-Prinzip
- [ ] Silver Labels (Cloud APIs) → Gold Labels (Human Raters) → In-House-Modelle
- [ ] Ablösungskriterien: Wann ersetzt der Student den Teacher?
- [ ] Daten-Flywheel & Feedback-Loop-Architektur

---

### Q2 — Souveränität & Cloud-Exit-Pfad

> *Warum ist Cloud-Nutzung im MVP kein Widerspruch zur Souveränität — und wie sieht der Exit-Pfad aus?*

- [ ] Was heute Cloud ist (und warum das strategisch okay ist)
- [ ] Was morgen on-prem / Edge sein muss (und welche OSS-Modelle das ermöglichen)
- [ ] Europäische Modell-Ökosysteme (Teuken, OpenGPT-X, LAION, …)
- [ ] DSGVO / Datensouveränität als Feature, nicht als Constraint

---

### Q3 — Evaluation & Benchmarking

> *Woher wissen wir, dass unser Stack besser wird — und wie beweisen wir das?*

- [ ] Metriken pro Domäne (①–⑦)
- [ ] Deutsches Evaluation-Set: Aufbau, Annotation, Versionierung
- [ ] Vergleich mit kommerziellen Baselines (Azure, Duolingo, EF, …)
- [ ] Regressionstests bei Modellwechsel / Pipeline-Änderung

---

## 3 — Das Kompositionsargument

> *Dieses Kapitel entsteht nicht a priori, sondern als Synthese: Es destilliert aus den sieben Domänen und drei Querschnitten die Antwort auf die Leitfrage.*

### 3.1 — Was jeder einzelne Baustein (Gamma) für sich genommen *nicht* kann
- [ ] …

### 3.2 — Welche Kompositionen (Beta) nur funktionieren, wenn man *alle* Domänen kontrolliert
- [ ] …

### 3.3 — Warum der Ziel-Stack (Alpha) mehr ist als die Summe seiner Teile
- [ ] …

### 3.4 — Replikationsbarrieren
- [ ] …

---

## Anhang (spätere Iteration)

- A — Dependency Map (welche Gamma-Bausteine fließen in welche Beta-Kompositionen)
- B — Glossar (CAF, GOP, MFA, CEFR, …)
- C — Roadmap-Entwurf (bewusst ausgeklammert in V1)
