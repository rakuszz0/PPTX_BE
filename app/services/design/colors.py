from __future__ import annotations
from typing import Dict, Tuple, Optional
from dataclasses import dataclass, field


@dataclass(frozen=True)
class ColorSwatch:
    name: str
    hex: str
    r: int
    g: int
    b: int

    @staticmethod
    def from_hex(name: str, hex_str: str) -> "ColorSwatch":
        h = hex_str.lstrip("#")
        r, g, b = int(h[0:2], 16), int(h[2:4], 16), int(h[4:6], 16)
        return ColorSwatch(name=name, hex=f"#{h.upper()}", r=r, g=g, b=b)

    def rgb_tuple(self) -> Tuple[int, int, int]:
        return (self.r, self.g, self.b)

    def rgb_float(self) -> Tuple[float, float, float]:
        return (self.r / 255.0, self.g / 255.0, self.b / 255.0)


class ColorSystem:
    def __init__(self) -> None:
        self.swatches: Dict[str, ColorSwatch] = {}

    def add(self, name: str, hex_color: str) -> ColorSwatch:
        sw = ColorSwatch.from_hex(name, hex_color)
        self.swatches[name] = sw
        return sw

    def get(self, name: str) -> Optional[ColorSwatch]:
        return self.swatches.get(name)

    def to_palette(self) -> Dict[str, str]:
        return {k: v.hex for k, v in self.swatches.items()}


def build_medical_color_system() -> ColorSystem:
    cs = ColorSystem()
    cs.add("primary", "#165DFF")
    cs.add("primary_dark", "#0E42B3")
    cs.add("primary_light", "#E8F0FF")
    cs.add("accent_teal", "#0CB0A9")
    cs.add("accent_teal_light", "#DFF5F4")
    cs.add("success", "#2BA471")
    cs.add("success_light", "#D5F1E3")
    cs.add("warning", "#D48806")
    cs.add("warning_light", "#FCE8C4")
    cs.add("danger", "#D9363E")
    cs.add("danger_light", "#FAD7D9")
    cs.add("neutral_900", "#0E1B2D")
    cs.add("neutral_800", "#1F2A44")
    cs.add("neutral_700", "#36435C")
    cs.add("neutral_600", "#4E5A75")
    cs.add("neutral_500", "#6B7790")
    cs.add("neutral_400", "#96A1B8")
    cs.add("neutral_300", "#C3CAD9")
    cs.add("neutral_200", "#E3E7EF")
    cs.add("neutral_100", "#F1F3F8")
    cs.add("neutral_50", "#F8F9FC")
    cs.add("white", "#FFFFFF")
    cs.add("background", "#FBFCFE")
    cs.add("surface", "#FFFFFF")
    cs.add("surface_alt", "#F3F6FB")
    cs.add("border", "#D9DFEA")
    cs.add("regulatory_stamp", "#0E42B3")
    cs.add("text_heading", "#0E1B2D")
    cs.add("text_body", "#1F2A44")
    cs.add("text_muted", "#4E5A75")
    cs.add("footer", "#36435C")
    return cs
