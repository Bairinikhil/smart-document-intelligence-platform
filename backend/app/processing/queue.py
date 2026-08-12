import json
from collections import deque
from dataclasses import asdict, dataclass
from typing import Any, Protocol


@dataclass(frozen=True)
class ProcessingJob:
    job_id: str
    event_type: str
    payload: dict[str, Any]
    attempt: int = 0

    def as_json(self) -> str:
        return json.dumps(asdict(self), separators=(",", ":"))

    @classmethod
    def from_json(cls, value: str) -> "ProcessingJob":
        return cls(**json.loads(value))


class JobQueue(Protocol):
    async def enqueue(self, job: ProcessingJob) -> None: ...

    async def dequeue(self) -> ProcessingJob | None: ...

    async def acknowledge(self, job: ProcessingJob) -> None: ...

    async def reject(self, job: ProcessingJob, reason: str, *, retry: bool) -> None: ...


class InMemoryJobQueue:
    """Local deterministic queue used by tests and development."""

    def __init__(self) -> None:
        self._jobs: deque[ProcessingJob] = deque()
        self.dead_letters: list[tuple[ProcessingJob, str]] = []

    async def enqueue(self, job: ProcessingJob) -> None:
        self._jobs.append(job)

    async def dequeue(self) -> ProcessingJob | None:
        return self._jobs.popleft() if self._jobs else None

    async def acknowledge(self, job: ProcessingJob) -> None:
        del job

    async def reject(self, job: ProcessingJob, reason: str, *, retry: bool) -> None:
        if retry:
            await self.enqueue(
                ProcessingJob(
                    job_id=job.job_id,
                    event_type=job.event_type,
                    payload=job.payload,
                    attempt=job.attempt + 1,
                )
            )
        else:
            self.dead_letters.append((job, reason))


class RedisJobQueue:
    """Redis list adapter; the Redis client is injected by deployment wiring."""

    def __init__(
        self,
        client: Any,
        queue_name: str = "sdi:processing",
        dead_letter_name: str = "sdi:dead-letter",
    ) -> None:
        self.client = client
        self.queue_name = queue_name
        self.dead_letter_name = dead_letter_name

    async def enqueue(self, job: ProcessingJob) -> None:
        await self.client.rpush(self.queue_name, job.as_json())

    async def dequeue(self) -> ProcessingJob | None:
        result = await self.client.blpop(self.queue_name, timeout=1)
        if result is None:
            return None
        _, raw_job = result
        if isinstance(raw_job, bytes):
            raw_job = raw_job.decode("utf-8")
        return ProcessingJob.from_json(raw_job)

    async def acknowledge(self, job: ProcessingJob) -> None:
        del job

    async def reject(self, job: ProcessingJob, reason: str, *, retry: bool) -> None:
        if retry:
            await self.enqueue(
                ProcessingJob(job.job_id, job.event_type, job.payload, job.attempt + 1)
            )
        else:
            await self.client.rpush(
                self.dead_letter_name,
                json.dumps({"job": asdict(job), "reason": reason}, separators=(",", ":")),
            )
