from typing import List, Optional
from uuid import uuid4
from datetime import UTC, datetime

from fastapi import APIRouter, Depends, status, BackgroundTasks
from sqlalchemy.orm import Session

from app.core.dependencies import get_db
from app.core.errors import NotFoundError, JobStateError
from app.core.config import get_settings
from app.database.models import Job, Module, Course
from app.database.models import JobStatus
from app.schemas import JobCreate, JobResponse

router = APIRouter(prefix="/jobs", tags=["jobs"])


async def _run_job(job_id: str) -> None:
    from app.services.pipeline.pipeline_runner import run_job_pipeline
    try:
        await run_job_pipeline(job_id)
    except Exception as exc:  # pragma: no cover
        print(f"[job:{job_id}] failed: {exc}")


@router.post("", response_model=JobResponse, status_code=status.HTTP_201_CREATED)
async def create_job(
    payload: JobCreate,
    background_tasks: BackgroundTasks,
    db: Session = Depends(get_db),
) -> JobResponse:
    course = db.query(Course).filter(Course.id == payload.course_id).first()
    if not course:
        raise NotFoundError(f"Course {payload.course_id} not found")

    if payload.module_id:
        module = db.query(Module).filter(Module.id == payload.module_id, Module.course_id == payload.course_id).first()
        if not module:
            raise NotFoundError(f"Module {payload.module_id} not found in course")

    job_id = f"job_{uuid4().hex[:12]}"
    job = Job(
        id=job_id,
        course_id=payload.course_id,
        module_id=payload.module_id,
        status=JobStatus.PENDING,
        stage="init",
        progress=0,
        current_slide=0,
        total_slides=0,
        config={
            "max_slides": payload.max_slides,
            "min_slides": payload.min_slides,
            "theme": payload.theme or "medical_professional",
        },
        created_by="dev_user_001",
        created_at=datetime.now(UTC),
        updated_at=datetime.now(UTC),
    )
    db.add(job)
    db.commit()
    db.refresh(job)

    background_tasks.add_task(_run_job, job_id)
    return JobResponse.model_validate(job)


@router.get("", response_model=List[JobResponse])
async def list_jobs(
    status: Optional[str] = None,
    course_id: Optional[str] = None,
    skip: int = 0,
    limit: int = 50,
    db: Session = Depends(get_db),
) -> List[JobResponse]:
    q = db.query(Job)
    if status:
        try:
            q = q.filter(Job.status == JobStatus(status.upper()))
        except ValueError:
            pass
    if course_id:
        q = q.filter(Job.course_id == course_id)
    jobs = q.order_by(Job.created_at.desc()).offset(skip).limit(limit).all()
    return [JobResponse.model_validate(j) for j in jobs]


@router.get("/{job_id}", response_model=JobResponse)
async def get_job(job_id: str, db: Session = Depends(get_db)) -> JobResponse:
    job = db.query(Job).filter(Job.id == job_id).first()
    if not job:
        raise NotFoundError(f"Job {job_id} not found")
    return JobResponse.model_validate(job)


@router.post("/{job_id}/resume", response_model=JobResponse)
async def resume_job(
    job_id: str,
    background_tasks: BackgroundTasks,
    db: Session = Depends(get_db),
) -> JobResponse:
    job = db.query(Job).filter(Job.id == job_id).first()
    if not job:
        raise NotFoundError(f"Job {job_id} not found")
    if job.status not in (JobStatus.FAILED, JobStatus.RETRYING):
        raise JobStateError(f"Cannot resume job in state {job.status}")
    job.status = JobStatus.RETRYING
    job.updated_at = datetime.now(UTC)
    db.commit()
    db.refresh(job)
    background_tasks.add_task(_run_job, job_id)
    return JobResponse.model_validate(job)


@router.post("/{job_id}/retry", response_model=JobResponse)
async def retry_job(
    job_id: str,
    background_tasks: BackgroundTasks,
    db: Session = Depends(get_db),
) -> JobResponse:
    return await resume_job(job_id, background_tasks, db)


@router.post("/{job_id}/cancel", response_model=JobResponse)
async def cancel_job(job_id: str, db: Session = Depends(get_db)) -> JobResponse:
    job = db.query(Job).filter(Job.id == job_id).first()
    if not job:
        raise NotFoundError(f"Job {job_id} not found")
    if job.status in (JobStatus.COMPLETED, JobStatus.FAILED):
        raise JobStateError(f"Cannot cancel job in terminal state {job.status}")
    job.status = JobStatus.FAILED
    job.error_message = "Cancelled by user"
    job.updated_at = datetime.now(UTC)
    job.completed_at = datetime.now(UTC)
    db.commit()
    db.refresh(job)
    return JobResponse.model_validate(job)
