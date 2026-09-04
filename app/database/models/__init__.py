from sqlalchemy import (
    Column, String, Integer, DateTime, Text, JSON, ForeignKey, BigInteger,
    Boolean, Enum as SAEnum, Index,
)
from sqlalchemy.orm import relationship, Mapped, mapped_column
from datetime import UTC, datetime
from typing import Optional
import enum

from app.core.dependencies import Base


class JobStatus(str, enum.Enum):
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


class User(Base):
    __tablename__ = "users"
    id = Column(String(64), primary_key=True)
    email = Column(String(255), unique=True, nullable=False)
    created_at = Column(DateTime(timezone=True), default=lambda: datetime.now(UTC))


class Workspace(Base):
    __tablename__ = "workspaces"
    id = Column(String(64), primary_key=True)
    name = Column(String(255), nullable=False)
    owner_id = Column(String(64), ForeignKey("users.id"))
    created_at = Column(DateTime(timezone=True), default=lambda: datetime.now(UTC))


class Project(Base):
    __tablename__ = "projects"
    id = Column(String(64), primary_key=True)
    name = Column(String(255), nullable=False)
    workspace_id = Column(String(64), ForeignKey("workspaces.id"))
    created_at = Column(DateTime(timezone=True), default=lambda: datetime.now(UTC))


class Course(Base):
    __tablename__ = "courses"
    id = Column(String(64), primary_key=True)
    title = Column(String(500), nullable=False)
    source_url = Column(String(2048))
    project_id = Column(String(64), ForeignKey("projects.id"))
    raw_content = Column(JSON, nullable=True)
    meta_data = Column("metadata", JSON, nullable=True)
    status = Column(String(64), default="DRAFT")
    created_at = Column(DateTime(timezone=True), default=lambda: datetime.now(UTC))
    updated_at = Column(DateTime(timezone=True), default=lambda: datetime.now(UTC), onupdate=lambda: datetime.now(UTC))
    modules: Mapped[list["Module"]] = relationship(back_populates="course", cascade="all, delete-orphan")


class Module(Base):
    __tablename__ = "modules"
    __table_args__ = (
        Index("uq_modules_course_number", "course_id", "module_number", unique=True),
        Index("ix_modules_course_number", "course_id", "module_number"),
    )
    id = Column(String(64), primary_key=True)
    course_id = Column(String(64), ForeignKey("courses.id"), nullable=False)
    module_number = Column(Integer, nullable=False)
    title = Column(String(500), nullable=False)
    summary = Column(Text, nullable=True)
    content = Column(JSON, nullable=True)
    raw_html = Column(Text, nullable=True)
    cleaned_content = Column(JSON, nullable=True)
    source_url = Column(String(2048))
    status = Column(String(64), default="PENDING")
    created_at = Column(DateTime(timezone=True), default=lambda: datetime.now(UTC))
    updated_at = Column(DateTime(timezone=True), default=lambda: datetime.now(UTC), onupdate=lambda: datetime.now(UTC))
    course: Mapped[Course] = relationship(back_populates="modules")


class Presentation(Base):
    __tablename__ = "presentations"
    __table_args__ = (
        Index("ix_presentations_course_created", "course_id", "created_at"),
        Index("ix_presentations_module_created", "module_id", "created_at"),
    )
    id = Column(String(64), primary_key=True)
    module_id = Column(String(64), ForeignKey("modules.id"))
    course_id = Column(String(64), ForeignKey("courses.id"))
    title = Column(String(500), nullable=False)
    version = Column(Integer, default=1)
    document_json = Column(JSON, nullable=True)
    blueprint_json = Column(JSON, nullable=True)
    qa_score = Column(Integer, nullable=True)
    output_path = Column(String(1024))
    status = Column(String(64), default="DRAFT")
    created_at = Column(DateTime(timezone=True), default=lambda: datetime.now(UTC))
    updated_at = Column(DateTime(timezone=True), default=lambda: datetime.now(UTC), onupdate=lambda: datetime.now(UTC))


