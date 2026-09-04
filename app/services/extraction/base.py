from __future__ import annotations
from typing import Protocol, runtime_checkable, Optional
import hashlib
import json
import os
from pathlib import Path
import re

from app.core.errors import ExtractionError, InvalidURLError
from app.core.security import validate_url
from app.core.logging import get_logger
from app.domain.courses.models import CourseDocument, CourseModule, ContentSection, ContentType, RegType

logger = get_logger(__name__)


CACHE_DIR = Path(os.environ.get("WIZAPE_CACHE_DIR", "cache"))


def _cache_path(key: str) -> Path:
    CACHE_DIR.mkdir(parents=True, exist_ok=True)
    return CACHE_DIR / f"{key}.json"


def _cache_get(key: str):
    p = _cache_path(key)
    if p.exists():
        try:
            return json.loads(p.read_text())
        except Exception:
            return None
    return None


def _cache_put(key: str, data) -> None:
    p = _cache_path(key)
    try:
        p.write_text(json.dumps(data, ensure_ascii=False, indent=2, default=str))
    except Exception as exc:
        logger.warning("cache put failed: %s", exc)


def _sha256(text: str) -> str:
    return hashlib.sha256(text.encode("utf-8")).hexdigest()


@runtime_checkable
class CourseExtractor(Protocol):
    def extract(self, url: str) -> CourseDocument: ...
