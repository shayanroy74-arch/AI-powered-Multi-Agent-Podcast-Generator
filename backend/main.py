from pathlib import Path
import traceback
from fastapi import FastAPI, Depends, BackgroundTasks
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import Response
from sqlalchemy.orm import Session
from sqlalchemy import text

from backend.database import SessionLocal
from backend.models import Podcast, Research, Outline, Script, AudioFile
from backend.schemas import (
    PodcastCreate,
    ResearchCreate,
    ScriptCreate,
    AudioFileCreate,
    PodcastGenerationRequest
)

from backend.agents.research_agent import generate_research
from backend.agents.producer_agent import generate_outline
from backend.agents.host_agent import generate_host_dialogue
from backend.agents.guest_agent import generate_guest_dialogue
from backend.agents.reviewer_agent import generate_final_script
from backend.agents.audio_agent import generate_podcast_audio


app = FastAPI()
app.add_middleware(
    CORSMiddleware,
    allow_origins=[
    "http://localhost:5173",
    "http://127.0.0.1:5173",
    "https://ai-powered-multi-agent-podcast-gene.vercel.app"
    ],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# ============================================================
# PERSISTENT AUDIO STORAGE
# ============================================================

def ensure_audio_data_column():
    """Add persistent audio storage to existing PostgreSQL databases."""
    with SessionLocal() as db:
        db.execute(
            text(
                "ALTER TABLE audio_files "
                "ADD COLUMN IF NOT EXISTS audio_data BYTEA"
            )
        )
        db.commit()


@app.on_event("startup")
def startup_audio_storage():
    ensure_audio_data_column()


# ============================================================
# DATABASE DEPENDENCY
# ============================================================

def get_db():
    db = SessionLocal()

    try:
        yield db
    finally:
        db.close()


# ============================================================
# BASIC ROUTES
# ============================================================

@app.get("/")
def root():
    return {
        "message": "Podcast Generator API is running"
    }


@app.get("/test-db")
def test_db():

    with SessionLocal() as db:

        result = db.execute(
            text("SELECT 1")
        )

        return {
            "database": "connected",
            "result": result.scalar()
        }


# ============================================================
# PODCAST ROUTES
# ============================================================

@app.post("/podcasts")
def create_podcast(
    podcast: PodcastCreate,
    db: Session = Depends(get_db)
):

    new_podcast = Podcast(
        user_id=podcast.user_id,
        title=podcast.title,
        topic=podcast.topic,
        duration=podcast.duration,
        language=podcast.language,
        speakers=podcast.speakers,
        status=podcast.status
        
    )

    db.add(new_podcast)
    db.commit()
    db.refresh(new_podcast)

    return {
        "message": "Podcast created successfully",
        "podcast_id": new_podcast.id
    }


@app.get("/podcasts")
def get_podcasts(
    db: Session = Depends(get_db)
):

    podcasts = (
        db.query(Podcast)
        .all()
    )

    return podcasts


@app.get("/podcasts/{podcast_id}/status")
def get_podcast_status(
    podcast_id: int,
    db: Session = Depends(get_db)
):

    podcast = (
        db.query(Podcast)
        .filter(Podcast.id == podcast_id)
        .first()
    )

    if not podcast:
        return {
            "error": "Podcast not found"
        }

    return {
        "podcast_id": podcast.id,
        "title": podcast.title,
        "status": podcast.status,
        "current_step": podcast.current_step
    }


@app.get("/podcasts/{podcast_id}")
def get_podcast_details(
    podcast_id: int,
    db: Session = Depends(get_db)
):

    podcast = (
        db.query(Podcast)
        .filter(Podcast.id == podcast_id)
        .first()
    )

    if not podcast:
        return {
            "error": "Podcast not found"
        }

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
            AudioFile.speaker == "combined"
        )
        .order_by(AudioFile.id.desc())
        .first()
    )

    # Persist older audio files if they still exist on the local filesystem.
    # This upgrades records created before persistent audio storage was added.
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
            "current_step": podcast.current_step
            
        },

        "research": (
            {
                "id": research.id,
                "content": research.content
            }
            if research else None
        ),

        "outline": (
            {
                "id": outline.id,
                "content": outline.content
            }
            if outline else None
        ),

        "script": (
            {
                "id": script.id,
                "content": script.content
            }
            if script else None
        ),

        "audio": (
            {
                "id": audio.id,
                "url": f"/audio/{podcast.id}"
            }
            if audio else None
        )
    }


