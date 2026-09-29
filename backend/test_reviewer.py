from backend.database import SessionLocal
from backend.models import Podcast, Outline, Script
from backend.agents.host_agent import generate_host_dialogue
from backend.agents.guest_agent import generate_guest_dialogue
from backend.agents.reviewer_agent import generate_final_script


db = SessionLocal()

try:
    podcast = (
        db.query(Podcast)
        .filter(Podcast.id == 2)
        .first()
    )

    outline = (
        db.query(Outline)
        .filter(Outline.podcast_id == 2)
        .order_by(Outline.id.desc())
        .first()
    )

    if not podcast:
        print("Podcast not found")
        exit()

    if not outline:
        print("Outline not found")
        exit()

    print("Generating host dialogue...")

    host_dialogue = generate_host_dialogue(
        podcast.topic,
        outline.content
    )

    print("Generating guest dialogue...")

    guest_dialogue = generate_guest_dialogue(
        podcast.topic,
        outline.content
    )

    print("Generating final script...")

    final_script = generate_final_script(
        podcast.topic,
        outline.content,
        host_dialogue,
        guest_dialogue
    )

    new_script = Script(
    podcast_id=podcast.id,
    content=final_script
    )

    db.add(new_script)
    db.commit()
    db.refresh(new_script)

    print("\n===== FINAL PODCAST SCRIPT =====\n")
    print(final_script)

    print("\n===== SCRIPT SAVED =====")
    print("Script ID:", new_script.id)  

finally:
    db.close()