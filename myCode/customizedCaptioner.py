from typing import List, Dict, Literal
from moviepy.editor import (
    VideoFileClip, TextClip, CompositeVideoClip,
    ColorClip, VideoClip, concatenate_videoclips
)
import whisper
import os
from multiprocessing import cpu_count
import time
from pathlib import Path
from tqdm import tqdm
import numpy as np

class FontManager:
    def __init__(self):
        self.custom_fonts = {}

    def add_font(self, name: str, path: str):
        """Add a custom font by path"""
        font_path = Path(path)
        if not font_path.exists():
            raise FileNotFoundError(f"Font file not found: {path}")
        self.custom_fonts[name] = str(font_path)

    def get_font_path(self, font_name: str) -> str:
        """Get the full path for a font by name"""
        if font_name in self.custom_fonts:
            return self.custom_fonts[font_name]
        return font_name

class ProgressBar:
    def __init__(self, total=None, desc=None):
        self.pbar = None if total is None else tqdm(total=total, desc=desc)

    def __call__(self, t=None, message=None):
        if message:
            tqdm.write(message)
        if self.pbar is not None and t is not None:
            self.pbar.update(1)

    def __enter__(self):
        return self

    def __exit__(self, exc_type, exc_val, exc_tb):
        if self.pbar is not None:
            self.pbar.close()

    def iter_bar(self, chunk=None, t=None, **kwargs):
        """Create iterator with progress bar"""
        if t is not None:
            return tqdm(t, desc="Processing frames")
        elif chunk is not None:
            return tqdm(chunk, desc="Processing")
        return tqdm(range(100), desc="Processing")

FONT_MANAGER = FontManager()

class CaptionStyle:
    def __init__(
        self,
        font: str = "Arial",
        font_size: int = 70,
        color: str = "white",
        stroke_color: str = "black",
        stroke_width: int = 4,
        position: Literal["top", "center", "bottom"] = "bottom",
        margin: int = 50,
        active_color: str = "lime",
        active_size_increase: int = 10
    ):
        self.font = font
        self.font_size = font_size
        self.color = color
        self.stroke_color = stroke_color
        self.stroke_width = stroke_width
        self.position = position
        self.margin = margin
        self.active_color = active_color
        self.active_size_increase = active_size_increase

class Word:
    def __init__(self, text: str, start: float, end: float):
        self.text = text
        self.start = start
        self.end = end

class CaptionGroup:
    def __init__(self, words: List[Dict], style: CaptionStyle):
        self.words = [Word(w["word"].strip(), w["start"], w["end"]) for w in words]
        self.start_time = words[0]["start"]
        self.end_time = words[-1]["end"]
        self.style = style

    def create_clip(self, video_size: tuple) -> VideoClip:
        """Create a text clip with animated words"""
        def make_frame(t):
            word_clips = []
            x_offset = 0

            for word in self.words:
                # Determine if word is active
                is_active = word.start <= t <= word.end

                # Create text clip for word with appropriate styling
                font_size = (self.style.font_size + self.style.active_size_increase
                           if is_active else self.style.font_size)
                color = self.style.active_color if is_active else self.style.color
                font_weight = 'bold' if is_active else 'normal'

                word_clip = TextClip(
                    txt=word.text + " ",
                    fontsize=font_size,
                    font=FONT_MANAGER.get_font_path(self.style.font),
                    color=color,
                    stroke_color=self.style.stroke_color,
                    stroke_width=self.style.stroke_width,
                    method='caption'
                )

                # Position word clip
                word_clip = word_clip.set_position((x_offset, 0))
                word_clips.append(word_clip)
                x_offset += word_clip.w

            # Create background for the group
            bg = ColorClip((video_size[0], max(clip.h for clip in word_clips)),
                         color=(0,0,0,0))

            # Compose all word clips
            comp = CompositeVideoClip([bg] + word_clips)
            return comp.get_frame(0)

        duration = self.end_time - self.start_time
        clip = VideoClip(make_frame, duration=duration)

        # Position the entire caption group
        x_pos = (video_size[0] - clip.w) // 2
        y_pos = (video_size[1] - clip.h - self.style.margin
                if self.style.position == "bottom"
                else self.style.margin)

        return clip.set_position((x_pos, y_pos))

