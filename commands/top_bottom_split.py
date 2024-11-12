import os
import subprocess

def get_video_info(input_file):
    try:
        # Get video info including audio streams
        probe_command = [
            'ffprobe', '-v', 'error',
            '-show_entries', 'stream=codec_type,width,height,duration',
            '-of', 'json', input_file
        ]
        result = subprocess.run(probe_command, capture_output=True, text=True)
        
        if result.returncode != 0:
            print(f"Error probing file: {result.stderr}")
            return None
            
        import json
        info = json.loads(result.stdout)
        
        # Initialize variables
        width = height = duration = 0
        has_audio = False
        
        # Parse the streams
        for stream in info.get('streams', []):
            if stream['codec_type'] == 'video':
                width = int(stream.get('width', 0))
                height = int(stream.get('height', 0))
                duration = float(stream.get('duration', 0))
            elif stream['codec_type'] == 'audio':
                has_audio = True
                
        return {
            'width': width,
            'height': height,
            'duration': duration,
            'has_audio': has_audio
        }
    except Exception as e:
        print(f"An error occurred while getting video info: {str(e)}")
        return None

def combine_videos_vertically(top_video, bottom_video, output_file):
    try:
        # Get info for both videos
        top_info = get_video_info(top_video)
        bottom_info = get_video_info(bottom_video)
        
        if not top_info or not bottom_info:
            print("Failed to get video information.")
            return

        # Calculate the target dimensions
        target_width = max(top_info['width'], bottom_info['width'])
        target_height = (top_info['height'] + bottom_info['height']) // 2
        
        # Build the complex filter for combining videos
        filter_complex = (
            f"[0:v]scale={target_width}:{target_height}:force_original_aspect_ratio=decrease,"
            f"pad={target_width}:{target_height}:(ow-iw)/2:0[top];"
            f"[1:v]scale={target_width}:{target_height}:force_original_aspect_ratio=decrease,"
            f"pad={target_width}:{target_height}:(ow-iw)/2:0[bottom];"
            "[top][bottom]vstack=inputs=2[v]"
        )

        # Start building the ffmpeg command
        ffmpeg_command = [
            'ffmpeg',
            '-i', top_video,
            '-i', bottom_video,
            '-filter_complex', filter_complex,
            '-map', '[v]'  # map the video output
        ]
        
        # Add audio mapping if available
        if top_info['has_audio']:
            ffmpeg_command.extend(['-map', '0:a'])
        elif bottom_info['has_audio']:
            ffmpeg_command.extend(['-map', '1:a'])
            
        # Add output options
        ffmpeg_command.extend([
            '-c:v', 'libx264',
            '-preset', 'medium',
            '-crf', '23'
        ])
        
        # Add audio codec if we have audio
        if top_info['has_audio'] or bottom_info['has_audio']:
            ffmpeg_command.extend([
                '-c:a', 'aac',
                '-b:a', '192k'
            ])
            
        # Add output file
        ffmpeg_command.append(output_file)
        
        # Run the ffmpeg command
        result = subprocess.run(ffmpeg_command, capture_output=True, text=True)
        
        # Check for errors
        if result.returncode != 0:
            print(f"Error running ffmpeg: {result.stderr}")
        else:
            print(f"Videos combined successfully and saved to {output_file}")
    
    except Exception as e:
        print(f"An error occurred: {str(e)}")

if __name__ == "__main__":
    top_video = 'video1.mp4'     # Replace with your top video file name
    bottom_video = 'video2.mp4'  # Replace with your bottom video file name
    output_file = 'combined_vertical.mp4'  # Replace with your desired output video file name
    
    # Check if input files exist
    if not os.path.isfile(top_video):
        print(f"Top video file '{top_video}' not found.")
    elif not os.path.isfile(bottom_video):
        print(f"Bottom video file '{bottom_video}' not found.")
    else:
        combine_videos_vertically(top_video, bottom_video, output_file)