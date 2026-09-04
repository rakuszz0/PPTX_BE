from __future__ import annotations
from typing import Dict, Any, Optional
from dataclasses import dataclass, field

from .colors import ColorSystem, build_medical_color_system
from .typography import TypographySystem, build_medical_typography_system
from .spacing_grid import SpacingSystem, GridSystem, GridSpec
from .shapes import ShapeSystem, ElevationSystem


@dataclass
class Theme:
    name: str
    description: str
    color_system: ColorSystem
    typography_system: TypographySystem
    spacing_system: SpacingSystem
    grid_system: GridSystem
    shape_system: ShapeSystem
    elevation_system: ElevationSystem
    metadata: Dict[str, Any] = field(default_factory=dict)

    def design_tokens(self) -> Dict[str, Any]:
        return {
            "colors": self.color_system.to_palette(),
            "typography": self.typography_system.to_dict(),
            "spacing": self.spacing_system.scale.values,
            "grid": {
                "slide_width_in": self.grid_system.spec.slide_width_in,
                "slide_height_in": self.grid_system.spec.slide_height_in,
                "columns": self.grid_system.spec.columns,
                "rows": self.grid_system.spec.rows,
                "margins": {
                    "left": self.grid_system.spec.margin_left,
                    "right": self.grid_system.spec.margin_right,
                    "top": self.grid_system.spec.margin_top,
                    "bottom": self.grid_system.spec.margin_bottom,
                },
                "gutter_x": self.grid_system.spec.gutter_x,
                "gutter_y": self.grid_system.spec.gutter_y,
            },
            "shapes": {k: {"fill": v.fill, "border": v.border, "border_radius_in": v.border_radius_in}
                       for k, v in self.shape_system.styles.items()},
            "elevation": {str(k): v for k, v in ElevationSystem.LEVELS.items()},
        }

    def get_color_hex(self, name: str, fallback: str = "#000000") -> str:
        sw = self.color_system.get(name)
        return sw.hex if sw else fallback

    def get_color_rgb(self, name: str):
        sw = self.color_system.get(name)
        return sw.rgb_tuple() if sw else (0, 0, 0)


class ThemeSystem:
    _registry: Dict[str, Theme] = {}

    @classmethod
    def register(cls, theme: Theme) -> None:
        cls._registry[theme.name] = theme

    @classmethod
    def get(cls, name: str) -> Optional[Theme]:
        return cls._registry.get(name) or cls._registry.get("medical_professional")


def create_medical_professional_theme() -> Theme:
    return Theme(
        name="medical_professional",
        description="Professional clinical theme for medical and regulatory content.",
        color_system=build_medical_color_system(),
        typography_system=build_medical_typography_system(),
        spacing_system=SpacingSystem(),
        grid_system=GridSystem(GridSpec()),
        shape_system=ShapeSystem(),
        elevation_system=ElevationSystem(),
        metadata={"mood": ["professional", "clinical", "academic", "trustworthy", "calm", "modern"]},
    )


ThemeSystem.register(create_medical_professional_theme())
