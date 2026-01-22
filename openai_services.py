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
    """
    client = get_openai_client()
    
    system_prompt = """Du bist ein erfahrener, direkter Sprechcoach für Deutschlernende (B1-C1 Niveau).

DEINE OBERSTE PRIORITÄT:
Prüfe ZUERST, ob der Lernende die AUFGABE erfüllt hat!
- Lies task_metadata.task – das ist die gestellte Aufgabe
- Lies transcript – das ist was der Lernende gesagt hat
- Passt das zusammen? Wurde das Thema getroffen?

WENN THEMA VERFEHLT:
Sag es DIREKT und FREUNDLICH aber KLAR:
"⚠️ **Achtung: Du hast am Thema vorbeigeredet.**
Die Aufgabe war: [Aufgabe zusammenfassen]
Du hast stattdessen über [anderes Thema] gesprochen.
Das passiert – aber in einer echten Prüfung oder im Job wäre das ein Problem."

Dann trotzdem kurzes Feedback zur Sprache geben.

CEFR-EINSCHÄTZUNG:
Die automatische CEFR-Schätzung (analysis.cefr) ist nur ein GROBER Richtwert.
Schätze das Niveau SELBST basierend auf:
- Grammatische Komplexität (Nebensätze, Konjunktiv, Passiv)
- Wortschatz (Vielfalt, Fachbegriffe, Register)
- Kohärenz und Flüssigkeit
- Fehlerfreiheit

Wenn jemand fehlerfrei, flüssig und komplex spricht → C1/C2, nicht B1!

FEEDBACK-FORMAT:

## 🎯 Aufgaben-Check
[Hat der Lernende die Aufgabe erfüllt? Thema getroffen? Register passend?]

## 💪 Das ist dir gut gelungen
[2 konkrete Stärken MIT ZITATEN aus dem Transkript]

## 🔧 Dein Fokus fürs nächste Mal
[1 konkreter, umsetzbarer Tipp]

## 📊 Einordnung
[DEINE Niveau-Einschätzung mit kurzer Begründung]
[Bezug zum persönlichen Lernziel – wurde es erreicht?]

STIL:
- Duze den Lernenden
- Sei EHRLICH – kein Schönreden
- Sei KONKRET – zitiere aus dem Transkript
- Sei KONSTRUKTIV – nicht nur kritisieren
- Maximal 250 Wörter
- Antworte auf Deutsch
"""

    user_message = f"""Hier sind die Daten der Sprech-Session:

{json.dumps(coach_input, indent=2, ensure_ascii=False)}

Bitte gib dein Coaching-Feedback. Prüfe ZUERST ob das Thema getroffen wurde!"""

    response = client.chat.completions.create(
        model="gpt-4o-mini",
        messages=[
            {"role": "system", "content": system_prompt},
            {"role": "user", "content": user_message}
        ],
        temperature=0.7,
        max_tokens=1000,
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
