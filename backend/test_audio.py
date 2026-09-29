from backend.database import SessionLocal
from backend.models import Podcast, Script
from backend.agents.audio_agent import generate_podcast_audio


db = SessionLocal()

try:
    podcast = (
        db.query(Podcast)
        .filter(Podcast.id == 2)
        .first()
    )

    script = (
        db.query(Script)
        .filter(Script.podcast_id == 2)
        .order_by(Script.id.desc())
        .first()
    )

    if not podcast:
        print("Podcast not found")
        exit()

    if not script:
        print("Script not found")
        exit()

    print("Generating podcast audio...")

    final_audio = generate_podcast_audio(
        script.content,
        podcast.id
    )

    print("\n===== AUDIO GENERATED =====")
    print(f"File: {final_audio}")

finally:
    db.close()