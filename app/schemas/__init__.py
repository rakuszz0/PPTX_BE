from __future__ import annotations
from typing import Any, Dict, List, Optional, Literal
from datetime import UTC, datetime
from enum import Enum
from pydantic import BaseModel, Field, ConfigDict


class ErrorResponse(BaseModel):
    code: str
    message: str
    details: Dict[str, Any] = Field(default_factory=dict)
    request_id: str


class ErrorWrapper(BaseModel):
    error: ErrorResponse


class HealthResponse(BaseModel):
    status: Literal["ok"] = "ok"
    app_env: str
    version: str = "0.1.0"
    timestamp: datetime = Field(default_factory=lambda: datetime.now(UTC))


class CourseCreate(BaseModel):
    source_url: str = Field(..., max_length=2048, description="WIZAPE course URL")
    project_id: Optional[str] = None
    title: Optional[str] = None


class CourseResponse(BaseModel):
    id: str
    title: str
    source_url: Optional[str] = None
    project_id: Optional[str] = None
    status: str
    created_at: datetime
    updated_at: datetime
    model_config = ConfigDict(from_attributes=True)


class CourseDetailResponse(CourseResponse):
    module_count: int = 0


class ModuleResponse(BaseModel):
    id: str
    course_id: str
    module_number: int
    title: str
    summary: Optional[str] = None
    status: str
    source_url: Optional[str] = None
    created_at: datetime
    updated_at: datetime
    model_config = ConfigDict(from_attributes=True)


class ModuleDetailResponse(ModuleResponse):
    word_count: int = 0
    section_count: int = 0


class JobStatusEnum(str, Enum):
    PENDING = "PENDING"
    EXTRACTING = "EXTRACTING"
    ANALYZING = "ANALYZING"
    DESIGNING = "DESIGNING"
    PLANNING = "PLANNING"
    GENERATING_ASSETS = "GENERATING_ASSETS"
    RENDERING = "RENDERING"
    VALIDATING = "VALIDATING"
    QA = "QA"
    COMPLETED = "COMPLETED"
    FAILED = "FAILED"
    RETRYING = "RETRYING"


class JobCreate(BaseModel):
    course_id: str
    module_id: Optional[str] = None
    max_slides: int = Field(default=12, ge=8, le=20)
    min_slides: int = Field(default=10, ge=8, le=20)
    theme: Optional[str] = "medical_professional"


class JobResponse(BaseModel):
    id: str
    course_id: str
    module_id: Optional[str] = None
    status: JobStatusEnum
    stage: Optional[str] = None
    progress: int = 0
    current_slide: int = 0
    total_slides: int = 0
    error_message: Optional[str] = None
    created_at: datetime
    updated_at: datetime
    completed_at: Optional[datetime] = None
    model_config = ConfigDict(from_attributes=True)


class PresentationResponse(BaseModel):
    id: str
    module_id: Optional[str] = None
    course_id: Optional[str] = None
    title: str
    version: int
    qa_score: Optional[int] = None
    status: str
    output_path: Optional[str] = None
    slide_count: int = 0
    created_at: datetime
    updated_at: datetime
    model_config = ConfigDict(from_attributes=True)


class SlideResponse(BaseModel):
    id: str
    presentation_id: str
    slide_number: int
    purpose: Optional[str] = None
    main_message: Optional[str] = None
    layout_type: Optional[str] = None
    component_count: int = 0
    created_at: datetime
    model_config = ConfigDict(from_attributes=True)


class SlideRegenerateRequest(BaseModel):
    reason: Optional[str] = None
    adjust_density: Optional[bool] = False


class SlideAIEditRequest(BaseModel):
    instruction: str = Field(..., min_length=3)


class QAResponse(BaseModel):
    id: str
    presentation_id: str
    overall_score: int
    content_score: Optional[int] = None
    educational_score: Optional[int] = None
    visual_score: Optional[int] = None
    readability_score: Optional[int] = None
    consistency_score: Optional[int] = None
    editability_score: Optional[int] = None
    technical_score: Optional[int] = None
    passed: bool
    issues: List[Dict[str, Any]] = Field(default_factory=list)
    created_at: datetime
    model_config = ConfigDict(from_attributes=True)


class ExportRequest(BaseModel):
    format: Literal["pptx", "pdf", "png"] = "pptx"


class EventType(str, Enum):
    JOB_STARTED = "JOB_STARTED"
    MODULE_STARTED = "MODULE_STARTED"
    STAGE_CHANGED = "STAGE_CHANGED"
    SLIDE_GENERATED = "SLIDE_GENERATED"
    RENDERING_STARTED = "RENDERING_STARTED"
    QA_STARTED = "QA_STARTED"
    QA_COMPLETED = "QA_COMPLETED"
    MODULE_COMPLETED = "MODULE_COMPLETED"
    JOB_COMPLETED = "JOB_COMPLETED"
    JOB_FAILED = "JOB_FAILED"


class JobEvent(BaseModel):
    event: EventType
    job_id: str
    stage: Optional[str] = None
    progress: Optional[int] = None
    message: Optional[str] = None
    timestamp: datetime = Field(default_factory=lambda: datetime.now(UTC))
