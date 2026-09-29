from pathlib import Path
import time
import traceback

from fastapi import FastAPI, Request
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import Response, JSONResponse
from sqlalchemy import text
from sqlalchemy.exc import OperationalError

from backend.database import SessionLocal
from backend.models import Podcast, Research, Outline, Script, AudioFile
from backend.schemas import (
    PodcastCreate,
    ResearchCreate,
    ScriptCreate,
    AudioFileCreate,
    PodcastGenerationRequest,
)

from backend.agents.research_agent import generate_research
from backend.agents.producer_agent import generate_outline
from backend.agents.host_agent import generate_host_dialogue
from backend.agents.guest_agent import generate_guest_dialogue
from backend.agents.reviewer_agent import generate_final_script
from backend.agents.audio_agent import generate_podcast_audio


app = FastAPI()



@app.exception_handler(OperationalError)
async def database_error_handler(request: Request, exc: OperationalError):
    """Return a clear 503 when PostgreSQL is temporarily unavailable."""
    return JSONResponse(
        status_code=503,
        content={
            "error": "Database temporarily unavailable. Please retry.",
        },
        headers={"Retry-After": "3"},
    )

app.add_middleware(
    CORSMiddleware,
    allow_origins=[
        "http://localhost:5173",
        "http://127.0.0.1:5173",
        "https://ai-powered-multi-agent-podcast-gene.vercel.app",
    ],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)


# ============================================================
# POSTGRES RETRY HELPERS
# ============================================================


def db_retry(operation, attempts=3, base_delay=1.0, commit=False):
    """Run one short DB operation with retries for transient PostgreSQL errors."""
    last_error = None

    for attempt in range(1, attempts + 1):
        db = SessionLocal()
        try:
            result = operation(db)

            if commit:
                db.commit()
            else:
                # End any read transaction cleanly before returning the connection.
                db.rollback()

            return result

        except OperationalError as exc:
            last_error = exc

            try:
                db.rollback()
            except Exception:
                pass

            if attempt < attempts:
                wait_time = base_delay * attempt
                print(
                    f"PostgreSQL operation failed (attempt {attempt}/{attempts}): {exc}"
                )
                print(f"Retrying database operation in {wait_time:.0f} seconds...")
                time.sleep(wait_time)

        finally:
            try:
                db.close()
            except Exception:
                pass

    raise last_error


# ============================================================
# PERSISTENT AUDIO STORAGE
# ============================================================


def ensure_audio_data_column():
    """Ensure the persistent audio column exists on the existing DB."""

    def operation(db):
        db.execute(
            text(
                "ALTER TABLE audio_files "
                "ADD COLUMN IF NOT EXISTS audio_data BYTEA"
            )
        )

    db_retry(operation, commit=True)


@app.on_event("startup")
def startup_audio_storage():
    ensure_audio_data_column()


# ============================================================
# BASIC ROUTES
# ============================================================


@app.get("/")
def root():
    return {"message": "Podcast Generator API is running"}


@app.get("/test-db")
def test_db():
    def operation(db):
        return db.execute(text("SELECT 1")).scalar()

    result = db_retry(operation)
    return {"database": "connected", "result": result}


# ============================================================
# PODCAST ROUTES
# ============================================================


@app.post("/podcasts")
def create_podcast(podcast: PodcastCreate):
    def operation(db):
        new_podcast = Podcast(
            user_id=podcast.user_id,
            title=podcast.title,
            topic=podcast.topic,
            duration=podcast.duration,
            language=podcast.language,
            speakers=podcast.speakers,
            status=podcast.status,
        )
        db.add(new_podcast)
        db.flush()
        return new_podcast.id

    podcast_id = db_retry(operation, commit=True)
    return {
        "message": "Podcast created successfully",
        "podcast_id": podcast_id,
    }


@app.get("/podcasts")
def get_podcasts():
    def operation(db):
        podcasts = db.query(Podcast).order_by(Podcast.id.desc()).all()
        return [
            {
                "id": podcast.id,
                "user_id": podcast.user_id,
                "title": podcast.title,
                "topic": podcast.topic,
                "duration": podcast.duration,
                "language": podcast.language,
                "speakers": podcast.speakers,
                "status": podcast.status,
                "current_step": podcast.current_step,
                "created_at": podcast.created_at,
                "updated_at": podcast.updated_at,
            }
            for podcast in podcasts
        ]

    return db_retry(operation)


@app.get("/podcasts/{podcast_id}/status")
def get_podcast_status(podcast_id: int):
    def operation(db):
        podcast = (
            db.query(Podcast)
            .filter(Podcast.id == podcast_id)
            .first()
        )

        if not podcast:
            return None

        return {
            "podcast_id": podcast.id,
            "title": podcast.title,
            "status": podcast.status,
            "current_step": podcast.current_step,
        }

    result = db_retry(operation)

    if result is None:
        return {"error": "Podcast not found"}

    return result


