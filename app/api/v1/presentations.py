import re
import unicodedata
from pathlib import Path
from typing import List
from datetime import UTC, datetime
from uuid import uuid4

from fastapi import APIRouter, Depends
from fastapi.responses import FileResponse
from sqlalchemy.orm import Session
from sqlalchemy import func

from app.core.dependencies import get_db
from app.core.errors import NotFoundError, RenderingError
from app.database.models import Presentation, PresentationVersion, Slide
from app.schemas import (
    PresentationResponse, PresentationDocumentResponse, PresentationUpdateRequest,
    SlideResponse, ExportRequest,
)
from app.domain.presentation.models import PresentationDocument
from app.services.design.theme import ThemeSystem
from app.services.rendering.pptx_renderer import PptxRenderer

router = APIRouter(prefix="/presentations", tags=["presentations"])

PPTX_MEDIA_TYPE = "application/vnd.openxmlformats-officedocument.presentationml.presentation"


def _download_filename(title: str, presentation_id: str) -> str:
    """Return a safe, recognizable filename for the downloaded PPTX."""
    ascii_title = unicodedata.normalize("NFKD", title).encode("ascii", "ignore").decode()
    stem = re.sub(r"[^A-Za-z0-9]+", "-", ascii_title).strip("-").lower()
    return f"{(stem or presentation_id)[:100]}.pptx"


def _presentation_file_path(output_path: str) -> Path:
    """Only serve generated files stored inside the configured output folder."""
    output_root = Path("output").resolve()
    file_path = Path(output_path).resolve()
    if output_root not in file_path.parents or file_path.suffix.lower() != ".pptx":
        raise NotFoundError("Presentation output not found")
    if not file_path.is_file():
        raise NotFoundError("Presentation output not found")
    return file_path


def _presentation_output_path(output_path: str) -> Path:
    output_root = Path("output").resolve()
    file_path = Path(output_path).resolve()
    if output_root not in file_path.parents or file_path.suffix.lower() != ".pptx":
        raise RenderingError("Presentation output path is invalid")
    return file_path


def _replace_presentation_slides(db: Session, presentation: Presentation, document: PresentationDocument) -> None:
    db.query(Slide).filter(Slide.presentation_id == presentation.id).delete(synchronize_session=False)
    for number, slide in enumerate(document.slides, start=1):
        db.add(Slide(
            id=f"slide_{uuid4().hex[:10]}", presentation_id=presentation.id,
            slide_number=number,
            purpose=slide.purpose.value if hasattr(slide.purpose, "value") else str(slide.purpose),
            main_message=slide.main_message,
            layout_type=slide.layout.type.value if hasattr(slide.layout.type, "value") else str(slide.layout.type),
            components_json=[component.to_dict() for component in slide.components],
            created_at=datetime.now(UTC),
        ))


@router.get("", response_model=List[PresentationResponse])
async def list_presentations(skip: int = 0, limit: int = 50, db: Session = Depends(get_db)) -> List[PresentationResponse]:
    slide_counts = (
        db.query(Slide.presentation_id, func.count(Slide.id).label("slide_count"))
        .group_by(Slide.presentation_id)
        .subquery()
    )
    records = (
        db.query(Presentation, func.coalesce(slide_counts.c.slide_count, 0))
        .outerjoin(slide_counts, Presentation.id == slide_counts.c.presentation_id)
        .order_by(Presentation.created_at.desc())
        .offset(skip)
        .limit(limit)
        .all()
    )
    result = []
    for presentation, slide_count in records:
        data = PresentationResponse.model_validate(presentation).model_dump()
        data["slide_count"] = slide_count
        result.append(PresentationResponse(**data))
    return result


@router.get("/{presentation_id}", response_model=PresentationResponse)
async def get_presentation(presentation_id: str, db: Session = Depends(get_db)) -> PresentationResponse:
    pres = db.query(Presentation).filter(Presentation.id == presentation_id).first()
    if not pres:
        raise NotFoundError(f"Presentation {presentation_id} not found")
    base = PresentationResponse.model_validate(pres).model_dump()
    slide_count = db.query(func.count(Slide.id)).filter(Slide.presentation_id == presentation_id).scalar() or 0
    base["slide_count"] = slide_count
    return PresentationResponse(**base)