class PresentationVersion(Base):
    __tablename__ = "presentation_versions"
    __table_args__ = (
        Index("uq_presentation_versions_version", "presentation_id", "version", unique=True),
    )
    id = Column(String(64), primary_key=True)
    presentation_id = Column(String(64), ForeignKey("presentations.id"))
    version = Column(Integer, nullable=False)
    document_json = Column(JSON, nullable=True)
    created_at = Column(DateTime(timezone=True), default=lambda: datetime.now(UTC))


class Slide(Base):
    __tablename__ = "slides"
    __table_args__ = (
        Index("uq_slides_presentation_number", "presentation_id", "slide_number", unique=True),
        Index("ix_slides_presentation_number", "presentation_id", "slide_number"),
    )
    id = Column(String(64), primary_key=True)
    presentation_id = Column(String(64), ForeignKey("presentations.id"))
    slide_number = Column(Integer, nullable=False)
    purpose = Column(String(64))
    main_message = Column(Text)
    layout_type = Column(String(64))
    components_json = Column(JSON, nullable=True)
    created_at = Column(DateTime(timezone=True), default=lambda: datetime.now(UTC))


class Job(Base):
    __tablename__ = "jobs"
    __table_args__ = (
        Index("ix_jobs_course_created", "course_id", "created_at"),
        Index("ix_jobs_status_created", "status", "created_at"),
    )
    id = Column(String(64), primary_key=True)
    course_id = Column(String(64), ForeignKey("courses.id"))
    module_id = Column(String(64), ForeignKey("modules.id"), nullable=True)
    status = Column(SAEnum(JobStatus), default=JobStatus.PENDING, nullable=False)
    stage = Column(String(64))
    progress = Column(Integer, default=0)
    current_slide = Column(Integer, default=0)
    total_slides = Column(Integer, default=0)
    error_message = Column(Text, nullable=True)
    error_details = Column(JSON, nullable=True)
    config = Column(JSON, nullable=True)
    checkpoint = Column(JSON, nullable=True)
    created_by = Column(String(64))
    created_at = Column(DateTime(timezone=True), default=lambda: datetime.now(UTC))
    updated_at = Column(DateTime(timezone=True), default=lambda: datetime.now(UTC), onupdate=lambda: datetime.now(UTC))
    completed_at = Column(DateTime(timezone=True), nullable=True)


class Asset(Base):
    __tablename__ = "assets"
    __table_args__ = (
        Index("ix_assets_presentation", "presentation_id"),
        Index("ix_assets_module", "module_id"),
    )
    id = Column(String(64), primary_key=True)
    presentation_id = Column(String(64), ForeignKey("presentations.id"))
    module_id = Column(String(64), ForeignKey("modules.id"), nullable=True)
    asset_type = Column(String(64))
    file_path = Column(String(1024))
    mime_type = Column(String(128))
    meta_data = Column("metadata", JSON, nullable=True)
    created_at = Column(DateTime(timezone=True), default=lambda: datetime.now(UTC))


class QAResult(Base):
    __tablename__ = "qa_results"
    __table_args__ = (
        Index("ix_qa_results_presentation_created", "presentation_id", "created_at"),
        Index("ix_qa_results_job", "job_id"),
    )
    id = Column(String(64), primary_key=True)
    presentation_id = Column(String(64), ForeignKey("presentations.id"))
    job_id = Column(String(64), ForeignKey("jobs.id"), nullable=True)
    overall_score = Column(Integer, nullable=False)
    content_score = Column(Integer)
    educational_score = Column(Integer)
    visual_score = Column(Integer)
    readability_score = Column(Integer)
    consistency_score = Column(Integer)
    editability_score = Column(Integer)
    technical_score = Column(Integer)
    checks = Column(JSON, nullable=True)
    issues = Column(JSON, nullable=True)
    passed = Column(Boolean, default=False)
    created_at = Column(DateTime(timezone=True), default=lambda: datetime.now(UTC))
