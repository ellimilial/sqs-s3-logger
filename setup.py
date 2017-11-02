from setuptools import setup
from pip.req import parse_requirements
from sqs_s3_logger import __version__


install_reqs = parse_requirements('requirements.txt', session='setup')
reqs = [str(ir.req) for ir in install_reqs]


# TODO package entrypoint correctly
setup(
    name='sqs-s3-logger',
    version=__version__,
    install_require=reqs,
    tests_require=reqs,
    url='https://github.com/ellimilial/sqs-s3-logger',
    download_url='https://github.com/ellimilial/sqs-s3-logger/releases/tag/'.format(__version__),
    author='Mateusz Kaczyński',
    author_email='contact@ellimilial.com',
    description='Store arbitrary messages to Amazon\'s S3 via SQS.',
    keywords=['logging', 'sqs', 's3', 'archive', 'storage']
)
