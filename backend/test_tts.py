from google import genai
from google.genai import types
import os
from pathlib import Path
from dotenv import load_dotenv
import wave

BASE_DIR = Path(__file__).resolve().parent
load_dotenv(BASE_DIR / ".env")

client = genai.Client(
    api_key=os.getenv("GEMINI_API_KEY")
)


text = """
Hello and welcome to our podcast.

Today we are going to talk about the future of artificial intelligence,
how AI is changing different industries, and what we can expect in the
coming years.
"""


response = client.models.generate_content(
    model="gemini-2.5-flash-preview-tts",
    contents=text,
    config=types.GenerateContentConfig(
        response_modalities=["AUDIO"],
        speech_config=types.SpeechConfig(
            voice_config=types.VoiceConfig(
                prebuilt_voice_config=types.PrebuiltVoiceConfig(
                    voice_name="Kore"
                )
            )
        )
    )
)


audio_data = response.candidates[0].content.parts[0].inline_data.data

output_file = Path("test_podcast.wav")

with wave.open(str(output_file), "wb") as wav_file:
    wav_file.setnchannels(1)
    wav_file.setsampwidth(2)
    wav_file.setframerate(24000)
    wav_file.writeframes(audio_data)

print(f"\nAudio generated successfully!")
print(f"Saved to: {output_file.resolve()}")