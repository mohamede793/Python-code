from .word_by_word_fade import word_by_word_fade
from .bounce import bounce
from ..types import CaptionAnimation, AnimationFunction


def get_animation_function(animation: CaptionAnimation) -> AnimationFunction:
    if animation == CaptionAnimation.WORD_BY_WORD_FADE:
        return word_by_word_fade
    elif animation == CaptionAnimation.BOUNCE:
        return bounce
    else:
        return lambda t: t  # No animation
