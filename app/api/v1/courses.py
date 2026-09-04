from uuid import uuid4
from datetime import datetime
from typing import List

from fastapi import APIRouter, HTTPException, Depends, status
from sqlalchemy.orm import Session
from sqlalchemy import func

from app.core.dependencies import get_db
from app.core.errors import NotFoundError
from app.core.security import validate_url
from app.database.models import Course, Module
from app.schemas import CourseCreate, CourseResponse, CourseDetailResponse, ModuleResponse

router = APIRouter(prefix="/courses", tags=["courses"])


@router.post("", response_model=CourseResponse, status_code=status.HTTP_201_CREATED)
async def create_course(payload: CourseCreate, db: Session = Depends(get_db)) -> CourseResponse:
    url = validate_url(payload.source_url)
    course_id = f"course_{uuid4().hex[:12]}"
    title = payload.title or "Kepatuhan Regulasi untuk Perangkat Medis"

    course = Course(
        id=course_id,
        title=title,
        source_url=url,
        project_id=payload.project_id,
        status="CREATED",
        created_at=datetime.utcnow(),
        updated_at=datetime.utcnow(),
    )
    db.add(course)
    db.commit()
    db.refresh(course)
    return CourseResponse.model_validate(course)


@router.get("", response_model=List[CourseResponse])
async def list_courses(skip: int = 0, limit: int = 50, db: Session = Depends(get_db)) -> List[CourseResponse]:
    courses = db.query(Course).order_by(Course.created_at.desc()).offset(skip).limit(limit).all()
    return [CourseResponse.model_validate(c) for c in courses]


@router.get("/{course_id}", response_model=CourseDetailResponse)
async def get_course(course_id: str, db: Session = Depends(get_db)) -> CourseDetailResponse:
    course = db.query(Course).filter(Course.id == course_id).first()
    if not course:
        raise NotFoundError(f"Course {course_id} not found")
    module_count = db.query(func.count(Module.id)).filter(Module.course_id == course_id).scalar() or 0
    data = CourseResponse.model_validate(course).model_dump()
    data["module_count"] = module_count
    return CourseDetailResponse(**data)


@router.delete("/{course_id}", status_code=status.HTTP_204_NO_CONTENT)
async def delete_course(course_id: str, db: Session = Depends(get_db)) -> None:
    course = db.query(Course).filter(Course.id == course_id).first()
    if not course:
        raise NotFoundError(f"Course {course_id} not found")
    db.delete(course)
    db.commit()


@router.get("/{course_id}/modules", response_model=List[ModuleResponse])
async def list_course_modules(course_id: str, db: Session = Depends(get_db)) -> List[ModuleResponse]:
    course = db.query(Course).filter(Course.id == course_id).first()
    if not course:
        raise NotFoundError(f"Course {course_id} not found")
    modules = db.query(Module).filter(Module.course_id == course_id).order_by(Module.module_number.asc()).all()
    return [ModuleResponse.model_validate(m) for m in modules]
