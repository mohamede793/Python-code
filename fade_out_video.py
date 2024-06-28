import os
import subprocess

def get_video_duration(input_file):
    try:
        # Use ffprobe to get the video duration
        probe_command = [
            'ffprobe', '-v', 'error', '-select_streams', 'v:0', '-show_entries', 
            'stream=duration', '-of', 'default=noprint_wrappers=1:nokey=1', input_file
        ]
        result = subprocess.run(probe_command, capture_output=True, text=True)
        duration = float(result.stdout.strip())
        return duration
    except Exception as e:
        print(f"An error occurred while getting video duration: {str(e)}")
        return None

def fade_out_video(input_file, output_file, fade_duration=0.5):
    try:
        # Get the duration of the input video
        duration = get_video_duration(input_file)
        if duration is None:
            print("Failed to get video duration.")
            return

        # Build the ffmpeg command
        ffmpeg_command = [
            'ffmpeg', '-i', input_file, '-vf', f'fade=t=out:st={duration - fade_duration}:d={fade_duration}',
            '-c:v', 'libx264', '-c:a', 'aac', '-strict', 'experimental', '-b:a', '192k', output_file
        ]
        
        # Run the ffmpeg command
        result = subprocess.run(ffmpeg_command, capture_output=True, text=True)
        
        # Check for errors
        if result.returncode != 0:
            print(f"Error running ffmpeg: {result.stderr}")
        else:
            print(f"Video faded out and saved to {output_file}")
    
    except Exception as e:
        print(f"An error occurred: {str(e)}")

if __name__ == "__main__":
    input_file = 'test2.mp4'  # Replace with your input video file name
    output_file = 'output_fade_out_video.mp4'  # Replace with your desired output video file name
    fade_duration = 1.0  # Replace with your desired fade-out duration in seconds (default is 0.5 seconds)
    
    if not os.path.isfile(input_file):
        print(f"Input file '{input_file}' not found.")
    else:
        fade_out_video(input_file, output_file, fade_duration)
