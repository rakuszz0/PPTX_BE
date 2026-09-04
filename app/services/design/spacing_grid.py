from __future__ import annotations
from dataclasses import dataclass, field
from typing import Dict


@dataclass
class SpacingScale:
    unit: str = "in"
    values: Dict[str, float] = field(default_factory=dict)


class SpacingSystem:
    def __init__(self) -> None:
        self.scale = SpacingScale()
        self._build_defaults()

    def _build_defaults(self) -> None:
        v = {
            "xs": 0.06,
            "sm": 0.12,
            "md": 0.2,
            "lg": 0.3,
            "xl": 0.5,
            "2xl": 0.8,
            "3xl": 1.2,
            "4xl": 1.6,
        }
        self.scale.values = v

    def get(self, key: str) -> float:
        return self.scale.values.get(key, 0.2)


@dataclass
class GridSpec:
    slide_width_in: float = 13.333
    slide_height_in: float = 7.5
    columns: int = 12
    rows: int = 8
    margin_left: float = 0.8
    margin_right: float = 0.8
    margin_top: float = 0.5
    margin_bottom: float = 0.5
    gutter_x: float = 0.16
    gutter_y: float = 0.16

    def content_width(self) -> float:
        return self.slide_width_in - self.margin_left - self.margin_right

    def content_height(self) -> float:
        return self.slide_height_in - self.margin_top - self.margin_bottom

    def column_width(self, span: int = 1) -> float:
        avail = self.content_width() - (self.columns - 1) * self.gutter_x
        return (avail / self.columns) * span + max(0, span - 1) * self.gutter_x

    def row_height(self, span: int = 1) -> float:
        avail = self.content_height() - (self.rows - 1) * self.gutter_y
        return (avail / self.rows) * span + max(0, span - 1) * self.gutter_y

    def area_rect(self, col_start: int, row_start: int, col_span: int, row_span: int):
        x = self.margin_left + (col_start - 1) * (self.column_width(1) + self.gutter_x)
        y = self.margin_top + (row_start - 1) * (self.row_height(1) + self.gutter_y)
        w = self.column_width(col_span)
        h = self.row_height(row_span)
        return x, y, w, h


class GridSystem:
    def __init__(self, spec: GridSpec | None = None) -> None:
        self.spec = spec or GridSpec()

    def with_margins(self, margins: Dict[str, float]) -> "GridSystem":
        s = GridSpec()
        for k, v in margins.items():
            setattr(s, f"margin_{k}", v)
        return GridSystem(s)
