from __future__ import annotations
from typing import Any, Dict, List, Optional, Literal
from pydantic import BaseModel, Field, ConfigDict
from enum import Enum
import json


class ComponentType(str, Enum):
    HEADING = "HEADING"
    SUBTITLE = "SUBTITLE"
    PARAGRAPH = "PARAGRAPH"
    BULLET_LIST = "BULLET_LIST"
    CARD = "CARD"
    METRIC = "METRIC"
    BADGE = "BADGE"
    ICON = "ICON"
    IMAGE = "IMAGE"
    QUOTE = "QUOTE"
    CALLOUT = "CALLOUT"
    TABLE = "TABLE"
    CHART = "CHART"
    TIMELINE = "TIMELINE"
    PROCESS = "PROCESS"
    FLOWCHART = "FLOWCHART"
    MATRIX = "MATRIX"
    COMPARISON = "COMPARISON"
    QUIZ = "QUIZ"
    QUESTION = "QUESTION"
    FOOTER = "FOOTER"
    PAGE_NUMBER = "PAGE_NUMBER"
    SOURCE_REFERENCE = "SOURCE_REFERENCE"


class LayoutType(str, Enum):
    TITLE = "TITLE"
    SECTION = "SECTION"
    AGENDA = "AGENDA"
    OBJECTIVES = "OBJECTIVES"
    ONE_COLUMN = "ONE_COLUMN"
    TWO_COLUMN = "TWO_COLUMN"
    THREE_COLUMN = "THREE_COLUMN"
    TEXT_VISUAL = "TEXT_VISUAL"
    BIG_STATEMENT = "BIG_STATEMENT"
    QUOTE = "QUOTE"
    CARD_GRID = "CARD_GRID"
    THREE_CARD = "THREE_CARD"
    COMPARISON = "COMPARISON"
    PROCESS = "PROCESS"
    TIMELINE = "TIMELINE"
    FLOWCHART = "FLOWCHART"
    CYCLE = "CYCLE"
    PYRAMID = "PYRAMID"
    FUNNEL = "FUNNEL"
    MATRIX = "MATRIX"
    HIERARCHY = "HIERARCHY"
    TABLE = "TABLE"
    CHART = "CHART"
    CASE_STUDY = "CASE_STUDY"
    SCENARIO = "SCENARIO"
    QUIZ = "QUIZ"
    DISCUSSION = "DISCUSSION"
    SUMMARY = "SUMMARY"
    TAKEAWAY = "TAKEAWAY"


class SlidePurpose(str, Enum):
    INTRODUCTION = "INTRODUCTION"
    AGENDA = "AGENDA"
    OBJECTIVES = "OBJECTIVES"
    CONCEPT = "CONCEPT"
    EXPLANATION = "EXPLANATION"
    REGULATION = "REGULATION"
    EXAMPLE = "EXAMPLE"
    PROCESS = "PROCESS"
    COMPARISON = "COMPARISON"
    CASE_STUDY = "CASE_STUDY"
    TIMELINE = "TIMELINE"
    SUMMARY = "SUMMARY"
    TAKEAWAY = "TAKEAWAY"
    QUIZ = "QUIZ"
    DISCUSSION = "DISCUSSION"


class ColorSpec(BaseModel):
    r: int = Field(ge=0, le=255)
    g: int = Field(ge=0, le=255)
    b: int = Field(ge=0, le=255)
    a: float = Field(default=1.0, ge=0.0, le=1.0)

    def to_hex(self) -> str:
        return "#{:02X}{:02X}{:02X}".format(self.r, self.g, self.b)

    @classmethod
    def from_hex(cls, hex_str: str) -> "ColorSpec":
        h = hex_str.lstrip("#")
        return cls(
            r=int(h[0:2], 16),
            g=int(h[2:4], 16),
            b=int(h[4:6], 16),
        )


class Position(BaseModel):
    x: float = 0.0
    y: float = 0.0
    unit: Literal["in", "cm", "px", "pt"] = "in"


