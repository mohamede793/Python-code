from enum import Enum
from dataclasses import dataclass
from typing import Callable, Any


class CaptionPosition(str, Enum):
    CENTER = "center"
    LEFT = "left"
    RIGHT = "right"
    TOP = "top"
    BOTTOM = "bottom"


class CaptionAnimation(str, Enum):
    NONE = "none"
    WORD_BY_WORD_FADE = "word_by_word_fade"
    BOUNCE = "bounce"


@dataclass
class CaptionStyle:
    font_path: str
    font_size: int
    color: str
    stroke_color: str = "black"
    stroke_width: int = 0


AnimationFunction = Callable[[Any], Any]  # Placeholder for more specific type hints
