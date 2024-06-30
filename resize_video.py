import os
import subprocess

def resize_video(body):
   
   return "THIS IS RESIZE VIDEO"



import boto3
import os
import subprocess
import uuid

s3_client = boto3.client('s3')

def handler(input_path, output_path, width, height):
    try:
        ffmpeg_command = [
            '/opt/ffmpeg', '-i', input_path, '-vf', f'scale={width}:{height}',
            '-c:v', 'libx264', '-c:a', 'aac', '-strict', 'experimental', '-b:a', '192k', output_path
        ]
        result = subprocess.run(ffmpeg_command, capture_output=True, text=True)
        if result.returncode != 0:
            return False
        else:
            return True
    except Exception as e:
        return False

def resize_video(body):
    bucket_name = "sora-prod-storage"
    object_name = "medias/0f2d79ab-33a3-4488-ba8d-788377c8804a"
    resized_suffix = "_resized"
    
    # Temporary file paths
    input_path = f"/tmp/{uuid.uuid4()}_{object_name}"
    output_path = f"/tmp/{uuid.uuid4()}_{resized_suffix}_{object_name}"
    
    try:
        # Download the video from S3
        s3_client.download_file(bucket_name, object_name, input_path)
        
        # Resize the video
        width, height = 220, 140
        if not resize_video(input_path, output_path, width, height):
            return {
                'statusCode': 500,
                'body': f"Error resizing video {object_name}"
            }
        
        # Upload the resized video back to S3
        resized_object_name = f"{os.path.splitext(object_name)[0]}{resized_suffix}{os.path.splitext(object_name)[1]}"
        s3_client.upload_file(output_path, bucket_name, resized_object_name)
        
        return {
            'statusCode': 200,
            'body': f"Resized video saved as {resized_object_name} in bucket {bucket_name}"
        }
    
    except Exception as e:
        return {
            'statusCode': 500,
            'body': f"An error occurred: {str(e)}"
        }
    finally:
        if os.path.exists(input_path):
            os.remove(input_path)
        if os.path.exists(output_path):
            os.remove(output_path)
