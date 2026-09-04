from __future__ import annotations
from typing import Any, Protocol, runtime_checkable, Optional
from app.domain.presentation.ai_pipeline import (
    ContentAnalysis, EducationalDesign, PresentationStory,
    SlideBlueprint, VisualPlan, AIPipelineResult,
)
from app.domain.courses.models import CourseModule


@runtime_checkable
class AIContentAnalyst(Protocol):
    def analyze(self, module: CourseModule) -> ContentAnalysis: ...


@runtime_checkable
class AIEducationalDesigner(Protocol):
    def design(self, module: CourseModule, analysis: ContentAnalysis) -> EducationalDesign: ...


@runtime_checkable
class AIStoryArchitect(Protocol):
    def build_story(self, module: CourseModule, analysis: ContentAnalysis,
                    design: EducationalDesign, target_slides: int = 12) -> PresentationStory: ...


@runtime_checkable
class AISlideArchitect(Protocol):
    def build_blueprint(self, module: CourseModule, analysis: ContentAnalysis,
                        design: EducationalDesign, story: PresentationStory,
                        min_slides: int = 10, max_slides: int = 12) -> SlideBlueprint: ...


@runtime_checkable
class AIVisualDesigner(Protocol):
    def plan_visuals(self, module: CourseModule, blueprint: SlideBlueprint,
                     theme_name: str = "medical_professional") -> VisualPlan: ...


class AIProvider:
    def __init__(self, provider: str = "mock"):
        self.provider = provider

    def analyst(self) -> AIContentAnalyst:
        from .mock_ai import MockContentAnalyst
        return MockContentAnalyst()

    def educational(self) -> AIEducationalDesigner:
        from .mock_ai import MockEducationalDesigner
        return MockEducationalDesigner()

    def story(self) -> AIStoryArchitect:
        from .mock_ai import MockStoryArchitect
        return MockStoryArchitect()

    def slide(self) -> AISlideArchitect:
        from .mock_ai import MockSlideArchitect
        return MockSlideArchitect()

    def visual(self) -> AIVisualDesigner:
        from .mock_ai import MockVisualDesigner
        return MockVisualDesigner()
