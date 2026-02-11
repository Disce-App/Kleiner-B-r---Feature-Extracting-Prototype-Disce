# Beta · B2 – Schnittstellenverträge & Datenformate

> **Beta-Leitfrage:** *Wie werden die sieben Gamma-Bausteine zu einem durchgängigen System verbunden?*
> **B2-Frage:** *Was genau übergibt jede Domäne an die nächste – und welche Garantien, Validierungsregeln und Invarianten gelten an jeder Schnittstelle?*

> **Abhängigkeit:** B2 baut auf B1 (End-to-End-Pipeline) auf. B1 zeigt *was* fließt; B2 spezifiziert *wie genau*.

---

## 1  Warum Schnittstellenverträge?

### 1.1  Das Problem ohne Verträge

Ohne explizite Schnittstellenverträge passiert in einer Multi-Domänen-Pipeline Folgendes:
- D2 (Alignment) erwartet Wort-Zeitstempel von D1 – aber D1 liefert bei kurzen Äußerungen manchmal `null` statt einer leeren Liste. D2 crasht.
- D3 (Pronunciation) erwartet Phonem-Labels in IPA. D2 liefert SAMPA. Die GOP-Scores sind Nonsens, aber die Pipeline gibt keinen Fehler.
- D6 (Scoring) rechnet mit Prosodie-Features. D4 liefert sie manchmal als Skalar, manchmal als Array. D6 normalisiert falsch.

Diese Bugs sind **die teuersten in ML-Pipelines**: Sie erzeugen keine Fehlermeldungen, sondern falsche Ergebnisse. Der Lerner bekommt ein falsches CEFR-Level, und niemand merkt es.

### 1.2  Contract-First als Prinzip

Disce nutzt **Contract-First Design**: Die Schnittstelle wird *vor* der Implementierung definiert. Jeder Domänenübergang hat:

| Element | Beschreibung |
|---------|--------------|
| **Schema** | Pydantic-Modell (Python-Klasse), das Struktur und Typen definiert |
| **Invarianten** | Bedingungen, die *immer* gelten müssen (z.B. "Zeitstempel sind monoton steigend") |
| **Validierungsregeln** | Automatisierte Prüfungen, die bei Verletzung Fehler oder Warnings erzeugen |
| **Degradation-Flags** | Markierungen, wenn der Output unsicher oder unvollständig ist |

### 1.3  Technologieentscheidung: Pydantic v2

Alle Schnittstellenverträge werden als **Pydantic v2 BaseModel**-Klassen definiert:

- **Runtime-Validierung:** Jedes Zwischenergebnis wird beim Schreiben in den Shared State validiert. Typfehler werden sofort erkannt.
- **JSON-Schema-Export:** Pydantic generiert automatisch JSON-Schemata, die für Dokumentation und externe Konsumenten nutzbar sind.
- **Performance:** Pydantic v2 (Rust-Core) validiert ~10x schneller als v1 – bei den Datenmengen irrelevant, aber ein Bonus.
- **IDE-Support:** Autovervollständigung und Typprüfung in der gesamten Pipeline.

---

## 2  Vertragskatalog: Die sechs Domänenübergänge

### 2.0  Übergangsübersicht

Die Disce-Pipeline hat **sechs explizite Domänenübergänge** und ein **Envelope**, das alles umschließt:

```
Übergang 1: Audio-Input    -> D1  (Eingang in die Pipeline)
Übergang 2: D1 -> D2             (ASR-Transkript -> Alignment)
Übergang 3: D2 -> D3 || D4 || D5  (Alignment -> parallele Analyse, Fork)
Übergang 4: D3 + D4 + D5 -> D6  (Analyse-Ergebnisse -> Scoring, Join)
Übergang 5: D6 -> D7             (Profil -> Coaching)
Übergang 6: D7 -> Client         (Coaching -> Endprodukt)
```

Jeder Übergang wird im Folgenden mit Pydantic-Schema, Invarianten und Validierungsregeln spezifiziert.

---

## 3  Übergang 1: Audio-Input -> D1 (Pipeline-Eingang)

### 3.1  Schema

```python
from pydantic import BaseModel, Field, field_validator
from enum import Enum
from typing import Optional

class AudioFormat(str, Enum):
    WAV = "wav"
    OPUS = "opus"
    MP3 = "mp3"
    OGG = "ogg"
    FLAC = "flac"

class TaskType(str, Enum):
    PICTURE_DESCRIPTION = "picture_description"
    RETELLING = "retelling"
    FREE_SPEECH = "free_speech"
    READ_ALOUD = "read_aloud"
    DIALOGUE = "dialogue"

class AudioInput(BaseModel):
    """Eingangsvertrag: Was die Pipeline als Input akzeptiert."""

    audio_path: str = Field(
        ...,
        description="Pfad zur Audio-Datei im Shared Storage"
    )
    audio_format: AudioFormat = Field(
        ...,
        description="Codec der Audio-Datei"
    )
    sample_rate_hz: int = Field(
        ...,
        ge=8000, le=48000,
        description="Abtastrate in Hz. Empfohlen: 16000"
    )
    channels: int = Field(
        default=1,
        ge=1, le=2,
        description="Kanalanzahl. Pipeline erwartet Mono (1)"
    )
    duration_s: float = Field(
        ...,
        gt=0.5, le=300.0,
        description="Audio-Dauer in Sekunden. Min 0.5s, Max 5 Minuten"
    )
    task_context: "TaskContext" = Field(
        ...,
        description="Aufgabenkontext: Was hat der Lerner gesprochen?"
    )

class TaskContext(BaseModel):
    """Kontext der Sprachaufgabe."""

    task_type: TaskType
    prompt_text: Optional[str] = Field(
        None,
        description="Aufgabenstellung, z.B. 'Beschreiben Sie das Bild'"
    )
    reference_text: Optional[str] = Field(
        None,
        description="Erwarteter Text (nur bei read_aloud)"
    )
    expected_level: Optional[str] = Field(
        None,
        pattern=r"^(A1|A2|B1|B2|C1|C2)(\-(A1|A2|B1|B2|C1|C2))?$",
        description="Erwartetes CEFR-Niveau, z.B. 'A2-B1'"
    )
```

### 3.2  Invarianten

| # | Invariante | Begründung |
|---|-----------|------------|
| I-1.1 | `duration_s >= 0.5` | Unter 0.5s kann kein sinnvolles ASR-Ergebnis erzeugt werden |
| I-1.2 | `channels == 1` oder automatische Mono-Konvertierung | MFA und Whisper erwarten Mono |
| I-1.3 | Wenn `task_type == "read_aloud"`, dann `reference_text is not None` | Ohne Referenztext kann D3 kein Script-basiertes GOP berechnen |
| I-1.4 | Audio-Datei existiert und ist lesbar | Trivial, aber Pipeline-Crash-Grund #1 |

