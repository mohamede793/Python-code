import speech_recognition as sr
from moviepy.editor import VideoFileClip, TextClip, CompositeVideoClip, AudioFileClip
import subprocess
import os
import numpy as np
from moviepy.config import change_settings
import whisper
import soundfile as sf
from scipy.io import wavfile
import numpy as np

# Configure MoviePy to use ImageMagick
change_settings({"IMAGEMAGICK_BINARY": "convert"})

def analyze_audio_energy(video_path, word_data):
    """Analyze audio energy to detect word elongation"""
    # Extract audio from the relevant segment
    video = VideoFileClip(video_path)
    audio = video.audio

    # Save audio segment to temporary file
    temp_audio = "temp_audio.wav"
    audio.write_audiofile(temp_audio, fps=16000, nbytes=2, codec='pcm_s16le')

    # Read audio data
    sample_rate, audio_data = wavfile.read(temp_audio)

    # Convert to mono if stereo
    if len(audio_data.shape) > 1:
        audio_data = np.mean(audio_data, axis=1)

    # Calculate start and end indices
    start_idx = int(word_data['start'] * sample_rate)
    end_idx = int((word_data['end'] + 1.0) * sample_rate)  # Look ahead 1 second

    if end_idx > len(audio_data):
        end_idx = len(audio_data)

    # Get the segment of audio for this word
    word_audio = audio_data[start_idx:end_idx]

    # Calculate energy in small windows
    window_size = int(0.03 * sample_rate)  # 30ms windows
    energy = []

    for i in range(0, len(word_audio) - window_size, window_size):
        window = word_audio[i:i + window_size]
        energy.append(np.sum(window ** 2))

    energy = np.array(energy)

    # Clean up
    os.remove(temp_audio)
    video.close()
    audio.close()

    return energy, sample_rate

def get_word_timings(video_path):
    """Get word-level timestamps using Whisper with improved timing"""
    print("Loading Whisper model...")
    model = whisper.load_model("large")  # Use larger model for better accuracy

    print("Transcribing audio...")
    result = model.transcribe(
        video_path,
        language="en",
        word_timestamps=True,
        initial_prompt="♪ Music Lyrics: ",  # Help model recognize it's music
        condition_on_previous_text=True,
        temperature=0.0
    )

    words_with_times = []
    if 'segments' in result:
        for segment in result['segments']:
            if 'words' in segment:
                for i, word_data in enumerate(segment['words']):
                    word = word_data['word'].strip()
                    if not word:
                        continue

                    # Get initial timing
                    timing = {
                        'word': word,
                        'start': word_data['start'],
                        'end': word_data['end']
                    }

                    # Analyze audio energy for this word
                    energy, sample_rate = analyze_audio_energy(video_path, timing)

                    if len(energy) > 0:
                        # Find significant energy dropoff
                        threshold = np.mean(energy) * 0.3
                        above_threshold = energy > threshold

                        # Find the last point where energy is above threshold
                        if np.any(above_threshold):
                            last_voiced = np.where(above_threshold)[0][-1]
                            potential_end = timing['start'] + (last_voiced * 0.03)

                            # Check next word to prevent overlap
                            if i < len(segment['words']) - 1:
                                next_word_start = segment['words'][i + 1]['start']
                                # Allow small overlap for flowing lyrics
                                timing['end'] = min(
                                    potential_end,
                                    next_word_start + 0.1  # 100ms overlap allowed
                                )
                            else:
                                timing['end'] = potential_end

                    words_with_times.append(timing)

    print(f"Found {len(words_with_times)} words in the audio")
    return words_with_times

def create_caption_clip(word_data, video_width, video_height):
    """Create an optimized TextClip for music"""
    exact_height = 60  # Larger text for music videos

    # Calculate opacity based on word duration
    duration = word_data['end'] - word_data['start']
    opacity = min(1.0, 1.5 - (duration / 10))  # Fade slightly for very long words

    text_clip = (TextClip(word_data['word'],
                         fontsize=exact_height,
                         color='white',
                         font='Impact',
                         method='label',
                         size=None,
                         align='center',
                         stroke_color='black',
                         stroke_width=4)  # Thicker stroke for better visibility
                 .set_start(word_data['start'])
                 .set_duration(word_data['end'] - word_data['start'])
                 .set_position(('center', 0.85, 'center'))  # Position near bottom
                 .set_opacity(opacity))

    return text_clip

def add_live_captions(video_path, output_path):
    """Main function optimized for music videos"""
    print("Starting video processing...")

    try:
        # Load video
        video = VideoFileClip(video_path)

        # Ensure we have FPS
        if video.fps is None:
            video.fps = 30.0

        print(f"Video FPS: {video.fps}")

        word_timings = get_word_timings(video_path)

        if not word_timings:
            print("No words were detected in the audio.")
            return

        print("Creating caption clips...")
        text_clips = []

        # Process words
        for i, word_data in enumerate(word_timings):
            if word_data['word'].strip():
                try:
                    clip = create_caption_clip(word_data, video.w, video.h)
                    text_clips.append(clip)
                except Exception as e:
                    print(f"Error with word {word_data['word']}: {e}")
                    continue
            print(f"Processed {i+1}/{len(word_timings)} words")

        print("Compositing final video...")
        final_video = CompositeVideoClip([video] + text_clips)
        final_video.fps = video.fps

        print("Writing final video...")
        final_video.write_videofile(
            output_path,
            codec='libx264',
            audio_codec='aac',
            threads=8,
            fps=video.fps,
            bitrate="6000k",  # Higher bitrate for better quality
            preset='medium',  # Better quality preset
            audio=True,
            logger=None
        )

    except Exception as e:
        print(f"An error occurred: {str(e)}")
        raise

    finally:
        # Clean up
        try:
            video.close()
            final_video.close()
            for clip in text_clips:
                clip.close()
        except:
            pass

    print("Video processing complete!")

if __name__ == "__main__":
    input_video = "faze2.mp4"
    output_video = "output_with_captions.mp4"
    add_live_captions(input_video, output_video)
