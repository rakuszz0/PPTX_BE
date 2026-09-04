from typing import List
from fastapi import APIRouter, Depends
from sqlalchemy.orm import Session
from sqlalchemy import func

from app.core.dependencies import get_db
from app.core.errors import NotFoundError
from app.database.models import Presentation, Slide
from app.schemas import PresentationResponse, SlideResponse, ExportRequest

router = APIRouter(prefix="/presentations", tags=["presentations"])


@router.get("/{presentation_id}", response_model=PresentationResponse)
async def get_presentation(presentation_id: str, db: Session = Depends(get_db)) -> PresentationResponse:
    pres = db.query(Presentation).filter(Presentation.id == presentation_id).first()
    if not pres:
        raise NotFoundError(f"Presentation {presentation_id} not found")
    base = PresentationResponse.model_validate(pres).model_dump()
    slide_count = db.query(func.count(Slide.id)).filter(Slide.presentation_id == presentation_id).scalar() or 0
    base["slide_count"] = slide_count
    return PresentationResponse(**base)


@router.put("/{presentation_id}", response_model=PresentationResponse)
async def update_presentation(presentation_id: str, db: Session = Depends(get_db)) -> PresentationResponse:
    pres = db.query(Presentation).filter(Presentation.id == presentation_id).first()
    if not pres:
        raise NotFoundError(f"Presentation {presentation_id} not found")
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
    from fastapi.responses import FileResponse
    import os
    pres = db.query(Presentation).filter(Presentation.id == presentation_id).first()
    if not pres or not pres.output_path or not os.path.exists(pres.output_path):
        raise NotFoundError("Presentation output not found")
    filename = os.path.basename(pres.output_path)
    return FileResponse(pres.output_path, media_type="application/vnd.openxmlformats-officedocument.presentationml.presentation", filename=filename)


@router.post("/{presentation_id}/export")
async def export_presentation_post(presentation_id: str, payload: ExportRequest, db: Session = Depends(get_db)):
    return await export_presentation_get(presentation_id, db)
