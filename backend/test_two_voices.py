from google import genai
from google.genai import types
import os
import wave
from pathlib import Path
from dotenv import load_dotenv


BASE_DIR = Path(__file__).resolve().parent
load_dotenv(BASE_DIR / ".env")

client = genai.Client(
    api_key=os.getenv("GEMINI_API_KEY")
)


def generate_voice(text, voice_name, output_file):

    response = client.models.generate_content(
        model="gemini-2.5-flash-preview-tts",
        contents=text,
        config=types.GenerateContentConfig(
            response_modalities=["AUDIO"],
            speech_config=types.SpeechConfig(
                voice_config=types.VoiceConfig(
                    prebuilt_voice_config=types.PrebuiltVoiceConfig(
                        voice_name=voice_name
                    )
                )
            )
        )
    )

    audio_data = response.candidates[0].content.parts[0].inline_data.data

    with wave.open(output_file, "wb") as wav_file:
        wav_file.setnchannels(1)
        wav_file.setsampwidth(2)
        wav_file.setframerate(24000)
        wav_file.writeframes(audio_data)

    print(f"Generated: {output_file}")


generate_voice(
    "Hello and welcome to our podcast. Today we are discussing the future of artificial intelligence.",
    "Kore",
    "host_test.wav"
)


generate_voice(
    "Thanks for having me. Artificial intelligence is developing very rapidly and is changing many industries.",
    "Puck",
    "guest_test.wav"
)