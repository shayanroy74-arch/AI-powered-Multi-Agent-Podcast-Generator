from sqlalchemy import Column, Integer, String, Text, DateTime, ForeignKey, LargeBinary, func
from sqlalchemy.orm import relationship

from backend.database import Base


class User(Base):
    __tablename__ = "users"

    id = Column(Integer, primary_key=True)
    name = Column(String, nullable=False)
    email = Column(String, nullable=False)
    password_hash = Column(Text, nullable=False)
    created_at = Column(DateTime, nullable=True)

    podcasts = relationship("Podcast", back_populates="user")


class Podcast(Base):
    __tablename__ = "podcasts"

    id = Column(Integer, primary_key=True)
    user_id = Column(Integer, ForeignKey("users.id"), nullable=False)
    title = Column(String, nullable=False)
    topic = Column(Text, nullable=False)
    duration = Column(Integer, nullable=True)
    language = Column(String, nullable=True)
    speakers = Column(Integer, nullable=True)
    status = Column(String, nullable=True)
    current_step = Column(String, nullable=True)
    created_at = Column(
        DateTime,
        server_default=func.now(),
        nullable=False
    )

    updated_at = Column(
        DateTime,
        server_default=func.now(),
        onupdate=func.now(),
        nullable=False
    )

    user = relationship("User", back_populates="podcasts")
    research = relationship("Research", back_populates="podcast")
    outlines = relationship("Outline", back_populates="podcast")
    scripts = relationship("Script", back_populates="podcast")
    audio_files = relationship("AudioFile", back_populates="podcast")
    


class Research(Base):
    __tablename__ = "research"

    id = Column(Integer, primary_key=True)
    podcast_id = Column(Integer, ForeignKey("podcasts.id"), nullable=False)
    content = Column(Text, nullable=False)
    created_at = Column(DateTime, nullable=True)

    podcast = relationship("Podcast", back_populates="research")

class Outline(Base):
    __tablename__ = "outlines"

    id = Column(Integer, primary_key=True)
    podcast_id = Column(Integer, ForeignKey("podcasts.id"), nullable=False)
    content = Column(Text, nullable=False)
    created_at = Column(DateTime, nullable=True)

    podcast = relationship("Podcast", back_populates="outlines")

class Script(Base):
    __tablename__ = "scripts"

    id = Column(Integer, primary_key=True)
    podcast_id = Column(Integer, ForeignKey("podcasts.id"), nullable=False)
    content = Column(Text, nullable=False)
    created_at = Column(DateTime, nullable=True)

    podcast = relationship("Podcast", back_populates="scripts")


class AudioFile(Base):
    __tablename__ = "audio_files"

    id = Column(Integer, primary_key=True)
    podcast_id = Column(Integer, ForeignKey("podcasts.id"), nullable=False)
    speaker = Column(String, nullable=True)
    file_url = Column(Text, nullable=False)
    audio_data = Column(LargeBinary, nullable=True)
    created_at = Column(DateTime, nullable=True)

    podcast = relationship("Podcast", back_populates="audio_files")