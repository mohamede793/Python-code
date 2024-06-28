import os
import subprocess

def resize_video(input_file, output_file, width, height):
    try:
        # Build the ffmpeg command
        ffmpeg_command = [
            'ffmpeg', '-i', input_file, '-vf', f'scale={width}:{height}',
            '-c:v', 'libx264', '-c:a', 'aac', '-strict', 'experimental', '-b:a', '192k', output_file
        ]
        
        # Run the ffmpeg command
        result = subprocess.run(ffmpeg_command, capture_output=True, text=True)
        
        # Check for errors
        if result.returncode != 0:
            print(f"Error running ffmpeg: {result.stderr}")
        else:
            print(f"Video resized and saved to {output_file}")
    
    except Exception as e:
        print(f"An error occurred: {str(e)}")

if __name__ == "__main__":
    input_file = 'test2.mp4'  # Replace with your input video file name
    output_file = 'output_video2.mp4'  # Replace with your desired output video file name
    width = 240
    height = 140
    
    if not os.path.isfile(input_file):
        print(f"Input file '{input_file}' not found.")
    else:
        resize_video(input_file, output_file, width, height)
