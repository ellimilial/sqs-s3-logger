import logging
from time import sleep
import boto3 as boto
from botocore.exceptions import ClientError


LOGGER = logging.getLogger(__name__)


class Environment(object):
    TWO_WEEKS = 1209600

    def __init__(self, queue_name, bucket_name, function_name, cron_schedule='rate(1 day)'):
        self._queue_name = queue_name
        self._bucket_name = bucket_name
        self._function_name = function_name,
        self._cron_schedule = cron_schedule,
        self._s3 = boto.resource('s3')
        self._sqs = boto.resource('sqs')
        self._lambda_client = boto.client('lambda')
        self._queue = None
        self._bucket = None

    def _create_queue_with_pushback(self, name, att_dict):
        """
        If a SQS queue is deleted recently (for example during testing), we have to wait 60 secs before recreating.
        """
        try:
            q = self._sqs.create_queue(QueueName=name, Attributes=att_dict)
        except ClientError as e:
            if e.response['Error']['Code'] == 'AWS.SimpleQueueService.QueueDeletedRecently':
                sleep(60)
                q = self._sqs.create_queue(QueueName=name, Attributes=att_dict)
            else:
                raise e
        return q

    def get_queue(self):
        if not self._queue:
            try:
                q = self._sqs.get_queue_by_name(QueueName=self._queue_name)
            except ClientError as e:
                if e.response['Error']['Code'] == 'AWS.SimpleQueueService.NonExistentQueue':
                    q = None
                else:
                    raise e
            if not q:
                LOGGER.info('Creating queue {}'.format(self._queue_name))
                q = self._create_queue_with_pushback(
                    self._queue_name,
                    {'MessageRetentionPeriod': str(self.TWO_WEEKS)}
                )

            self._queue = q
        return self._queue

    def _bucket_exists(self, name):
        try:
            self._s3.meta.client.head_bucket(Bucket=name)
            return True
        except ClientError as e:
            if e.response['Error']['Code'] == '404':
                return False
            else:
                raise e

    def get_bucket(self):
        if not self._bucket:
            b = self._s3.Bucket(self._bucket_name)
            if not self._bucket_exists(self._bucket_name):
                LOGGER.info('Creating bucket {}'.format(self._bucket_name))
                region_name = boto.session.Session().region_name
                b = self._s3.create_bucket(
                    Bucket=self._bucket_name,
                    CreateBucketConfiguration={
                        'LocationConstraint': region_name
                    }
                )
            self._bucket = b
        return self._bucket

    def destroy(self, delete_s3_bucket=False):
        LOGGER.info('Deleting queue {}'.format(self._queue_name))
        self.get_queue().delete()
        if delete_s3_bucket:
            b = self.get_bucket()
            for k in b.objects.all():
                k.delete()
            b.delete()
