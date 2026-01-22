# openai_services.py
"""
OpenAI-Integration für Großer Bär
- Whisper: Audio → Transkript
- GPT-4o-mini: Coach-Feedback
"""

import json
import tempfile
from pathlib import Path

import streamlit as st
from openai import OpenAI


def get_openai_client():
    """Erstellt OpenAI Client mit API Key aus Secrets."""
    api_key = st.secrets.get("OPENAI_API_KEY")
    if not api_key:
        raise ValueError("OPENAI_API_KEY nicht in Streamlit Secrets gefunden!")
    return OpenAI(api_key=api_key)


def transcribe_audio(audio_bytes: bytes) -> str:
    """
    Transkribiert Audio mit Whisper.
    
    Args:
        audio_bytes: Audio-Daten als Bytes (WAV format)
    
    Returns:
        Transkribierter Text
    """
    client = get_openai_client()
    
    # Audio temporär speichern (Whisper braucht eine Datei)
    with tempfile.NamedTemporaryFile(suffix=".wav", delete=False) as f:
        f.write(audio_bytes)
        temp_path = Path(f.name)
    
    try:
        with open(temp_path, "rb") as audio_file:
            response = client.audio.transcriptions.create(
                model="whisper-1",
                file=audio_file,
                language="de",
                response_format="text",
            )
        return response
    finally:
        # Temp-Datei aufräumen
        temp_path.unlink(missing_ok=True)


def generate_coach_feedback(coach_input: dict) -> str:
    """
    Generiert Coaching-Feedback mit GPT-4o-mini.
    
    Args:
        coach_input: Der komplette Coach-Input JSON-Block
    
    Returns:
        Markdown-formatiertes Feedback
    """
    client = get_openai_client()
    
    # System-Prompt für den Coach
    system_prompt = """Du bist ein erfahrener, warmherziger Sprechcoach für Deutschlernende (B1-C1 Niveau).

DEINE ROLLE:
- Du gibst ehrliches, datenbasiertes Feedback
- Du bist ermutigend, aber nicht verzuckert
- Du fokussierst auf konkrete, umsetzbare Verbesserungen

WICHTIG – BEZIEHE DICH AUF:
1. Das LERNZIEL des Nutzers (learner_planning.goal) – war das der Fokus?
2. Die METRIKEN (analysis) – nutze konkrete Zahlen
3. Das TRANSKRIPT – zitiere gute Stellen oder Verbesserungspotenzial
4. Die AUFGABE (task_metadata) – wurde das Ziel-Register getroffen?

DEIN FEEDBACK-FORMAT:

## 💪 Das ist dir gut gelungen
[2 konkrete Stärken mit Beispielen aus dem Transkript]

## 🎯 Dein Fokus fürs nächste Mal
[1 konkreter, umsetzbarer Tipp – nicht zu viel auf einmal!]

## 📊 Zur Einordnung
[Kurze Einordnung: Niveau, Register-Match, Sprechtempo]
[Beziehe dich auf das persönliche Lernziel – wurde es erreicht?]

STIL:
- Duze den Lernenden
- Sei konkret, nicht vage
- Maximal 200 Wörter
- Antworte auf Deutsch
"""

    # User-Message mit den Session-Daten
    user_message = f"""Hier sind die Daten der Sprech-Session:

{json.dumps(coach_input, indent=2, ensure_ascii=False)}

Bitte gib dein Coaching-Feedback."""

    response = client.chat.completions.create(
        model="gpt-4o-mini",
        messages=[
            {"role": "system", "content": system_prompt},
            {"role": "user", "content": user_message}
        ],
        temperature=0.7,
        max_tokens=800,
    )
    
    return response.choices[0].message.content


def check_api_connection() -> tuple[bool, str]:
    """
    Testet die OpenAI API-Verbindung.
    
    Returns:
        (success, message)
    """
    try:
        client = get_openai_client()
        # Minimaler API-Call zum Testen
        response = client.chat.completions.create(
            model="gpt-4o-mini",
            messages=[{"role": "user", "content": "Sag nur: OK"}],
            max_tokens=5,
        )
        return True, "API-Verbindung OK"
    except Exception as e:
        return False, f"API-Fehler: {str(e)}"
