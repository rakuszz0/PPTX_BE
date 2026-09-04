from __future__ import annotations
from typing import Any, Dict, Optional, List
from uuid import uuid4
from datetime import datetime
import asyncio
import os
import json
from pathlib import Path

from app.core.config import get_settings
from app.database.session import get_session
from app.core.errors import AppError, NotFoundError, AIServiceError, ExtractionError, RenderingError
from app.core.logging import get_logger
from app.core.security import safe_filename_component

from app.database.models import (
    Course, Module, Presentation, Slide, Job, Asset, QAResult, JobStatus,
)
from app.domain.courses.models import CourseDocument, CourseModule, ContentSection
from app.domain.presentation.models import (
    PresentationDocument, Slide as PresSlide, Component, ComponentType,
    SlidePurpose, SlideLayout, LayoutType, SourceReference, Theme, DesignTokens,
    PresentationSettings, ComponentContent, ComponentStyle, Constraints, Position, Size,
    BulletItem,
)
from app.domain.presentation.ai_pipeline import AIPipelineResult, BlueprintSlide
from app.services.extraction import WizapeExtractor
from app.services.ai.mock_ai import MockAIPipelineRunner
from app.services.design.theme import ThemeSystem as DesignThemeSystem
from app.services.layout.engine import LayoutResolver

logger = get_logger(__name__)


def _now() -> datetime:
    return datetime.utcnow()


def _output_root() -> Path:
    root = Path("output")
    root.mkdir(parents=True, exist_ok=True)
    return root


class JobProgressManager:
    def __init__(self, job_id: str):
        self.job_id = job_id
        self.session = get_session()
        self._update_fields: Dict[str, Any] = {}

    def __enter__(self):
        return self

    def __exit__(self, exc_type, exc_val, exc_tb):
        self.session.close()

    def set_status(self, status: JobStatus, stage: Optional[str] = None, progress: Optional[int] = None,
                   current_slide: Optional[int] = None, total_slides: Optional[int] = None,
                   error: Optional[str] = None, error_details: Optional[Dict[str, Any]] = None,
                   checkpoint: Optional[Dict[str, Any]] = None, completed: bool = False) -> None:
        job = self.session.query(Job).filter(Job.id == self.job_id).first()
        if not job:
            return
        job.status = status
        job.updated_at = _now()
        if stage is not None:
            job.stage = stage
        if progress is not None:
            job.progress = progress
        if current_slide is not None:
            job.current_slide = current_slide
        if total_slides is not None:
            job.total_slides = total_slides
        if error is not None:
            job.error_message = error
        if error_details is not None:
            job.error_details = error_details
        if checkpoint is not None:
            job.checkpoint = checkpoint
        if completed:
            job.completed_at = _now()
        self.session.commit()


