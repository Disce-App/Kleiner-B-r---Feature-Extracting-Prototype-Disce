# mistral_services.py
"""
Mistral-Integration für Großer Bär
- Voxtral: Audio → Transkript
- Mistral Small: Coach-Feedback

Ersetzt openai_services.py – Function-Signaturen bleiben identisch,
damit pages/grosser_baer.py ohne Änderung funktioniert.
"""

import json
import tempfile
import base64
from pathlib import Path

import streamlit as st
from mistralai.client.sdk import Mistral

# Zentraler System-Prompt aus prompts.py
from grosser_baer.prompts import SYSTEM_PROMPT_COACH


# ---------------------------------------------------------------------------
# Config – Modelle zentral definiert, leicht austauschbar
# ---------------------------------------------------------------------------
TRANSCRIPTION_MODEL = "mistral-audio-latest"   # Voxtral Transcription
CHAT_MODEL = "mistral-small-latest"            # Mistral Small (günstig & schnell)


def get_mistral_client() -> Mistral:
    """Erstellt Mistral Client mit API Key aus Streamlit Secrets."""
    api_key = st.secrets.get("MISTRAL_API_KEY")
    if not api_key:
        raise ValueError("MISTRAL_API_KEY nicht in Streamlit Secrets gefunden!")
    return Mistral(api_key=api_key)


def transcribe_audio(audio_bytes: bytes) -> str:
    """
    Transkribiert Audio mit Voxtral.

    Args:
        audio_bytes: Audio-Daten als Bytes (WAV format)

    Returns:
        Transkribierter Text
    """
    client = get_mistral_client()

    # Voxtral erwartet Base64-encoded Audio als Data-URI
    audio_b64 = base64.b64encode(audio_bytes).decode("utf-8")
    data_uri = f"data:audio/wav;base64,{audio_b64}"

    response = client.chat.complete(
        model=TRANSCRIPTION_MODEL,
        messages=[
            {
                "role": "user",
                "content": [
                    {
                        "type": "audio_url",
                        "audio_url": data_uri,
                    },
                    {
                        "type": "text",
                        "text": (
                            "Transkribiere diese Audioaufnahme wortgetreu auf Deutsch. "
                            "Gib ausschließlich den transkribierten Text zurück, "
                            "ohne Erklärungen oder Zusätze."
                        ),
                    },
                ],
            }
        ],
        temperature=0.0,
    )

    return response.choices[0].message.content.strip()


def generate_coach_feedback(coach_input: dict) -> str:
    """
    Generiert Coaching-Feedback mit Mistral Small.

    Nutzt den zentralen SYSTEM_PROMPT_COACH aus grosser_baer/prompts.py,
    damit Feedback-Format und Kategorien konsistent sind.

    Args:
        coach_input: Vollständiger Session-Kontext (Task, Transkript, Metriken, etc.)

    Returns:
        Formatiertes Feedback-String
    """
    client = get_mistral_client()

    user_message = (
        "Hier sind alle Daten zu einer Speaking-Session im JSON-Format.\n"
        "Nutze diese Informationen, um Feedback gemäß deinen Anweisungen zu geben.\n"
        "Prüfe ZUERST, ob das Thema der Aufgabe getroffen wurde!\n\n"
        + json.dumps(coach_input, indent=2, ensure_ascii=False)
    )

    response = client.chat.complete(
        model=CHAT_MODEL,
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
    Testet die Mistral API-Verbindung.

    Returns:
        (success, message)
    """
    try:
        client = get_mistral_client()
        response = client.chat.complete(
            model=CHAT_MODEL,
            messages=[{"role": "user", "content": "Sag nur: OK"}],
            max_tokens=5,
        )
        return True, "Mistral API-Verbindung OK"
    except Exception as e:
        return False, f"Mistral API-Fehler: {str(e)}"
