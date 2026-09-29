from google import genai
import os
import time
from pathlib import Path
from dotenv import load_dotenv


# Load backend/.env
BASE_DIR = Path(__file__).resolve().parent.parent
load_dotenv(BASE_DIR / ".env")


# Create Gemini client
client = genai.Client(
    api_key=os.getenv("GEMINI_API_KEY")
)


def generate_guest_dialogue(topic: str, outline: str) -> str:

    prompt = f"""
You are the GUEST agent in an AI-powered multi-agent podcast generator.

Podcast topic:

{topic}

Podcast outline:

{outline}

Your job is to write the GUEST's dialogue for the podcast.

The guest should:

- Answer the host's questions naturally
- Explain important concepts clearly
- Provide examples and real-world context
- Share different perspectives
- Add interesting insights
- Respond naturally to the discussion points
- Avoid repeating the same information
- Sound like a knowledgeable human guest
- Keep the conversation engaging and conversational
- Avoid sounding like an academic lecture

Write ONLY the guest's dialogue.

Do not write the host's questions.

Use this format:

GUEST:

[dialogue]
"""

    primary_model = "gemini-3.5-flash"
    fallback_model = "gemini-3.5-flash-lite"

    # ---------------------------------------------------------
    # PRIMARY MODEL
    # ---------------------------------------------------------

    for attempt in range(3):

        try:

            print(
                f"Guest Agent: trying {primary_model} "
                f"(attempt {attempt + 1}/3)"
            )

            response = client.models.generate_content(
                model=primary_model,
                contents=prompt
            )

            return response.text

        except Exception as e:

            print(
                f"Guest Agent: {primary_model} failed: {e}"
            )

            if attempt < 2:

                wait_time = 5 * (attempt + 1)

                print(
                    f"Retrying in {wait_time} seconds..."
                )

                time.sleep(wait_time)

    # ---------------------------------------------------------
    # FALLBACK MODEL
    # ---------------------------------------------------------

    print(
        f"Guest Agent: switching to {fallback_model}"
    )

    for attempt in range(3):

        try:

            print(
                f"Guest Agent: trying {fallback_model} "
                f"(attempt {attempt + 1}/3)"
            )

            response = client.models.generate_content(
                model=fallback_model,
                contents=prompt
            )

            return response.text

        except Exception as e:

            print(
                f"Guest Agent: {fallback_model} failed: {e}"
            )

            if attempt < 2:

                wait_time = 5 * (attempt + 1)

                print(
                    f"Retrying in {wait_time} seconds..."
                )

                time.sleep(wait_time)

    raise RuntimeError(
        "Guest Agent failed after multiple attempts "
        "using both Gemini models."
    )