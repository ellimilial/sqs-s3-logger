import datetime
from unittest import TestCase
from sqs_s3_logger.environment import Environment


class EnvironmentCreation(TestCase):

    @classmethod
    def setUpClass(cls):
        now = datetime.datetime.now()
        cls.environment = Environment(
            queue_name='sqs_s3_logger_test',
            bucket_name='sqs-s3-logger-test-{}'.format(now.isoformat().lower().replace(':', '-')),
            function_name='sqs_s3_logger_test'
        )

    @classmethod
    def tearDownClass(cls):
        cls.environment.destroy(delete_s3_bucket=True)

    def test_can_get_queue(self):
        q = self.environment.get_queue()
        self.assertIn('sqs_s3_logger_test', q.url)

    def test_can_get_bucket(self):
        b = self.environment.get_bucket()
        self.assertIn('sqs-s3-logger-test', b.name)
        self.assertIsNotNone(b.creation_date)