class Size(BaseModel):
    width: float
    height: float
    unit: Literal["in", "cm", "px", "pt"] = "in"


class TextStyle(BaseModel):
    font_family: Optional[str] = None
    font_size: Optional[float] = None
    bold: Optional[bool] = None
    italic: Optional[bool] = None
    underline: Optional[bool] = None
    color: Optional[ColorSpec] = None
    align: Optional[Literal["left", "center", "right", "justify"]] = None
    line_spacing: Optional[float] = None


class ComponentStyle(BaseModel):
    text: Optional[TextStyle] = None
    background: Optional[ColorSpec] = None
    border_color: Optional[ColorSpec] = None
    border_width: Optional[float] = None
    border_radius: Optional[float] = None
    padding: Optional[Dict[str, float]] = None
    margin: Optional[Dict[str, float]] = None
    shadow: Optional[bool] = None
    variant: Optional[str] = None
    elevation: Optional[int] = None


class Constraints(BaseModel):
    min_width: Optional[float] = None
    max_width: Optional[float] = None
    min_height: Optional[float] = None
    max_height: Optional[float] = None
    flex_grow: Optional[float] = None
    weight: Optional[float] = None
    area: Optional[str] = None


class BulletItem(BaseModel):
    text: str
    level: int = 0
    bold: Optional[bool] = None
    sub_items: List["BulletItem"] = Field(default_factory=list)


class ComponentContent(BaseModel):
    text: Optional[str] = None
    items: Optional[List[BulletItem]] = None
    level: Optional[int] = None
    heading: Optional[str] = None
    subheading: Optional[str] = None
    value: Optional[str | int | float] = None
    label: Optional[str] = None
    icon: Optional[str] = None
    url: Optional[str] = None
    source: Optional[str] = None
    author: Optional[str] = None
    citation: Optional[str] = None
    accent: Optional[str] = None
    caption: Optional[str] = None
    description: Optional[str] = None
    data: Optional[Any] = None
    rows: Optional[List[List[str]]] = None
    headers: Optional[List[str]] = None
    steps: Optional[List[Dict[str, Any]]] = None
    columns: Optional[List[Dict[str, Any]]] = None


