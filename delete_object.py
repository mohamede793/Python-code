import boto3
import logging
import os
import time

# Configure logging
logging.basicConfig(filename='/tmp/delete_object.log', level=logging.INFO, 
                    format='%(asctime)s:%(levelname)s:%(message)s')

s3_client = boto3.client('s3')

def delete_object_from_s3(bucket_name, object_key):
    try:
        response = s3_client.delete_object(Bucket=bucket_name, Key=object_key)
        logging.info(f"Deleted object {object_key} from bucket {bucket_name}: {response}")
        return response
    except Exception as e:
        logging.error(f"Error deleting object: {str(e)}")
        return None

def delete_object(variables):
    bucket_name = "sora-prod-storage"
    object_key = variables['object_name']
    
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

        # Delete the object from S3
        delete_response = delete_object_from_s3(bucket_name, object_key)

        if delete_response:
            return {
                'statusCode': 200,
                'body': f"Object {object_key} deleted successfully"
            }
        else:
            return {
                'statusCode': 500,
                'body': f"Error deleting object"
            }
    
    except Exception as e:
        logging.error(f"Exception in delete_object: {str(e)}")
        return {
            'statusCode': 500,
            'body': f"An error occurred: {str(e)}"
        }

# Example usage:
# body = {"variables": {"object_name": "example_object.mp4"}}  # Replace with actual body content if needed
# print(delete_object(body['variables']))
