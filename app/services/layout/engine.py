from __future__ import annotations
from typing import List, Dict, Any, Optional, Tuple
from dataclasses import dataclass

from app.domain.presentation.models import (
    Slide, Component, SlideLayout, LayoutType, Position, Size,
)
from app.services.design.theme import Theme


@dataclass
class Area:
    name: str
    x: float
    y: float
    width: float
    height: float


class LayoutResolver:
    def __init__(self, theme: Theme):
        self.theme = theme
        self.grid = theme.grid_system
        self.spacing = theme.spacing_system

    def _usable_area(self, margins: Optional[Dict[str, float]] = None) -> Tuple[float, float, float, float]:
        spec = self.grid.spec
        if margins:
            ml = margins.get("left", spec.margin_left)
            mr = margins.get("right", spec.margin_right)
            mt = margins.get("top", spec.margin_top)
            mb = margins.get("bottom", spec.margin_bottom)
        else:
            ml, mr, mt, mb = spec.margin_left, spec.margin_right, spec.margin_top, spec.margin_bottom
        width = spec.slide_width_in - ml - mr
        height = spec.slide_height_in - mt - mb
        return ml, mt, width, height

    def areas_for(self, layout: SlideLayout) -> List[Area]:
        base_x, base_y, content_w, content_h = self._usable_area(layout.margins)
        lt = LayoutType(layout.type) if isinstance(layout.type, str) else layout.type
        sp_sm = self.spacing.get("sm")
        sp_md = self.spacing.get("md")
        sp_lg = self.spacing.get("lg")
        areas: List[Area] = []

        if lt in (LayoutType.TITLE, LayoutType.BIG_STATEMENT):
            areas.append(Area("title", base_x, base_y + content_h * 0.18, content_w, content_h * 0.30))
            areas.append(Area("subtitle", base_x, base_y + content_h * 0.50, content_w, content_h * 0.18))
            areas.append(Area("meta", base_x, base_y + content_h * 0.80, content_w, content_h * 0.15))

        elif lt == LayoutType.SECTION:
            areas.append(Area("eyebrow", base_x, base_y + content_h * 0.25, content_w, content_h * 0.08))
            areas.append(Area("title", base_x, base_y + content_h * 0.35, content_w, content_h * 0.20))
            areas.append(Area("subtitle", base_x, base_y + content_h * 0.60, content_w, content_h * 0.20))

        elif lt == LayoutType.AGENDA:
            areas.append(Area("heading", base_x, base_y, content_w, content_h * 0.15))
            item_h = (content_h * 0.82 - sp_md * 4) / 5
            for i in range(5):
                areas.append(Area(f"item_{i+1}", base_x,
                                  base_y + content_h * 0.18 + i * (item_h + sp_md),
                                  content_w, item_h))

        elif lt == LayoutType.OBJECTIVES:
            areas.append(Area("heading", base_x, base_y, content_w, content_h * 0.18))
            obj_h = (content_h * 0.78 - sp_md * 2) / 3
            for i in range(3):
                areas.append(Area(f"objective_{i+1}", base_x,
                                  base_y + content_h * 0.22 + i * (obj_h + sp_md),
                                  content_w, obj_h))

        elif lt == LayoutType.ONE_COLUMN:
            areas.append(Area("heading", base_x, base_y, content_w, content_h * 0.14))
            areas.append(Area("body", base_x, base_y + content_h * 0.16, content_w, content_h * 0.70))
            areas.append(Area("footer", base_x, base_y + content_h * 0.88, content_w, content_h * 0.10))

        elif lt == LayoutType.TWO_COLUMN:
            areas.append(Area("heading", base_x, base_y, content_w, content_h * 0.14))
            col_w = (content_w - sp_lg) / 2
            body_y = base_y + content_h * 0.16
            body_h = content_h * 0.70
            areas.append(Area("left", base_x, body_y, col_w, body_h))
            areas.append(Area("right", base_x + col_w + sp_lg, body_y, col_w, body_h))
            areas.append(Area("footer", base_x, base_y + content_h * 0.88, content_w, content_h * 0.10))

        elif lt in (LayoutType.THREE_COLUMN, LayoutType.THREE_CARD, LayoutType.CARD_GRID):
            areas.append(Area("heading", base_x, base_y, content_w, content_h * 0.16))
            card_w = (content_w - sp_md * 2) / 3
            card_y = base_y + content_h * 0.20
            card_h = content_h * 0.68
            positions = ["left", "center", "right"] if lt == LayoutType.THREE_COLUMN else ["card_1", "card_2", "card_3"]
            for i, pos in enumerate(positions):
                areas.append(Area(pos, base_x + i * (card_w + sp_md), card_y, card_w, card_h))
            areas.append(Area("footer", base_x, base_y + content_h * 0.90, content_w, content_h * 0.08))

        elif lt == LayoutType.TEXT_VISUAL:
            areas.append(Area("heading", base_x, base_y, content_w, content_h * 0.14))
            split_x = int(content_w * 0.58)
            left_w = split_x - sp_lg / 2
            right_w = content_w - split_x - sp_lg / 2
            body_y = base_y + content_h * 0.16
            body_h = content_h * 0.70
            areas.append(Area("text", base_x, body_y, left_w, body_h))
            areas.append(Area("visual", base_x + split_x + sp_lg / 2, body_y, right_w, body_h))
            areas.append(Area("footer", base_x, base_y + content_h * 0.88, content_w, content_h * 0.10))

        elif lt in (LayoutType.PROCESS, LayoutType.TIMELINE, LayoutType.CYCLE):
            areas.append(Area("heading", base_x, base_y, content_w, content_h * 0.16))
            step_count = 4
            step_w = (content_w - sp_md * (step_count - 1)) / step_count
            step_y = base_y + content_h * 0.24
            step_h = content_h * 0.52
            for i in range(step_count):
                areas.append(Area(f"step_{i+1}",
                                  base_x + i * (step_w + sp_md),
                                  step_y, step_w, step_h))
            areas.append(Area("summary", base_x, base_y + content_h * 0.80, content_w, content_h * 0.15))

        elif lt == LayoutType.COMPARISON:
            areas.append(Area("heading", base_x, base_y, content_w, content_h * 0.14))
            col_w = (content_w - sp_lg) / 2
            areas.append(Area("left_header", base_x, base_y + content_h * 0.16, col_w, content_h * 0.08))
            areas.append(Area("right_header", base_x + col_w + sp_lg, base_y + content_h * 0.16, col_w, content_h * 0.08))
            row_h = (content_h * 0.70 - sp_sm * 2) / 3
            for i in range(3):
                ry = base_y + content_h * 0.26 + i * (row_h + sp_sm)
                areas.append(Area(f"left_row_{i+1}", base_x, ry, col_w, row_h))
                areas.append(Area(f"right_row_{i+1}", base_x + col_w + sp_lg, ry, col_w, row_h))

        elif lt == LayoutType.CASE_STUDY:
            areas.append(Area("heading", base_x, base_y, content_w, content_h * 0.14))
            areas.append(Area("scenario", base_x, base_y + content_h * 0.16, content_w, content_h * 0.22))
            split_y = base_y + content_h * 0.40
            bottom_h = content_h * 0.48
            col_w = (content_w - sp_lg) / 2
            areas.append(Area("problem", base_x, split_y, col_w, bottom_h))
            areas.append(Area("solution", base_x + col_w + sp_lg, split_y, col_w, bottom_h))

        elif lt == LayoutType.TABLE:
            areas.append(Area("heading", base_x, base_y, content_w, content_h * 0.14))
            areas.append(Area("table", base_x, base_y + content_h * 0.16, content_w, content_h * 0.70))
            areas.append(Area("footer", base_x, base_y + content_h * 0.88, content_w, content_h * 0.10))

        elif lt in (LayoutType.QUOTE, LayoutType.BIG_STATEMENT):
            if lt == LayoutType.QUOTE:
                areas.append(Area("mark", base_x, base_y + content_h * 0.05, content_w * 0.10, content_h * 0.15))
                areas.append(Area("text", base_x + content_w * 0.06, base_y + content_h * 0.22,
                                  content_w * 0.88, content_h * 0.48))
                areas.append(Area("source", base_x, base_y + content_h * 0.76, content_w, content_h * 0.15))
            else:
                areas.append(Area("statement", base_x, base_y + content_h * 0.25, content_w, content_h * 0.40))
                areas.append(Area("attribution", base_x, base_y + content_h * 0.70, content_w, content_h * 0.15))

        elif lt == LayoutType.MATRIX:
            areas.append(Area("heading", base_x, base_y, content_w, content_h * 0.14))
            quad_w = (content_w - sp_md) / 2
            quad_h = (content_h * 0.74 - sp_md) / 2
            mx = base_y + content_h * 0.16
            areas.append(Area("q1", base_x, mx, quad_w, quad_h))
            areas.append(Area("q2", base_x + quad_w + sp_md, mx, quad_w, quad_h))
            areas.append(Area("q3", base_x, mx + quad_h + sp_md, quad_w, quad_h))
            areas.append(Area("q4", base_x + quad_w + sp_md, mx + quad_h + sp_md, quad_w, quad_h))

        elif lt in (LayoutType.SUMMARY, LayoutType.TAKEAWAY):
            areas.append(Area("heading", base_x, base_y, content_w, content_h * 0.14))
            item_h = (content_h * 0.76 - sp_sm * 2) / 3
            for i in range(3):
                iy = base_y + content_h * 0.20 + i * (item_h + sp_sm)
                areas.append(Area(f"point_{i+1}", base_x, iy, content_w, item_h))

        elif lt == LayoutType.QUIZ:
            areas.append(Area("heading", base_x, base_y, content_w, content_h * 0.12))
            areas.append(Area("question", base_x, base_y + content_h * 0.14, content_w, content_h * 0.20))
            option_h = (content_h * 0.56 - sp_sm * 3) / 4
            for i in range(4):
                oy = base_y + content_h * 0.36 + i * (option_h + sp_sm)
                areas.append(Area(f"option_{chr(65+i)}", base_x, oy, content_w, option_h))

        elif lt == LayoutType.DISCUSSION:
            areas.append(Area("heading", base_x, base_y, content_w, content_h * 0.12))
            areas.append(Area("prompt", base_x, base_y + content_h * 0.14, content_w, content_h * 0.28))
            col_w = (content_w - sp_lg) / 2
            areas.append(Area("angle_1", base_x, base_y + content_h * 0.46, col_w, content_h * 0.42))
            areas.append(Area("angle_2", base_x + col_w + sp_lg, base_y + content_h * 0.46, col_w, content_h * 0.42))

        else:
            areas.append(Area("heading", base_x, base_y, content_w, content_h * 0.14))
            areas.append(Area("body", base_x, base_y + content_h * 0.16, content_w, content_h * 0.80))

        return areas

    def layout_slide(self, slide: Slide) -> Slide:
        areas = self.areas_for(slide.layout)
        area_map: Dict[str, Area] = {a.name: a for a in areas}
        comps_by_area: Dict[str, List[Component]] = {}

        for comp in slide.components:
            area = comp.constraints.area or self._guess_area_for(comp)
            comps_by_area.setdefault(area, []).append(comp)

        for area_name, comps in comps_by_area.items():
            area = area_map.get(area_name)
            if not area:
                continue
            self._stack_in_area(comps, area)

        return slide

    def _guess_area_for(self, comp: Component) -> str:
        from app.domain.presentation.models import ComponentType as CT
        mapping = {
            CT.HEADING: "heading",
            CT.SUBTITLE: "subtitle",
            CT.PARAGRAPH: "body",
            CT.BULLET_LIST: "body",
            CT.TABLE: "table",
            CT.IMAGE: "visual",
            CT.QUOTE: "text",
            CT.FOOTER: "footer",
            CT.PAGE_NUMBER: "footer",
        }
        return mapping.get(comp.type, "body")

    def _stack_in_area(self, comps: List[Component], area: Area) -> None:
        sp = self.spacing.get("xs")
        n = len(comps)
        if n == 0:
            return
        measured = []
        for c in comps:
            mw, mh = c.measure()
            measured.append((c, max(mh, 0.3)))
        total_h = sum(h for _, h in measured) + sp * max(0, n - 1)
        if total_h > area.height and n > 0:
            scale = area.height / total_h
        else:
            scale = 1.0
        cursor_y = area.y
        for comp, mh in measured:
            h = max(mh * scale, 0.25)
            comp.position = Position(x=area.x, y=cursor_y, unit="in")
            comp.size = Size(width=area.width, height=min(h, area.height - (cursor_y - area.y)), unit="in")
            cursor_y += h + sp
            if cursor_y - area.y > area.height:
                break
