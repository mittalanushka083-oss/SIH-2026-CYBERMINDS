from dataclasses import dataclass, field
from threading import Lock


@dataclass
class Job:
    job_id: str
    status: str = "QUEUED"
    progress: float = 0.0
    message: str = "Queued"
    output_file: str | None = None
    events_created: int = 0


class JobManager:
    def __init__(self):
        self.jobs: dict[str, Job] = {}
        self.lock = Lock()

    def create(self, job_id: str) -> Job:
        with self.lock:
            job = Job(job_id)
            self.jobs[job_id] = job
            return job

    def update(self, job_id: str, **kwargs):
        with self.lock:
            job = self.jobs[job_id]
            for key, value in kwargs.items():
                setattr(job, key, value)
            return job

    def get(self, job_id: str) -> Job | None:
        with self.lock:
            return self.jobs.get(job_id)


job_manager = JobManager()