# ============================================================
# RESEARCH ROUTES
# ============================================================

@app.post("/research")
def create_research(
    research: ResearchCreate,
    db: Session = Depends(get_db)
):

    new_research = Research(
        podcast_id=research.podcast_id,
        content=research.content
    )

    db.add(new_research)
    db.commit()
    db.refresh(new_research)

    return {
        "message": "Research created successfully",
        "research_id": new_research.id
    }


@app.get("/research/{podcast_id}")
def get_research(
    podcast_id: int,
    db: Session = Depends(get_db)
):

    research = (
        db.query(Research)
        .filter(
            Research.podcast_id == podcast_id
        )
        .all()
    )

    return research


# ============================================================
# SCRIPT ROUTES
# ============================================================

@app.post("/scripts")
def create_script(
    script: ScriptCreate,
    db: Session = Depends(get_db)
):

    new_script = Script(
        podcast_id=script.podcast_id,
        content=script.content
    )

    db.add(new_script)
    db.commit()
    db.refresh(new_script)

    return {
        "message": "Script created successfully",
        "script_id": new_script.id
    }


@app.get("/scripts/{podcast_id}")
def get_scripts(
    podcast_id: int,
    db: Session = Depends(get_db)
):

    scripts = (
        db.query(Script)
        .filter(
            Script.podcast_id == podcast_id
        )
        .all()
    )

    return scripts


# ============================================================
# AUDIO DATABASE ROUTES
# ============================================================

@app.post("/audio-files")
def create_audio_file(
    audio: AudioFileCreate,
    db: Session = Depends(get_db)
):

    new_audio = AudioFile(
        podcast_id=audio.podcast_id,
        speaker=audio.speaker,
        file_url=audio.file_url
    )

    db.add(new_audio)
    db.commit()
    db.refresh(new_audio)

    return {
        "message": "Audio file created successfully",
        "audio_file_id": new_audio.id
    }


@app.get("/audio-files/{podcast_id}")
def get_audio_files(
    podcast_id: int,
    db: Session = Depends(get_db)
):

    audio_files = (
        db.query(AudioFile)
        .filter(
            AudioFile.podcast_id == podcast_id
        )
        .all()
    )

    return audio_files