### 3.3  Vorverarbeitung (Pre-D1)

Bevor D1 startet, durchläuft der Audio-Input eine **Normalisierungsstufe**, die *kein* eigener Domänenbaustein ist, sondern ein Pipeline-Gate:

```python
class AudioPreprocessor:
    """Normalisiert Audio auf Pipeline-Standard."""

    def normalize(self, input: AudioInput) -> AudioInput:
        # 1. Stereo -> Mono (Mittelung beider Kanäle)
        # 2. Resample auf 16 kHz (falls nötig)
        # 3. Normalisierung auf -3 dBFS Peak
        # 4. Stille-Trimming am Anfang/Ende (> 1s Stille)
        # 5. Format-Konvertierung -> WAV 16-bit PCM
        ...
```

---

## 4  Übergang 2: D1 -> D2 (ASR -> Alignment)

### 4.1  D1-Output-Schema

```python
from typing import List
from pydantic import BaseModel, Field, field_validator, model_validator

class WordTimestamp(BaseModel):
    """Einzelnes Wort mit Zeitstempel aus ASR."""

    word: str = Field(..., min_length=1)
    start: float = Field(..., ge=0.0, description="Startzeit in Sekunden")
    end: float = Field(..., ge=0.0, description="Endzeit in Sekunden")
    confidence: float = Field(..., ge=0.0, le=1.0, description="ASR-Konfidenz")

    @model_validator(mode="after")
    def end_after_start(self):
        if self.end <= self.start:
            raise ValueError(f"end ({self.end}) must be > start ({self.start})")
        return self

class ASRSegment(BaseModel):
    """Ein Transkriptions-Segment (typisch: 1 Satz oder Phrase)."""

    text: str = Field(..., min_length=1)
    start: float = Field(..., ge=0.0)
    end: float = Field(..., ge=0.0)
    words: List[WordTimestamp] = Field(..., min_length=1)

class D1Output(BaseModel):
    """Vertrag: Was D1 (ASR) an D2 (Alignment) uebergibt."""

    transcript: str = Field(
        ...,
        min_length=1,
        description="Vollstaendiger Transkriptionstext"
    )
    segments: List[ASRSegment] = Field(
        ...,
        min_length=1,
        description="Segmentierte Transkription mit Zeitstempeln"
    )
    language: str = Field(
        default="de",
        pattern=r"^[a-z]{2}$",
        description="ISO 639-1 Sprachcode"
    )
    language_confidence: float = Field(
        ...,
        ge=0.0, le=1.0,
        description="Konfidenz der Spracherkennung"
    )
    meta: "D1Meta" = Field(...)

    @field_validator("segments")
    @classmethod
    def segments_chronological(cls, v):
        for i in range(1, len(v)):
            if v[i].start < v[i-1].start:
                raise ValueError(f"Segment {i} starts before segment {i-1}")
        return v

class D1Meta(BaseModel):
    """Metadaten des ASR-Laufs."""

    model: str = Field(..., description="z.B. 'whisper-large-v3'")
    runtime: str = Field(..., description="z.B. 'faster-whisper'")
    duration_audio_s: float = Field(..., gt=0)
    duration_processing_s: float = Field(..., gt=0)
    realtime_factor: float = Field(
        ..., gt=0,
        description="Audio-Dauer / Processing-Dauer. >1 = schneller als Echtzeit"
    )
```

### 4.2  Invarianten D1 -> D2

| # | Invariante | Prüfung | Konsequenz bei Verletzung |
|---|-----------|---------|--------------------------|
| I-2.1 | **Transkript nicht leer** | `len(transcript) > 0` | Pipeline-Abbruch: Ohne Text kein Alignment |
| I-2.2 | **Zeitstempel monoton steigend** pro Segment | `words[i].start <= words[i+1].start` | Warning + Reorder (autokorrigierbar) |
| I-2.3 | **Zeitstempel innerhalb Audio-Dauer** | `max(end) <= duration_audio_s + 0.5` | Warning, toleriert 0.5s Überlauf (Whisper-Artefakt) |
| I-2.4 | **Sprache ist Deutsch** | `language == "de"` | Soft-Warning: Pipeline läuft weiter, aber Flag wird gesetzt |
| I-2.5 | **Mindest-Konfidenz** | `mean(word.confidence) >= 0.3` | Degradation-Flag: D6 gewichtet alle D1-abhängigen Scores runter |

### 4.3  D2-Input-Anforderungen

D2 konsumiert nicht nur D1Output, sondern auch das Original-Audio:

```python
class D2Input(BaseModel):
    """Was D2 (Alignment) als Input benoetigt."""

    audio_path: str = Field(..., description="Pfad zum normalisierten Audio (16 kHz, Mono, WAV)")
    d1_output: D1Output = Field(..., description="ASR-Ergebnis aus D1")
    dictionary_id: str = Field(
        default="disce_de_ipa_v2",
        description="ID des Pronunciation Dictionary"
    )
```

---

## 5  Übergang 3: D2 -> D3 || D4 || D5 (Der Fork)

### 5.1  D2-Output-Schema (Alignment-Ergebnis)