class VideoProcessor:
    def __init__(
        self,
        input_path: str,
        output_path: str,
        caption_style: CaptionStyle = None,
        resize_to_1080p: bool = False
    ):
        if not os.path.exists(input_path):
            raise FileNotFoundError(f"Input video not found: {input_path}")

        self.input_path = input_path
        self.output_path = output_path

        # Get the input video's size
        temp_video = VideoFileClip(input_path)
        self.original_size = temp_video.size
        if resize_to_1080p:
            self.video_size = (1920, 1080)
        else:
            self.video_size = self.original_size
        temp_video.close()

        self.max_words = 5
        self.caption_style = caption_style or CaptionStyle()
        self.n_cores = max(cpu_count() - 1, 1)

    def process(self):
        """Main processing pipeline"""
        try:
            print("\nStarting video processing...")
            transcriptions = self._transcribe_video()
            if not transcriptions:
                print("No transcriptions were generated. Check if the video has audio.")
                return

            # Load the original video once
            original_video = VideoFileClip(self.input_path)
            if self.video_size != self.original_size:
                original_video = original_video.resize(self.video_size)

            # Create caption clips
            caption_groups = [
                CaptionGroup(t["words"], self.caption_style)
                for t in transcriptions
            ]

            # Create caption overlay clips with proper timing
            caption_clips = []
            for group in caption_groups:
                clip = group.create_clip(self.video_size)
                clip = clip.set_start(group.start_time).set_end(group.end_time)
                caption_clips.append(clip)

            # Combine original video with captions
            final_video = CompositeVideoClip(
                [original_video] + caption_clips,
                size=self.video_size
            )

            # Write final video
            print("\nRendering final video...")
            with ProgressBar(desc="Rendering video") as progress:
                final_video.write_videofile(
                    self.output_path,
                    codec='libx264',
                    audio_codec='aac',
                    temp_audiofile='temp_audio_final.m4a',
                    remove_temp=True,
                    fps=original_video.fps,
                    threads=self.n_cores,
                    preset='veryfast',
                    ffmpeg_params=[
                        '-crf', '20',
                        '-tune', 'fastdecode',
                        '-movflags', '+faststart',
                        '-bf', '2',
                        '-g', '30',
                        '-profile:v', 'high',
                        '-level', '4.1',
                        '-bufsize', '20000k',
                        '-maxrate', '25000k',
                        '-pix_fmt', 'yuv420p'
                    ],
                    logger=progress,
                    verbose=False
                )

            original_video.close()
            final_video.close()
            print("\nProcessing complete! Output saved to:", self.output_path)

        except Exception as e:
            print(f"\nAn error occurred: {str(e)}")
            import traceback
            traceback.print_exc()

    def _transcribe_video(self) -> List[Dict]:
        """Extract audio and transcribe with word-level timing"""
        print("\nLoading Whisper model...")
        model = whisper.load_model("small")

        print("Extracting audio...")
        audio_path = "temp_audio.wav"
        video = VideoFileClip(self.input_path)

        with ProgressBar(desc="Extracting audio") as progress:
            video.audio.write_audiofile(
                audio_path,
                fps=16000,
                logger=progress,
                verbose=False
            )

        print("\nTranscribing audio...")
        result = model.transcribe(audio_path, language="en", word_timestamps=True)
        video.close()
        os.remove(audio_path)
        print("Transcription complete!")

        return self._process_transcription(result)

    def _process_transcription(self, result: Dict) -> List[Dict]:
        """Process whisper output into word groups"""
        transcriptions = []
        current_words = []
        current_start = None

        for segment in result["segments"]:
            for word_info in segment.get("words", []):
                word = word_info["word"].strip()
                start = word_info["start"]
                end = word_info["end"]

                if not current_words:
                    current_start = start

                current_words.append({
                    "word": word,
                    "start": start,
                    "end": end
                })

                if len(current_words) >= self.max_words or (
                    len(current_words) > 0 and
                    start - current_words[-1]["end"] > 0.5
                ):
                    transcriptions.append({
                        'start_time': current_start,
                        'end_time': current_words[-1]["end"],
                        'words': current_words
                    })
                    current_words = []
                    current_start = None

        if current_words:
            transcriptions.append({
                'start_time': current_start,
                'end_time': current_words[-1]["end"],
                'words': current_words
            })

        return transcriptions

if __name__ == "__main__":
    try:
        # Add custom font if available
        try:
            FONT_MANAGER.add_font("PermanentMarker", "PermanentMarker-Regular.ttf")
            font_name = "PermanentMarker"
        except FileNotFoundError:
            print("PermanentMarker font not found, using Arial instead.")
            font_name = "Arial"

        # Create custom style with active word highlighting
        custom_style = CaptionStyle(
            font=font_name,
            font_size=40,
            color="white",
            stroke_color="black",
            stroke_width=3,
            position="bottom",
            margin=40,
            active_color="lime",  # Color for actively spoken words
            active_size_increase=5  # Size increase for active words
        )

        # Process the video
        processor = VideoProcessor(
            input_path="default.mp4",  # Change this to your input video file
            output_path="output.mp4",  # Change this to your desired output file
            caption_style=custom_style,
            resize_to_1080p=False
        )

        processor.process()

    except Exception as e:
        print(f"\nFatal error: {str(e)}")
        import traceback
        traceback.print_exc()
