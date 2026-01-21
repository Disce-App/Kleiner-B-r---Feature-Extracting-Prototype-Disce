# grosser_baer/audio_handler.py
"""
Audio-Handling für Großer Bär.
- Browser-Aufnahme via Streamlit-Komponenten
- STT (Speech-to-Text) mit Mock und Azure-Integration
- Prosodie-Analyse mit Mock und Azure Pronunciation Assessment

Architektur:
    AudioRecorder → AudioProcessor → (STT + Prosody)
                                          ↓
                                    TranscriptResult
"""

import io
import os
import tempfile
import random
from dataclasses import dataclass, field
from pathlib import Path
from typing import Callable
from datetime import datetime


# =============================================================================
# DATENKLASSEN
# =============================================================================

@dataclass
class TranscriptResult:
    """Ergebnis der Speech-to-Text Verarbeitung."""
    text: str
    word_count: int
    confidence: float | None = None
    language: str = "de-DE"
    duration_seconds: float | None = None
    is_mock: bool = False
    
    @classmethod
    def from_text(cls, text: str, **kwargs) -> "TranscriptResult":
        """Factory-Methode für einfache Erstellung."""
        return cls(
            text=text,
            word_count=len(text.split()) if text else 0,
            **kwargs
        )


@dataclass
class ProsodyResult:
    """Ergebnis der Prosodie-Analyse."""
    speech_rate_wpm: float | None = None  # Wörter pro Minute
    pause_ratio: float | None = None       # Anteil Pausen an Gesamtzeit
    filler_count: int = 0                  # Anzahl Füllwörter ("ähm", "also", etc.)
    filler_rate: float | None = None       # Füllwörter pro 100 Wörter
    pronunciation_score: float | None = None  # 0-100 (Azure)
    fluency_score: float | None = None        # 0-100 (Azure)
    completeness_score: float | None = None   # 0-100 (Azure)
    is_mock: bool = False
    raw_response: dict = field(default_factory=dict)
    
    def to_dict(self) -> dict:
        """Für Session-Logger."""
        return {
            "speech_rate_wpm": self.speech_rate_wpm,
            "pause_ratio": self.pause_ratio,
            "filler_count": self.filler_count,
            "filler_rate": self.filler_rate,
            "pronunciation_score": self.pronunciation_score,
            "fluency_score": self.fluency_score,
            "completeness_score": self.completeness_score,
            "is_mock": self.is_mock,
        }


@dataclass
class AudioAnalysisResult:
    """Kombiniertes Ergebnis: Transkript + Prosodie."""
    transcript: TranscriptResult
    prosody: ProsodyResult
    audio_duration_seconds: float | None = None
    processing_time_seconds: float | None = None
    
    @property
    def text(self) -> str:
        return self.transcript.text
    
    @property
    def word_count(self) -> int:
        return self.transcript.word_count


# =============================================================================
# DEUTSCHE FÜLLWÖRTER
# =============================================================================

GERMAN_FILLERS = {
    "ähm", "äh", "hm", "hmm", "öhm", 
    "also", "halt", "quasi", "sozusagen",
    "irgendwie", "eigentlich", "praktisch",
    "ja", "ne", "naja", "nun",
}

def count_fillers(text: str) -> int:
    """Zählt deutsche Füllwörter im Text."""
    words = text.lower().split()
    return sum(1 for w in words if w.strip(".,!?") in GERMAN_FILLERS)


# =============================================================================
# MOCK IMPLEMENTATIONS (für Testing ohne APIs)
# =============================================================================