```python
from typing import List, Optional
from enum import Enum

class PhoneInterval(BaseModel):
    """Einzelnes Phonem mit Zeitgrenzen."""

    phone: str = Field(
        ...,
        min_length=1,
        description="IPA-Symbol des Phonems, z.B. 'c', 'e:', 'S'"
    )
    start: float = Field(..., ge=0.0)
    end: float = Field(..., ge=0.0)

    @model_validator(mode="after")
    def end_after_start(self):
        if self.end <= self.start:
            raise ValueError(f"Phone '{self.phone}': end ({self.end}) must be > start ({self.start})")
        return self

class AlignmentConfidenceLevel(str, Enum):
    HIGH = "high"           # MFA + WebMAUS uebereinstimmend
    MEDIUM = "medium"       # MFA allein, plausibel
    LOW = "low"             # MFA/WebMAUS divergent > 30ms
    FALLBACK = "fallback"   # Whisper-Timestamps als Fallback genutzt

class AlignedWord(BaseModel):
    """Wort mit Phonem-Alignment."""

    word: str = Field(..., min_length=1)
    start: float = Field(..., ge=0.0)
    end: float = Field(..., ge=0.0)
    phones: List[PhoneInterval] = Field(
        ...,
        min_length=1,
        description="Phoneme innerhalb dieses Wortes, chronologisch"
    )
    alignment_confidence: AlignmentConfidenceLevel = Field(
        default=AlignmentConfidenceLevel.MEDIUM
    )
    canonical_phones: List[str] = Field(
        ...,
        min_length=1,
        description="Erwartete Phonem-Sequenz laut Dictionary, z.B. ['I', 'c']"
    )

    @model_validator(mode="after")
    def phones_within_word(self):
        if self.phones:
            if self.phones[0].start < self.start - 0.01:
                raise ValueError("First phone starts before word")
            if self.phones[-1].end > self.end + 0.01:
                raise ValueError("Last phone ends after word")
        return self

class D2Output(BaseModel):
    """Vertrag: Was D2 (Alignment) an D3/D4/D5 uebergibt."""

    words: List[AlignedWord] = Field(
        ...,
        min_length=1,
        description="Woerter mit Phonem-Alignment"
    )
    total_phones: int = Field(
        ..., gt=0,
        description="Gesamtzahl der Phoneme"
    )
    alignment_confidence_overall: float = Field(
        ..., ge=0.0, le=1.0,
        description="Gesamt-Alignment-Konfidenz (0-1)"
    )
    meta: "D2Meta" = Field(...)

    @field_validator("words")
    @classmethod
    def words_chronological(cls, v):
        for i in range(1, len(v)):
            if v[i].start < v[i-1].start:
                raise ValueError(f"Word {i} ('{v[i].word}') starts before word {i-1}")
        return v

class D2Meta(BaseModel):
    """Metadaten des Alignment-Laufs."""

    aligner: str = Field(..., description="z.B. 'MFA-3.0'")
    acoustic_model: str = Field(..., description="z.B. 'german_mfa_l2_adapted'")
    dictionary: str = Field(..., description="z.B. 'disce_de_ipa_v2'")
    verification: Optional[str] = Field(
        None, description="z.B. 'webmaus_local'. None = keine Verifikation"
    )
    duration_processing_s: float = Field(..., gt=0)
    phones_divergent_count: int = Field(
        default=0,
        ge=0,
        description="Anzahl Phoneme mit MFA/WebMAUS-Divergenz > 30ms"
    )
```

### 5.2  Invarianten D2 -> D3/D4/D5

| # | Invariante | Prüfung | Konsequenz |
|---|-----------|---------|-----------|
| I-3.1 | **Alle Phoneme in IPA** | Regex-Check gegen IPA-Charakter-Set | Fehler: SAMPA/X-SAMPA würde GOP-Berechnung verfälschen |
| I-3.2 | **Phoneme lückenlos innerhalb Wort** | `phones[i].end ~ phones[i+1].start` (Toleranz 10ms) | Warning: Lücken werden mit Stille-Segment gefüllt |
| I-3.3 | **Canonical Phones vorhanden** | `len(canonical_phones) > 0` für jedes Wort | Fehler: Ohne kanonische Sequenz kein GOP-Vergleich in D3 |
| I-3.4 | **Mindestens 3 Wörter** | `len(words) >= 3` | Degradation: Zu wenig Material für robuste Analyse. D4 (Prosodie) und D5 (Textdiagnostik) produzieren reduziertes Output |
| I-3.5 | **Alignment-Konfidenz** | `alignment_confidence_overall >= 0.5` | Degradation-Flag: D3-Scores erhalten Unsicherheits-Marker |

### 5.3  Der Fork: Wer bekommt was?

Die drei parallelen Domänen konsumieren **unterschiedliche Teilmengen** des D2-Outputs (plus weitere Inputs):

```python
class D3Input(BaseModel):
    """Input fuer Pronunciation Scoring."""
    audio_path: str
    d2_output: D2Output                  # Phonem-Alignment (Kernbedarf)
    d1_transcript: str                    # Transkript als Referenz
    reference_text: Optional[str] = None  # Bei read_aloud: der Soll-Text

class D4Input(BaseModel):
    """Input fuer Prosodie & Suprasegmentalia."""
    audio_path: str
    word_timestamps: List[WordTimestamp]   # Nur Wort-Ebene aus D2 (keine Phoneme noetig)
    d1_transcript: str                     # Fuer Intonationsanalyse (Frage vs. Aussage)

class D5Input(BaseModel):
    """Input fuer Textbasierte Diagnostik (CAF+)."""
    transcript: str                        # Transkript-Text aus D1
    word_timestamps: Optional[List[WordTimestamp]] = None  # Fuer zeitliche Zuordnung der Fehler
```

**Designentscheidung:** D4 und D5 brauchen *kein* Phonem-Alignment. Sie erhalten nur Wort-Zeitstempel. Das minimiert die Kopplung: Selbst wenn das Phonem-Alignment komplett fehlschlägt, können D4 und D5 mit Whisper-Zeitstempeln als Fallback arbeiten.

---

## 6  Übergang 4: D3 + D4 + D5 -> D6 (Der Join)

### 6.1  D3-Output-Schema (Pronunciation Scoring)

```python
class MDDLabel(str, Enum):
    CORRECT = "correct"
    SUBSTITUTION = "substitution"
    DELETION = "deletion"
    INSERTION = "insertion"

class ArticulatoryDetail(BaseModel):
    """Artikulatorische Fehlerbeschreibung."""
    place_error: bool = False
    place_target: Optional[str] = None      # z.B. "palatal"
    place_produced: Optional[str] = None    # z.B. "postalveolar"
    manner_error: bool = False
    manner_target: Optional[str] = None
    manner_produced: Optional[str] = None
    voicing_error: bool = False

class PhoneScore(BaseModel):
    """Pronunciation Score fuer ein einzelnes Phonem."""

    phone_target: str = Field(..., description="Ziel-Phonem (IPA)")
    phone_produced: Optional[str] = Field(
        None, description="Tatsaechlich produziertes Phonem (IPA). None bei Deletion"
    )
    gop_score: float = Field(
        ...,
        description="Goodness of Pronunciation Score (log-posterior, typisch -15 bis 2)"
    )
    mdd_label: MDDLabel = Field(...)
    articulatory_detail: Optional[ArticulatoryDetail] = None
    time_ref: "TimeRef" = Field(...)
    confidence: float = Field(
        ..., ge=0.0, le=1.0,
        description="Konfidenz des Pronunciation Scores"
    )

class TimeRef(BaseModel):
    """Zeitreferenz, bindet Score an Audio-Position."""
    start: float = Field(..., ge=0.0)
    end: float = Field(..., ge=0.0)

class WordPronunciationScore(BaseModel):
    """Aggregierter Pronunciation Score pro Wort."""

    word: str = Field(...)
    pronunciation_score: float = Field(
        ..., ge=0.0, le=1.0,
        description="Normalisierter Score 0-1"
    )
    phone_scores: List[PhoneScore] = Field(...)
    flags: List[str] = Field(
        default_factory=list,
        description="z.B. ['substitution:c->S', 'deletion:@']"
    )

class D3Output(BaseModel):
    """Vertrag: Was D3 (Pronunciation Scoring) an D6 uebergibt."""

    word_scores: List[WordPronunciationScore] = Field(..., min_length=1)
    utterance_score: float = Field(
        ..., ge=0.0, le=1.0,
        description="Gesamt-Aussprache-Score der Aeusserung"
    )
    error_summary: "PronunciationErrorSummary" = Field(...)
    meta: "D3Meta" = Field(...)

class PronunciationErrorSummary(BaseModel):
    """Aggregierte Fehlerstatistik."""
    total_phones: int = Field(..., gt=0)
    correct_phones: int = Field(..., ge=0)
    substitutions: int = Field(..., ge=0)
    deletions: int = Field(..., ge=0)
    insertions: int = Field(..., ge=0)
    error_rate: float = Field(
        ..., ge=0.0, le=1.0,
        description="(sub + del + ins) / total_phones"
    )
    top_error_patterns: List[str] = Field(
        default_factory=list,
        description="Haeufigste Fehler, z.B. ['c->S (3x)', 'R->r (2x)']"
    )

class D3Meta(BaseModel):
    gop_backend: str = Field(..., description="z.B. 'kaldi_dnn_ali'")
    mdd_backend: str = Field(..., description="z.B. 'wav2vec2_ctc'")
    articulatory_backend: Optional[str] = Field(None)
    duration_processing_s: float = Field(..., gt=0)
```

