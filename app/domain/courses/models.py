from __future__ import annotations
from typing import Any, Dict, List, Optional
from pydantic import BaseModel, Field
from datetime import UTC, datetime
from enum import Enum


class ContentType(str, Enum):
    MODULE = "MODULE"
    SECTION = "SECTION"
    PARAGRAPH = "PARAGRAPH"
    HEADING = "HEADING"
    LIST = "LIST"
    TABLE = "TABLE"
    IMAGE = "IMAGE"
    CALLOUT = "CALLOUT"
    REGULATION = "REGULATION"


class RegType(str, Enum):
    FACT = "FACT"
    REGULATORY_REQUIREMENT = "REGULATORY_REQUIREMENT"
    EXPLANATION = "EXPLANATION"
    EXAMPLE = "EXAMPLE"
    INTERPRETATION = "INTERPRETATION"


class ContentSection(BaseModel):
    id: str
    title: Optional[str] = None
    content_type: ContentType = ContentType.SECTION
    reg_type: Optional[RegType] = None
    text: str = ""
    subsections: List["ContentSection"] = Field(default_factory=list)
    source_ref: Optional[str] = None
    order: int = 0


class CourseModule(BaseModel):
    id: str
    module_number: int
    title: str
    summary: str = ""
    sections: List[ContentSection] = Field(default_factory=list)
    source_url: Optional[str] = None
    word_count: int = 0
    metadata: Dict[str, Any] = Field(default_factory=dict)


class CourseDocument(BaseModel):
    id: str
    title: str
    source_url: Optional[str] = None
    description: str = ""
    modules: List[CourseModule] = Field(default_factory=list)
    author: Optional[str] = None
    metadata: Dict[str, Any] = Field(default_factory=dict)
    extracted_at: datetime = Field(default_factory=lambda: datetime.now(UTC))

    def get_module(self, module_number: int) -> Optional[CourseModule]:
        for m in self.modules:
            if m.module_number == module_number:
                return m
        return None

    def module_count(self) -> int:
        return len(self.modules)

    def to_dict(self) -> dict:
        return self.model_dump(mode="json")
