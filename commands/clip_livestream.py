import whisper
import torch
from moviepy.editor import VideoFileClip, TextClip, CompositeVideoClip
from moviepy.config import change_settings
import os
import time

# Configure MoviePy to use ImageMagick
change_settings({"IMAGEMAGICK_BINARY": "convert"})

class EnhancedVideoCaptioner:
    def __init__(self, input_video="input.mp4", output_video="output_captioned.mp4"):
        self.input_video = input_video
        self.output_video = output_video
        self.device = "cuda" if torch.cuda.is_available() else "cpu"
        print(f"Using device: {self.device}")

    def get_word_timestamps(self):
        """Extract word-level timestamps using Whisper"""
        print("Loading Whisper model...")
        model = whisper.load_model("base", device=self.device)

        print("Transcribing audio...")
        result = model.transcribe(
            self.input_video,
            language="en",
            word_timestamps=True,
            verbose=False
        )

        words_with_times = []
        if 'segments' in result:
            for segment in result['segments']:
                if 'words' in segment:
                    for word_data in segment['words']:
                        words_with_times.append({
                            'word': word_data['word'].strip(),
                            'start': word_data['start'],
                            'end': word_data['end']
                        })

        print(f"Found {len(words_with_times)} words in the audio")
        return words_with_times

    def create_text_clip(self, word_data, video_width, video_height):
        """Create an optimized text clip for each word"""
        # Calculate font size based on video height (responsive)
        font_size = min(video_height // 16, 60)

        return (TextClip(word_data['word'],
                        fontsize=font_size,
                        font='Impact',
                        color='white',
                        stroke_color='black',
                        stroke_width=2,
                        method='label',
                        align='center')
                .set_start(word_data['start'])
                .set_duration(word_data['end'] - word_data['start'])
                .set_position(('center', 'bottom')))

    def process_video(self):
        """Main processing function"""
        start_time = time.time()
        print(f"Starting processing at: {time.strftime('%H:%M:%S')}")

        try:
            # Load video
            print("Loading video...")
            video = VideoFileClip(self.input_video)

            # Get word timings
            word_timings = self.get_word_timestamps()
            if not word_timings:
                raise Exception("No words detected in the audio")

            # Create text clips
            print("Creating caption clips...")
            text_clips = []
            batch_size = 20  # Process words in batches for better memory management

            for i in range(0, len(word_timings), batch_size):
                batch = word_timings[i:i + batch_size]
                for word_data in batch:
                    if word_data['word'].strip():
                        try:
                            clip = self.create_text_clip(word_data, video.w, video.h)
                            text_clips.append(clip)
                        except Exception as e:
                            print(f"Warning: Skipped word '{word_data['word']}' due to error: {str(e)}")
                            continue

                print(f"Processed {min(i + batch_size, len(word_timings))}/{len(word_timings)} words")

            # Combine video and captions
            print("Creating final video...")
            final_video = CompositeVideoClip([video] + text_clips)

            # Write output video
            print("Writing final video...")
            final_video.write_videofile(
                self.output_video,
                codec='libx264',
                audio_codec='aac',
                threads=4,
                fps=video.fps,
                preset='ultrafast',
                audio=True,
                logger=None
            )

            # Cleanup
            video.close()
            final_video.close()
            for clip in text_clips:
                clip.close()

            end_time = time.time()
            print(f"Finished processing at: {time.strftime('%H:%M:%S')}")
            print(f"Total processing time: {end_time - start_time:.2f} seconds")

        except Exception as e:
            print(f"Error during processing: {str(e)}")
            raise

if __name__ == "__main__":
    try:
        captioner = EnhancedVideoCaptioner(
            input_video="faze2.mp4",
            output_video="captioned_output.mp4"
        )
        captioner.process_video()
    except Exception as e:
        print(f"\nError: {str(e)}")
        input("\nPress Enter to exit...")