@router.get("/{presentation_id}/document", response_model=PresentationDocumentResponse)
async def get_presentation_document(presentation_id: str, db: Session = Depends(get_db)) -> PresentationDocumentResponse:
    pres = db.query(Presentation).filter(Presentation.id == presentation_id).first()
    if not pres or not pres.document_json:
        raise NotFoundError(f"Presentation {presentation_id} not found")
    data = PresentationResponse.model_validate(pres).model_dump()
    data["document_json"] = pres.document_json
    return PresentationDocumentResponse(**data)


@router.put("/{presentation_id}", response_model=PresentationResponse)
async def update_presentation(
    presentation_id: str, payload: PresentationUpdateRequest, db: Session = Depends(get_db)
) -> PresentationResponse:
    pres = db.query(Presentation).filter(Presentation.id == presentation_id).first()
    if not pres:
        raise NotFoundError(f"Presentation {presentation_id} not found")
    try:
        document = PresentationDocument.from_dict(payload.document_json)
    except Exception as exc:
        raise RenderingError(f"Presentation document is invalid: {exc}") from exc
    document.id = pres.id
    document.version = (pres.version or 1) + 1
    if payload.title:
        document.title = payload.title
    pres.version = document.version
    pres.title = document.title
    pres.document_json = document.to_dict()
    pres.status = "DRAFT"
    pres.updated_at = datetime.now(UTC)
    db.add(PresentationVersion(
        id=f"presver_{uuid4().hex[:12]}", presentation_id=pres.id,
        version=pres.version, document_json=pres.document_json, created_at=datetime.now(UTC),
    ))
    _replace_presentation_slides(db, pres, document)
    db.commit()
    db.refresh(pres)
    return PresentationResponse.model_validate(pres)


@router.post("/{presentation_id}/rerender", response_model=PresentationResponse)
async def rerender_presentation(presentation_id: str, db: Session = Depends(get_db)) -> PresentationResponse:
    pres = db.query(Presentation).filter(Presentation.id == presentation_id).first()
    if not pres or not pres.document_json or not pres.output_path:
        raise NotFoundError(f"Presentation {presentation_id} not found")
    try:
        document = PresentationDocument.from_dict(pres.document_json)
        destination = _presentation_output_path(pres.output_path)
        destination.parent.mkdir(parents=True, exist_ok=True)
        temporary = destination.with_suffix(".tmp.pptx")
        theme = ThemeSystem.get(document.theme.name)
        if not theme:
            raise RenderingError(f"Unknown presentation theme: {document.theme.name}")
        PptxRenderer(theme).render(document, str(temporary))
        temporary.replace(destination)
    except RenderingError:
        raise
    except Exception as exc:
        raise RenderingError(f"Unable to render presentation: {exc}") from exc
    pres.status = "PUBLISHED"
    pres.updated_at = datetime.now(UTC)
    db.commit()
    db.refresh(pres)
    return PresentationResponse.model_validate(pres)


@router.get("/{presentation_id}/slides", response_model=List[SlideResponse])
async def list_presentation_slides(presentation_id: str, db: Session = Depends(get_db)) -> List[SlideResponse]:
    pres = db.query(Presentation).filter(Presentation.id == presentation_id).first()
    if not pres:
        raise NotFoundError(f"Presentation {presentation_id} not found")
    slides = db.query(Slide).filter(Slide.presentation_id == presentation_id).order_by(Slide.slide_number.asc()).all()
    result = []
    for s in slides:
        data = SlideResponse.model_validate(s).model_dump()
        comps = s.components_json or []
        if isinstance(comps, list):
            data["component_count"] = len(comps)
        result.append(SlideResponse(**data))
    return result


@router.get("/{presentation_id}/export")
async def export_presentation_get(presentation_id: str, db: Session = Depends(get_db)):
    pres = db.query(Presentation).filter(Presentation.id == presentation_id).first()
    if not pres or not pres.output_path:
        raise NotFoundError("Presentation output not found")
    file_path = _presentation_file_path(pres.output_path)
    return FileResponse(
        file_path,
        media_type=PPTX_MEDIA_TYPE,
        filename=_download_filename(pres.title, pres.id),
    )


@router.post("/{presentation_id}/export")
async def export_presentation_post(presentation_id: str, payload: ExportRequest, db: Session = Depends(get_db)):
    return await export_presentation_get(presentation_id, db)