# Beispiel-Transkripte für Mock-Modus
MOCK_TRANSCRIPTS = {
    "meeting_update": (
        "Ich möchte kurz den aktuellen Stand unseres Teilprojekts zusammenfassen. "
        "In den letzten zwei Wochen haben wir die Datenanalyse abgeschlossen und "
        "die ersten Ergebnisse liegen vor. Aktuell befinden wir uns in der Phase "
        "der Dokumentation. Was die nächsten Schritte betrifft, planen wir bis "
        "Ende der Woche den Zwischenbericht fertigzustellen."
    ),
    "phone_complaint": (
        "Guten Tag, ich rufe an wegen meiner Bestellung vom letzten Montag. "
        "Leider ist das Paket beschädigt angekommen, der Karton war eingedrückt "
        "und das Produkt funktioniert nicht mehr. Ich würde mir wünschen, dass "
        "Sie mir entweder Ersatz schicken oder den Betrag erstatten."
    ),
    "job_interview_strength": (
        "Eine meiner größten Stärken ist definitiv meine Fähigkeit, komplexe "
        "Sachverhalte verständlich zu erklären. Das hat sich zum Beispiel in "
        "meiner letzten Position gezeigt, als ich ein neues System einführen "
        "musste und die Schulungen für das gesamte Team übernommen habe. "
        "Ich denke, das ist besonders relevant für diese Position, weil auch "
        "hier viel Kundenkontakt gefragt ist."
    ),
    "explain_technical": (
        "Im Grunde kann man sich Machine Learning so vorstellen wie ein Kind, "
        "das durch Beispiele lernt. Statt dass wir dem Computer genau sagen, "
        "was er tun soll, zeigen wir ihm tausende Beispiele und er findet "
        "selbst die Muster. Ein einfaches Beispiel wäre Spam-Erkennung: Der "
        "Computer sieht viele E-Mails, die als Spam markiert sind, und lernt "
        "dann selbstständig, woran er Spam erkennt."
    ),
    "small_talk_network": (
        "Wie hat Ihnen der Vortrag gefallen? Ich fand besonders den Teil "
        "über die neuen Marktentwicklungen interessant. Arbeiten Sie auch "
        "in diesem Bereich? Das klingt wirklich spannend! Es war sehr nett, "
        "Sie kennenzulernen. Vielleicht sieht man sich ja später noch."
    ),
    "default": (
        "Das ist ein Beispieltranskript für den Mock-Modus. "
        "Es simuliert eine gesprochene Antwort auf die gestellte Aufgabe. "
        "In der echten Anwendung würde hier das Transkript aus Azure Speech stehen."
    )
}


def mock_transcribe(
    audio_bytes: bytes | None = None,
    task_id: str | None = None,
    duration_seconds: float = 60.0
) -> TranscriptResult:
    """
    Mock-STT für Testing ohne Azure.
    Gibt kontextabhängige Beispiel-Transkripte zurück.
    """
    # Wähle passendes Mock-Transkript
    text = MOCK_TRANSCRIPTS.get(task_id, MOCK_TRANSCRIPTS["default"])
    
    # Simuliere etwas Variabilität
    confidence = random.uniform(0.85, 0.98)
    
    return TranscriptResult(
        text=text,
        word_count=len(text.split()),
        confidence=confidence,
        language="de-DE",
        duration_seconds=duration_seconds,
        is_mock=True
    )


def mock_analyze_prosody(
    text: str,
    duration_seconds: float = 60.0
) -> ProsodyResult:
    """
    Mock-Prosodie-Analyse für Testing ohne Azure.
    Berechnet realistische Werte basierend auf dem Text.
    """
    word_count = len(text.split())
    filler_count = count_fillers(text)
    
    # Berechne WPM (normale Sprechgeschwindigkeit: 120-150 WPM)
    if duration_seconds > 0:
        speech_rate = (word_count / duration_seconds) * 60
    else:
        speech_rate = random.uniform(120, 150)
    
    # Simuliere Prosodie-Werte
    return ProsodyResult(
        speech_rate_wpm=speech_rate,
        pause_ratio=random.uniform(0.15, 0.30),  # 15-30% Pausen ist normal
        filler_count=filler_count,
        filler_rate=(filler_count / word_count * 100) if word_count > 0 else 0,
        pronunciation_score=random.uniform(70, 95),
        fluency_score=random.uniform(65, 90),
        completeness_score=random.uniform(80, 100),
        is_mock=True,
        raw_response={"mock": True, "note": "Simulierte Werte für Testing"}
    )


# =============================================================================
# AZURE SPEECH INTEGRATION (Placeholder)
# =============================================================================

def get_azure_credentials() -> tuple[str, str] | None:
    """
    Holt Azure Speech Credentials aus Environment.
    Returns (key, region) oder None wenn nicht konfiguriert.
    """
    key = os.environ.get("AZURE_SPEECH_KEY")
    region = os.environ.get("AZURE_SPEECH_REGION", "westeurope")
    
    if not key:
        return None
    return (key, region)


