import asyncio

from app.processing.queue import InMemoryJobQueue, ProcessingJob
from app.processing.state import PIPELINE_STAGES, stage_idempotency_key
from app.processing.worker import ProcessingWorker


def test_queue_retries_then_dead_letters_a_failed_job() -> None:
    async def scenario() -> None:
        queue = InMemoryJobQueue()
        job = ProcessingJob(job_id="job-1", event_type="document.uploaded", payload={})
        await queue.enqueue(job)
        first_attempt = await queue.dequeue()
        assert first_attempt is not None
        await queue.reject(first_attempt, "OCRTimeout", retry=True)
        retried = await queue.dequeue()
        assert retried is not None
        assert retried.attempt == 1
        await queue.reject(retried, "OCRTimeout", retry=False)
        assert len(queue.dead_letters) == 1

    asyncio.run(scenario())


def test_worker_acknowledges_successful_jobs() -> None:
    async def scenario() -> None:
        queue = InMemoryJobQueue()
        handled: list[str] = []

        async def handler(job: ProcessingJob) -> None:
            handled.append(job.job_id)

        await queue.enqueue(ProcessingJob("job-1", "event", {}))
        worker = ProcessingWorker(queue, handler)
        assert await worker.run_once()
        assert handled == ["job-1"]
        assert await queue.dequeue() is None

    asyncio.run(scenario())


def test_worker_retries_failures_until_the_attempt_budget() -> None:
    async def scenario() -> None:
        queue = InMemoryJobQueue()

        async def handler(job: ProcessingJob) -> None:
            raise TimeoutError("provider timeout")

        await queue.enqueue(ProcessingJob("job-1", "event", {}))
        worker = ProcessingWorker(queue, handler, max_attempts=2)
        assert await worker.run_once()
        assert await worker.run_once()
        assert len(queue.dead_letters) == 1

    asyncio.run(scenario())


def test_pipeline_order_and_stage_key_are_stable() -> None:
    assert PIPELINE_STAGES == ("preprocess", "ocr", "classify", "extract", "validate")
    key = stage_idempotency_key("version-1", "ocr", "v1")
    assert key == "version-1:ocr:v1"