class Component(BaseModel):
    id: str
    type: ComponentType
    content: ComponentContent = Field(default_factory=ComponentContent)
    style: ComponentStyle = Field(default_factory=ComponentStyle)
    constraints: Constraints = Field(default_factory=Constraints)
    position: Position = Field(default_factory=Position)
    size: Size = Field(default_factory=lambda: Size(width=0, height=0))
    metadata: Dict[str, Any] = Field(default_factory=dict)

    def measure(self) -> tuple[float, float]:
        lines = 0
        text = (self.content.text or "") + (self.content.heading or "")
        if text:
            lines = max(1, len(text) // 80 + text.count("\n"))
        if self.content.items:
            lines += len(self.content.items)
        if self.content.rows:
            lines += len(self.content.rows)
        width = self.size.width or 6
        height = max(self.size.height, 0.3 + lines * 0.28)
        return width, height

    def validate(self) -> list[str]:
        issues = []
        if not self.id:
            issues.append("component.id is required")
        return issues

    def to_dict(self) -> dict:
        return self.model_dump(mode="json")


class SlideLayout(BaseModel):
    type: LayoutType = LayoutType.ONE_COLUMN
    variant: Optional[str] = None
    grid_columns: int = 1
    grid_rows: int = 1
    areas: Dict[str, Any] = Field(default_factory=dict)
    margins: Dict[str, float] = Field(default_factory=lambda: {"top": 0.5, "bottom": 0.5, "left": 0.8, "right": 0.8})
    metadata: Dict[str, Any] = Field(default_factory=dict)


class Slide(BaseModel):
    model_config = ConfigDict(use_enum_values=False)

    id: str
    purpose: SlidePurpose | str = SlidePurpose.CONCEPT
    main_message: str = ""
    layout: SlideLayout = Field(default_factory=SlideLayout)
    components: List[Component] = Field(default_factory=list)
    speaker_notes: List[str] = Field(default_factory=list)
    source_references: List[str] = Field(default_factory=list)
    metadata: Dict[str, Any] = Field(default_factory=dict)

    def add_component(self, component: Component) -> None:
        self.components.append(component)

    def info_density(self) -> Dict[str, Any]:
        text_all = ""
        bullet_count = 0
        comp_count = len(self.components)
        for c in self.components:
            if c.content.text:
                text_all += " " + c.content.text
            if c.content.heading:
                text_all += " " + c.content.heading
            if c.content.items:
                bullet_count += len(c.content.items)
                for it in c.content.items:
                    text_all += " " + it.text
        words = text_all.split()
        char_count = len(text_all)
        word_count = len(words)
        paragraph_count = max(1, text_all.count("\n") + 1)
        reading_minutes = max(1, word_count / 130)
        score = word_count + bullet_count * 3 + comp_count * 5
        if score < 40:
            density = "UNDERLOADED"
        elif score < 90:
            density = "BALANCED"
        elif score < 160:
            density = "DENSE"
        else:
            density = "OVERLOADED"
        return {
            "word_count": word_count,
            "character_count": char_count,
            "bullet_count": bullet_count,
            "paragraph_count": paragraph_count,
            "component_count": comp_count,
            "reading_time_minutes": round(reading_minutes, 2),
            "density": density,
        }

    def to_dict(self) -> dict:
        return self.model_dump(mode="json")


class Asset(BaseModel):
    id: str
    asset_type: str
    file_path: Optional[str] = None
    mime_type: Optional[str] = None
    metadata: Dict[str, Any] = Field(default_factory=dict)


class Theme(BaseModel):
    name: str = "medical_professional"
    palette: Dict[str, str] = Field(default_factory=dict)
    typography: Dict[str, Any] = Field(default_factory=dict)
    metadata: Dict[str, Any] = Field(default_factory=dict)


class DesignTokens(BaseModel):
    colors: Dict[str, Any] = Field(default_factory=dict)
    typography: Dict[str, Any] = Field(default_factory=dict)
    spacing: Dict[str, Any] = Field(default_factory=dict)
    grid: Dict[str, Any] = Field(default_factory=dict)
    shapes: Dict[str, Any] = Field(default_factory=dict)
    elevation: Dict[str, Any] = Field(default_factory=dict)


class PresentationSettings(BaseModel):
    slide_width_in: float = 13.333
    slide_height_in: float = 7.5
    orientation: Literal["landscape", "portrait"] = "landscape"
    locale: str = "id_ID"
    footer: Optional[str] = None
    show_page_numbers: bool = True
    min_slides: int = 10
    max_slides: int = 12


class SourceReference(BaseModel):
    id: str
    type: Literal["module", "section", "external", "regulation"]
    ref: str
    title: Optional[str] = None
    url: Optional[str] = None


class PresentationDocument(BaseModel):
    model_config = ConfigDict(use_enum_values=False)

    id: str
    title: str
    theme: Theme = Field(default_factory=Theme)
    design_tokens: DesignTokens = Field(default_factory=DesignTokens)
    slides: List[Slide] = Field(default_factory=list)
    assets: List[Asset] = Field(default_factory=list)
    settings: PresentationSettings = Field(default_factory=PresentationSettings)
    version: int = 1
    source_references: List[SourceReference] = Field(default_factory=list)
    metadata: Dict[str, Any] = Field(default_factory=dict)

    def add_slide(self, slide: Slide) -> None:
        self.slides.append(slide)

    def slide_count(self) -> int:
        return len(self.slides)

    def total_words(self) -> int:
        total = 0
        for s in self.slides:
            total += s.info_density()["word_count"]
        return total

    def to_json(self, indent: int = 2) -> str:
        return self.model_dump_json(indent=indent)

    def to_dict(self) -> dict:
        return self.model_dump(mode="json")

    @classmethod
    def from_dict(cls, data: dict) -> "PresentationDocument":
        return cls.model_validate(data)
