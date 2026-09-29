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


def generate_research(topic: str) -> str:

    prompt = f"""
You are a research agent for an AI-powered podcast generator.

Research the following podcast topic:

{topic}

Create a clear research report that includes:

1. Introduction to the topic
2. Important facts and concepts
3. Recent developments
4. Different perspectives
5. Interesting examples
6. Key points that could be discussed in a podcast

Keep the information structured and easy for another AI agent
to use when writing a podcast script.
"""

    # ---------------------------------------------------------
    # PRIMARY MODEL
    # ---------------------------------------------------------

    primary_model = "gemini-3.5-flash"

    # ---------------------------------------------------------
    # FALLBACK MODEL
    # ---------------------------------------------------------

    fallback_model = "gemini-3.5-flash-lite"

    # ---------------------------------------------------------
    # RETRY PRIMARY MODEL
    # ---------------------------------------------------------

    for attempt in range(3):

        try:

            print(
                f"Research Agent: trying {primary_model} "
                f"(attempt {attempt + 1}/3)"
            )

            response = client.models.generate_content(
                model=primary_model,
                contents=prompt
            )

            return response.text

        except Exception as e:

            print(
                f"Research Agent: {primary_model} failed: {e}"
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
        f"Research Agent: switching to {fallback_model}"
    )

    for attempt in range(3):

        try:

            print(
                f"Research Agent: trying {fallback_model} "
                f"(attempt {attempt + 1}/3)"
            )

            response = client.models.generate_content(
                model=fallback_model,
                contents=prompt
            )

            return response.text

        except Exception as e:

            print(
                f"Research Agent: {fallback_model} failed: {e}"
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
        "Research Agent failed after multiple attempts "
        "using both Gemini models."
    )