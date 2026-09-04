from fastapi import APIRouter, Depends
from sqlalchemy.orm import Session

from app.core.dependencies import get_db
from app.core.errors import NotFoundError
from app.database.models import QAResult
from app.schemas import QAResponse
from typing import List

router = APIRouter(prefix="/qa", tags=["qa"])


@router.get("/{presentation_id}", response_model=List[QAResponse])
async def get_qa_results(presentation_id: str, db: Session = Depends(get_db)) -> List[QAResponse]:
    results = (
        db.query(QAResult)
        .filter(QAResult.presentation_id == presentation_id)
        .order_by(QAResult.created_at.desc())
        .all()
    )
    return [QAResponse.model_validate(r) for r in results]
