from typing import List, Optional, Tuple, Dict
from moviepy.editor import (
    VideoFileClip, AudioFileClip, TextClip, CompositeVideoClip,
    ColorClip, VideoClip
)
import whisper
import numpy as np
import os
from multiprocessing import cpu_count

class WordAnimator:
    def __init__(self, word: str, start_time: float, end_time: float):
        self.word = word
        self.start_time = start_time
        self.end_time = end_time
        self.duration = end_time - start_time

    def get_color(self, current_time: float) -> str:
        """Get color based on word timing with smooth transition"""
        fade_duration = 0.1  # Duration of fade in/out

        # Before word starts
        if current_time < self.start_time:
            return "white"
        # During fade in
        elif current_time < self.start_time + fade_duration:
            progress = (current_time - self.start_time) / fade_duration
            return self._interpolate_color("white", "lime", progress)
        # During main word display
        elif current_time < self.end_time - fade_duration:
            return "lime"
        # During fade out
        elif current_time < self.end_time:
            progress = (self.end_time - current_time) / fade_duration
            return self._interpolate_color("lime", "white", 1 - progress)
        # After word ends
        else:
            return "white"

    def _interpolate_color(self, color1: str, color2: str, progress: float) -> str:
        """Smoothly interpolate between two colors"""
        if color1 == "white" and color2 == "lime":
            r = int(255 - (255 - 50) * progress)  # 50 is approx R value for lime
            g = 255
            b = int(255 - 255 * progress)
            return f"rgb({r},{g},{b})"
        else:  # lime to white
            r = int(50 + (255 - 50) * progress)
            g = 255
            b = int(0 + 255 * progress)
            return f"rgb({r},{g},{b})"

class CaptionGroup:
    def __init__(self, words: List[Dict], font_size: int = 70, font: str = "Arial-Bold"):
        self.words = [
            WordAnimator(w["word"], w["start"], w["end"])
            for w in words
        ]
        self.start_time = words[0]["start"]
        self.end_time = words[-1]["end"]
        self.font_size = font_size
        self.font = font
        self._clip_cache = {}  # Cache for word clips

    def create_frame(self, t: float) -> VideoClip:
        """Create a frame with animated words"""
        word_clips = []
        x_offset = 0

        for word_animator in self.words:
            color = word_animator.get_color(t)

            # Create or get cached clip
            cache_key = f"{word_animator.word}_{color}"
            if cache_key not in self._clip_cache:
                self._clip_cache[cache_key] = TextClip(
                    txt=word_animator.word,
                    fontsize=self.font_size,
                    font=self.font,
                    color=color,
                    stroke_color='black',
                    stroke_width=4,
                    method='caption'
                ).set_duration(0.1)

            word_clip = self._clip_cache[cache_key]
            word_clips.append(word_clip.set_position((x_offset, 0)))
            x_offset += word_clip.w + 20

        return CompositeVideoClip(word_clips)

class VideoProcessor:
    def __init__(self, input_path: str, output_path: str):
        self.input_path = input_path
        self.output_path = output_path
        self.video_size = (1920, 1080)  # Maintaining 1080p resolution
        self.max_words = 5
        self.font_size = 70
        self.font = "Arial-Bold"
        self.n_cores = max(cpu_count() - 1, 1)

    def process(self):
        """Main processing pipeline"""
        try:
            # Pre-load the video to check properties
            video = VideoFileClip(self.input_path)
            if video.size != self.video_size:
                print(f"Warning: Input video size {video.size} doesn't match target size {self.video_size}")
            video.close()

            transcriptions = self._transcribe_video()
            caption_groups = [
                CaptionGroup(t["words"], self.font_size, self.font)
                for t in transcriptions
            ]
            caption_video = self._create_caption_video(caption_groups)
            self._create_final_video(caption_video)
            print("Processing complete!")
        except Exception as e:
            print(f"An error occurred: {str(e)}")
            import traceback
            traceback.print_exc()

    def _transcribe_video(self) -> List[Dict]:
        """Extract audio and transcribe with word-level timing"""
        print("Loading Whisper model...")
        model = whisper.load_model("small")

        print("Extracting audio and transcribing...")
        audio_path = "temp_audio.wav"
        video = VideoFileClip(self.input_path)
        video.audio.write_audiofile(audio_path, fps=16000, verbose=False, logger=None)

        result = model.transcribe(audio_path, language="en", word_timestamps=True)
        os.remove(audio_path)

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
                    len(current_words) > 0 and start - current_words[-1]["end"] > 0.5
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

    def _create_caption_video(self, caption_groups: List[CaptionGroup]) -> VideoClip:
        """Create transparent video with animated captions (optimized for 1080p)"""
        print("Creating animated caption video...")

        # Pre-create background frame
        bg = ColorClip(self.video_size, color=(0,0,0,0)).set_duration(0.1)
        bg_frame = bg.get_frame(0)

        def make_frame(t):
            # Find the current caption group
            current_group = None
            for group in caption_groups:
                if group.start_time <= t <= group.end_time:
                    current_group = group
                    break

            if not current_group:
                return bg_frame

            # Create caption frame
            caption = current_group.create_frame(t)

            # Center the caption
            x_pos = (self.video_size[0] - caption.w) // 2
            y_pos = self.video_size[1] - 150  # Position captions near bottom
            caption = caption.set_position((x_pos, y_pos))

            return CompositeVideoClip([bg, caption]).get_frame(0)

        video = VideoFileClip(self.input_path)
        duration = video.duration
        video.close()

        return VideoClip(make_frame, duration=duration)

    def _create_final_video(self, caption_video: VideoClip):
        """Overlay captions on original video with optimized encoding"""
        print("Creating final video...")
        original_video = VideoFileClip(self.input_path)
        final_video = CompositeVideoClip([original_video, caption_video])

        # Optimized encoding settings for 1080p
        final_video.write_videofile(
            self.output_path,
            codec='libx264',
            audio_codec='aac',
            temp_audiofile='temp_audio_final.m4a',
            remove_temp=True,
            fps=original_video.fps,
            threads=self.n_cores,
            preset='veryfast',  # Using veryfast preset for better speed
            ffmpeg_params=[
                '-crf', '20',  # Quality setting (20 is high quality, visually lossless)
                '-tune', 'fastdecode',
                '-movflags', '+faststart',
                '-bf', '2',
                '-g', '30',
                '-profile:v', 'high',
                '-level', '4.1',  # Optimal for 1080p
                '-bufsize', '20000k',  # Larger buffer size for better quality
                '-maxrate', '25000k',  # Maximum bitrate
                '-pix_fmt', 'yuv420p'  # Ensure compatibility
            ],
            verbose=False,
            logger=None
        )

        original_video.close()
        final_video.close()

if __name__ == "__main__":
    processor = VideoProcessor("default.mp4", "output.mp4")
    processor.process()
