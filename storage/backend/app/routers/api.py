import csv
import io
import uuid
from pathlib import Path
from threading import Thread

from fastapi import APIRouter, Depends, File, HTTPException, UploadFile
from fastapi.responses import StreamingResponse
from sqlalchemy import desc, func
from sqlalchemy.orm import Session

from ..config import UPLOAD_DIR, settings
from ..database import Camera, Event, TemperatureReading, get_db
from ..schemas import CameraOut, EventOut, JobOut, TemperatureOut
from ..services.analytics import AnalyticsEngine
from ..services.job_manager import job_manager
from ..services.temperature import create_demo_reading, seed_demo_history

router = APIRouter(prefix="/api")

ALLOWED_EXTENSIONS = {".mp4", ".avi", ".mov", ".mkv", ".webm"}


@router.get("/health")
def health():
    return {"status": "ok", "service": settings.app_name, "model": settings.yolo_model}


@router.get("/dashboard/summary")
def dashboard_summary(db: Session = Depends(get_db)):
    total = db.query(func.count(Event.id)).scalar() or 0
    high = db.query(func.count(Event.id)).filter(Event.severity == "HIGH").scalar() or 0
    medium = db.query(func.count(Event.id)).filter(Event.severity == "MEDIUM").scalar() or 0
    return {"total_events": total, "high_severity": high, "medium_severity": medium,
            "cameras_online": db.query(func.count(Camera.id)).filter(Camera.status == "ONLINE").scalar() or 0}


@router.get("/events", response_model=list[EventOut])
def events(limit: int = 50, db: Session = Depends(get_db)):
    limit = max(1, min(limit, 500))
    return db.query(Event).order_by(desc(Event.created_at)).limit(limit).all()


@router.get("/cameras", response_model=list[CameraOut])
def cameras(db: Session = Depends(get_db)):
    return db.query(Camera).order_by(Camera.id).all()


@router.post("/cameras/demo", response_model=CameraOut)
def create_demo_camera(db: Session = Depends(get_db)):
    existing = db.query(Camera).filter(Camera.name == "Demo Camera").first()
    if existing:
        return existing
    camera = Camera(name="Demo Camera", source="UPLOAD", status="ONLINE")
    db.add(camera)
    db.commit()
    db.refresh(camera)
    return camera


@router.post("/analyze/upload", response_model=JobOut)
async def analyze_upload(file: UploadFile = File(...)):
    suffix = Path(file.filename or "").suffix.lower()
    if suffix not in ALLOWED_EXTENSIONS:
        raise HTTPException(400, f"Unsupported video type. Use: {', '.join(sorted(ALLOWED_EXTENSIONS))}")

    job_id = uuid.uuid4().hex[:12]
    destination = UPLOAD_DIR / f"{job_id}{suffix}"
    max_bytes = settings.max_upload_mb * 1024 * 1024
    size = 0

    with destination.open("wb") as output:
        while chunk := await file.read(1024 * 1024):
            size += len(chunk)
            if size > max_bytes:
                destination.unlink(missing_ok=True)
                raise HTTPException(413, f"Video exceeds {settings.max_upload_mb} MB limit")
            output.write(chunk)

    job_manager.create(job_id)
    Thread(target=_run_analysis, args=(job_id, destination), daemon=True).start()
    return JobOut(job_id=job_id, status="QUEUED", progress=0, message="Video queued")


def _run_analysis(job_id: str, input_path: Path):
    from ..database import SessionLocal
    job_manager.update(job_id, status="RUNNING", message="Loading YOLO11 model")
    db = SessionLocal()
    try:
        engine = AnalyticsEngine()
        job_manager.update(job_id, message="YOLO11 loaded; analyzing video")
        output_file, count = engine.process_video(
            input_path, job_id, db,
            lambda p, m: job_manager.update(job_id, progress=p, message=m),
        )
        job_manager.update(job_id, status="COMPLETED", progress=100, message="Analysis completed",
                           output_file=output_file, events_created=count)
    except Exception as exc:
        job_manager.update(job_id, status="FAILED", message=str(exc))
    finally:
        db.close()


@router.get("/jobs/{job_id}", response_model=JobOut)
def job_status(job_id: str):
    job = job_manager.get(job_id)
    if not job:
        raise HTTPException(404, "Job not found")
    return job


@router.get("/temperature/current", response_model=TemperatureOut)
def temperature_current(db: Session = Depends(get_db)):
    seed_demo_history(db)
    reading = db.query(TemperatureReading).order_by(desc(TemperatureReading.created_at)).first()
    if not reading:
        reading = create_demo_reading(db)
    return reading


@router.get("/temperature/history", response_model=list[TemperatureOut])
def temperature_history(limit: int = 20, db: Session = Depends(get_db)):
    limit = max(1, min(limit, 100))
    seed_demo_history(db)
    return (db.query(TemperatureReading)
            .order_by(desc(TemperatureReading.created_at))
            .limit(limit).all())


@router.post("/temperature/simulate", response_model=TemperatureOut)
def temperature_simulate(scenario: str = "normal", db: Session = Depends(get_db)):
    if scenario not in {"normal", "alert"}:
        raise HTTPException(400, "scenario must be 'normal' or 'alert'")
    return create_demo_reading(db, scenario)


@router.get("/events/export.csv")
def export_events(db: Session = Depends(get_db)):
    rows = db.query(Event).order_by(desc(Event.created_at)).all()
    stream = io.StringIO()
    writer = csv.writer(stream)
    writer.writerow(["id", "event_type", "severity", "camera", "object", "track_id", "confidence", "timestamp_sec", "message", "created_at"])
    for e in rows:
        writer.writerow([e.id, e.event_type, e.severity, e.camera_name, e.object_class, e.track_id,
                         e.confidence, e.timestamp_sec, e.message, e.created_at.isoformat()])
    stream.seek(0)
    return StreamingResponse(iter([stream.getvalue()]), media_type="text/csv",
                             headers={"Content-Disposition": "attachment; filename=events.csv"})
