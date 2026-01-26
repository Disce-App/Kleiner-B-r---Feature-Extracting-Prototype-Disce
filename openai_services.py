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

# Zentraler System-Prompt aus prompts.py
from grosser_baer.prompts import SYSTEM_PROMPT_COACH


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
    
    Nutzt den zentralen SYSTEM_PROMPT_COACH aus grosser_baer/prompts.py,
    damit Feedback-Format und Kategorien konsistent sind.
    
    Args:
        coach_input: Vollständiger Session-Kontext (Task, Transkript, Metriken, etc.)
    
    Returns:
        Formatiertes Feedback-String
    """
    client = get_openai_client()
    
    # User-Prompt: Session-Daten als JSON
    user_message = (
        "Hier sind alle Daten zu einer Speaking-Session im JSON-Format.\n"
        "Nutze diese Informationen, um Feedback gemäß deinen Anweisungen zu geben.\n"
        "Prüfe ZUERST, ob das Thema der Aufgabe getroffen wurde!\n\n"
        + json.dumps(coach_input, indent=2, ensure_ascii=False)
    )

    response = client.chat.completions.create(
        model="gpt-4o-mini",
        messages=[
            {"role": "system", "content": SYSTEM_PROMPT_COACH},
            {"role": "user", "content": user_message},
        ],
        temperature=0.7,
        max_tokens=1200,
    )
    
    return response.choices[0].message.content.strip()


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