async def run_job_pipeline(job_id: str) -> None:
    try:
        with JobProgressManager(job_id) as jpm:
            jpm.set_status(JobStatus.EXTRACTING, stage="extraction", progress=2)
            settings = get_settings()

            job = jpm.session.query(Job).filter(Job.id == job_id).first()
            if not job:
                raise NotFoundError(f"Job {job_id} not found")

            course = jpm.session.query(Course).filter(Course.id == job.course_id).first()
            if not course:
                raise NotFoundError(f"Course {job.course_id} not found")

            jpm.set_status(JobStatus.EXTRACTING, stage="wizape_extract", progress=5)
            source_url = course.source_url or "https://wizape.example/course/medical-regulation"
            try:
                extractor = WizapeExtractor()
                course_doc = extractor.extract(source_url)
            except Exception as exc:
                raise ExtractionError(f"Wizape extraction failed: {exc}")

            jpm.set_status(JobStatus.EXTRACTING, stage="persist_course", progress=10)
            _persist_course_modules(jpm.session, course, course_doc)

            target_module_id = job.module_id
            target_module = None
            if target_module_id:
                target_module = jpm.session.query(Module).filter(Module.id == target_module_id).first()
                if not target_module:
                    raise NotFoundError(f"Module {target_module_id} not found")
            else:
                target_module = jpm.session.query(Module).filter(Module.course_id == course.id).order_by(Module.module_number.asc()).first()
                if not target_module:
                    raise NotFoundError(f"No modules found in course {course.id}")
                job.module_id = target_module.id
                jpm.session.commit()

            jpm.set_status(JobStatus.ANALYZING, stage="ai_mock_pipeline", progress=18)
            max_slides = (job.config or {}).get("max_slides", 12)
            min_slides = (job.config or {}).get("min_slides", 10)
            theme_name = (job.config or {}).get("theme", "medical_professional")

            module_domain = _db_module_to_domain(target_module)

            jpm.set_status(JobStatus.ANALYZING, stage="content_analysis", progress=22)
            ai_runner = MockAIPipelineRunner(theme_name=theme_name)
            ai_result = ai_runner.run(module_domain, min_slides=min_slides, max_slides=max_slides)

            jpm.set_status(JobStatus.DESIGNING, stage="educational_design", progress=30)
            jpm.set_status(JobStatus.PLANNING, stage="story_and_blueprint", progress=42)

            jpm.set_status(JobStatus.DESIGNING, stage="presentation_document", progress=52)
            theme = DesignThemeSystem.get(theme_name)
            pres_doc = _blueprint_to_presentation_document(
                module=module_domain,
                course_title=course.title,
                blueprint=ai_result.blueprint,
                visual_plan=ai_result.visual_plan,
                theme=theme,
                min_slides=min_slides,
                max_slides=max_slides,
            )

            jpm.set_status(JobStatus.DESIGNING, stage="layout_resolution", progress=62)
            resolver = LayoutResolver(theme)
            for slide in pres_doc.slides:
                resolver.layout_slide(slide)

            jpm.set_status(JobStatus.RENDERING, stage="persist_presentation", progress=70,
                           total_slides=pres_doc.slide_count())
            presentation_id = f"pres_{uuid4().hex[:12]}"
            output_dir, pptx_path = _output_paths(course.title, module_domain.module_number, target_module.id)
            output_dir.mkdir(parents=True, exist_ok=True)

            (output_dir / "content.json").write_text(
                json.dumps(module_domain.model_dump(mode="json"), ensure_ascii=False, indent=2), encoding="utf-8"
            )
            (output_dir / "blueprint.json").write_text(
                json.dumps(ai_result.blueprint.model_dump(mode="json"), ensure_ascii=False, indent=2), encoding="utf-8"
            )
            (output_dir / "course.json").write_text(
                json.dumps(course_doc.model_dump(mode="json"), ensure_ascii=False, indent=2), encoding="utf-8"
            )

            pres = Presentation(
                id=presentation_id,
                module_id=target_module.id,
                course_id=course.id,
                title=pres_doc.title,
                version=pres_doc.version,
                document_json=pres_doc.to_dict(),
                blueprint_json=ai_result.blueprint.model_dump(mode="json"),
                qa_score=None,
                output_path=str(pptx_path),
                status="RENDERING",
                created_at=_now(),
                updated_at=_now(),
            )
            jpm.session.add(pres)

            for i, s in enumerate(pres_doc.slides, start=1):
                db_slide = Slide(
                    id=f"slide_{uuid4().hex[:10]}",
                    presentation_id=presentation_id,
                    slide_number=i,
                    purpose=s.purpose if isinstance(s.purpose, str) else s.purpose.value,
                    main_message=s.main_message,
                    layout_type=s.layout.type if isinstance(s.layout.type, str) else s.layout.type.value,
                    components_json=[c.to_dict() for c in s.components],
                    created_at=_now(),
                )
                jpm.session.add(db_slide)
                jpm.set_status(JobStatus.RENDERING, stage=f"persist_slide_{i}", progress=70 + i,
                               current_slide=i, total_slides=pres_doc.slide_count())

            jpm.session.commit()

            jpm.set_status(JobStatus.RENDERING, stage="pptx_render", progress=85)
            try:
                from app.services.rendering.pptx_renderer import PptxRenderer
                renderer = PptxRenderer(theme)
                renderer.render(pres_doc, str(pptx_path))
            except Exception as exc:
                raise RenderingError(f"PPTX rendering failed: {exc}")

            jpm.set_status(JobStatus.VALIDATING, stage="qa_programmatic", progress=90)
            from app.services.qa.engine import QARunner
            qa_runner = QARunner(theme)
            qa = qa_runner.run(pres_doc, str(pptx_path))

            qa_id = f"qa_{uuid4().hex[:12]}"
            db_qa = QAResult(
                id=qa_id,
                presentation_id=presentation_id,
                job_id=job_id,
                overall_score=qa.overall_score,
                content_score=qa.scores.get("content"),
                educational_score=qa.scores.get("educational"),
                visual_score=qa.scores.get("visual_hierarchy"),
                readability_score=qa.scores.get("readability"),
                consistency_score=qa.scores.get("design_consistency"),
                editability_score=qa.scores.get("editability"),
                technical_score=qa.scores.get("technical_validity"),
                checks=qa.checks,
                issues=qa.issues,
                passed=qa.passed,
                created_at=_now(),
            )
            jpm.session.add(db_qa)

            (output_dir / "qa.json").write_text(
                json.dumps({
                    "overall_score": qa.overall_score,
                    "scores": qa.scores,
                    "passed": qa.passed,
                    "issues": qa.issues,
                    "checks": qa.checks,
                }, ensure_ascii=False, indent=2, default=str), encoding="utf-8"
            )

            pres.qa_score = qa.overall_score
            pres.status = "PUBLISHED" if qa.passed else "QA_WARNING"
            pres.updated_at = _now()

            min_score = settings.MIN_QA_SCORE
            if qa.overall_score < min_score:
                job.error_message = f"QA score {qa.overall_score} below minimum {min_score}"
                job.error_details = {"issues": qa.issues[:5]}

            jpm.session.commit()

            jpm.set_status(
                JobStatus.COMPLETED if qa.passed else JobStatus.QA,
                stage="finished",
                progress=100,
                current_slide=pres_doc.slide_count(),
                total_slides=pres_doc.slide_count(),
                checkpoint={"presentation_id": presentation_id, "qa_id": qa_id, "output_path": str(pptx_path)},
                completed=True,
            )
            logger.info("[job:%s] completed with QA=%s", job_id, qa.overall_score)
    except Exception as exc:
        logger.exception("[job:%s] failed", job_id)
        try:
            with JobProgressManager(job_id) as jpm:
                jpm.set_status(
                    JobStatus.FAILED,
                    stage="error",
                    error=str(exc),
                    error_details={"type": type(exc).__name__},
                    completed=True,
                )
        except Exception:
            pass
        raise


