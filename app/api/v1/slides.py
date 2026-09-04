from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session

from app.core.dependencies import get_db
from app.core.errors import NotFoundError
from app.database.models import Slide
from app.schemas import SlideRegenerateRequest, SlideAIEditRequest, SlideResponse

router = APIRouter(prefix="/slides", tags=["slides"])


@router.post("/{slide_id}/regenerate", response_model=SlideResponse)
async def regenerate_slide(
    slide_id: str,
    payload: SlideRegenerateRequest,
    db: Session = Depends(get_db),
) -> SlideResponse:
    slide = db.query(Slide).filter(Slide.id == slide_id).first()
    if not slide:
        raise NotFoundError(f"Slide {slide_id} not found")
    return SlideResponse.model_validate(slide)


@router.post("/{slide_id}/ai-edit", response_model=SlideResponse)
async def ai_edit_slide(
    slide_id: str,
    payload: SlideAIEditRequest,
    db: Session = Depends(get_db),
) -> SlideResponse:
    slide = db.query(Slide).filter(Slide.id == slide_id).first()
    if not slide:
        raise NotFoundError(f"Slide {slide_id} not found")
    return SlideResponse.model_validate(slide)