@app.get("/podcasts/{podcast_id}")
def get_podcast_details(podcast_id: int):
    def operation(db):
        podcast = (
            db.query(Podcast)
            .filter(Podcast.id == podcast_id)
            .first()
        )

        if not podcast:
            return None

        research = (
            db.query(Research)
            .filter(Research.podcast_id == podcast_id)
            .order_by(Research.id.desc())
            .first()
        )

        outline = (
            db.query(Outline)
            .filter(Outline.podcast_id == podcast_id)
            .order_by(Outline.id.desc())
            .first()
        )

        script = (
            db.query(Script)
            .filter(Script.podcast_id == podcast_id)
            .order_by(Script.id.desc())
            .first()
        )

        audio = (
            db.query(AudioFile)
            .filter(
                AudioFile.podcast_id == podcast_id,
                AudioFile.speaker == "combined",
            )
            .order_by(AudioFile.id.desc())
            .first()
        )

        # Migrate older records if the original local file still exists.
        if audio and not audio.audio_data:
            audio_path = Path(audio.file_url)
            if audio_path.exists():
                audio.audio_data = audio_path.read_bytes()
                db.commit()

        return {
            "podcast": {
                "id": podcast.id,
                "title": podcast.title,
                "topic": podcast.topic,
                "duration": podcast.duration,
                "language": podcast.language,
                "speakers": podcast.speakers,
                "status": podcast.status,
                "current_step": podcast.current_step,
            },
            "research": (
                {"id": research.id, "content": research.content}
                if research
                else None
            ),
            "outline": (
                {"id": outline.id, "content": outline.content}
                if outline
                else None
            ),
            "script": (
                {"id": script.id, "content": script.content}
                if script
                else None
            ),
            "audio": (
                {"id": audio.id, "url": f"/audio/{podcast.id}"}
                if audio
                else None
            ),
        }

    result = db_retry(operation)

    if result is None:
        return {"error": "Podcast not found"}

    return result


# ============================================================
# RESEARCH ROUTES
# ============================================================


@app.post("/research")
def create_research(research: ResearchCreate):
    def operation(db):
        new_research = Research(
            podcast_id=research.podcast_id,
            content=research.content,
        )
        db.add(new_research)
        db.flush()
        return new_research.id

    research_id = db_retry(operation, commit=True)
    return {
        "message": "Research created successfully",
        "research_id": research_id,
    }


@app.get("/research/{podcast_id}")
def get_research(podcast_id: int):
    def operation(db):
        research = (
            db.query(Research)
            .filter(Research.podcast_id == podcast_id)
            .all()
        )
        return [
            {
                "id": item.id,
                "podcast_id": item.podcast_id,
                "content": item.content,
            }
            for item in research
        ]

    return db_retry(operation)


# ============================================================
# SCRIPT ROUTES
# ============================================================


@app.post("/scripts")
def create_script(script: ScriptCreate):
    def operation(db):
        new_script = Script(
            podcast_id=script.podcast_id,
            content=script.content,
        )
        db.add(new_script)
        db.flush()
        return new_script.id

    script_id = db_retry(operation, commit=True)
    return {
        "message": "Script created successfully",
        "script_id": script_id,
    }


@app.get("/scripts/{podcast_id}")
def get_scripts(podcast_id: int):
    def operation(db):
        scripts = (
            db.query(Script)
            .filter(Script.podcast_id == podcast_id)
            .all()
        )
        return [
            {
                "id": item.id,
                "podcast_id": item.podcast_id,
                "content": item.content,
            }
            for item in scripts
        ]

    return db_retry(operation)


# ============================================================
# AUDIO DATABASE ROUTES
# ============================================================


@app.post("/audio-files")
def create_audio_file(audio: AudioFileCreate):
    def operation(db):
        new_audio = AudioFile(
            podcast_id=audio.podcast_id,
            speaker=audio.speaker,
            file_url=audio.file_url,
        )
        db.add(new_audio)
        db.flush()
        return new_audio.id

    audio_file_id = db_retry(operation, commit=True)
    return {
        "message": "Audio file created successfully",
        "audio_file_id": audio_file_id,
    }


@app.get("/audio-files/{podcast_id}")
def get_audio_files(podcast_id: int):
    def operation(db):
        audio_files = (
            db.query(AudioFile)
            .filter(AudioFile.podcast_id == podcast_id)
            .all()
        )
        return [
            {
                "id": item.id,
                "podcast_id": item.podcast_id,
                "speaker": item.speaker,
                "file_url": item.file_url,
            }
            for item in audio_files
        ]

    return db_retry(operation)


