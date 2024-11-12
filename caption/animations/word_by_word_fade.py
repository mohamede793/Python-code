from typing import List
from moviepy.editor import CompositeVideoClip, TextClip


def word_by_word_fade(
    clause: str,
    font_path: str,
    font_size: int,
    color: str,
    word_timings: List[float],
    clip_duration: float,
    method: str = "label",
    kerning: int = -2,
    fade_duration: float = 0.5,
    stroke_color: str = "#000000",
    stroke_width: int = 0,
) -> CompositeVideoClip:
    words = clause.split()
    word_clips = []

    # Create a clip for each word to get their sizes
    temp_clips = [
        TextClip(
            txt=word,
            fontsize=font_size,
            font=font_path,
            color=color,
            method=method,
            kerning=kerning,
            align="West",
            stroke_color=stroke_color,
            stroke_width=stroke_width,
        )
        for word in words
    ]

    # Calculate the maximum width and total height
    max_width = max(clip.w for clip in temp_clips)
    total_height = sum(clip.h for clip in temp_clips)

    y_offset = 0
    for i, (word, start_time) in enumerate(zip(words, word_timings)):
        word_clip = TextClip(
            txt=word,
            fontsize=font_size,
            font=font_path,
            color=color,
            method=method,
            kerning=kerning,
            align="West",
            size=(max_width, None),
            stroke_color=stroke_color,
            stroke_width=stroke_width,
        ).set_duration(clip_duration - start_time)

        # Create a transparent clip for crossfade
        transparent_clip = (
            TextClip(
                txt=" ",
                fontsize=font_size,
                font=font_path,
                color=color,
                method=method,
                kerning=kerning,
                align="West",
                size=word_clip.size,
                stroke_color=stroke_color,
                stroke_width=stroke_width,
            )
            .set_opacity(0)
            .set_duration(clip_duration - start_time)
        )

        # Apply crossfade effect
        word_clip = CompositeVideoClip([transparent_clip, word_clip])
        word_clip = word_clip.crossfadein(fade_duration)  # type: ignore (crossfadein is not recognized)

        # Set the position after applying the crossfade
        word_clip = word_clip.set_position((0, y_offset))

        word_clip = word_clip.set_start(start_time).set_duration(
            clip_duration - start_time
        )
        word_clips.append(word_clip)

        y_offset += word_clip.h

    return CompositeVideoClip(word_clips, size=(max_width, total_height))
