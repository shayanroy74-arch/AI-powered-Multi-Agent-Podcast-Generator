from backend.database import SessionLocal
from backend.models import Podcast, Research
from backend.agents.producer_agent import generate_outline


db = SessionLocal()

try:
    podcast = db.query(Podcast).filter(Podcast.id == 2).first()
    research = (
        db.query(Research)
        .filter(Research.id == 3)
        .first()
    )

    if not podcast:
        print("Podcast not found")
        exit()

    if not research:
        print("Research not found")
        exit()

    outline = generate_outline(
        podcast.topic,
        research.content
    )

    print("\n===== PODCAST OUTLINE =====\n")
    print(outline)

finally:
    db.close()