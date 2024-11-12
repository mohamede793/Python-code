import speech_recognition as sr
from moviepy.editor import VideoFileClip, TextClip, CompositeVideoClip, AudioFileClip
import subprocess
import os
import numpy as np
from moviepy.config import change_settings
import whisper
import librosa
import torch

# Configure MoviePy to use ImageMagick
change_settings({"IMAGEMAGICK_BINARY": "convert"})

def get_audio_features(video_path):
    """Extract audio features for better word boundary detection"""
    # Extract audio from video
    video = VideoFileClip(video_path)
    audio = video.audio

    # Save audio temporarily
    temp_audio = "temp_audio.wav"
    audio.write_audiofile(temp_audio, fps=16000, nbytes=2, codec='pcm_s16le')

    # Load audio with librosa for better music analysis
    y, sr = librosa.load(temp_audio)

    # Get onset strength for detecting word boundaries in music
    onset_env = librosa.onset.onset_strength(y=y, sr=sr)
    onset_frames = librosa.onset.onset_detect(onset_envelope=onset_env, sr=sr)
    onset_times = librosa.frames_to_time(onset_frames, sr=sr)

    # Get RMS energy for detecting sustained vocals
    rms = librosa.feature.rms(y=y)[0]
    rms_times = librosa.times_like(rms, sr=sr)

    # Clean up
    os.remove(temp_audio)
    video.close()
    audio.close()

    return onset_times, rms, rms_times

def adjust_word_timing(word, start, end, onset_times, rms, rms_times, next_word_start=None):
    """Adjust word timing based on audio features"""
    # Find relevant RMS segment
    start_idx = np.searchsorted(rms_times, start)
    end_idx = np.searchsorted(rms_times, end)

    if start_idx >= len(rms) or end_idx >= len(rms):
        return start, end

    word_rms = rms[start_idx:end_idx+1]

    # Find sustained vocals
    threshold = np.mean(word_rms) * 0.3
    is_voiced = word_rms > threshold

    if len(is_voiced) > 0:
        # Extend end time if we detect sustained vocals
        voiced_regions = np.where(is_voiced)[0]
        if len(voiced_regions) > 0:
            last_voiced = voiced_regions[-1]
            potential_end = rms_times[start_idx + last_voiced]

            # If there's a next word, don't overlap more than 100ms
            if next_word_start is not None:
                potential_end = min(potential_end, next_word_start - 0.1)

            # Ensure minimum duration and maximum extension
            end = max(end, min(potential_end, start + 5.0))  # Max 5 seconds per word

    return start, end

def get_word_timings(video_path):
    """Get word-level timestamps using Whisper with music optimization"""
    print("Loading Whisper model...")
    # Use larger model for better accuracy with music
    model = whisper.load_model("large")

    print("Extracting audio features...")
    onset_times, rms, rms_times = get_audio_features(video_path)

    print("Transcribing audio...")
    result = model.transcribe(
        video_path,
        language="en",
        word_timestamps=True,
        condition_on_previous_text=True,
        initial_prompt="♪ Music Lyrics: ",  # Help model recognize it's music
        temperature=0.0,
        no_speech_threshold=0.1,
        compression_ratio_threshold=2.4,
        beam_size=5
    )

    words_with_times = []
    if 'segments' in result:
        for segment in result['segments']:
            if 'words' in segment:
                for i, word_data in enumerate(segment['words']):
                    word = word_data['word'].strip()
                    if not word:
                        continue

                    start = word_data['start']
                    end = word_data['end']

                    # Get next word's start time if available
                    next_word_start = None
                    if i < len(segment['words']) - 1:
                        next_word_start = segment['words'][i + 1]['start']

                    # Adjust timing based on audio features
                    adjusted_start, adjusted_end = adjust_word_timing(
                        word, start, end, onset_times, rms, rms_times, next_word_start
                    )

                    words_with_times.append({
                        'word': word,
                        'start': adjusted_start,
                        'end': adjusted_end,
                        'confidence': word_data.get('confidence', 0.0)
                    })

    print(f"Found {len(words_with_times)} words in the audio")
    return words_with_times

def create_caption_clip(word_data, video_width, video_height):
    """Create an enhanced TextClip for music lyrics"""
    # Larger text for music videos
    exact_height = 70  # Increased size for better visibility

    # Calculate opacity based on duration (longer words fade slightly)
    duration = word_data['end'] - word_data['start']
    opacity = min(1.0, 1.5 - (duration / 10))  # Gradually reduce opacity for longer words

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
        video = VideoFileClip(video_path)

        if video.fps is None:
            video.fps = 30.0

        print(f"Video FPS: {video.fps}")

        print("Getting word timings...")
        word_timings = get_word_timings(video_path)

        if not word_timings:
            print("No words were detected in the audio.")
            return

        print("Creating caption clips...")
        text_clips = []

        # Process words with overlap consideration
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