### 6.2  D4-Output-Schema (Prosodie & Suprasegmentalia)

```python
class PauseType(str, Enum):
    SILENT = "silent"
    FILLED = "filled"   # "aehm", "aeh"

class Pause(BaseModel):
    """Einzelne Pause in der Aeusserung."""
    start: float = Field(..., ge=0.0)
    end: float = Field(..., ge=0.0)
    duration: float = Field(..., gt=0.0)
    pause_type: PauseType
    filler: Optional[str] = Field(
        None, description="Fuellwort, z.B. 'aehm'. Nur bei FILLED"
    )

class RhythmMetrics(BaseModel):
    """Rhythmusmetriken der Aeusserung."""
    pvi_vocalic: float = Field(..., description="Pairwise Variability Index (vokalisch)")
    pvi_consonantal: float = Field(..., description="PVI (konsonantisch)")
    percent_v: float = Field(
        ..., ge=0.0, le=1.0,
        description="Anteil vokalischer Intervalle an Gesamtdauer"
    )

class FluencyMetrics(BaseModel):
    """Sprechfluessigkeits-Metriken (audiobasiert)."""
    speech_rate_syl_per_s: float = Field(
        ..., gt=0,
        description="Silben pro Sekunde (inkl. Pausen)"
    )
    articulation_rate: float = Field(
        ..., gt=0,
        description="Silben pro Sekunde (exkl. Pausen)"
    )
    mean_length_of_run: float = Field(
        ..., gt=0,
        description="Mittlere Silbenzahl zwischen Pausen"
    )
    pause_frequency: float = Field(
        ..., ge=0.0,
        description="Pausen pro Sekunde"
    )
    total_pause_duration_s: float = Field(..., ge=0.0)
    total_speech_duration_s: float = Field(..., gt=0.0)

class D4Output(BaseModel):
    """Vertrag: Was D4 (Prosodie) an D6 uebergibt."""

    rhythm: RhythmMetrics = Field(...)
    fluency: FluencyMetrics = Field(...)
    pauses: List[Pause] = Field(
        default_factory=list,
        description="Liste aller Pausen. Kann leer sein (bei sehr fluessiger Sprache)"
    )
    f0_summary: "F0Summary" = Field(...)
    meta: "D4Meta" = Field(...)

class F0Summary(BaseModel):
    """Zusammenfassung der Grundfrequenz-Analyse."""
    f0_mean_hz: float = Field(..., gt=0)
    f0_std_hz: float = Field(..., ge=0)
    f0_range_hz: float = Field(..., ge=0, description="max(F0) - min(F0)")
    f0_contour_available: bool = Field(
        default=True,
        description="Ob die volle F0-Kontur im Detail-Store verfuegbar ist"
    )

class D4Meta(BaseModel):
    f0_method: str = Field(..., description="z.B. 'parselmouth_cc'")
    vad_method: str = Field(default="energy_based")
    sample_rate: int = Field(default=16000)
    duration_processing_s: float = Field(..., gt=0)
```

**Designentscheidung: F0-Kontur nicht im Vertrag.**
Die vollstaendige F0-Kontur (tausende Werte) wird *nicht* im D4Output-Vertrag transportiert, sondern in den Detail-Store geschrieben. D6 braucht nur die Summary-Statistiken. Die volle Kontur ist fuer Visualisierung (Frontend) und Debugging verfuegbar, aber kein Vertrags-Bestandteil.

### 6.3  D5-Output-Schema (Textbasierte Diagnostik)

