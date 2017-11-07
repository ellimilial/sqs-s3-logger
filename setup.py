import os
from setuptools import setup
from pip.req import parse_requirements
from sqs_s3_logger import __version__


install_reqs = parse_requirements('requirements.txt', session='setup')
reqs = [str(ir.req) for ir in install_reqs]
curr_dir = os.path.abspath(os.path.dirname(__file__))
with open(os.path.join(curr_dir, 'README.rst'), encoding='utf-8') as f:
    long_description = f.read()

setup(
    name='sqs-s3-logger',
    version=__version__,
    install_requires=reqs,
    tests_require=reqs,
    packages=['sqs_s3_logger'],
    entry_points={
        'console_scripts': ['sqs-s3-logger=sqs_s3_logger.main:main'],
    },
    url='https://github.com/ellimilial/sqs-s3-logger',
    author='Mateusz Kaczyński',
    author_email='contact@ellimilial.com',
    description='Automated serverless logging to S3 via SQS.',
    long_description=long_description,
    keywords='logging sqs s3 archive storage'
)
