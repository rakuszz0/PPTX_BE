from typing import List
from fastapi import APIRouter, Depends
from sqlalchemy.orm import Session

from app.core.dependencies import get_db
from app.core.errors import NotFoundError
from app.database.models import Module
from app.schemas import ModuleResponse, ModuleDetailResponse

router = APIRouter(prefix="/modules", tags=["modules"])


@router.get("/{module_id}", response_model=ModuleDetailResponse)
async def get_module(module_id: str, db: Session = Depends(get_db)) -> ModuleDetailResponse:
    module = db.query(Module).filter(Module.id == module_id).first()
    if not module:
        raise NotFoundError(f"Module {module_id} not found")
    base = ModuleResponse.model_validate(module).model_dump()
    word_count = 0
    section_count = 0
    if module.cleaned_content and isinstance(module.cleaned_content, dict):
        sections = module.cleaned_content.get("sections") or []
        section_count = len(sections)
        for s in sections:
            if isinstance(s, dict):
                text = s.get("text") or ""
                word_count += len(text.split())
    base["word_count"] = word_count
    base["section_count"] = section_count
    return ModuleDetailResponse(**base)
