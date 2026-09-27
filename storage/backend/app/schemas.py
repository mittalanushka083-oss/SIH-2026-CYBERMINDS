from datetime import datetime
from pydantic import BaseModel, ConfigDict


class EventOut(BaseModel):
    model_config = ConfigDict(from_attributes=True)
    id: int
    event_type: str
    severity: str
    camera_name: str
    object_class: str | None
    track_id: int | None
    confidence: float | None
    timestamp_sec: float | None
    message: str
    created_at: datetime


class JobOut(BaseModel):
    job_id: str
    status: str
    progress: float
    message: str
    output_file: str | None = None
    events_created: int = 0


class CameraOut(BaseModel):
    model_config = ConfigDict(from_attributes=True)
    id: int
    name: str
    source: str
    status: str


class TemperatureOut(BaseModel):
    model_config = ConfigDict(from_attributes=True)
    id: int
    sensor_mode: str
    human_reference_c: float | None
    ambient_c: float | None
    surface_c: float | None
    camera_c: float | None
    human_status: str
    created_at: datetime
