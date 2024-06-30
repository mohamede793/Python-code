import boto3
import os
import subprocess
import uuid

s3_client = boto3.client('s3')

def resize_video_handler(input_path, output_path, width, height):
    try:
        ffmpeg_command = [
            'ffmpeg', '-i', input_path, '-vf', f'scale={width}:{height}',
            '-c:v', 'libx264', '-c:a', 'aac', '-strict', 'experimental', '-b:a', '192k', output_path
        ]
        result = subprocess.run(ffmpeg_command, capture_output=True, text=True)
        if result.returncode != 0:
            print(result.stderr)
            return False
        else:
            print(result.stdout)
            return True
    except Exception as e:
        print(str(e))
        return False

def resize_video(body):
    bucket_name = "sora-prod-storage"
    object_key = "medias/0f2d79ab-33a3-4488-ba8d-788377c8804a"
    resized_suffix = "_resized"
    
    # Extract the file name from the S3 object key
    file_name = os.path.basename(object_key)
    
    # Temporary file paths
    input_path = f"/tmp/{uuid.uuid4()}_{file_name}"
    output_path = f"/tmp/{uuid.uuid4()}_{resized_suffix}_{file_name}"
    
    try:
        # Download the video from S3
        s3_client.download_file(bucket_name, object_key, input_path)
        
        # Resize the video
        width, height = 220, 140
        if not resize_video_handler(input_path, output_path, width, height):
            return {
                'statusCode': 500,
                'body': f"Error resizing video {object_key}"
            }
        
        # Upload the resized video back to S3
        resized_object_key = f"{os.path.splitext(object_key)[0]}{resized_suffix}{os.path.splitext(object_key)[1]}"
        s3_client.upload_file(output_path, bucket_name, resized_object_key)
        
        return {
            'statusCode': 200,
            'body': f"Resized video saved as {resized_object_key} in bucket {bucket_name}"
        }
    
    except Exception as e:
        print(str(e))
        return {
            'statusCode': 500,
            'body': f"An error occurred: {str(e)}"
        }
    finally:
        if os.path.exists(input_path):
            os.remove(input_path)
        if os.path.exists(output_path):
            os.remove(output_path)