def _persist_course_modules(session, course: Course, course_doc: CourseDocument) -> None:
    existing_nums = {m.module_number for m in (course.modules or [])}
    for m in course_doc.modules:
        if m.module_number in existing_nums:
            continue
        mod = Module(
            id=f"mod_{uuid4().hex[:10]}",
            course_id=course.id,
            module_number=m.module_number,
            title=m.title,
            summary=m.summary,
            content={"sections": [s.model_dump(mode="json") for s in m.sections]},
            raw_html=None,
            cleaned_content={"sections": [s.model_dump(mode="json") for s in m.sections]},
            source_url=m.source_url,
            status="EXTRACTED",
            created_at=_now(),
            updated_at=_now(),
        )
        session.add(mod)
    course.status = "EXTRACTED"
    course.updated_at = _now()
    if course.raw_content is None:
        course.raw_content = course_doc.to_dict()
    session.commit()


def _db_module_to_domain(mod: Module) -> CourseModule:
    sections: List[ContentSection] = []
    raw_sections = None
    if mod.cleaned_content and isinstance(mod.cleaned_content, dict):
        raw_sections = mod.cleaned_content.get("sections")
    elif mod.content and isinstance(mod.content, dict):
        raw_sections = mod.content.get("sections")
    if raw_sections and isinstance(raw_sections, list):
        for s in raw_sections:
            try:
                sections.append(ContentSection.model_validate(s))
            except Exception:
                continue
    word_count = sum(len(s.text.split()) for s in sections) or 0
    return CourseModule(
        id=mod.id,
        module_number=mod.module_number,
        title=mod.title,
        summary=mod.summary or "",
        sections=sections,
        source_url=mod.source_url,
        word_count=word_count,
    )


