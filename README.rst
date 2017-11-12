sqs-s3-logger
=============

A library to persist messages on S3 using serverless architecture. It is
mainly targeted at cheaply archiving low-volume, sporadic events from
applications without a need to spin additional infrastructure.

|Overall idea|

What it’s not
-------------

Not a replacement for general logging systems or libraries. Provides no
filtering or aggregation.

AWS Alternatives
----------------

- `Cloudwach Logs`_
- `Kinesis Firehose`_

Usage
=====

Configure ``boto3``\ ’s credentials as per:
http://boto3.readthedocs.io/en/latest/guide/quickstart.html#configuration

Make sure you setup:

-  ``AWS_ACCESS_KEY_ID``
-  ``AWS_SECRET_ACCESS_KEY``
-  ``AWS_DEFAULT_REGION`` (optionally)

Take a look at ``main.py``.

For help: ``python3 main.py -h``

For example (backup at midnight each Saturday from ``app-logs`` queue to
``app-logs-archive`` bucket):

::

    sqs-s3-logger create -b app-logs-archive -q app-logs -f app-logs-backup -s 'cron(0 0 ? * SAT *)'

Sending messages to a queue
---------------------------

Ideally you should use another AWS IAM user with permissions restricted
to getting SQS queues and writing messages.

::

    import boto3
    sqs = boto3.resource('sqs')
    queue = sqs.get_queue_by_name(QueueName='<QUEUE_NAME>')
    queue.send_message(MessageBody='<MSG_BODY_NOT_EXCEEDING_256KB>')

Limitations
===========

-  Maximum SQS message size is limited to 256 KB
-  There could be no more than 120,000 messages in a queue at a time.
-  SQS messages cannot persist for longer than 14 days.
-  Lambda environment has up to 512MB of ephemeral disk capacity.
-  By default it does not guarantee correct time-based ordering

You may need to adjust your CRON settings depending on your volume.

Testing
=======

``python3 setup.py test``

These will use your AWS account to instantiate a temporary integration
environment.

.. |Overall idea| image:: assets/graph-overview.png?raw=true :
.. _Kinesis Firehose: https://aws.amazon.com/kinesis/firehose/
.. _Cloudwach logs: https://aws.amazon.com/cloudwatch/details/#log-monitoring