# ============================================================
# SMALL DATABASE UPDATE HELPERS
# ============================================================


def set_podcast_step(podcast_id: int, step: str):
    def operation(db):
        podcast = (
            db.query(Podcast)
            .filter(Podcast.id == podcast_id)
            .first()
        )
        if not podcast:
            raise ValueError(f"Podcast {podcast_id} not found")
        podcast.status = "generating"
        podcast.current_step = step

    db_retry(operation, commit=True)


def get_podcast_topic(podcast_id: int):
    def operation(db):
        podcast = (
            db.query(Podcast)
            .filter(Podcast.id == podcast_id)
            .first()
        )
        if not podcast:
            return None
        return podcast.topic

    return db_retry(operation)


def get_existing_research(podcast_id: int):
    def operation(db):
        research = (
            db.query(Research)
            .filter(Research.podcast_id == podcast_id)
            .order_by(Research.id.desc())
            .first()
        )
        if not research:
            return None
        return research.content

    return db_retry(operation)


def save_research(podcast_id: int, content: str):
    def operation(db):
        db.add(Research(podcast_id=podcast_id, content=content))

    db_retry(operation, commit=True)


def save_outline(podcast_id: int, content: str):
    def operation(db):
        db.add(Outline(podcast_id=podcast_id, content=content))

    db_retry(operation, commit=True)


def save_script(podcast_id: int, content: str):
    def operation(db):
        db.add(Script(podcast_id=podcast_id, content=content))

    db_retry(operation, commit=True)


def save_audio(podcast_id: int, final_audio_path: Path, audio_bytes: bytes):
    def operation(db):
        db.add(
            AudioFile(
                podcast_id=podcast_id,
                speaker="combined",
                file_url=str(final_audio_path),
                audio_data=audio_bytes,
            )
        )

    db_retry(operation, commit=True)


def mark_completed(podcast_id: int):
    def operation(db):
        podcast = (
            db.query(Podcast)
            .filter(Podcast.id == podcast_id)
            .first()
        )
        if podcast:
            podcast.status = "completed"
            podcast.current_step = "completed"

    db_retry(operation, commit=True)


def mark_failed(podcast_id: int):
    def operation(db):
        podcast = (
            db.query(Podcast)
            .filter(Podcast.id == podcast_id)
            .first()
        )
        if podcast:
            podcast.status = "failed"
            podcast.current_step = "failed"

    db_retry(operation, commit=True)


# ============================================================
# BACKGROUND GENERATION PIPELINE
# ============================================================


def run_podcast_generation(podcast_id: int):
    """
    Run the multi-agent pipeline without keeping any DB session alive
    during Gemini, Edge-TTS, or FFmpeg work.
    """
    try:
        # --------------------------------------------------------
        # START
        # --------------------------------------------------------
        topic = get_podcast_topic(podcast_id)
        if not topic:
            print(f"Podcast {podcast_id} not found")
            return

        set_podcast_step(podcast_id, "researching")

        # --------------------------------------------------------
        # STEP 1: RESEARCH
        # --------------------------------------------------------
        research_content = get_existing_research(podcast_id)
        if research_content is None:
            research_content = generate_research(topic)
            save_research(podcast_id, research_content)

        # --------------------------------------------------------
        # STEP 2: OUTLINE
        # --------------------------------------------------------
        set_podcast_step(podcast_id, "outlining")
        outline_content = generate_outline(topic, research_content)
        save_outline(podcast_id, outline_content)

        # --------------------------------------------------------
        # STEP 3: HOST
        # --------------------------------------------------------
        set_podcast_step(podcast_id, "writing_host")
        host_dialogue = generate_host_dialogue(topic, outline_content)

        # --------------------------------------------------------
        # STEP 4: GUEST
        # --------------------------------------------------------
        set_podcast_step(podcast_id, "writing_guest")
        guest_dialogue = generate_guest_dialogue(topic, outline_content)

        # --------------------------------------------------------
        # STEP 5: REVIEWER
        # --------------------------------------------------------
        set_podcast_step(podcast_id, "reviewing")
        final_script = generate_final_script(
            topic,
            outline_content,
            host_dialogue,
            guest_dialogue,
        )
        save_script(podcast_id, final_script)

        # --------------------------------------------------------
        # STEP 6: AUDIO
        # --------------------------------------------------------
        set_podcast_step(podcast_id, "generating_audio")
        final_audio = generate_podcast_audio(final_script, podcast_id)
        audio_bytes = final_audio.read_bytes()
        save_audio(podcast_id, final_audio, audio_bytes)

        # --------------------------------------------------------
        # COMPLETE
        # --------------------------------------------------------
        mark_completed(podcast_id)
        print(f"Podcast {podcast_id} generated successfully.")

    except Exception as exc:
        print("\n========================================")
        print("PODCAST GENERATION FAILED")
        print("========================================")
        print(f"Podcast ID: {podcast_id}")
        print(f"Error: {exc}")
        traceback.print_exc()
        print("========================================\n")

        try:
            mark_failed(podcast_id)
        except Exception as failure_update_error:
            print(
                "Failed to update podcast failure status: "
                f"{failure_update_error}"
            )