def run_podcast_generation(podcast_id: int):
    db = SessionLocal()

    try:
        # --------------------------------------------------------
        # FIND PODCAST
        # --------------------------------------------------------

        podcast = (
            db.query(Podcast)
            .filter(Podcast.id == podcast_id)
            .first()
        )

        if not podcast:
            return

        # --------------------------------------------------------
        # START GENERATION
        # --------------------------------------------------------

        podcast.status = "generating"
        podcast.current_step = "researching"
        db.commit()

        # --------------------------------------------------------
        # STEP 1: RESEARCH AGENT
        # --------------------------------------------------------

        existing_research = (
            db.query(Research)
            .filter(
                Research.podcast_id == podcast.id
            )
            .order_by(
                Research.id.desc()
            )
            .first()
        )

        if existing_research:
            research_content = existing_research.content
            research_id = existing_research.id

        else:
            research_content = generate_research(
                podcast.topic
            )

            new_research = Research(
                podcast_id=podcast.id,
                content=research_content
            )

            db.add(new_research)
            db.commit()
            db.refresh(new_research)

            research_id = new_research.id

        # --------------------------------------------------------
        # STEP 2: PRODUCER AGENT
        # --------------------------------------------------------

        podcast.current_step = "outlining"
        db.commit()

        outline_content = generate_outline(
            podcast.topic,
            research_content
        )

        new_outline = Outline(
            podcast_id=podcast.id,
            content=outline_content
        )

        db.add(new_outline)
        db.commit()
        db.refresh(new_outline)

        # --------------------------------------------------------
        # STEP 3: HOST AGENT
        # --------------------------------------------------------

        podcast.current_step = "writing_host"
        db.commit()

        host_dialogue = generate_host_dialogue(
            podcast.topic,
            outline_content
        )

        # --------------------------------------------------------
        # STEP 4: GUEST AGENT
        # --------------------------------------------------------

        podcast.current_step = "writing_guest"
        db.commit()

        guest_dialogue = generate_guest_dialogue(
            podcast.topic,
            outline_content
        )

        # --------------------------------------------------------
        # STEP 5: REVIEWER / DIRECTOR AGENT
        # --------------------------------------------------------

        podcast.current_step = "reviewing"
        db.commit()

        final_script = generate_final_script(
            podcast.topic,
            outline_content,
            host_dialogue,
            guest_dialogue
        )

        # --------------------------------------------------------
        # STEP 6: SAVE FINAL SCRIPT
        # --------------------------------------------------------

        new_script = Script(
            podcast_id=podcast.id,
            content=final_script
        )

        db.add(new_script)
        db.commit()
        db.refresh(new_script)

        # --------------------------------------------------------
        # STEP 7: GENERATE AUDIO
        # --------------------------------------------------------

        podcast.current_step = "generating_audio"
        db.commit()

        final_audio = generate_podcast_audio(
            final_script,
            podcast.id
        )

        # --------------------------------------------------------
        # STEP 8: SAVE AUDIO INFORMATION
        # --------------------------------------------------------

        # Persist the final audio in PostgreSQL. Render's local filesystem
        # is ephemeral, so the database copy survives instance restarts.
        audio_bytes = final_audio.read_bytes()

        new_audio = AudioFile(
            podcast_id=podcast.id,
            speaker="combined",
            file_url=str(final_audio),
            audio_data=audio_bytes
        )

        db.add(new_audio)
        db.commit()
        db.refresh(new_audio)

        # --------------------------------------------------------
        # GENERATION COMPLETED
        # --------------------------------------------------------

        podcast.status = "completed"
        podcast.current_step = "completed"
        db.commit()

    except Exception as e:
        print("\n========================================")
        print("PODCAST GENERATION FAILED")
        print("========================================")
        print(f"Podcast ID: {podcast_id}")
        print(f"Error: {e}")
        traceback.print_exc()
        print("========================================\n")

        podcast = (
            db.query(Podcast)
            .filter(Podcast.id == podcast_id)
            .first()
        )

        if podcast:
            podcast.status = "failed"
            podcast.current_step = "failed"
            db.commit()

    finally:
        db.close()
# ============================================================
# COMPLETE PODCAST GENERATION PIPELINE
# ============================================================

@app.post("/generate-podcast")
def generate_podcast(
    request: PodcastGenerationRequest,
    background_tasks: BackgroundTasks,
    db: Session = Depends(get_db)
):

    # --------------------------------------------------------
    # FIND PODCAST
    # --------------------------------------------------------

    podcast = (
        db.query(Podcast)
        .filter(Podcast.id == request.podcast_id)
        .first()
    )

    if not podcast:
        return {
            "error": "Podcast not found"
        }

    # --------------------------------------------------------
    # PREVENT DUPLICATE GENERATION
    # --------------------------------------------------------

    if podcast.status == "generating":
        return {
            "message": "Podcast generation is already in progress",
            "podcast_id": podcast.id,
            "status": "generating",
            "current_step": podcast.current_step
        }

    if podcast.status == "completed":
        return {
            "message": "Podcast has already been generated",
            "podcast_id": podcast.id,
            "status": "completed",
            "current_step": podcast.current_step
        }

    # --------------------------------------------------------
    # MARK AS GENERATING
    # --------------------------------------------------------

    podcast.status = "generating"
    podcast.current_step = "researching"

    db.commit()

    # --------------------------------------------------------
    # START BACKGROUND GENERATION
    # --------------------------------------------------------

    background_tasks.add_task(
        run_podcast_generation,
        podcast.id
    )

    # --------------------------------------------------------
    # RETURN IMMEDIATELY
    # --------------------------------------------------------

    return {
        "message": "Podcast generation started",
        "podcast_id": podcast.id,
        "status": "generating",
        "current_step": "researching"
    }

