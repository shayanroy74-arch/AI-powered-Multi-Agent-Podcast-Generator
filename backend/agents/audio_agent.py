import asyncio
import time
import edge_tts
from pathlib import Path
from pydub import AudioSegment
from dotenv import load_dotenv


# ============================================================
# LOAD ENVIRONMENT
# ============================================================

BASE_DIR = Path(__file__).resolve().parent.parent
load_dotenv(BASE_DIR / ".env")


# ============================================================
# AUDIO DIRECTORY
# ============================================================

AUDIO_DIR = BASE_DIR / "generated_audio"
AUDIO_DIR.mkdir(exist_ok=True)


# ============================================================
# GENERATE ONE VOICE SEGMENT
# ============================================================

def generate_voice(text, voice_name, output_file):

    async def generate():
        communicate = edge_tts.Communicate(
            text,
            voice_name
        )

        await communicate.save(str(output_file))

    # --------------------------------------------------------
    # RETRY EDGE TTS
    # --------------------------------------------------------

    for attempt in range(3):

        try:

            print(
                f"TTS: generating {output_file.name} "
                f"(attempt {attempt + 1}/3)"
            )

            asyncio.run(generate())

            # Verify file was actually created
            if not output_file.exists():
                raise RuntimeError(
                    "Edge TTS completed but audio file "
                    "was not created."
                )

            # Verify file is not empty
            if output_file.stat().st_size == 0:
                raise RuntimeError(
                    "Generated audio file is empty."
                )

            return

        except Exception as e:

            print(
                f"TTS failed for {output_file.name}: {e}"
            )

            # Remove incomplete file
            if output_file.exists():
                try:
                    output_file.unlink()
                except OSError:
                    pass

            if attempt < 2:

                wait_time = 3 * (attempt + 1)

                print(
                    f"Retrying TTS in {wait_time} seconds..."
                )

                time.sleep(wait_time)

    raise RuntimeError(
        f"Failed to generate voice audio after "
        f"3 attempts: {output_file.name}"
    )


# ============================================================
# GENERATE COMPLETE PODCAST AUDIO
# ============================================================

def generate_podcast_audio(script: str, podcast_id: int):

    lines = script.splitlines()

    audio_segments = []

    segment_number = 0

    current_speaker = None
    current_dialogue = []


    # ========================================================
    # PROCESS ONE SPEAKER SEGMENT
    # ========================================================

    def process_segment(
        speaker,
        dialogue_lines,
        segment_number
    ):

        if not dialogue_lines:
            return segment_number

        dialogue = " ".join(
            line.strip()
            for line in dialogue_lines
            if line.strip()
        )

        if not dialogue:
            return segment_number

        # ----------------------------------------------------
        # SELECT VOICE
        # ----------------------------------------------------

        if speaker == "HOST":
            voice = "en-US-GuyNeural"

        elif speaker == "GUEST":
            voice = "en-US-JennyNeural"

        else:
            raise ValueError(
                f"Unknown speaker: {speaker}"
            )

        # ----------------------------------------------------
        # CREATE SEGMENT FILE
        # ----------------------------------------------------

        segment_number += 1

        segment_file = (
            AUDIO_DIR /
            f"podcast_{podcast_id}_{segment_number}.mp3"
        )

        print(
            f"Generating segment {segment_number}: "
            f"{speaker}"
        )

        # ----------------------------------------------------
        # GENERATE VOICE
        # ----------------------------------------------------

        generate_voice(
            dialogue,
            voice,
            segment_file
        )

        # ----------------------------------------------------
        # LOAD AUDIO
        # ----------------------------------------------------

        try:

            audio_segment = AudioSegment.from_file(
                segment_file,
                format="mp3"
            )

        except Exception as e:

            raise RuntimeError(
                f"Failed to read generated audio "
                f"segment {segment_number}: {e}"
            ) from e

        audio_segments.append(audio_segment)

        return segment_number


    # ========================================================
    # PARSE SCRIPT
    # ========================================================

    for line in lines:

        line = line.strip()

        if not line:
            continue

        # ----------------------------------------------------
        # HOST
        # ----------------------------------------------------

        if line.upper().startswith("HOST:"):

            segment_number = process_segment(
                current_speaker,
                current_dialogue,
                segment_number
            )

            current_speaker = "HOST"

            first_line = (
                line.split(":", 1)[1].strip()
            )

            current_dialogue = []

            if first_line:
                current_dialogue.append(first_line)

        # ----------------------------------------------------
        # GUEST
        # ----------------------------------------------------

        elif line.upper().startswith("GUEST:"):

            segment_number = process_segment(
                current_speaker,
                current_dialogue,
                segment_number
            )

            current_speaker = "GUEST"

            first_line = (
                line.split(":", 1)[1].strip()
            )

            current_dialogue = []

            if first_line:
                current_dialogue.append(first_line)

        # ----------------------------------------------------
        # CONTINUATION OF CURRENT SPEAKER
        # ----------------------------------------------------

        else:

            if current_speaker:
                current_dialogue.append(line)


    # ========================================================
    # PROCESS FINAL SEGMENT
    # ========================================================

    segment_number = process_segment(
        current_speaker,
        current_dialogue,
        segment_number
    )


    # ========================================================
    # VALIDATE AUDIO
    # ========================================================

    if not audio_segments:

        raise ValueError(
            "No HOST or GUEST dialogue found in the script."
        )


    # ========================================================
    # COMBINE ALL SEGMENTS
    # ========================================================

    print(
        f"Combining {len(audio_segments)} "
        f"audio segments..."
    )

    final_audio = AudioSegment.empty()

    for segment in audio_segments:
        final_audio += segment


    # ========================================================
    # EXPORT FINAL AUDIO
    # ========================================================

    final_file = (
        AUDIO_DIR /
        f"podcast_{podcast_id}_final.wav"
    )

    final_audio.export(
        final_file,
        format="wav"
    )


    # ========================================================
    # VERIFY FINAL FILE
    # ========================================================

    if not final_file.exists():

        raise RuntimeError(
            "Final podcast audio file was not created."
        )

    if final_file.stat().st_size == 0:

        raise RuntimeError(
            "Final podcast audio file is empty."
        )


    print(
        f"Podcast audio generated successfully: "
        f"{final_file}"
    )

    return final_file