from __future__ import annotations
from typing import Any, Dict, List, Optional, Literal, Tuple
from pydantic import BaseModel, Field


class ContentTopic(BaseModel):
    id: str
    name: str
    description: str = ""
    importance: float = Field(default=0.5, ge=0.0, le=1.0)
    keywords: List[str] = Field(default_factory=list)
    suggested_slide_purpose: Optional[str] = None


class ContentAnalysis(BaseModel):
    module_id: str
    title: str
    summary: str = ""
    topics: List[ContentTopic] = Field(default_factory=list)
    key_concepts: List[str] = Field(default_factory=list)
    regulatory_items: List[Dict[str, Any]] = Field(default_factory=list)
    difficulty: Literal["beginner", "intermediate", "advanced"] = "intermediate"
    target_audience: str = "profesional medis"
    prerequisites: List[str] = Field(default_factory=list)
    estimated_reading_time_min: int = 0
    word_count: int = 0
    metadata: Dict[str, Any] = Field(default_factory=dict)


class LearningObjective(BaseModel):
    id: str
    text: str
    bloom_level: str = "understand"
    measurable: bool = True


class EducationalDesign(BaseModel):
    module_id: str
    title: str
    learning_objectives: List[LearningObjective] = Field(default_factory=list)
    pedagogical_approach: str = "expository-guided"
    assessment_strategy: str = "formative"
    recommended_structure: List[Dict[str, Any]] = Field(default_factory=list)
    instructional_sequence: List[Dict[str, Any]] = Field(default_factory=list)
    common_misconceptions: List[str] = Field(default_factory=list)
    real_world_connections: List[str] = Field(default_factory=list)
    metadata: Dict[str, Any] = Field(default_factory=dict)


class StoryBeat(BaseModel):
    id: str
    beat_type: Literal["opening", "exposition", "climax", "transition", "closing"]
    title: str
    narrative: str = ""
    emotional_arc: str = "informative"
    duration_slide_range: tuple[int, int] = (0, 0)


class PresentationStory(BaseModel):
    module_id: str
    title: str
    hook: str = ""
    narrative_arc: str = "problem-solution"
    beats: List[StoryBeat] = Field(default_factory=list)
    opening_message: str = ""
    closing_message: str = ""
    target_slide_count: int = 12
    metadata: Dict[str, Any] = Field(default_factory=dict)


class BlueprintSlide(BaseModel):
    id: str
    slide_number: int
    purpose: str = "CONCEPT"
    layout: str = "ONE_COLUMN"
    title: str = ""
    main_message: str = ""
    components: List[Dict[str, Any]] = Field(default_factory=list)
    source_references: List[str] = Field(default_factory=list)
    speaker_notes: List[str] = Field(default_factory=list)
    density_hint: str = "BALANCED"


class SlideBlueprint(BaseModel):
    module_id: str
    title: str
    slides: List[BlueprintSlide] = Field(default_factory=list)
    metadata: Dict[str, Any] = Field(default_factory=dict)

    def slide_count(self) -> int:
        return len(self.slides)


class VisualPlan(BaseModel):
    module_id: str
    theme_name: str
    color_scheme: Dict[str, str] = Field(default_factory=dict)
    typography: Dict[str, Any] = Field(default_factory=dict)
    visual_emphasis: Dict[str, Any] = Field(default_factory=dict)
    icon_plan: List[Dict[str, Any]] = Field(default_factory=list)
    asset_plan: List[Dict[str, Any]] = Field(default_factory=list)
    metadata: Dict[str, Any] = Field(default_factory=dict)


class AIPipelineResult(BaseModel):
    module_id: str
    analysis: Optional[ContentAnalysis] = None
    educational_design: Optional[EducationalDesign] = None
    story: Optional[PresentationStory] = None
    blueprint: Optional[SlideBlueprint] = None
    visual_plan: Optional[VisualPlan] = None
