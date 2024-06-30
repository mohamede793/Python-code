import boto3
import os
import subprocess
import uuid
import logging
import time

# Configure logging
logging.basicConfig(filename='/tmp/trim_video.log', level=logging.INFO, 
                    format='%(asctime)s:%(levelname)s:%(message)s')

s3_client = boto3.client('s3')

def trim_video_handler(input_path, output_path, max_duration=15):
    try:
        # Get the video duration
        ffprobe_command = [
            'ffprobe', '-v', 'error', '-show_entries', 'format=duration',
            '-of', 'default=noprint_wrappers=1:nokey=1', input_path
        ]
        result = subprocess.run(ffprobe_command, capture_output=True, text=True)
        duration = float(result.stdout.strip())

        logging.info(f"Video duration: {duration}")

        # Trim the video if it's longer than max_duration
        if duration > max_duration:
            ffmpeg_command = [
                'ffmpeg', '-i', input_path, '-t', str(max_duration),
                '-c:v', 'libx264', '-c:a', 'aac', '-strict', 'experimental', '-b:a', '192k', output_path
            ]
        else:
            # Just copy the original video if it's within the duration limit
            ffmpeg_command = [
                'ffmpeg', '-i', input_path, '-c:v', 'copy', '-c:a', 'copy', output_path
            ]


        result = subprocess.run(ffmpeg_command, capture_output=True, text=True)
        print("finished trimming")
        print(result)

        if result.returncode != 0:
            logging.error(f"FFmpeg error: {result.stderr}")
            return False
        else:
            logging.info(f"FFmpeg output: {result.stdout}")
            return True
    except Exception as e:
        logging.error(f"Exception in trim_video_handler: {str(e)}")
        return False

def trim_video(variables):
    bucket_name = "sora-prod-storage"
    object_key = 'medias/' + variables['object_name']
    trimmed_suffix = "_trimmed"

    print("in trimmer")
    
    # Extract the file name from the S3 object key
    file_name = os.path.basename(object_key)
    
    print(file_name)
    # Temporary file paths
    input_path = f"/tmp/{uuid.uuid4()}_{file_name}"
    output_path = f"/tmp/{uuid.uuid4()}_{trimmed_suffix}_{os.path.splitext(file_name)[0]}.mp4"
    
    try:
        # Check if the object exists in S3
        logging.info(f"Checking existence of {object_key} in bucket {bucket_name}")
        print(f"Checking existence of {object_key} in bucket {bucket_name}")
        max_retries = 10
        retries = 0
        while retries < max_retries:
            try:
                s3_client.head_object(Bucket=bucket_name, Key=object_key)
                break
            except Exception as e:
                retries += 1
                logging.warning(f"Attempt {retries} - Object {object_key} not found in bucket {bucket_name}: {str(e)}")
                time.sleep(1)
        else:
            logging.error(f"Object {object_key} not found in bucket {bucket_name} after {max_retries} retries")
            return {
                'statusCode': 404,
                'body': f"Object {object_key} not found in bucket {bucket_name}"
            }
        print("done that")
        
        # Download the video from S3
        logging.info(f"Downloading {object_key} from bucket {bucket_name} to {input_path}")
        s3_client.download_file(bucket_name, object_key, input_path)

        print("downloaded")
        
        logging.info(f"Trimming video from {input_path} to {output_path} to max 15 seconds")
        if not trim_video_handler(input_path, output_path):
            logging.error(f"Error trimming video {object_key}")
            return {
                'statusCode': 500,
                'body': f"Error trimming video {object_key}"
            }
        
        # Upload the trimmed video back to S3
        trimmed_object_key = f"{os.path.splitext(object_key)[0]}{trimmed_suffix}.mp4"
        logging.info(f"Uploading trimmed video to {trimmed_object_key} in bucket {bucket_name}")
        s3_client.upload_file(output_path, bucket_name, trimmed_object_key)
        
        return {
            'statusCode': 200,
            'body': f"Trimmed video saved as {trimmed_object_key} in bucket {bucket_name}"
        }
    
    except Exception as e:
        logging.error(f"Exception in trim_video: {str(e)}")
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
# body = {"variables": {"object_name": "example_object.mp4"}}  # Replace with actual body content if needed
# print(trim_video(body['variables']))
