import sys, os
sys.path.insert(0, os.path.join(os.path.dirname(__file__), "..", "backend"))
import pytest


def test_design_system_colors():
    from app.services.design.theme import ThemeSystem
    theme = ThemeSystem.get("medical_professional")
    assert theme is not None
    primary = theme.color_system.get("primary")
    assert primary is not None
    assert primary.hex == "#165DFF"
    palette = theme.color_system.to_palette()
    assert "neutral_900" in palette
    assert "white" in palette


def test_design_typography_has_presets():
    from app.services.design.theme import ThemeSystem
    theme = ThemeSystem.get("medical_professional")
    names = list(theme.typography_system.presets.keys())
    assert "title" in names
    assert "heading_1" in names
    assert "body" in names
    assert "bullet" in names


def test_grid_system_content_area():
    from app.services.design.spacing_grid import GridSystem, GridSpec
    gs = GridSystem(GridSpec())
    cw = gs.spec.content_width()
    ch = gs.spec.content_height()
    assert 10.0 < cw < 13.0
    assert 5.0 < ch < 8.0


def test_presentation_document_serialization():
    from app.domain.presentation.models import PresentationDocument, Slide, Component, ComponentType
    doc = PresentationDocument(id="p1", title="Test")
    s = Slide(id="s1", main_message="Hi")
    c = Component(id="c1", type=ComponentType.HEADING, content={"text": "Hello"})
    s.add_component(c)
    doc.add_slide(s)
    d = doc.to_dict()
    restored = PresentationDocument.from_dict(d)
    assert restored.title == doc.title
    assert restored.slide_count() == 1


def test_slide_info_density():
    from app.domain.presentation.models import Slide, Component, ComponentType, BulletItem, ComponentContent
    s = Slide(id="s1")
    c = Component(
        id="c1", type=ComponentType.BULLET_LIST,
        content=ComponentContent(items=[
            BulletItem(text="One two three four five six seven eight nine ten"),
            BulletItem(text="second item"),
            BulletItem(text="third item with longer words to count things"),
        ])
    )
    s.add_component(c)
    info = s.info_density()
    assert info["word_count"] >= 5
    assert info["bullet_count"] == 3
    assert "density" in info


def test_layout_resolver_areas():
    from app.services.design.theme import ThemeSystem
    from app.services.layout.engine import LayoutResolver
    from app.domain.presentation.models import SlideLayout, LayoutType
    theme = ThemeSystem.get("medical_professional")
    resolver = LayoutResolver(theme)
    areas = resolver.areas_for(SlideLayout(type=LayoutType.THREE_CARD))
    names = [a.name for a in areas]
    assert "heading" in names
    assert any("card" in n for n in names)


def test_wizape_extractor_module_detection():
    from app.services.extraction import WizapeExtractor
    ext = WizapeExtractor(use_cache=False)
    doc = ext.extract("https://wizape.example/course/med")
    assert doc.title
    assert doc.module_count() >= 1
    mod1 = doc.get_module(1)
    assert mod1 is not None
    assert len(mod1.sections) >= 3
    assert mod1.word_count > 0


def test_mock_ai_pipeline_generates_blueprint():
    from app.services.extraction import WizapeExtractor
    from app.services.ai.mock_ai import MockAIPipelineRunner
    ext = WizapeExtractor(use_cache=False)
    course = ext.extract("https://wizape.example/course/med")
    m1 = course.get_module(1)
    runner = MockAIPipelineRunner()
    res = runner.run(m1, min_slides=10, max_slides=12)
    assert res.analysis is not None
    assert res.blueprint is not None
    assert 10 <= res.blueprint.slide_count() <= 12