```python
class GrammarErrorType(str, Enum):
    CASE = "case"                    # Kasusmarkierung
    GENDER = "gender"                # Genus
    NUMBER = "number"                # Numerus
    TENSE = "tense"                  # Tempus
    WORD_ORDER = "word_order"        # Wortstellung
    AGREEMENT = "agreement"          # Kongruenz
    PREPOSITION = "preposition"      # Praeposition
    ARTICLE = "article"              # Artikelgebrauch
    CONJUGATION = "conjugation"      # Konjugation
    OTHER = "other"

class GrammarError(BaseModel):
    """Einzelner Grammatikfehler."""
    error_type: GrammarErrorType
    subtype: Optional[str] = Field(
        None, description="Feinere Klassifikation, z.B. 'present_for_past'"
    )
    surface: str = Field(..., description="Fehlerhafter Text im Original")
    correction: Optional[str] = Field(
        None, description="Korrekturvorschlag. None = keine sichere Korrektur"
    )
    position: "TextPosition" = Field(...)
    confidence: float = Field(..., ge=0.0, le=1.0)
    rule_id: Optional[str] = Field(
        None, description="LanguageTool-Rule-ID, z.B. 'DE_CASE'"
    )

class TextPosition(BaseModel):
    """Position eines Tokens / Fehlers im Transkript."""
    word_idx: int = Field(..., ge=0, description="Index im Wort-Array")
    char_start: int = Field(..., ge=0, description="Zeichenposition im Transkript")
    char_end: int = Field(..., ge=0)
    time_ref: Optional[TimeRef] = Field(
        None, description="Zeitreferenz (wenn Alignment verfuegbar)"
    )

class ComplexityMetrics(BaseModel):
    """Syntaktische Komplexitaet."""
    mls: float = Field(..., gt=0, description="Mean Length of Sentence (in Woertern)")
    subordination_index: float = Field(
        ..., ge=1.0,
        description="Verhaeltnis Nebensaetze/T-Units. 1.0 = keine Subordination"
    )
    max_dependency_depth: int = Field(..., ge=1)
    clause_count: int = Field(..., ge=1)
    t_unit_count: int = Field(..., ge=1)

class LexicalMetrics(BaseModel):
    """Lexikalische Diversitaet und Reichhaltigkeit."""
    ttr: float = Field(
        ..., ge=0.0, le=1.0,
        description="Type-Token-Ratio"
    )
    mtld: float = Field(
        ..., ge=0,
        description="Measure of Textual Lexical Diversity"
    )
    hd_d: float = Field(
        ..., ge=0.0, le=1.0,
        description="HD-D lexical diversity"
    )
    frequency_bands: dict = Field(
        ...,
        description="Verteilung nach CEFR-Wortschatz: {'A1': 0.45, 'A2': 0.25, ...}"
    )

class TextFluencyMetrics(BaseModel):
    """Textbasierte Fluessigkeits-Indikatoren (ergaenzt D4-Audio-Fluency)."""
    repairs: int = Field(..., ge=0, description="Selbstkorrekturen")
    repetitions: int = Field(..., ge=0, description="Wortwiederholungen")
    false_starts: int = Field(..., ge=0, description="Satzabbrueche")
    total_words: int = Field(..., gt=0)
    disfluency_rate: float = Field(
        ..., ge=0.0, le=1.0,
        description="(repairs + repetitions + false_starts) / total_words"
    )

class D5Output(BaseModel):
    """Vertrag: Was D5 (Textdiagnostik) an D6 uebergibt."""

    complexity: ComplexityMetrics = Field(...)
    accuracy: "AccuracyResult" = Field(...)
    fluency_text: TextFluencyMetrics = Field(...)
    lexical: LexicalMetrics = Field(...)
    meta: "D5Meta" = Field(...)

class AccuracyResult(BaseModel):
    """Grammatische Korrektheit."""
    error_rate: float = Field(
        ..., ge=0.0, le=1.0,
        description="Fehler pro Wort"
    )
    errors: List[GrammarError] = Field(
        default_factory=list,
        description="Detaillierte Fehlerliste"
    )
    total_words: int = Field(..., gt=0)
    error_count: int = Field(..., ge=0)

class D5Meta(BaseModel):
    nlp_model: str = Field(..., description="z.B. 'de_dep_news_trf'")
    gec_engine: str = Field(..., description="z.B. 'languagetool_6.4'")
    duration_processing_s: float = Field(..., gt=0)
```

### 6.4  D6-Input: Der Join-Vertrag

```python
class DegradationFlag(str, Enum):
    """Flags, die anzeigen, dass ein Upstream-Ergebnis unsicher oder fehlend ist."""
    D1_LOW_CONFIDENCE = "d1_low_confidence"         # ASR-Konfidenz < 0.3
    D2_ALIGNMENT_UNSTABLE = "d2_alignment_unstable" # Alignment-Konfidenz < 0.5
    D3_MISSING = "d3_missing"                       # D3 komplett ausgefallen
    D3_LOW_CONFIDENCE = "d3_low_confidence"          # D3 teilweise unsicher
    D4_MISSING = "d4_missing"                       # D4 komplett ausgefallen
    D5_MISSING = "d5_missing"                       # D5 komplett ausgefallen
    INSUFFICIENT_MATERIAL = "insufficient_material"  # < 3 Woerter

class D6Input(BaseModel):
    """Vertrag: Was D6 (Scoring) als Input erhaelt (Join aller Analyseergebnisse)."""

    d3_output: Optional[D3Output] = Field(
        None,
        description="Pronunciation Scoring. None = D3 ausgefallen"
    )
    d4_output: Optional[D4Output] = Field(
        None,
        description="Prosodie. None = D4 ausgefallen"
    )
    d5_output: Optional[D5Output] = Field(
        None,
        description="Textdiagnostik. None = D5 ausgefallen"
    )
    d1_meta: D1Meta = Field(
        ...,
        description="ASR-Metadaten fuer Konfidenz-Gewichtung"
    )
    degradation_flags: List[DegradationFlag] = Field(
        default_factory=list,
        description="Aktive Degradation-Flags"
    )

    @model_validator(mode="after")
    def at_least_one_analysis(self):
        if self.d3_output is None and self.d4_output is None and self.d5_output is None:
            raise ValueError(
                "Mindestens ein Analyse-Ergebnis (D3, D4 oder D5) muss vorliegen. "
                "Komplettausfall aller drei Domaenen -> Pipeline-Abbruch."
            )
        return self
```

**Die zentrale Designentscheidung:** D3, D4 und D5 sind alle `Optional`. D6 *muss* mit partiellen Ergebnissen umgehen koennen. Wenn nur D5 (Text) vorliegt, erstellt D6 ein reines Text-Profil (Grammatik + Lexik), ohne Aussprache und Prosodie. Das Profil traegt dann die entsprechenden Degradation-Flags.

### 6.5  Invarianten am Join-Punkt

| # | Invariante | Prüfung | Konsequenz |
|---|-----------|---------|-----------|
| I-4.1 | **Mindestens 1 von 3 Analysen** | `d3 or d4 or d5 is not None` | Pipeline-Abbruch (s.o.) |
| I-4.2 | **Konsistente Wort-Counts** | `D3.word_count ~ D5.total_words` (+/-10 %) | Warning: Inkonsistenz deutet auf ASR-Instabilitaet hin |
| I-4.3 | **Degradation-Flags korrekt gesetzt** | Wenn `d3 is None`, dann `D3_MISSING in flags` | Automatisch: Der Orchestrator setzt Flags, nicht die Domaenen |
| I-4.4 | **Zeitliche Konsistenz** | D3-Zeitreferenzen und D4-Pausenzeiten passen zum selben Audio | Plausibilitaetspruefung, kein Hard-Fail |

---

## 7  Übergang 5: D6 -> D7 (Profil -> Coaching)

### 7.1  D6-Output-Schema