def azure_transcribe(
    audio_bytes: bytes,
    language: str = "de-DE"
) -> TranscriptResult:
    """
    Azure Speech-to-Text.
    
    Requires:
        pip install azure-cognitiveservices-speech
        
    Environment:
        AZURE_SPEECH_KEY: Azure Speech API Key
        AZURE_SPEECH_REGION: Azure Region (default: westeurope)
    """
    credentials = get_azure_credentials()
    
    if not credentials:
        raise RuntimeError(
            "Azure Speech nicht konfiguriert. "
            "Setze AZURE_SPEECH_KEY und AZURE_SPEECH_REGION."
        )
    
    try:
        import azure.cognitiveservices.speech as speechsdk
    except ImportError:
        raise ImportError(
            "azure-cognitiveservices-speech nicht installiert. "
            "Führe aus: pip install azure-cognitiveservices-speech"
        )
    
    key, region = credentials
    
    # Temporäre WAV-Datei erstellen
    with tempfile.NamedTemporaryFile(suffix=".wav", delete=False) as f:
        f.write(audio_bytes)
        temp_path = f.name
    
    try:
        # Azure Speech Config
        speech_config = speechsdk.SpeechConfig(
            subscription=key,
            region=region
        )
        speech_config.speech_recognition_language = language
        
        # Audio Config
        audio_config = speechsdk.audio.AudioConfig(filename=temp_path)
        
        # Recognizer
        recognizer = speechsdk.SpeechRecognizer(
            speech_config=speech_config,
            audio_config=audio_config
        )
        
        # Kontinuierliche Erkennung für längere Aufnahmen
        all_results = []
        done = False
        
        def handle_result(evt):
            if evt.result.reason == speechsdk.ResultReason.RecognizedSpeech:
                all_results.append(evt.result.text)
        
        def handle_stop(evt):
            nonlocal done
            done = True
        
        recognizer.recognized.connect(handle_result)
        recognizer.session_stopped.connect(handle_stop)
        recognizer.canceled.connect(handle_stop)
        
        recognizer.start_continuous_recognition()
        
        # Warte auf Abschluss (max 5 Minuten)
        import time
        timeout = 300
        start = time.time()
        while not done and (time.time() - start) < timeout:
            time.sleep(0.1)
        
        recognizer.stop_continuous_recognition()
        
        # Ergebnis zusammenbauen
        full_text = " ".join(all_results)
        
        return TranscriptResult(
            text=full_text,
            word_count=len(full_text.split()),
            confidence=None,  # Azure gibt keine Gesamt-Confidence
            language=language,
            is_mock=False
        )
        
    finally:
        # Temp-Datei aufräumen
        Path(temp_path).unlink(missing_ok=True)


def azure_pronunciation_assessment(
    audio_bytes: bytes,
    reference_text: str | None = None,
    language: str = "de-DE"
) -> ProsodyResult:
    """
    Azure Pronunciation Assessment für Prosodie-Analyse.
    
    Gibt detaillierte Scores für:
    - Pronunciation (Aussprache)
    - Fluency (Flüssigkeit)
    - Completeness (Vollständigkeit)
    - Prosody (seit Azure 2023)
    """
    credentials = get_azure_credentials()
    
    if not credentials:
        raise RuntimeError("Azure Speech nicht konfiguriert.")
    
    try:
        import azure.cognitiveservices.speech as speechsdk
    except ImportError:
        raise ImportError("azure-cognitiveservices-speech nicht installiert.")
    
    key, region = credentials
    
    # Temporäre Datei
    with tempfile.NamedTemporaryFile(suffix=".wav", delete=False) as f:
        f.write(audio_bytes)
        temp_path = f.name
    
    try:
        speech_config = speechsdk.SpeechConfig(
            subscription=key,
            region=region
        )
        
        # Pronunciation Assessment Config
        pronunciation_config = speechsdk.PronunciationAssessmentConfig(
            reference_text=reference_text or "",
            grading_system=speechsdk.PronunciationAssessmentGradingSystem.HundredMark,
            granularity=speechsdk.PronunciationAssessmentGranularity.Phoneme,
            enable_miscue=True
        )
        
        # Prosody aktivieren (falls verfügbar)
        pronunciation_config.enable_prosody_assessment()
        
        audio_config = speechsdk.audio.AudioConfig(filename=temp_path)
        
        recognizer = speechsdk.SpeechRecognizer(
            speech_config=speech_config,
            audio_config=audio_config
        )
        
        pronunciation_config.apply_to(recognizer)
        
        result = recognizer.recognize_once()
        
        if result.reason == speechsdk.ResultReason.RecognizedSpeech:
            pronunciation_result = speechsdk.PronunciationAssessmentResult(result)
            
            return ProsodyResult(
                pronunciation_score=pronunciation_result.pronunciation_score,
                fluency_score=pronunciation_result.fluency_score,
                completeness_score=pronunciation_result.completeness_score,
                is_mock=False,
                raw_response={
                    "accuracy_score": pronunciation_result.accuracy_score,
                    "pronunciation_score": pronunciation_result.pronunciation_score,
                    "fluency_score": pronunciation_result.fluency_score,
                    "completeness_score": pronunciation_result.completeness_score,
                }
            )
        else:
            return ProsodyResult(
                is_mock=False,
                raw_response={"error": str(result.reason)}
            )
            
    finally:
        Path(temp_path).unlink(missing_ok=True)