# ============================================================
# REGENERATE PODCAST
# ============================================================

@app.post("/podcasts/{podcast_id}/regenerate")
def regenerate_podcast(
    podcast_id: int,
    background_tasks: BackgroundTasks,
    db: Session = Depends(get_db)
):

    # --------------------------------------------------------
    # FIND PODCAST
    # --------------------------------------------------------

    podcast = (
        db.query(Podcast)
        .filter(Podcast.id == podcast_id)
        .first()
    )

    if not podcast:
        return {
            "error": "Podcast not found"
        }

    # --------------------------------------------------------
    # PREVENT DUPLICATE GENERATION
    # --------------------------------------------------------

    if podcast.status == "generating":
        return {
            "message": "Podcast generation is already in progress",
            "podcast_id": podcast.id,
            "status": "generating",
            "current_step": podcast.current_step
        }

    # --------------------------------------------------------
    # RESET GENERATION STATE
    # --------------------------------------------------------

    podcast.status = "generating"
    podcast.current_step = "researching"

    db.commit()

    # --------------------------------------------------------
    # START BACKGROUND GENERATION
    # --------------------------------------------------------

    background_tasks.add_task(
        run_podcast_generation,
        podcast.id
    )

    # --------------------------------------------------------
    # RETURN IMMEDIATELY
    # --------------------------------------------------------

    return {
        "message": "Podcast regeneration started",
        "podcast_id": podcast.id,
        "status": "generating",
        "current_step": "researching"
    }

# ============================================================
# SERVE GENERATED PODCAST AUDIO
# ============================================================

@app.get("/audio/{podcast_id}")
def get_podcast_audio(
    podcast_id: int,
    db: Session = Depends(get_db)
):

    audio = (
        db.query(AudioFile)
        .filter(
            AudioFile.podcast_id == podcast_id,
            AudioFile.speaker == "combined"
        )
        .order_by(
            AudioFile.id.desc()
        )
        .first()
    )

    if not audio:

        return {
            "error": "Audio not found"
        }

    # Preferred path: serve the persistent database copy.
    if audio.audio_data:
        return Response(
            content=audio.audio_data,
            media_type="audio/wav",
            headers={
                "Content-Disposition": (
                    f'inline; filename="podcast_{podcast_id}_final.wav"'
                )
            },
        )

    # Backward-compatible fallback for older records. If the local file
    # still exists, persist it before returning it.
    audio_path = Path(audio.file_url)

    if audio_path.exists():
        audio_bytes = audio_path.read_bytes()
        audio.audio_data = audio_bytes
        db.commit()

        return Response(
            content=audio_bytes,
            media_type="audio/wav",
            headers={
                "Content-Disposition": (
                    f'inline; filename="{audio_path.name}"'
                )
            },
        )

    return {
        "error": "Audio file is not available. Please regenerate this podcast once."
    }

@app.delete("/podcasts/{podcast_id}")
def delete_podcast(
    podcast_id: int,
    db: Session = Depends(get_db)
):
    podcast = (
        db.query(Podcast)
        .filter(Podcast.id == podcast_id)
        .first()
    )

    if not podcast:
        return {
            "error": "Podcast not found"
        }

    # Delete related records
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

    # Delete the podcast itself
    db.delete(podcast)

    db.commit()

    return {
        "message": "Podcast deleted successfully",
        "podcast_id": podcast_id
    }