import boto3
import os
import subprocess
import uuid
import logging

# Configure logging
logging.basicConfig(filename='/tmp/resize_video.log', level=logging.INFO, 
                    format='%(asctime)s:%(levelname)s:%(message)s')

s3_client = boto3.client('s3')

def resize_video_handler(input_path, output_path, width, height):
    try:
        ffmpeg_command = [
            'ffmpeg', '-i', input_path, '-vf', f'scale={width}:{height}',
            '-c:v', 'libx264', '-c:a', 'aac', '-strict', 'experimental', '-b:a', '192k', output_path
        ]
        result = subprocess.run(ffmpeg_command, capture_output=True, text=True)
        if result.returncode != 0:
            logging.error(f"FFmpeg error: {result.stderr}")
            return False
        else:
            logging.info(f"FFmpeg output: {result.stdout}")
            return True
    except Exception as e:
        logging.error(f"Exception in resize_video_handler: {str(e)}")
        return False

def resize_video(body):
    # bucket_name = "sora-prod-storage"
    # object_key = body.variables.object_name
    # aspect_ratio = body.variables.aspect_ratio
    # resized_suffix = "_resized"

    return body.variables.object_name
    
    # Extract the file name from the S3 object key
    file_name = os.path.basename(object_key)
    
    # Temporary file paths
    input_path = f"/tmp/{uuid.uuid4()}_{file_name}"
    output_path = f"/tmp/{uuid.uuid4()}_{resized_suffix}_{os.path.splitext(file_name)[0]}.mp4"
    
    try:
        # Download the video from S3
        logging.info(f"Downloading {object_key} from bucket {bucket_name} to {input_path}")
        s3_client.download_file(bucket_name, object_key, input_path)
        
        if aspect_ratio == "16:9":
            width, height = 220, 140
        elif aspect_ratio == "9:16":
            height, width = 220, 140
        else:
            width, height = 220, 220

        logging.info(f"Resizing video from {input_path} to {output_path} with width {width} and height {height}")
        if not resize_video_handler(input_path, output_path, width, height):
            logging.error(f"Error resizing video {object_key}")
            return {
                'statusCode': 500,
                'body': f"Error resizing video {object_key}"
            }
        
        # Upload the resized video back to S3
        resized_object_key = f"{os.path.splitext(object_key)[0]}{resized_suffix}.mp4"
        logging.info(f"Uploading resized video to {resized_object_key} in bucket {bucket_name}")
        s3_client.upload_file(output_path, bucket_name, resized_object_key)
        
        return {
            'statusCode': 200,
            'body': f"Resized video saved as {resized_object_key} in bucket {bucket_name}"
        }
    
    except Exception as e:
        logging.error(f"Exception in resize_video: {str(e)}")
        return {
            'statusCode': 500,
            'body': f"An error occurred: {str(e)}"
        }
    finally:
        if os.path.exists(input_path):
            os.remove(input_path)
        if os.path.exists(output_path):
            os.remove(output_path)

# Example usage:
# body = {"some_key": "some_value"}  # Replace with actual body content if needed
# print(resize_video(body))