# ============================================================
# GENERATION ROUTES
# ============================================================


@app.post("/generate-podcast")
def generate_podcast(
    request: PodcastGenerationRequest,
):
    def operation(db):
        podcast = (
            db.query(Podcast)
            .filter(Podcast.id == request.podcast_id)
            .first()
        )
        if not podcast:
            return None

        if podcast.status == "generating":
            return {
                "message": "Podcast generation is already in progress",
                "podcast_id": podcast.id,
                "status": "generating",
                "current_step": podcast.current_step,
                "queue": False,
            }

        if podcast.status == "completed":
            return {
                "message": "Podcast has already been generated",
                "podcast_id": podcast.id,
                "status": "completed",
                "current_step": podcast.current_step,
                "queue": False,
            }

        podcast.status = "generating"
        podcast.current_step = "researching"
        return {
            "message": "Podcast generation started",
            "podcast_id": podcast.id,
            "status": "generating",
            "current_step": "researching",
            "queue": True,
        }

    result = db_retry(operation, commit=True)

    if result is None:
        return {"error": "Podcast not found"}

    # The Render background worker picks up podcasts with
    # status="generating" from PostgreSQL.
    return result


@app.post("/podcasts/{podcast_id}/regenerate")
def regenerate_podcast(
    podcast_id: int,
):
    def operation(db):
        podcast = (
            db.query(Podcast)
            .filter(Podcast.id == podcast_id)
            .first()
        )
        if not podcast:
            return None

        if podcast.status == "generating":
            return {
                "message": "Podcast generation is already in progress",
                "podcast_id": podcast.id,
                "status": "generating",
                "current_step": podcast.current_step,
                "queue": False,
            }

        podcast.status = "generating"
        podcast.current_step = "researching"
        return {
            "message": "Podcast regeneration started",
            "podcast_id": podcast.id,
            "status": "generating",
            "current_step": "researching",
            "queue": True,
        }

    result = db_retry(operation, commit=True)

    if result is None:
        return {"error": "Podcast not found"}

    # The Render background worker picks up podcasts with
    # status="generating" from PostgreSQL.
    return result


# ============================================================
# SERVE GENERATED PODCAST AUDIO
# ============================================================


@app.get("/audio/{podcast_id}")
def get_podcast_audio(podcast_id: int):
    def operation(db):
        audio = (
            db.query(AudioFile)
            .filter(
                AudioFile.podcast_id == podcast_id,
                AudioFile.speaker == "combined",
            )
            .order_by(AudioFile.id.desc())
            .first()
        )

        if not audio:
            return None

        if audio.audio_data:
            return {
                "data": audio.audio_data,
                "filename": f"podcast_{podcast_id}_final.wav",
            }

        audio_path = Path(audio.file_url)
        if audio_path.exists():
            audio_bytes = audio_path.read_bytes()
            audio.audio_data = audio_bytes
            db.commit()
            return {
                "data": audio_bytes,
                "filename": audio_path.name,
            }

        return "missing"

    result = db_retry(operation)

    if result is None:
        return {"error": "Audio not found"}

    if result == "missing":
        return {
            "error": "Audio file is not available. Please regenerate this podcast once."
        }

    return Response(
        content=result["data"],
        media_type="audio/wav",
        headers={
            "Content-Disposition": (
                f'inline; filename="{result["filename"]}"'
            )
        },
    )


# ============================================================
# DELETE PODCAST
# ============================================================


@app.delete("/podcasts/{podcast_id}")
def delete_podcast(podcast_id: int):
    def operation(db):
        podcast = (
            db.query(Podcast)
            .filter(Podcast.id == podcast_id)
            .first()
        )
        if not podcast:
            return False

        db.query(Research).filter(
            Research.podcast_id == podcast_id
        ).delete(synchronize_session=False)

        db.query(Outline).filter(
            Outline.podcast_id == podcast_id
        ).delete(synchronize_session=False)

        db.query(Script).filter(
            Script.podcast_id == podcast_id
        ).delete(synchronize_session=False)

        db.query(AudioFile).filter(
            AudioFile.podcast_id == podcast_id
        ).delete(synchronize_session=False)

        db.delete(podcast)
        return True

    deleted = db_retry(operation, commit=True)

    if not deleted:
        return {"error": "Podcast not found"}

    return {
        "message": "Podcast deleted successfully",
        "podcast_id": podcast_id,
    }
