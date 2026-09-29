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


def generate_final_script(
    topic: str,
    outline: str,
    host_dialogue: str,
    guest_dialogue: str
) -> str:

    prompt = f"""
You are the REVIEWER and DIRECTOR agent in an
AI-powered multi-agent podcast generator.

Your job is to transform separate Host and Guest dialogue
into one natural, engaging podcast conversation.

Podcast topic:

{topic}

Podcast outline:

{outline}

HOST DIALOGUE:

{host_dialogue}

GUEST DIALOGUE:

{guest_dialogue}

Create the FINAL PODCAST SCRIPT.

Requirements:

1. Preserve the important information from the outline.

2. Organize the conversation logically from introduction
   to conclusion.

3. Combine the Host and Guest dialogue into a natural conversation.

4. The host should ask questions and guide the discussion.

5. The guest should provide detailed and informative answers.

6. Make the conversation sound natural and spontaneous.

7. Remove unnecessary repetition.

8. Add smooth transitions between discussion topics.

9. Keep the host curious and engaging.

10. Keep the guest informative and conversational.

11. Include an engaging opening.

12. End the podcast with a natural conclusion.

13. Do not add unsupported factual claims.

14. Do not make the conversation sound like an academic lecture.

15. Keep the number of exchanges appropriate for the
    amount of information in the research and outline.

16. Do not unnecessarily shorten the conversation.

17. Preserve useful questions, explanations, examples,
    perspectives and insights from the Host and Guest dialogue.

18. Do not include stage directions, narration, sound effects,
    or descriptions of how a speaker should deliver a line.

19. Write only spoken dialogue.

Use this format:

HOST:

[Host dialogue]

GUEST:

[Guest dialogue]

HOST:

[Host dialogue]

GUEST:

[Guest dialogue]

Continue the conversation naturally for as many exchanges
as are necessary to properly cover the podcast topic.

FINAL VALIDATION:

Make sure every speaker section begins with exactly:

HOST:

or

GUEST:

Do not add labels such as:

NARRATOR:
STAGE DIRECTION:
SOUND EFFECT:

Return ONLY the final podcast script.

Do not include analysis, explanations, headings, numbering,
or validation information.
"""

    primary_model = "gemini-3.5-flash"
    fallback_model = "gemini-3.5-flash-lite"

    # ---------------------------------------------------------
    # PRIMARY MODEL
    # ---------------------------------------------------------

    for attempt in range(3):

        try:

            print(
                f"Reviewer Agent: trying {primary_model} "
                f"(attempt {attempt + 1}/3)"
            )

            response = client.models.generate_content(
                model=primary_model,
                contents=prompt
            )

            return response.text

        except Exception as e:

            print(
                f"Reviewer Agent: {primary_model} failed: {e}"
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
        f"Reviewer Agent: switching to {fallback_model}"
    )

    for attempt in range(3):

        try:

            print(
                f"Reviewer Agent: trying {fallback_model} "
                f"(attempt {attempt + 1}/3)"
            )

            response = client.models.generate_content(
                model=fallback_model,
                contents=prompt
            )

            return response.text

        except Exception as e:

            print(
                f"Reviewer Agent: {fallback_model} failed: {e}"
            )

            if attempt < 2:

                wait_time = 5 * (attempt + 1)

                print(
                    f"Retrying in {wait_time} seconds..."
                )

                time.sleep(wait_time)

    raise RuntimeError(
        "Reviewer Agent failed after multiple attempts "
        "using both Gemini models."
    )