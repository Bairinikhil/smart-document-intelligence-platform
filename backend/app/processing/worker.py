from collections.abc import Awaitable, Callable

from app.processing.queue import JobQueue, ProcessingJob


JobHandler = Callable[[ProcessingJob], Awaitable[None]]


class ProcessingWorker:
    def __init__(self, queue: JobQueue, handler: JobHandler, max_attempts: int = 3) -> None:
        self.queue = queue
        self.handler = handler
        self.max_attempts = max_attempts

    async def run_once(self) -> bool:
        job = await self.queue.dequeue()
        if job is None:
            return False
        try:
            await self.handler(job)
        except Exception as exc:  # noqa: BLE001 - worker must classify all handler failures
            await self.queue.reject(
                job,
                reason=type(exc).__name__,
                retry=job.attempt + 1 < self.max_attempts,
            )
        else:
            await self.queue.acknowledge(job)
        return True
