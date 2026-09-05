# Catatan: Endpoint di file ini saat ini STUB / belum diimplementasikan secara nyata.
# Editor front-end mengubah slide via PUT /presentations/{presentation_id} yang
# menyimpan full document_json dan menimpa keseluruhan rows di tabel slides,
# bukan endpoint per-slide di bawah ini. Lihat app/api/v1/presentations.py:update_presentation.

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
    # TODO(regenerate-slide): Implementasikan regenerasi per-slide (AI rewrite,
    # adjust density, refresh layout) lalu persist components_json baru. Saat
    # ini hanya mengembalikan slide yang sudah ada tanpa modifikasi.
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
    # TODO(ai-edit-slide): Implementasikan AI edit berdasarkan `instruction`
    # (misal: ubah nada bahasa, ringkas, perbaiki ejaan, tambah poin, dll.),
    # lalu update components_json slide ini. Saat ini hanya mengembalikan
    # slide yang sudah ada tanpa menerapkan instruction apapun.
    slide = db.query(Slide).filter(Slide.id == slide_id).first()
    if not slide:
        raise NotFoundError(f"Slide {slide_id} not found")
    return SlideResponse.model_validate(slide)
