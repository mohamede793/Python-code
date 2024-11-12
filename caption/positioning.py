from moviepy.editor import CompositeVideoClip, VideoClip
from .types import CaptionPosition


def position_caption(
    clip: VideoClip, position: CaptionPosition, video_size: tuple[int, int]
) -> CompositeVideoClip:
    w, h = video_size

    if position == CaptionPosition.CENTER:
        pos = ("center", "center")
    elif position == CaptionPosition.LEFT:
        pos = (10, "center")
    elif position == CaptionPosition.RIGHT:
        pos = (w - 10, "center")
    elif position == CaptionPosition.TOP:
        pos = ("center", 10)
    elif position == CaptionPosition.BOTTOM:
        pos = ("center", h - 10)
    else:
        raise ValueError(f"Invalid position: {position}")

    return clip.set_position(pos)
