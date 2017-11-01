import logging
import datetime
from time import sleep
import boto3 as boto
from botocore.exceptions import ClientError


LOGGER = logging.getLogger(__name__)


class Environment(object):
    TWO_WEEKS = 1209600

    def __init__(self, queue_name, bucket_name, function_name, cron_schedule='rate(1 day)'):
        self._queue_name = queue_name
        self._bucket_name = bucket_name
        self._function_name = function_name
        self._cron_schedule = cron_schedule,
        self._s3 = boto.resource('s3')
        self._sqs = boto.resource('sqs')
        self._lambda_client = boto.client('lambda')
        self._iam_client = boto.client('iam')
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

    def get_create_queue(self):
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

    def get_create_bucket(self):
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

    def _delete_function_if_exists(self, function_name):
        try:
            self._lambda_client.get_function(FunctionName=self._function_name)
            logging.info('Deleting old version of the function {}'.format(self._function_name))
            self._lambda_client.delete_function(FunctionName=self._function_name)
        except ClientError as e:
            if e.response['Error']['Code'] == 'ResourceNotFoundException':
                pass
            else:
                raise e

    def update_function(self, role_arn, filepath, memory_size=128, timeout=300, schedule=None):
        env_variables = {
            'QUEUE_NAME': self._queue_name,
            'BUCKET_NAME': self._bucket_name
        }
        self._delete_function_if_exists(function_name=self._function_name)

        uploaded_package_name = '_function/{}{}.zip'.format(self._function_name, datetime.datetime.now())
        self.get_create_bucket().upload_file(filepath, uploaded_package_name)
        res = self._lambda_client.create_function(
            FunctionName=self._function_name,
            Runtime='python3.6',
            Role=role_arn,
            Handler='lambda_function.handler',
            Code={
                'S3Bucket': self._bucket_name,
                'S3Key': uploaded_package_name,
            },
            MemorySize=memory_size,
            Timeout=timeout,
            Environment={
                'Variables': env_variables
            }
        )

        self.get_create_queue()
        # TODO This doesn't seem to be deleting the temp function.
        self.get_create_bucket().delete_objects(Delete={'Objects': [{'Key': uploaded_package_name}]})
        if schedule:
            self._schedule_function(res['FunctionArn'], schedule)

        return res

    def _schedule_function(self, function_arn, schedule):
        LOGGER.info('Scheduling function {} to {}'.format(self._function_name, schedule))
        events_client = boto.client('events')
        trigger_name = '{}-trigger'.format(self._function_name)

        rule_response = events_client.put_rule(
            Name=trigger_name,
            ScheduleExpression=schedule,
            State='ENABLED',
        )
        self._lambda_client.add_permission(
            FunctionName=self._function_name,
            StatementId="{0}-Event".format(trigger_name),
            Action='lambda:InvokeFunction',
            Principal='events.amazonaws.com',
            SourceArn=rule_response['RuleArn'],
        )
        events_client.put_targets(
            Rule=trigger_name,
            Targets=[{'Id': "1", 'Arn': function_arn}]
        )

    def update_role_policy(self, role_name, policy_config):
        assume_role_policy = '''{
            "Version": "2012-10-17",
            "Statement": [
                {
                    "Effect": "Allow",
                    "Principal": {
                        "Service": "lambda.amazonaws.com"
                    },
                    "Action": "sts:AssumeRole"
                }
            ]
        }
        '''
        LOGGER.info('Updating role policy {}'.format(role_name))
        try:
            self._iam_client.create_role(RoleName=role_name, AssumeRolePolicyDocument=assume_role_policy)
        except ClientError as e:
            if e.response['Error']['Code'] == 'EntityAlreadyExists':
                pass
            else:
                raise e
        self._iam_client.put_role_policy(
            PolicyDocument=policy_config,
            PolicyName=role_name+'Policy',
            RoleName=role_name
        )
        return self._iam_client.get_role(RoleName=role_name)['Role']['Arn']

    def destroy(self, delete_function=False, delete_s3_bucket=False):
        LOGGER.info('Deleting queue {}'.format(self._queue_name))
        self.get_create_queue().delete()
        if delete_function:
            LOGGER.info('Deleting function {}'.format(self._function_name))
            self._lambda_client.delete_function(FunctionName=self._function_name)
        if delete_s3_bucket:
            LOGGER.info('Deleting bucket {}'.format(self._bucket_name))
            b = self.get_create_bucket()
            for k in b.objects.all():
                k.delete()
            b.delete()