```python
class CEFRLevel(str, Enum):
    A1 = "A1"
    A1_PLUS = "A1+"
    A2 = "A2"
    A2_PLUS = "A2+"
    B1 = "B1"
    B1_PLUS = "B1+"
    B2 = "B2"
    B2_PLUS = "B2+"
    C1 = "C1"
    C1_PLUS = "C1+"
    C2 = "C2"

class DimensionScore(BaseModel):
    """Score fuer eine einzelne Profil-Dimension."""

    score: float = Field(
        ..., ge=0, le=100,
        description="Normalisierter Score 0-100"
    )
    cefr_indication: CEFRLevel = Field(
        ...,
        description="Indikative CEFR-Stufe fuer diese Dimension"
    )
    confidence: float = Field(
        ..., ge=0.0, le=1.0,
        description="Konfidenz des Scores"
    )
    is_degraded: bool = Field(
        default=False,
        description="True wenn dieser Score auf unvollstaendigen Daten basiert"
    )
    evidence_refs: List[str] = Field(
        default_factory=list,
        description="Verweise auf konkrete Evidenz, z.B. 'D3.phone_scores[5]'"
    )

class PriorityTarget(BaseModel):
    """Empfehlung fuer Lernfokus, abgeleitet aus dem Profil."""

    dimension: str = Field(..., description="z.B. 'grammar'")
    specific: str = Field(
        ..., description="Konkretes Lernziel, z.B. 'Kasusmarkierung Akkusativ/Dativ'"
    )
    severity: str = Field(
        ...,
        description="'focus_area' | 'improvement_possible' | 'minor'"
    )
    source: str = Field(
        ..., description="Welche Domaene die Evidenz liefert, z.B. 'D5_errors'"
    )
    examples: List[str] = Field(
        default_factory=list,
        description="Konkrete Beispiele aus der Aeusserung"
    )

class D6Output(BaseModel):
    """Vertrag: Was D6 (Scoring) an D7 (Coaching) uebergibt."""

    profile: dict = Field(
        ...,
        description="Radar-Profil: Keys = 'pronunciation', 'prosody', 'grammar', 'lexical', 'fluency'"
    )
    cefr_overall: "CEFROverall" = Field(...)
    priority_targets: List[PriorityTarget] = Field(
        ...,
        description="1-5 priorisierte Lernziele"
    )
    meta: "D6Meta" = Field(...)

class CEFROverall(BaseModel):
    """CEFR-Gesamteinstufung."""
    level: CEFRLevel
    confidence: float = Field(..., ge=0.0, le=1.0)
    caveat: Optional[str] = Field(
        None,
        description="Einschraenkung, z.B. 'Prosodie-Daten fehlen, Level basiert nur auf Text + Aussprache'"
    )

class D6Meta(BaseModel):
    scoring_model: str = Field(..., description="z.B. 'ordinal_regression_v1'")
    reference_corpus: str = Field(..., description="z.B. 'merlin_de_stats_v3'")
    degraded_dimensions: List[str] = Field(
        default_factory=list,
        description="Dimensionen mit reduzierter Aussagekraft"
    )
    duration_processing_s: float = Field(..., gt=0)
```

### 7.2  Invarianten D6 -> D7

| # | Invariante | Prüfung | Konsequenz |
|---|-----------|---------|-----------|
| I-5.1 | **Profil hat mindestens 2 Dimensionen** | `len(profile) >= 2` | Mindestanforderung fuer sinnvolles Feedback |
| I-5.2 | **Priority Targets vorhanden** | `len(priority_targets) >= 1` | Ohne Targets kann D7 kein fokussiertes Coaching generieren |
| I-5.3 | **Scores im Bereich 0-100** | `0 <= score <= 100` fuer alle Dimensionen | Pydantic-Validierung, automatisch |
| I-5.4 | **CEFR-Level plausibel** | `cefr_overall.level` in {A1..C2} | Pydantic-Enum, automatisch |
| I-5.5 | **Caveat gesetzt bei Degradation** | Wenn `degraded_dimensions` nicht leer, dann `caveat is not None` | Transparenz: D7 muss Einschraenkungen im Feedback kommunizieren |

---

## 8  Übergang 6: D7 -> Client (Pipeline-Ausgang)

### 8.1  D7-Output-Schema (Endprodukt)

```python
class FeedbackDimension(BaseModel):
    """Feedback fuer eine einzelne Dimension."""
    dimension: str
    message: str = Field(
        ..., min_length=10,
        description="Natuerlichsprachliches Feedback"
    )
    severity: str = Field(
        ..., description="'strength' | 'focus_area' | 'improvement_possible'"
    )
    examples: List[str] = Field(default_factory=list)

class ExerciseItem(BaseModel):
    """Einzelne Uebungsaufgabe."""
    prompt: str = Field(...)
    target: str = Field(...)
    distractors: List[str] = Field(default_factory=list)
    hint: Optional[str] = None

class ExerciseType(str, Enum):
    FILL_IN_THE_BLANK = "fill_in_the_blank"
    MULTIPLE_CHOICE = "multiple_choice"
    MINIMAL_PAIR = "minimal_pair"
    SENTENCE_CORRECTION = "sentence_correction"
    REPEAT_AFTER_MODEL = "repeat_after_model"

class Exercise(BaseModel):
    """Generierte Uebung."""
    exercise_type: ExerciseType
    topic: str = Field(...)
    target_dimension: str = Field(...)
    target_cefr: CEFRLevel = Field(...)
    items: List[ExerciseItem] = Field(..., min_length=1)

class D7Output(BaseModel):
    """Vertrag: Was die Pipeline an den Client liefert."""

    feedback: "FeedbackResult" = Field(...)
    exercise: Optional[Exercise] = Field(
        None,
        description="Generierte Uebung. None = keine Uebung generiert"
    )
    profile_summary: D6Output = Field(
        ...,
        description="Das vollstaendige Profil (Durchreiche von D6)"
    )
    meta: "D7Meta" = Field(...)

class FeedbackResult(BaseModel):
    """Strukturiertes Feedback."""
    summary: str = Field(
        ..., min_length=20,
        description="Zusammenfassung in 2-3 Saetzen"
    )
    dimension_feedback: List[FeedbackDimension] = Field(
        ..., min_length=1,
        description="Feedback pro Dimension"
    )
    tone: str = Field(
        default="encouraging",
        description="Tonalitaet des Feedbacks: 'encouraging' | 'neutral'"
    )

class D7Meta(BaseModel):
    llm_model: str = Field(..., description="z.B. 'mistral-7b-instruct'")
    prompt_template: str = Field(..., description="z.B. 'coaching_v2_de'")
    guardrail_passed: bool = Field(...)
    guardrail_flags: List[str] = Field(
        default_factory=list,
        description="z.B. ['tone_adjusted', 'hallucination_filtered']"
    )
    duration_processing_s: float = Field(..., gt=0)
```

### 8.2  Invarianten D7 -> Client

