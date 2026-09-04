import sys, os
sys.path.insert(0, os.path.join(os.path.dirname(__file__), "..", "backend"))
import pytest
from pathlib import Path


def _ensure_dirs():
    for d in ["data", "cache", "output", "assets"]:
        Path(d).mkdir(parents=True, exist_ok=True)


def test_pptx_renderer_creates_file(tmp_path: Path):
    _ensure_dirs()
    from app.services.design.theme import ThemeSystem
    from app.domain.presentation.models import (
        PresentationDocument, Slide, Component, ComponentType,
        SlidePurpose, SlideLayout, LayoutType, ComponentContent,
    )
    from app.services.layout.engine import LayoutResolver
    from app.services.rendering.pptx_renderer import PptxRenderer

    theme = ThemeSystem.get("medical_professional")
    doc = PresentationDocument(id="pres_render_test", title="Unit Test PPTX")
    s1 = Slide(id="s1", purpose=SlidePurpose.INTRODUCTION,
               layout=SlideLayout(type=LayoutType.TITLE))
    s1.add_component(Component(
        id="c1", type=ComponentType.HEADING,
        content=ComponentContent(text="Judul Presentasi"),
        constraints={"area": "title"},
    ))
    s1.add_component(Component(
        id="c2", type=ComponentType.SUBTITLE,
        content=ComponentContent(text="Subtitle testing"),
        constraints={"area": "subtitle"},
    ))
    doc.add_slide(s1)

    s2 = Slide(id="s2", purpose=SlidePurpose.OBJECTIVES,
               layout=SlideLayout(type=LayoutType.THREE_CARD))
    s2.add_component(Component(
        id="c3", type=ComponentType.HEADING,
        content=ComponentContent(text="Tiga Konsep Utama"),
        constraints={"area": "heading"},
    ))
    for idx, (h, t) in enumerate([
        ("Pertama", "Deskripsi konsep pertama secara singkat."),
        ("Kedua", "Deskripsi konsep kedua."),
        ("Ketiga", "Deskripsi konsep ketiga."),
    ]):
        s2.add_component(Component(
            id=f"c_card_{idx}",
            type=ComponentType.CARD,
            content=ComponentContent(heading=h, text=t),
            style={"variant": f"card_primary" if idx == 0 else "card"},
            constraints={"area": f"card_{idx+1}"},
        ))
    doc.add_slide(s2)

    s3 = Slide(id="s3", purpose=SlidePurpose.SUMMARY,
               layout=SlideLayout(type=LayoutType.ONE_COLUMN))
    s3.add_component(Component(
        id="c_head", type=ComponentType.HEADING,
        content=ComponentContent(text="Ringkasan"),
        constraints={"area": "heading"},
    ))
    s3.add_component(Component(
        id="c_body", type=ComponentType.BULLET_LIST,
        content=ComponentContent(items=[
            {"text": "Poin pertama ringkasan", "level": 0},
            {"text": "Poin kedua ringkasan", "level": 0},
            {"text": "Poin ketiga ringkasan", "level": 0},
        ]),
        constraints={"area": "body"},
    ))
    doc.add_slide(s3)

    resolver = LayoutResolver(theme)
    for s in doc.slides:
        resolver.layout_slide(s)

    out_path = tmp_path / "test_presentation.pptx"
    renderer = PptxRenderer(theme)
    final_path = renderer.render(doc, str(out_path))
    assert Path(final_path).exists()
    assert Path(final_path).stat().st_size > 20_000

    from app.services.qa.engine import QARunner
    qa = QARunner(theme, min_score=70)
    result = qa.run(doc, final_path)
    assert result.overall_score >= 60
    assert doc.slide_count() == 3


def test_qa_scoring_reasonable():
    _ensure_dirs()
    from app.domain.presentation.models import (
        PresentationDocument, Slide, Component, ComponentType,
        SlidePurpose, SlideLayout, LayoutType, ComponentContent, BulletItem,
    )
    from app.services.design.theme import ThemeSystem
    doc = PresentationDocument(id="qa_test", title="QA Test")
    for i in range(10):
        s = Slide(
            id=f"s{i}",
            purpose=list(SlidePurpose)[i % len(SlidePurpose)],
            layout=SlideLayout(type=list(LayoutType)[i % 10]),
            main_message=f"Main message for slide {i}",
            source_references=[f"sec_{i}"] if i % 3 == 0 else [],
        )
        s.add_component(Component(
            id=f"s{i}_head", type=ComponentType.HEADING,
            content=ComponentContent(text=f"Slide {i} Heading"),
        ))
        s.add_component(Component(
            id=f"s{i}_b", type=ComponentType.BULLET_LIST,
            content=ComponentContent(items=[
                BulletItem(text=f"Poin pertama pada slide {i}"),
                BulletItem(text=f"Poin kedua pada slide {i}"),
            ]),
        ))
        doc.add_slide(s)
    from app.services.qa.engine import QARunner
    runner = QARunner()
    res = runner.run(doc)
    assert 0 <= res.overall_score <= 100
    assert all(k in res.scores for k in ["content", "educational", "visual_hierarchy",
                                         "readability", "design_consistency",
                                         "editability", "technical_validity"])
