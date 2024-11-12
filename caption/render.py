from textwrap import wrap
from typing import List, Optional
from moviepy.editor import TextClip, CompositeVideoClip

from artisanads import video
from animations.bounce import bounce
from animations.word_by_word_fade import word_by_word_fade
from .types import (
    AnimationFunction,
    CaptionStyle,
    CaptionPosition,
    CaptionAnimation,
)
from .positioning import position_caption
from .animations import get_animation_function


def render_caption(
    text: str,
    duration: float,
    style: CaptionStyle,
    position: CaptionPosition,
    animation: CaptionAnimation,
    word_timings: List[float],
    video_size: tuple[int, int] = (1920, 1080),
) -> CompositeVideoClip:
    if animation == CaptionAnimation.WORD_BY_WORD_FADE and word_timings is None:
        raise ValueError("Word timings are required for word-by-word fade animation")

    animation_func = get_animation_function(animation)

    if animation == CaptionAnimation.WORD_BY_WORD_FADE:
        clip = render_word_by_word(text, duration, style, word_timings, animation)
    elif animation == CaptionAnimation.NONE:
        clip = render_full_text(
            text, duration, style, animation_func=None, video_size=video_size
        )
    else:
        clip = render_full_text(
            text, duration, style, animation_func, video_size=video_size
        )

    positioned_clip = position_caption(clip, position, video_size)
    return positioned_clip


def render_word_by_word(
    text: str,
    duration: float,
    style: CaptionStyle,
    word_timings: List[float],
    animation: CaptionAnimation,
) -> CompositeVideoClip:
    if animation == CaptionAnimation.WORD_BY_WORD_FADE:
        return word_by_word_fade(
            text,
            style.font_path,
            style.font_size,
            style.color,
            word_timings,
            duration,
            stroke_color=style.stroke_color,
            stroke_width=style.stroke_width,
        )
    else:
        # Implement other word-by-word animations here if needed
        raise NotImplementedError(
            f"Animation {animation} not implemented for word-by-word rendering"
        )


def render_full_text(
    text: str,
    duration: float,
    style: CaptionStyle,
    animation_func: Optional[AnimationFunction],
    video_size: tuple[int, int] = (1920, 1080),
    position: CaptionPosition = CaptionPosition.CENTER,
    max_width_percentage: float = 0.7,
) -> TextClip:
    # Calculate maximum width for text
    max_width = int(video_size[0] * max_width_percentage)

    # Create a temporary TextClip to measure text width
    temp_clip = TextClip(
        txt="test",
        fontsize=style.font_size,
        font=style.font_path,
        color=style.color,
        stroke_color=style.stroke_color,
        stroke_width=style.stroke_width,
    )

    # Estimate characters per line
    char_width = temp_clip.w / 4  # Assuming 'test' is representative
    chars_per_line = int(max_width / char_width)

    # Wrap text
    wrapped_text = "\n".join(wrap(text, width=chars_per_line))

    # Create the actual TextClip with wrapped text
    clip = TextClip(
        txt=wrapped_text,
        fontsize=style.font_size,
        font=style.font_path,
        color=style.color,
        stroke_color=style.stroke_color,
        stroke_width=style.stroke_width,
        method="caption",  # This method better handles multiline text
        align="center",
        size=(max_width, None),  # Set maximum width, height will adjust automatically
    ).set_duration(duration)

    if animation_func:
        clip = clip.resize(lambda t: animation_func(t))

    return clip
