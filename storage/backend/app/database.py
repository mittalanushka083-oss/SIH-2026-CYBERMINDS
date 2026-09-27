from datetime import datetime
from pathlib import Path
from sqlalchemy import create_engine, String, Integer, Float, DateTime, Text
from sqlalchemy.orm import DeclarativeBase, Mapped, mapped_column, sessionmaker

ROOT_DIR = Path(__file__).resolve().parents[2]
DB_PATH = ROOT_DIR / "bordervision.db"
DATABASE_URL = f"sqlite:///{DB_PATH}"

engine = create_engine(DATABASE_URL, connect_args={"check_same_thread": False})
SessionLocal = sessionmaker(bind=engine, autoflush=False, autocommit=False)


class Base(DeclarativeBase):
    pass


class Camera(Base):
    __tablename__ = "cameras"
    id: Mapped[int] = mapped_column(Integer, primary_key=True)
    name: Mapped[str] = mapped_column(String(120), unique=True)
    source: Mapped[str] = mapped_column(String(500))
    status: Mapped[str] = mapped_column(String(30), default="OFFLINE")
    created_at: Mapped[datetime] = mapped_column(DateTime, default=datetime.utcnow)


class TemperatureReading(Base):
    __tablename__ = "temperature_readings"
    id: Mapped[int] = mapped_column(Integer, primary_key=True)
    sensor_mode: Mapped[str] = mapped_column(String(30), default="SIMULATION")
    human_reference_c: Mapped[float | None] = mapped_column(Float, nullable=True)
    ambient_c: Mapped[float | None] = mapped_column(Float, nullable=True)
    surface_c: Mapped[float | None] = mapped_column(Float, nullable=True)
    camera_c: Mapped[float | None] = mapped_column(Float, nullable=True)
    human_status: Mapped[str] = mapped_column(String(40), default="NORMAL_REFERENCE")
    created_at: Mapped[datetime] = mapped_column(DateTime, default=datetime.utcnow)


class Event(Base):
    __tablename__ = "events"
    id: Mapped[int] = mapped_column(Integer, primary_key=True)
    event_type: Mapped[str] = mapped_column(String(80))
    severity: Mapped[str] = mapped_column(String(20), default="MEDIUM")
    camera_name: Mapped[str] = mapped_column(String(120), default="Upload")
    object_class: Mapped[str | None] = mapped_column(String(50), nullable=True)
    track_id: Mapped[int | None] = mapped_column(Integer, nullable=True)
    confidence: Mapped[float | None] = mapped_column(Float, nullable=True)
    timestamp_sec: Mapped[float | None] = mapped_column(Float, nullable=True)
    message: Mapped[str] = mapped_column(Text)
    created_at: Mapped[datetime] = mapped_column(DateTime, default=datetime.utcnow)


Base.metadata.create_all(bind=engine)


def get_db():
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()
