from __future__ import annotations

import csv
import json
import math
from pathlib import Path
from typing import Callable

import cv2
import numpy as np
from sqlalchemy.orm import Session
from ultralytics import YOLO

from ..config import EVENT_DIR, PROCESSED_DIR, settings
from ..database import Event

# COCO labels supported by the standard YOLO11 checkpoints.
TRACKABLE = {"person", "car", "motorcycle", "bus", "truck"}

# Example normalized restricted zone. Replace these points with coordinates from your camera calibration/UI.
DEFAULT_ZONE = [(0.05, 0.60), (0.95, 0.60), (0.95, 0.98), (0.05, 0.98)]


class AnalyticsEngine:
    def __init__(self, model_path: str | None = None):
        self.model = YOLO(model_path or settings.yolo_model)

    @staticmethod
    def _polygon(frame_w: int, frame_h: int, normalized_points=DEFAULT_ZONE):
        return np.array([(int(x * frame_w), int(y * frame_h)) for x, y in normalized_points], np.int32)

    @staticmethod
    def _inside(point: tuple[int, int], polygon: np.ndarray) -> bool:
        return cv2.pointPolygonTest(polygon, point, False) >= 0

    @staticmethod
    def _draw_label(frame, text, x, y):
        cv2.rectangle(frame, (x, max(0, y - 24)), (x + max(110, len(text) * 8), y), (20, 20, 20), -1)
        cv2.putText(frame, text, (x + 5, y - 6), cv2.FONT_HERSHEY_SIMPLEX, 0.55, (255, 255, 255), 1, cv2.LINE_AA)

    def process_video(
        self,
        input_path: Path,
        job_id: str,
        db: Session,
        progress_cb: Callable[[float, str], None],
        camera_name: str = "Upload",
    ) -> tuple[str, int]:
        cap = cv2.VideoCapture(str(input_path))
        if not cap.isOpened():
            raise RuntimeError("Unable to open the uploaded video.")

        width = int(cap.get(cv2.CAP_PROP_FRAME_WIDTH) or 1280)
        height = int(cap.get(cv2.CAP_PROP_FRAME_HEIGHT) or 720)
        fps = float(cap.get(cv2.CAP_PROP_FPS) or 25.0)
        total = int(cap.get(cv2.CAP_PROP_FRAME_COUNT) or 0)
        duration = total / fps if fps else 0

        output_path = PROCESSED_DIR / f"{job_id}_annotated.mp4"
        writer = cv2.VideoWriter(
            str(output_path), cv2.VideoWriter_fourcc(*"mp4v"), fps, (width, height)
        )
        if not writer.isOpened():
            cap.release()
            raise RuntimeError("Unable to create the processed output video.")

        zone = self._polygon(width, height)
        zone_events: set[tuple[int, int]] = set()
        line_y = int(height * 0.60)
        previous_centers: dict[int, tuple[int, int]] = {}
        event_records: list[dict] = []
        frame_index = 0

        try:
            while True:
                ok, frame = cap.read()
                if not ok:
                    break
                frame_index += 1
                timestamp = frame_index / fps if fps else 0

                results = self.model.track(
                    frame,
                    persist=True,
                    conf=settings.confidence_threshold,
                    iou=settings.iou_threshold,
                    verbose=False,
                    tracker="bytetrack.yaml",
                )
                result = results[0]

                cv2.polylines(frame, [zone], True, (0, 180, 255), 2)
                cv2.putText(frame, "RESTRICTED ZONE", (zone[0][0], max(25, zone[0][1] - 10)),
                            cv2.FONT_HERSHEY_SIMPLEX, 0.7, (0, 180, 255), 2, cv2.LINE_AA)
                cv2.line(frame, (0, line_y), (width, line_y), (255, 180, 0), 2)
                cv2.putText(frame, "VIRTUAL LINE", (15, line_y - 10),
                            cv2.FONT_HERSHEY_SIMPLEX, 0.6, (255, 180, 0), 2, cv2.LINE_AA)

                boxes = result.boxes
                if boxes is not None:
                    names = result.names
                    for i in range(len(boxes)):
                        cls_id = int(boxes.cls[i].item())
                        label = str(names.get(cls_id, cls_id))
                        if label not in TRACKABLE:
                            continue
                        conf = float(boxes.conf[i].item())
                        x1, y1, x2, y2 = map(int, boxes.xyxy[i].tolist())
                        cx, cy = (x1 + x2) // 2, (y1 + y2) // 2
                        track_id = int(boxes.id[i].item()) if boxes.id is not None else -1

                        in_zone = self._inside((cx, cy), zone)
                        if in_zone:
                            key = (track_id, int(timestamp))
                            if key not in zone_events:
                                zone_events.add(key)
                                event_records.append(self._event(
                                    "RESTRICTED_ZONE_ENTRY", "HIGH", camera_name, label,
                                    track_id, conf, timestamp,
                                    f"{label.title()} entered the restricted zone."
                                ))

                        if track_id >= 0 and track_id in previous_centers:
                            py = previous_centers[track_id][1]
                            if py < line_y <= cy:
                                event_records.append(self._event(
                                    "LINE_CROSSING", "MEDIUM", camera_name, label,
                                    track_id, conf, timestamp,
                                    f"{label.title()} crossed the virtual monitoring line."
                                ))
                        if track_id >= 0:
                            previous_centers[track_id] = (cx, cy)

                        box_color = (0, 220, 100) if not in_zone else (0, 80, 255)
                        cv2.rectangle(frame, (x1, y1), (x2, y2), box_color, 2)
                        self._draw_label(frame, f"{label} {conf:.2f} ID:{track_id}", x1, max(25, y1))
                        cv2.circle(frame, (cx, cy), 4, box_color, -1)

                # Header telemetry
                cv2.rectangle(frame, (0, 0), (width, 46), (15, 23, 42), -1)
                cv2.putText(frame, f"BORDERVISION AI | {camera_name} | {timestamp:06.1f}s",
                            (14, 30), cv2.FONT_HERSHEY_SIMPLEX, 0.65, (240, 240, 240), 2, cv2.LINE_AA)
                writer.write(frame)

                if frame_index % 10 == 0:
                    progress = (frame_index / total * 100) if total else 0
                    progress_cb(min(progress, 99.0), f"Analyzing frame {frame_index}/{total or '?'}")

        finally:
            cap.release()
            writer.release()

        # Persist events and a machine-readable report.
        for rec in event_records:
            db.add(Event(**rec))
        db.commit()

        report_path = EVENT_DIR / f"{job_id}_events.json"
        report_path.write_text(json.dumps(event_records, indent=2), encoding="utf-8")
        progress_cb(100.0, "Analysis completed")
        return output_path.name, len(event_records)

    @staticmethod
    def _event(event_type, severity, camera_name, object_class, track_id, confidence, timestamp, message):
        return {
            "event_type": event_type,
            "severity": severity,
            "camera_name": camera_name,
            "object_class": object_class,
            "track_id": None if track_id < 0 else track_id,
            "confidence": round(confidence, 4),
            "timestamp_sec": round(timestamp, 2),
            "message": message,
        }
