from __future__ import annotations

from datetime import datetime, timedelta
from random import uniform

from sqlalchemy.orm import Session

from ..database import TemperatureReading


# These are demonstration thresholds, not medical diagnostic limits.
HUMAN_MIN_C = 36.1
HUMAN_MAX_C = 37.2
HUMAN_ALERT_C = 37.5
AMBIENT_MIN_C = 0.0
AMBIENT_MAX_C = 55.0
SURFACE_MAX_C = 70.0
CAMERA_MAX_C = 75.0


def classify_human_reference(value: float) -> str:
    if value < HUMAN_MIN_C:
        return "BELOW_REFERENCE"
    if value <= HUMAN_MAX_C:
        return "NORMAL_REFERENCE"
    if value < HUMAN_ALERT_C:
        return "ABOVE_REFERENCE"
    return "TEMPERATURE_ALERT"


def create_demo_reading(db: Session, scenario: str = "normal") -> TemperatureReading:
    """Create clearly simulated telemetry for the SIH dashboard demo."""
    scenario = scenario.lower().strip()
    if scenario == "alert":
        human = round(uniform(37.6, 38.4), 1)
        ambient = round(uniform(27.0, 34.0), 1)
        surface = round(uniform(35.0, 43.0), 1)
        camera = round(uniform(42.0, 52.0), 1)
    else:
        human = round(uniform(36.4, 37.1), 1)
        ambient = round(uniform(22.0, 31.0), 1)
        surface = round(uniform(26.0, 36.0), 1)
        camera = round(uniform(35.0, 45.0), 1)

    reading = TemperatureReading(
        sensor_mode="SIMULATION",
        human_reference_c=human,
        ambient_c=ambient,
        surface_c=surface,
        camera_c=camera,
        human_status=classify_human_reference(human),
        created_at=datetime.utcnow(),
    )
    db.add(reading)
    db.commit()
    db.refresh(reading)
    return reading


def seed_demo_history(db: Session, count: int = 12) -> None:
    if db.query(TemperatureReading).count() > 0:
        return

    now = datetime.utcnow()
    for index in range(count, 0, -1):
        reading = TemperatureReading(
            sensor_mode="SIMULATION",
            human_reference_c=round(uniform(36.4, 37.1), 1),
            ambient_c=round(uniform(23.0, 30.0), 1),
            surface_c=round(uniform(27.0, 35.0), 1),
            camera_c=round(uniform(36.0, 44.0), 1),
            human_status="NORMAL_REFERENCE",
            created_at=now - timedelta(minutes=index * 2),
        )
        db.add(reading)
    db.commit()
