import os
import logging
import boto3 as boto
import datetime

LOGGER = logging.getLogger()
LOGGER.setLevel(logging.INFO)

sqs = boto.resource('sqs')
s3 = boto.resource('s3')


def handler(event, context):
    """
    Reads contents of a SQS queue messages' body and uploads them as a timestamped file to a S3 bucket.
    Requires QUEUE_NAME, BUCKET_NAME env variables in addition to boto3 credentials.
    """
    LOGGER.info('event: {}\ncontext: {}'.format(event, context))

    q_name = os.environ['QUEUE_NAME']
    b_name = os.environ['BUCKET_NAME']
    temp_filepath = os.environ.get('TEMP_FILE_PATH', '/tmp/logs.txt')

    LOGGER.info('Storing messages from queue {} to bucket {}'.format(q_name, b_name))
    q = sqs.get_queue_by_name(QueueName=q_name)
    s3.meta.client.head_bucket(Bucket=b_name)  # Check that the bucket exists.
    b = s3.Bucket(b_name)
    msgs = read_queue(q)
    written = dump_messages_to_file(msgs, temp_filepath)
    b.upload_file(temp_filepath, '{}.txt'.format(datetime.datetime.now()))

    failed_deletions = batch_delete_messages(q, written)
    if failed_deletions:
        LOGGER.info('Deletion of {} messages failed'.format(len(failed_deletions)))


def batch_delete_messages(queue, messages):
    deletion_results = []
    for i in range(0, len(messages), 10):
        deletion_result = queue.delete_messages(
            Entries=[
                {'Id': m.message_id, 'ReceiptHandle': m.receipt_handle}
                for m in messages[i : i + 10]
            ]
        )
        deletion_results += deletion_result.get('Failed', [])
    return deletion_results


def read_queue(queue):
    messages = queue.receive_messages(
        MaxNumberOfMessages=10, WaitTimeSeconds=1)
    while len(messages) > 0:
        for message in messages:
            yield message
        messages = queue.receive_messages(
            MaxNumberOfMessages=10, WaitTimeSeconds=1)


def dump_messages_to_file(msgs, file_name):
    written_messages = []
    with open(file_name, 'w') as f:
        for message in msgs:
            f.write(message.body + '\n')
            written_messages.append(message)
    return written_messages
