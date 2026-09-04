from __future__ import annotations
from typing import Dict, Literal, Optional
from dataclasses import dataclass, field


FontWeight = Literal["Light", "Normal", "Regular", "Medium", "SemiBold", "Bold", "ExtraBold"]


@dataclass
class TypographyPreset:
    name: str
    font_family: str
    size_pt: float
    weight: FontWeight = "Regular"
    line_height: float = 1.3
    letter_spacing_pt: float = 0.0
    color_name: str = "text_heading"


class TypographySystem:
    def __init__(self) -> None:
        self.presets: Dict[str, TypographyPreset] = {}
        self.base_family_sans = "Calibri"
        self.base_family_serif = "Georgia"

    def add(self, preset: TypographyPreset) -> None:
        self.presets[preset.name] = preset

    def get(self, name: str) -> Optional[TypographyPreset]:
        return self.presets.get(name)

    def to_dict(self) -> Dict[str, Dict]:
        return {
            k: {
                "font_family": v.font_family,
                "size_pt": v.size_pt,
                "weight": v.weight,
                "line_height": v.line_height,
                "color_name": v.color_name,
            }
            for k, v in self.presets.items()
        }


def build_medical_typography_system() -> TypographySystem:
    ts = TypographySystem()
    ts.base_family_sans = "Calibri"
    ts.add(TypographyPreset("title", "Calibri", 40, "Bold", 1.15, "text_heading"))
    ts.add(TypographyPreset("subtitle", "Calibri", 24, "SemiBold", 1.25, "neutral_600"))
    ts.add(TypographyPreset("heading_1", "Calibri", 28, "Bold", 1.20, "text_heading"))
    ts.add(TypographyPreset("heading_2", "Calibri", 22, "SemiBold", 1.25, "neutral_800"))
    ts.add(TypographyPreset("heading_3", "Calibri", 18, "SemiBold", 1.25, "neutral_800"))
    ts.add(TypographyPreset("body_large", "Calibri", 16, "Regular", 1.40, "text_body"))
    ts.add(TypographyPreset("body", "Calibri", 14, "Regular", 1.45, "text_body"))
    ts.add(TypographyPreset("body_small", "Calibri", 12, "Regular", 1.45, "neutral_600"))
    ts.add(TypographyPreset("caption", "Calibri", 10, "Regular", 1.5, "text_muted"))
    ts.add(TypographyPreset("bullet", "Calibri", 14, "Regular", 1.4, "text_body"))
    ts.add(TypographyPreset("quote", "Georgia", 18, "Italic", 1.5, "neutral_700"))
    ts.add(TypographyPreset("metric_value", "Calibri", 36, "Bold", 1.1, "primary"))
    ts.add(TypographyPreset("metric_label", "Calibri", 12, "Regular", 1.3, "text_muted"))
    ts.add(TypographyPreset("badge", "Calibri", 10, "SemiBold", 1.1, "white"))
    ts.add(TypographyPreset("footer", "Calibri", 10, "Regular", 1.2, "footer"))
    ts.add(TypographyPreset("page_number", "Calibri", 10, "Regular", 1.1, "text_muted"))
    ts.add(TypographyPreset("regulatory_label", "Calibri", 11, "SemiBold", 1.2, "regulatory_stamp"))
    return ts