# =============================================================================
# UNIFIED AUDIO PROCESSOR
# =============================================================================

class AudioProcessor:
    """
    Einheitliche Schnittstelle für Audio-Verarbeitung.
    Wählt automatisch zwischen Mock und Azure basierend auf Konfiguration.
    
    Usage:
        processor = AudioProcessor(use_mock=True)
        result = processor.process(audio_bytes, task_id="meeting_update")
        print(result.text)
        print(result.prosody.speech_rate_wpm)
    """
    
    def __init__(
        self,
        use_mock: bool | None = None,
        language: str = "de-DE"
    ):
        """
        Args:
            use_mock: True = immer Mock, False = immer Azure, None = auto
            language: Sprache für STT (default: de-DE)
        """
        self.language = language
        
        # Auto-detect wenn nicht spezifiziert
        if use_mock is None:
            self.use_mock = get_azure_credentials() is None
        else:
            self.use_mock = use_mock
    
    def process(
        self,
        audio_bytes: bytes | None = None,
        task_id: str | None = None,
        duration_seconds: float | None = None,
        reference_text: str | None = None
    ) -> AudioAnalysisResult:
        """
        Verarbeitet Audio und gibt Transkript + Prosodie zurück.
        
        Args:
            audio_bytes: Raw Audio-Daten (WAV/WebM)
            task_id: Für Mock-Modus: welches Beispiel-Transkript
            duration_seconds: Aufnahmedauer (für Mock-Berechnung)
            reference_text: Für Pronunciation Assessment
            
        Returns:
            AudioAnalysisResult mit Transkript und Prosodie
        """
        start_time = datetime.now()
        
        duration = duration_seconds or 60.0
        
        if self.use_mock:
            # Mock-Modus
            transcript = mock_transcribe(
                audio_bytes=audio_bytes,
                task_id=task_id,
                duration_seconds=duration
            )
            prosody = mock_analyze_prosody(
                text=transcript.text,
                duration_seconds=duration
            )
        else:
            # Azure-Modus
            if not audio_bytes:
                raise ValueError("audio_bytes erforderlich für Azure-Modus")
            
            transcript = azure_transcribe(
                audio_bytes=audio_bytes,
                language=self.language
            )
            
            # Prosodie-Analyse
            try:
                prosody = azure_pronunciation_assessment(
                    audio_bytes=audio_bytes,
                    reference_text=reference_text,
                    language=self.language
                )
            except Exception as e:
                # Fallback: Basis-Prosodie aus Text
                prosody = ProsodyResult(
                    filler_count=count_fillers(transcript.text),
                    is_mock=False,
                    raw_response={"error": str(e)}
                )
            
            # Füllwörter zählen (Azure macht das nicht)
            prosody.filler_count = count_fillers(transcript.text)
            if transcript.word_count > 0:
                prosody.filler_rate = prosody.filler_count / transcript.word_count * 100
        
        processing_time = (datetime.now() - start_time).total_seconds()
        
        return AudioAnalysisResult(
            transcript=transcript,
            prosody=prosody,
            audio_duration_seconds=duration,
            processing_time_seconds=processing_time
        )
    
    def transcribe_only(
        self,
        audio_bytes: bytes | None = None,
        task_id: str | None = None,
        duration_seconds: float = 60.0
    ) -> TranscriptResult:
        """Nur Transkription, ohne Prosodie-Analyse."""
        if self.use_mock:
            return mock_transcribe(audio_bytes, task_id, duration_seconds)
        else:
            if not audio_bytes:
                raise ValueError("audio_bytes erforderlich")
            return azure_transcribe(audio_bytes, self.language)


