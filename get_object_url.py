import boto3
import logging
import os
import time

# Configure logging
logging.basicConfig(filename='/tmp/resize_video.log', level=logging.INFO, 
                    format='%(asctime)s:%(levelname)s:%(message)s')

s3_client = boto3.client('s3')

def generate_presigned_url(bucket_name, object_key, expiration=3600):
    try:
        response = s3_client.generate_presigned_url('get_object',
                                                    Params={'Bucket': bucket_name,
                                                            'Key': object_key},
                                                    ExpiresIn=expiration)
    except Exception as e:
        logging.error(f"Error generating presigned URL: {str(e)}")
        return None

    return response

def get_object_url(variables):
    bucket_name = "sora-prod-storage"
    object_key = 'medias/' + variables['object_name']
    
    print(object_key)
    try:
        # Check if the object exists in S3
        logging.info(f"Checking existence of {object_key} in bucket {bucket_name}")
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

        # Generate the presigned URL for the object
        presigned_url = generate_presigned_url(bucket_name, object_key)

        if presigned_url:
            return {
                'statusCode': 200,
                'body': f"Object URL generated successfully",
                'url': presigned_url
            }
        else:
            return {
                'statusCode': 500,
                'body': f"Error generating object URL"
            }
    
    except Exception as e:
        logging.error(f"Exception in get_object_url: {str(e)}")
        return {
            'statusCode': 500,
            'body': f"An error occurred: {str(e)}"
        }

# Example usage:
# body = {"variables": {"object_name": "example_object.mp4"}}  # Replace with actual body content if needed
# print(get_object_url(body['
