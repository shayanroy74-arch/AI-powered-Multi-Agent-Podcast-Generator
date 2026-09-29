import time
import traceback

from backend.database import SessionLocal
from backend.models import Podcast
from backend.main import run_podcast_generation


POLL_INTERVAL_SECONDS = 5


def get_next_pending_podcast():
    db = SessionLocal()

    try:
        podcast = (
            db.query(Podcast)
            .filter(Podcast.status == "generating")
            .order_by(Podcast.id.asc())
            .first()
        )

        if podcast:
            return podcast.id

        return None

    finally:
        db.close()


def main():
    print("========================================")
    print("PODCAST BACKGROUND WORKER STARTED")
    print("========================================")

    while True:
        try:
            podcast_id = get_next_pending_podcast()

            if podcast_id is None:
                time.sleep(POLL_INTERVAL_SECONDS)
                continue

            print(
                f"Found podcast {podcast_id} "
                f"with status=generating"
            )

            print(
                f"Starting generation for podcast "
                f"{podcast_id}..."
            )

            run_podcast_generation(podcast_id)

            print(
                f"Finished processing podcast "
                f"{podcast_id}."
            )

        except Exception as exc:
            print("")
            print("========================================")
            print("WORKER ERROR")
            print("========================================")
            print(f"Error: {exc}")
            traceback.print_exc()
            print("========================================")
            print("Worker will continue running.")
            print("")

            time.sleep(POLL_INTERVAL_SECONDS)


if __name__ == "__main__":
    main()