import datetime
import os
import tempfile
from unittest import TestCase, skip
from sqs_s3_logger.environment import Environment
from sqs_s3_logger.lambda_function import read_queue, handler
from sqs_s3_logger.lambda_function_builder import build_package, ROLE_NAME, ROLE_POLICY


class EnvironmentMixin(object):
    @classmethod
    def _init_environment(cls):
        now = datetime.datetime.now()
        cls.environment = Environment(
            queue_name='sqs_s3_logger_test-{}'.format(cls.__name__),
            bucket_name='sqs-s3-logger-test-{}'.format(
                now.isoformat().lower().replace(':', '-')),
            function_name='sqs_s3_logger_test'
        )

    @classmethod
    def _tear_environment(cls):
        cls.environment.destroy(delete_s3_bucket=True)


class EnvironmentTest(TestCase, EnvironmentMixin):

    @classmethod
    def setUpClass(cls):
        cls._init_environment()

    @classmethod
    def tearDownClass(cls):
        cls.environment.destroy(delete_s3_bucket=True)

    def test_can_get_queue(self):
        q = self.environment.get_create_queue()
        self.assertIn('sqs_s3_logger_test', q.url)

    def test_can_get_bucket(self):
        b = self.environment.get_create_bucket()
        self.assertIn('sqs-s3-logger-test', b.name)
        self.assertIsNotNone(b.creation_date)

    def test_can_create_function(self):
        package_file = build_package()
        role_arn = self.environment.update_role_policy(ROLE_NAME, ROLE_POLICY)
        res = self.environment.update_function(role_arn, package_file)
        self.assertIsNotNone(res)

    def test_can_create_role_policy(self):
        r = self.environment.update_role_policy(ROLE_NAME, ROLE_POLICY)
        self.assertIsNotNone(r)
        self.assertIn('LambdaS3WriteSQSRead', r)


class LambdaFunctionTest(TestCase, EnvironmentMixin):
    @classmethod
    def setUpClass(cls):
        cls._init_environment()

    @classmethod
    def tearDownClass(cls):
        cls._tear_environment()

    def _send_messages_to_the_queue(self, count):
        q = self.environment.get_create_queue()
        for i in range(count):
            q.send_message(MessageBody='message {}'.format(i))

    def test_can_read_single_message(self):
        self._send_messages_to_the_queue(1)
        res = [m for m in read_queue(self.environment.get_create_queue())]
        self.assertIsNotNone(res)
        self.assertEqual(1, len(res))
        self.assertEqual('message 0', res[0].body)

    def test_handler_uploads_queue_contents_to_bucket(self):
        self._send_messages_to_the_queue(1)
        b = self.environment.get_create_bucket()
        self.assertEqual(0, sum(1 for _ in b.objects.all()))
        _, temp_filepath = tempfile.mkstemp()
        os.environ.update({
            'QUEUE_NAME': self.environment._queue_name,
            'BUCKET_NAME': self.environment._bucket_name,
            'TEMP_FILE_PATH': temp_filepath
        })
        handler(None, None)
        self.assertEqual(1, sum(1 for _ in b.objects.all()))

    @skip('Heavier load test, takes too long to be worth it.')
    def test_can_handle_many_messages(self):
        msg_count = 10000
        self._send_messages_to_the_queue(msg_count)
        res = [m for m in read_queue(self.environment.get_create_queue())]
        self.assertEqual(msg_count, len(res))


class LambdaFunctionBuilderTest(TestCase):
    def test_zip_file_is_created(self):
        archive_path = build_package()
        self.assertTrue(archive_path.endswith('.zip'))
        self.assertTrue(os.path.exists(archive_path))