| # | Invariante | Prüfung | Konsequenz |
|---|-----------|---------|-----------|
| I-6.1 | **Guardrails bestanden** | `guardrail_passed == True` | Wenn False: generisches Fallback-Feedback statt LLM-Output |
| I-6.2 | **Feedback referenziert nur existierende Dimensionen** | Dimensions in `dimension_feedback` sind Subset von `profile.keys()` | Kein Feedback zu Prosodie, wenn Prosodie-Score degraded/missing |
| I-6.3 | **Übung passt zum Profil** | `exercise.target_cefr` <= `cefr_overall.level` + 1 Stufe | Übung darf maximal eine Stufe über dem aktuellen Level sein |
| I-6.4 | **Feedback-Sprache = Deutsch** | Spracherkennung auf `summary` | LLM-Output muss in der Lerner-Sprache sein |
| I-6.5 | **Keine PII im Feedback** | Regex-/NER-Check auf summary + dimension_feedback | Kein Durchleaken von Audio-Pfaden, IDs etc. |

---

## 9  Das Assessment-Envelope: Gesamtvertrag

### 9.1  Envelope-Schema

Alle Domänen-Outputs werden in ein **Assessment-Envelope** eingebettet, das als Audit-Trail und Replay-Basis dient:

```python
from datetime import datetime
from typing import Optional, List
from enum import Enum

class StageStatus(str, Enum):
    PENDING = "pending"
    RUNNING = "running"
    COMPLETED = "completed"
    FAILED = "failed"
    SKIPPED = "skipped"

class StageResult(BaseModel):
    """Wrapper fuer ein einzelnes Domaenen-Ergebnis im Envelope."""
    status: StageStatus
    result: Optional[dict] = Field(
        None, description="Domaenen-Output als dict (serialisiertes Pydantic-Modell)"
    )
    error: Optional[str] = Field(
        None, description="Fehlermeldung bei status=FAILED"
    )
    started_at: Optional[datetime] = None
    completed_at: Optional[datetime] = None
    duration_s: Optional[float] = None

class AssessmentEnvelope(BaseModel):
    """Das vollstaendige Assessment-Ergebnis aller Domaenen."""

    job_id: str = Field(..., description="UUID v4")
    audio_ref: str = Field(..., description="Pfad zur Audio-Datei")
    created_at: datetime
    task_context: TaskContext

    stages: dict = Field(
        ...,
        description="Keys: 'd1_asr', 'd2_alignment', 'd3_pronunciation', 'd4_prosody', 'd5_text', 'd6_scoring', 'd7_coaching'"
    )

    pipeline_meta: "PipelineMeta" = Field(...)

class PipelineMeta(BaseModel):
    """Pipeline-Level Metadaten."""
    pipeline_version: str = Field(..., description="SemVer, z.B. '0.1.0'")
    total_duration_s: float = Field(..., gt=0)
    degraded_stages: List[str] = Field(default_factory=list)
    degradation_flags: List[DegradationFlag] = Field(default_factory=list)
```

### 9.2  Envelope-Invarianten

| # | Invariante | Begründung |
|---|-----------|------------|
| E-1 | **Alle 7 Stages haben einen Eintrag** | Auch `SKIPPED` oder `FAILED` werden protokolliert |
| E-2 | **Timestamps chronologisch** | `stages[d1].started_at < stages[d2].started_at < ...` (mit Ausnahme der parallelen Stufe) |
| E-3 | **Job-ID ist UUID v4** | Eindeutigkeit ueber Sessions hinweg |
| E-4 | **Versionierung** | `pipeline_version` ermoeglicht Reproduzierbarkeit und A/B-Tests |

---

## 10  Validierungsstrategie: Wann und wie werden Verträge geprüft?

### 10.1  Validierungspunkte

```
Audio-In                    D1-Out                   D2-Out
   |                          |                        |
   v                          v                        v
+------+  validate()    +------+  validate()    +------+  validate()
| Gate | ------------->| Gate | ------------->| Gate | ------ ...
|  0   |                |  1   |                |  2   |
+------+                +------+                +------+
```

Jeder **Gate** ist ein `validate()`-Call auf dem Pydantic-Modell, der vor dem Schreiben in den Shared State ausgeführt wird:

```python
def write_stage_result(job_id: str, stage: str, output: BaseModel):
    """Schreibt ein validiertes Domaenen-Ergebnis in den Shared State."""

    # 1. Pydantic-Validierung (Typen, Ranges, Invarianten)
    validated = output.model_validate(output.model_dump())

    # 2. Serialisierung
    data = validated.model_dump(mode="json")

    # 3. Schreiben in Redis (Shared State)
    redis_client.hset(f"job:{job_id}", stage, json.dumps(data))

    # 4. Envelope-Update
    update_envelope_stage(job_id, stage, status="completed", result=data)
```

### 10.2  Validierungs-Ebenen

| Ebene | Was | Wann | Wie |
|-------|-----|------|-----|
| **L1: Typ-Validierung** | Sind alle Felder vorhanden und korrekt typisiert? | Bei jedem `model_validate()` | Pydantic automatisch |
| **L2: Range-Validierung** | Sind Werte in plausiblen Bereichen? | Bei jedem `model_validate()` | Pydantic-Constraints (`ge=0`, `le=1` etc.) |
| **L3: Struktur-Invarianten** | Sind Zeitstempel monoton? Sind Phoneme innerhalb von Wörtern? | Bei jedem `model_validate()` | Pydantic-Validatoren (`@model_validator`) |
| **L4: Cross-Domain-Invarianten** | Stimmen Wort-Counts über D3/D5 überein? | Am Join-Punkt (D6-Input) | Explizite Prüfung im Orchestrator |
| **L5: Semantische Plausibilität** | Ist ein CEFR-C2-Score bei 80 % Fehlerrate plausibel? | Post-D6, vor D7 | Regelbasierte Plausibilitäts-Checks |

### 10.3  Fehlerbehandlung bei Validierungsverletzung

```python
class ValidationFailureStrategy(str, Enum):
    ABORT = "abort"           # Pipeline-Abbruch
    DEGRADE = "degrade"       # Weitermachen mit Degradation-Flag
    AUTOFIX = "autofix"       # Automatisch korrigieren (z.B. Reorder)
    WARN = "warn"             # Warning loggen, weitermachen

VALIDATION_RULES = {
    "I-2.1_transcript_empty":        ValidationFailureStrategy.ABORT,
    "I-2.2_timestamps_unordered":    ValidationFailureStrategy.AUTOFIX,
    "I-2.3_timestamps_overflow":     ValidationFailureStrategy.WARN,
    "I-2.4_language_not_german":     ValidationFailureStrategy.WARN,
    "I-2.5_low_confidence":          ValidationFailureStrategy.DEGRADE,
    "I-3.1_not_ipa":                 ValidationFailureStrategy.ABORT,
    "I-3.5_alignment_unstable":      ValidationFailureStrategy.DEGRADE,
    "I-4.1_no_analysis":             ValidationFailureStrategy.ABORT,
    "I-6.1_guardrail_failed":        ValidationFailureStrategy.DEGRADE,
}
```

