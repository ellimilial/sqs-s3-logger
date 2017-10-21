from setuptools import setup
from pip.req import parse_requirements

exec(open('sqs_s3_logger/version.py').read())

install_reqs = parse_requirements('requirements.txt', session='setup')
reqs = [str(ir.req) for ir in install_reqs]


setup(
    name='sqs-s3-logger',
    version=__version__,
    install_require=reqs,
    tests_require=reqs,
    description='Logging to Amazon\'s S3 via SQS.',
)
