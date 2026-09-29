from backend.database import SessionLocal
from backend.models import Podcast, Outline
from backend.agents.host_agent import generate_host_dialogue


db = SessionLocal()

try:
    podcast = db.query(Podcast).filter(Podcast.id == 2).first()

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

    host_dialogue = generate_host_dialogue(
        podcast.topic,
        outline.content
    )

    print("\n===== HOST DIALOGUE =====\n")
    print(host_dialogue)

finally:
    db.close()