---

## 11  Spezialthemen

### 11.1  IPA vs. SAMPA: Die Phonem-Encoding-Frage

**Problem:** MFA produziert SAMPA-kompatible Labels. WebMAUS produziert SAMPA. Kaldi-GOP erwartet tool-spezifische Labels. Das Pronunciation Dictionary kann IPA oder SAMPA enthalten.

**Entscheidung:** IPA ist der kanonische Standard in der Disce-Pipeline.

| Punkt | Entscheidung |
|-------|-------------|
| Internes Format | **IPA** (Unicode) |
| Dictionary | Enthält IPA-Transkriptionen |
| MFA-Output | SAMPA -> IPA Konvertierung als Teil der D2-Postprocessing-Stufe |
| GOP-Berechnung | Verwendet IPA-Labels, Kaldi-Mapping als Adapter |
| D7-Feedback an Lerner | IPA fuer phonetisch vorgebildete Nutzer, vereinfachte Notation fuer Anfänger |

Konvertierungstabelle (Auszug Deutsch):

| SAMPA | IPA | Beispiel |
|-------|-----|---------|
| `C` | `ç` | i**ch** |
| `S` | `ʃ` | **sch**ön |
| `Z` | `ʒ` | Gara**g**e |
| `R` | `ʁ` | **r**ot |
| `2:` | `øː` | sch**ö**n |
| `9` | `œ` | k**ö**nnte |
| `E:` | `ɛː` | sp**ä**t |
| `a~` | `ã` | Ch**an**ce |

### 11.2  Zeitreferenzen: Die Synchronisationsschicht

**Problem:** D3, D4 und D5 produzieren Ergebnisse, die auf verschiedene Zeitpunkte im Audio verweisen. D6 und D7 müssen diese zusammenführen können.

**Lösung:** Alle Zeitreferenzen nutzen dasselbe Koordinatensystem:
- **Nullpunkt:** Start des normalisierten Audio (nach Stille-Trimming)
- **Einheit:** Sekunden (float, Millisekunden-Präzision)
- **Referenz:** Audio-Sample-Position, nicht Segment-relativ

```python
class TimeRef(BaseModel):
    """Universelle Zeitreferenz in der Disce-Pipeline."""
    start: float = Field(..., ge=0.0, description="Sekunden ab Audio-Start")
    end: float = Field(..., ge=0.0, description="Sekunden ab Audio-Start")

    @model_validator(mode="after")
    def end_after_start(self):
        if self.end < self.start:
            raise ValueError(f"end ({self.end}) < start ({self.start})")
        return self
```

### 11.3  Versionierung der Verträge

**Schema-Evolution:** Wenn sich ein Vertrag ändert (z.B. neues Feld in D3Output), muss das versioniert werden:

```python
class SchemaVersion(BaseModel):
    """Jeder Domaenen-Output traegt seine Schema-Version."""
    schema_name: str      # z.B. "D3Output"
    schema_version: str   # SemVer, z.B. "1.2.0"
```

**Kompatibilitätsregeln:**
- **Neue optionale Felder:** Rueckwärtskompatibel (Minor-Version)
- **Neue Pflichtfelder:** Breaking Change (Major-Version)
- **Geänderte Typen:** Breaking Change (Major-Version)
- **Geänderte Validierungsregeln (strenger):** Breaking Change (Major-Version)
- **Geänderte Validierungsregeln (lockerer):** Rueckwärtskompatibel (Minor-Version)

---

## 12  Zusammenfassung: Die Vertragskarte

```
+------------------------------------------------------------------+
|                    ASSESSMENT ENVELOPE                             |
|                                                                    |
|  +---------+     +---------+     +---------+                      |
|  |AudioInput|---->|D1Output |---->|D2Output |                      |
|  | I-1.1-4  |     | I-2.1-5 |     | I-3.1-5 |                      |
|  +---------+     +---------+     +----+----+                      |
|                                   FORK |                           |
|                          +---------+---+---+---------+             |
|                          v         v       v         |             |
|                    +---------++---------++---------+  |             |
|                    |D3Output ||D4Output ||D5Output |  |             |
|                    +----+----++---+-----++----+----+  |             |
|                         +---------+----------+        |             |
|                             JOIN |                     |             |
|                          +-------v------+              |             |
|                          |   D6Input    |              |             |
|                          |  I-4.1-4     |              |             |
|                          |  Optional[]  |              |             |
|                          +-------+------+              |             |
|                                  v                     |             |
|                          +-------------+               |             |
|                          |  D6Output   |               |             |
|                          |  I-5.1-5    |               |             |
|                          +------+------+               |             |
|                                 v                      |             |
|                          +-------------+               |             |
|                          |  D7Output   |               |             |
|                          |  I-6.1-5    |               |             |
|                          +-------------+               |             |
|                                                        |             |
+------------------------------------------------------------------- +
```

**In Zahlen:**
- **6 Domänenübergänge** mit expliziten Verträgen
- **10 Pydantic-Hauptmodelle** (D1Output bis D7Output + Inputs)
- **~30 Pydantic-Submodelle** (TimeRef, PhoneScore, GrammarError, ...)
- **~25 Invarianten** (I-1.1 bis I-6.5)
- **5 Validierungsebenen** (L1-L5)
- **4 Fehlerbehandlungsstrategien** (Abort, Degrade, Autofix, Warn)

---

## Referenzen

| Quelle | Relevanz fuer B2 |
|--------|----------------|
| **B1** End-to-End-Pipeline | DAG-Struktur, Stufenaufteilung, grobe JSON-Beispiele |
| **Gamma D1** Transkription & ASR | Whisper-Output-Format, Confidence-Semantik |
| **Gamma D2** Phonetisches Alignment | MFA-TextGrid-Format, Dual-Stack-Design, SAMPA/IPA |
| **Gamma D3** Pronunciation Scoring | GOP-Score-Semantik, MDD-Labels, artikulatorische Features |
| **Gamma D4** Prosodie | Parselmouth-Features, Rhythmusmetriken, F0-Kontur |
| **Gamma D5** Textdiagnostik | CAF-Dimensionen, LanguageTool-Fehlerklassen |
| **Gamma D6** Diagnostisches Scoring | 5-Schichten-Modell, Feature-Vektor, Radar-Profil |
| **Gamma D7** Generatives Coaching | LLM-Feedback-Struktur, Guardrails, Uebungstypen |
| **Pydantic v2 Docs** | BaseModel, Validatoren, JSON-Schema-Export |

---

*Nächstes Dokument: **B3 – Fehlerpropagation & Graceful Degradation** -> Was passiert, wenn Bausteine versagen?*
