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


def generate_outline(topic: str, research: str) -> str:

    prompt = f"""
You are the producer agent for an AI-powered multi-agent podcast generator.

The podcast topic is:

{topic}

Here is the research prepared by the research agent:

{research}

Create a structured podcast outline that another group of AI agents
can use to write the final podcast conversation.

The podcast should have multiple speakers.

Include:

1. Podcast title
2. Opening hook
3. Introduction
4. Main discussion sections
5. Important questions for the host to ask
6. Key points the guest should discuss
7. Examples or stories to include
8. Different viewpoints or debates
9. Smooth transitions between sections
10. Closing section

Make the outline conversational rather than an academic report.

Do not write the full dialogue yet.

Only create the structured outline.
"""

    # ---------------------------------------------------------
    # MODELS
    # ---------------------------------------------------------

    primary_model = "gemini-3.5-flash"
    fallback_model = "gemini-3.5-flash-lite"

    # ---------------------------------------------------------
    # TRY PRIMARY MODEL
    # ---------------------------------------------------------

    for attempt in range(3):

        try:

            print(
                f"Producer Agent: trying {primary_model} "
                f"(attempt {attempt + 1}/3)"
            )

            response = client.models.generate_content(
                model=primary_model,
                contents=prompt
            )

            return response.text

        except Exception as e:

            print(
                f"Producer Agent: {primary_model} failed: {e}"
            )

            if attempt < 2:

                wait_time = 5 * (attempt + 1)

                print(
                    f"Retrying in {wait_time} seconds..."
                )

                time.sleep(wait_time)

    # ---------------------------------------------------------
    # TRY FALLBACK MODEL
    # ---------------------------------------------------------

    print(
        f"Producer Agent: switching to {fallback_model}"
    )

    for attempt in range(3):

        try:

            print(
                f"Producer Agent: trying {fallback_model} "
                f"(attempt {attempt + 1}/3)"
            )

            response = client.models.generate_content(
                model=fallback_model,
                contents=prompt
            )

            return response.text

        except Exception as e:

            print(
                f"Producer Agent: {fallback_model} failed: {e}"
            )

            if attempt < 2:

                wait_time = 5 * (attempt + 1)

                print(
                    f"Retrying in {wait_time} seconds..."
                )

                time.sleep(wait_time)

    # ---------------------------------------------------------
    # BOTH MODELS FAILED
    # ---------------------------------------------------------

    raise RuntimeError(
        "Producer Agent failed after multiple attempts "
        "using both Gemini models."
    )