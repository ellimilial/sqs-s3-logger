# sqs-s3-logger

A library to persist messages on S3 using serverless architecture. 
It is mainly targeted at cheaply archiving low-volume, sporadic logs from applications without a need to spin additional infrastructure.  

## Usage
Make sure to configure `boto(3)`'s credentials as per:
http://boto3.readthedocs.io/en/latest/guide/quickstart.html#configuration

Make sure you configure:
- `AWS_ACCESS_KEY_ID`
- `AWS_SECRET_ACCESS_KEY`
- `AWS_DEFAULT_REGION` (optionally)

## Limitations
- Maximum SQS message size is limited to 256 KB
- There could be no more than 120,000 messages 
- SQS messages cannot persist for longer than 14 days.

You may need to adjust your CRON settings depending on your volume.

## Testing
`python3 setup.py test`

These will use your AWS account to instantiate a temporary integration environment.  
