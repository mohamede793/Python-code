import os
import subprocess

def trim_video(input_file, output_file, start_time, end_time):
    try:
        # Build the ffmpeg command
        ffmpeg_command = [
            'ffmpeg', '-i', input_file, '-ss', start_time, '-to', end_time,
            '-c:v', 'libx264', '-c:a', 'aac', '-strict', 'experimental', '-b:a', '192k', output_file
        ]
        
        # Run the ffmpeg command
        result = subprocess.run(ffmpeg_command, capture_output=True, text=True)
        
        # Check for errors
        if result.returncode != 0:
            print(f"Error running ffmpeg: {result.stderr}")
        else:
            print(f"Video trimmed and saved to {output_file}")
    
    except Exception as e:
        print(f"An error occurred: {str(e)}")

if __name__ == "__main__":
    input_file = 'test1.mp4'  # Replace with your input video file name
    output_file = 'output_video2.mp4'  # Replace with your desired output video file name
    start_time = '00:00:01'  # Replace with your desired start time (HH:MM:SS format)
    end_time = '00:00:03'  # Replace with your desired end time (HH:MM:SS format)
    
    if not os.path.isfile(input_file):
        print(f"Input file '{input_file}' not found.")
    else:
        trim_video(input_file, output_file, start_time, end_time)
