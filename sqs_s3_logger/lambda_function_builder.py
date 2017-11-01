import os
import zipfile
import pip
import shutil
import tempfile
import datetime
import logging

LOGGER = logging.getLogger(__name__)

module_path = os.path.dirname(os.path.realpath(__file__))

REQUIRED_PACKAGES = []
REQUIRED_FILES = ['lambda_function.py']
ROLE_NAME = 'LambdaS3WriteSQSRead'
ROLE_POLICY = '''{
    "Version": "2012-10-17",
    "Statement": [
        {
            "Effect": "Allow",
            "Action": [
                "logs:CreateLogGroup",
                "logs:CreateLogStream",
                "logs:PutLogEvents"
            ],
            "Resource": "*"
        },
        {
            "Effect": "Allow",
            "Action": [
                "sqs:DeleteMessage",
                "sqs:GetQueueUrl",
                "sqs:ReceiveMessage"
            ],
            "Resource": "*"
        },
        {
            "Effect": "Allow",
            "Action": [
                "s3:ListBucket",
                "s3:PutObject"
            ],
            "Resource": "*"
        }
    ]
}
'''


def build_package():
    build_dir = tempfile.mkdtemp(prefix='lambda_package_')
    install_packages(build_dir, REQUIRED_PACKAGES)
    for f in REQUIRED_FILES:
        shutil.copyfile(
            src=os.path.join(module_path, f),
            dst=os.path.join(build_dir, f)
        )

    out_file = os.path.join(
        tempfile.mkdtemp(prefix='lambda_package_built'),
        'sqs_s3_logger_lambda_{}.zip'.format(datetime.datetime.now().isoformat())
    )
    LOGGER.info('Creating a function package file at {}'.format(out_file))

    archive(build_dir, out_file)
    return out_file


def install_packages(dest, packages):
    for p in packages:
        pip.main(['install', '-t', dest, p])


def archive(src_dir, output_file):
    with zipfile.ZipFile(output_file, 'w', zipfile.ZIP_DEFLATED) as f:
        src_dir_len = len(src_dir)
        for root, _, files in os.walk(src_dir):
            for file in files:
                fn = os.path.join(root, file)
                f.write(fn, fn[src_dir_len+1:])

if __name__ == '__main__':
    build_package()