# =============================================================================
# STREAMLIT AUDIO RECORDER HELPER
# =============================================================================

def get_audio_recorder_component():
    """
    Gibt die beste verfügbare Audio-Recorder-Komponente zurück.
    
    Priorität:
    1. audio_recorder_streamlit (einfacher, empfohlen)
    2. streamlit_webrtc (komplexer, mehr Features)
    3. None (nicht verfügbar)
    """
    try:
        from audio_recorder_streamlit import audio_recorder
        return ("audio_recorder_streamlit", audio_recorder)
    except ImportError:
        pass
    
    try:
        from streamlit_webrtc import webrtc_streamer
        return ("streamlit_webrtc", webrtc_streamer)
    except ImportError:
        pass
    
    return (None, None)


def render_audio_recorder(
    key: str = "audio_recorder",
    pause_threshold: float = 3.0,
    sample_rate: int = 16000
) -> bytes | None:
    """
    Rendert einen Audio-Recorder in Streamlit und gibt Audio-Bytes zurück.
    
    Usage in Streamlit:
        audio_bytes = render_audio_recorder()
        if audio_bytes:
            st.success("Aufnahme erhalten!")
            processor = AudioProcessor(use_mock=False)
            result = processor.process(audio_bytes)
    
    Returns:
        Audio-Bytes wenn Aufnahme verfügbar, sonst None
    """
    component_name, component = get_audio_recorder_component()
    
    if component_name == "audio_recorder_streamlit":
        audio_bytes = component(
            pause_threshold=pause_threshold,
            sample_rate=sample_rate,
            key=key
        )
        return audio_bytes
    
    elif component_name == "streamlit_webrtc":
        # WebRTC ist komplexer - vereinfachte Version
        import streamlit as st
        st.warning(
            "streamlit_webrtc wird noch nicht vollständig unterstützt. "
            "Installiere: pip install audio-recorder-streamlit"
        )
        return None
    
    else:
        import streamlit as st
        st.error(
            "Kein Audio-Recorder verfügbar. Installiere:\n"
            "`pip install audio-recorder-streamlit`"
        )
        return None


# =============================================================================
# CONVENIENCE FUNCTION FÜR GROSSER BÄR
# =============================================================================

def process_speaking_task(
    audio_bytes: bytes | None = None,
    task_id: str | None = None,
    duration_seconds: float | None = None,
    use_mock: bool | None = None
) -> AudioAnalysisResult:
    """
    High-Level-Funktion für Großer Bär Speaking-Tasks.
    
    Args:
        audio_bytes: Aufgenommenes Audio
        task_id: Task-ID aus task_templates.py
        duration_seconds: Dauer der Aufnahme
        use_mock: True = Mock-Modus, None = Auto-Detect
        
    Returns:
        AudioAnalysisResult mit allem was für Feedback nötig ist
        
    Usage:
        result = process_speaking_task(
            audio_bytes=recorded_audio,
            task_id="meeting_update",
            duration_seconds=85.3
        )
        
        # Für disce_core:
        from disce_core import analyze_text_for_llm
        analysis = analyze_text_for_llm(result.text)
        
        # Für Feedback:
        print(f"Wörter: {result.word_count}")
        print(f"Geschwindigkeit: {result.prosody.speech_rate_wpm:.0f} WPM")
        print(f"Füllwörter: {result.prosody.filler_count}")
    """
    processor = AudioProcessor(use_mock=use_mock)
    return processor.process(
        audio_bytes=audio_bytes,
        task_id=task_id,
        duration_seconds=duration_seconds
    )
