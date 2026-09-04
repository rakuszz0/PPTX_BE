from __future__ import annotations
from typing import Dict, Optional
from dataclasses import dataclass, field


@dataclass
class ShapeStyle:
    name: str
    fill: str = "surface"
    border: str = "border"
    border_width_pt: float = 0.75
    border_style: str = "solid"
    border_radius_in: float = 0.08
    shadow: bool = False


class ShapeSystem:
    def __init__(self) -> None:
        self.styles: Dict[str, ShapeStyle] = {}
        self._register_defaults()

    def _register_defaults(self) -> None:
        self.register(ShapeStyle("card", "surface", "border", 0.75, "solid", 0.1, True))
        self.register(ShapeStyle("card_primary", "primary_light", "primary", 1.0, "solid", 0.1, False))
        self.register(ShapeStyle("card_success", "success_light", "success", 1.0, "solid", 0.1, False))
        self.register(ShapeStyle("card_warning", "warning_light", "warning", 1.0, "solid", 0.1, False))
        self.register(ShapeStyle("card_danger", "danger_light", "danger", 1.0, "solid", 0.1, False))
        self.register(ShapeStyle("card_teal", "accent_teal_light", "accent_teal", 1.0, "solid", 0.1, False))
        self.register(ShapeStyle("pill", "primary", "primary", 0.0, "solid", 0.3, False))
        self.register(ShapeStyle("badge_success", "success", "success", 0.0, "solid", 0.2, False))
        self.register(ShapeStyle("badge_warning", "warning", "warning", 0.0, "solid", 0.2, False))
        self.register(ShapeStyle("badge_danger", "danger", "danger", 0.0, "solid", 0.2, False))
        self.register(ShapeStyle("regulatory", "primary_light", "regulatory_stamp", 1.5, "solid", 0.05, False))
        self.register(ShapeStyle("callout", "accent_teal_light", "accent_teal", 1.0, "solid", 0.08, False))

    def register(self, style: ShapeStyle) -> None:
        self.styles[style.name] = style

    def get(self, name: str) -> Optional[ShapeStyle]:
        return self.styles.get(name)


class ElevationSystem:
    LEVELS = {
        0: {"shadow": False},
        1: {"shadow": True, "intensity": 0.15, "offset_y": 0.02},
        2: {"shadow": True, "intensity": 0.22, "offset_y": 0.04},
        3: {"shadow": True, "intensity": 0.3, "offset_y": 0.08},
    }

    @classmethod
    def level(cls, n: int) -> Dict:
        return cls.LEVELS.get(n, cls.LEVELS[0])
