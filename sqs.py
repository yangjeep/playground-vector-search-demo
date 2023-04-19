import os
import boto3
import json

from getpass import getuser
from firexkit.argument_conversion import SingleArgDecorator
from firexkit.task import FireXTask

from firexapp.engine.celery import app
from firexapp.submit.arguments import InputConverter
from dotenv import load_dotenv
import os
import json


@app.task()
def process_data(data_chunk):
    # Implement your data processing logic here
    print(len(data_chunk))
    pass


@app.task()
def get_s3_object(s3_client, bucket, key):
    obj = s3_client.get_object(Bucket=bucket, Key=key)
    return obj['Body'].read()


@app.task()
def receive_sqs_message(sqs_client, queue_url):
    response = sqs_client.receive_message(
        QueueUrl=queue_url,
        MaxNumberOfMessages=1,
        WaitTimeSeconds=20
    )
    if 'Messages' in response:
        message = response['Messages'][0]
        receipt_handle = message['ReceiptHandle']
        body = json.loads(message['Body'])
        sqs_client.delete_message(
            QueueUrl=queue_url, ReceiptHandle=receipt_handle)
        return body
    return None


def main():
    # Read input from environment variables
    sqs_queue_url = os.environ['SQS_QUEUE_URL']
    bucket_name = os.environ['S3_BUCKET_NAME']

    # Initialize the S3 and SQS clients
    s3_client = boto3.client('s3')
    sqs_client = boto3.client('sqs')

    while True:
        # Receive a message from the SQS queue
        message = receive_sqs_message(sqs_client, sqs_queue_url)
        if message:
            object_key = message['s3_object_key']

            # Fetch the data chunk from S3
            data_chunk = get_s3_object(s3_client, bucket_name, object_key)

            # Process the data
            process_data(data_chunk)


if __name__ == "__main__":
    main()
