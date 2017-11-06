from setuptools import setup
from pip.req import parse_requirements
from sqs_s3_logger import __version__


install_reqs = parse_requirements('requirements.txt', session='setup')
reqs = [str(ir.req) for ir in install_reqs]


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
    description='Store arbitrary messages to Amazon\'s S3 via SQS.',
    keywords='logging sqs s3 archive storage'

)