def _output_paths(course_title: str, module_no: int, module_id: str) -> tuple[Path, Path]:
    safe_course = safe_filename_component(course_title)
    dir_path = _output_root() / safe_course / f"module-{module_no:03d}-{module_id[-8:]}"
    pptx_path = dir_path / "presentation.pptx"
    return dir_path, pptx_path


def _blueprint_to_presentation_document(
    module: CourseModule,
    course_title: str,
    blueprint,
    visual_plan,
    theme: Theme,
    min_slides: int = 10,
    max_slides: int = 12,
) -> PresentationDocument:
    tokens = DesignTokens(**theme.design_tokens())

    doc = PresentationDocument(
        id=f"presdoc_{uuid4().hex[:12]}",
        title=f"{module.title} \u2014 {course_title}",
        theme=Theme(
            name=theme.name,
            palette=theme.color_system.to_palette(),
            typography=theme.typography_system.to_dict(),
        ),
        design_tokens=tokens,
        slides=[],
        assets=[],
        settings=PresentationSettings(
            slide_width_in=theme.grid_system.spec.slide_width_in,
            slide_height_in=theme.grid_system.spec.slide_height_in,
            orientation="landscape",
            locale="id_ID",
            footer=f"Kepatuhan Regulasi untuk Perangkat Medis \u2022 Modul {module.module_number}",
            show_page_numbers=True,
            min_slides=min_slides,
            max_slides=max_slides,
        ),
        version=1,
        source_references=[
            SourceReference(
                id="src_module_01", type="module", ref=f"module_{module.module_number:02d}",
                title=module.title, url=module.source_url
            )
        ],
        metadata={"module_id": module.id, "course_title": course_title, "theme": theme.name},
    )

    for i, bp in enumerate(blueprint.slides, start=1):
        slide = _blueprint_slide_to_slide(bp, i)
        doc.add_slide(slide)

    return doc


def _blueprint_slide_to_slide(bp: BlueprintSlide, num: int) -> PresSlide:
    purpose_str = bp.purpose or "CONCEPT"
    layout_str = bp.layout or "ONE_COLUMN"
    try:
        purpose = SlidePurpose(purpose_str)
    except Exception:
        purpose = purpose_str
    try:
        layout_type = LayoutType(layout_str)
    except Exception:
        try:
            layout_type = LayoutType.ONE_COLUMN
        except Exception:
            layout_type = "ONE_COLUMN"
    slide = PresSlide(
        id=f"s_{num:02d}_{uuid4().hex[:8]}",
        purpose=purpose,
        main_message=bp.main_message or "",
        layout=SlideLayout(type=layout_type, grid_columns=12, grid_rows=8),
        components=[],
        speaker_notes=bp.speaker_notes or [],
        source_references=bp.source_references or [],
    )
    for idx, comp_spec in enumerate(bp.components or []):
        comp = _component_from_spec(comp_spec, f"{slide.id}_c{idx}")
        if comp:
            slide.add_component(comp)
    return slide


def _component_from_spec(spec: Dict[str, Any], cid: str) -> Optional[Component]:
    try:
        ct_name = spec.get("type", "PARAGRAPH")
        try:
            ctype = ComponentType(ct_name)
        except Exception:
            ctype = ComponentType.PARAGRAPH
        content = ComponentContent()
        for k, v in (spec.get("content") or {}).items():
            if hasattr(content, k):
                if k == "items" and isinstance(v, list):
                    items = []
                    for it in v:
                        sub_items = []
                        for si in (it.get("sub_items") or []):
                            sub_items.append(BulletItem(text=si.get("text", ""), level=si.get("level", 0) + 1,
                                                        bold=si.get("bold")))
                        items.append(BulletItem(
                            text=it.get("text", ""),
                            level=it.get("level", 0),
                            bold=it.get("bold"),
                            sub_items=sub_items,
                        ))
                    content.items = items
                else:
                    try:
                        setattr(content, k, v)
                    except Exception:
                        pass
        style = ComponentStyle(variant=spec.get("variant"))
        constraints = Constraints(area=spec.get("area"))
        return Component(
            id=cid,
            type=ctype,
            content=content,
            style=style,
            constraints=constraints,
            position=Position(),
            size=Size(width=0, height=0),
        )
    except Exception as exc:
        logger.warning("skip malformed component %s: %s", cid, exc)
        return None
