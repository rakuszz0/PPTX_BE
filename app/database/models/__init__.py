from sqlalchemy import (
    Column, String, Integer, DateTime, Text, JSON, ForeignKey, BigInteger, Boolean, Enum as SAEnum
)
from sqlalchemy.orm import relationship, Mapped, mapped_column
from datetime import datetime
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
    created_at = Column(DateTime, default=datetime.utcnow)


class Workspace(Base):
    __tablename__ = "workspaces"
    id = Column(String(64), primary_key=True)
    name = Column(String(255), nullable=False)
    owner_id = Column(String(64), ForeignKey("users.id"))
    created_at = Column(DateTime, default=datetime.utcnow)


class Project(Base):
    __tablename__ = "projects"
    id = Column(String(64), primary_key=True)
    name = Column(String(255), nullable=False)
    workspace_id = Column(String(64), ForeignKey("workspaces.id"))
    created_at = Column(DateTime, default=datetime.utcnow)


class Course(Base):
    __tablename__ = "courses"
    id = Column(String(64), primary_key=True)
    title = Column(String(500), nullable=False)
    source_url = Column(String(2048))
    project_id = Column(String(64), ForeignKey("projects.id"))
    raw_content = Column(JSON, nullable=True)
    meta_data = Column("metadata", JSON, nullable=True)
    status = Column(String(64), default="DRAFT")
    created_at = Column(DateTime, default=datetime.utcnow)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)
    modules: Mapped[list["Module"]] = relationship(back_populates="course", cascade="all, delete-orphan")


class Module(Base):
    __tablename__ = "modules"
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
    created_at = Column(DateTime, default=datetime.utcnow)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)
    course: Mapped[Course] = relationship(back_populates="modules")


class Presentation(Base):
    __tablename__ = "presentations"
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
    created_at = Column(DateTime, default=datetime.utcnow)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)


class PresentationVersion(Base):
    __tablename__ = "presentation_versions"
    id = Column(String(64), primary_key=True)
    presentation_id = Column(String(64), ForeignKey("presentations.id"))
    version = Column(Integer, nullable=False)
    document_json = Column(JSON, nullable=True)
    created_at = Column(DateTime, default=datetime.utcnow)


class Slide(Base):
    __tablename__ = "slides"
    id = Column(String(64), primary_key=True)
    presentation_id = Column(String(64), ForeignKey("presentations.id"))
    slide_number = Column(Integer, nullable=False)
    purpose = Column(String(64))
    main_message = Column(Text)
    layout_type = Column(String(64))
    components_json = Column(JSON, nullable=True)
    created_at = Column(DateTime, default=datetime.utcnow)


class Job(Base):
    __tablename__ = "jobs"
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
    created_at = Column(DateTime, default=datetime.utcnow)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)
    completed_at = Column(DateTime, nullable=True)


class Asset(Base):
    __tablename__ = "assets"
    id = Column(String(64), primary_key=True)
    presentation_id = Column(String(64), ForeignKey("presentations.id"))
    module_id = Column(String(64), ForeignKey("modules.id"), nullable=True)
    asset_type = Column(String(64))
    file_path = Column(String(1024))
    mime_type = Column(String(128))
    meta_data = Column("metadata", JSON, nullable=True)
    created_at = Column(DateTime, default=datetime.utcnow)


class QAResult(Base):
    __tablename__ = "qa_results"
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
    created_at = Column(DateTime, default=datetime.utcnow)
