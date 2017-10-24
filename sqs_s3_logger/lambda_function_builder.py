import os
import zipfile
import pip
import shutil
import tempfile
import datetime

module_path = os.path.dirname(os.path.realpath(__file__))

REQUIRED_PACKAGES = ['boto3==1.4.7.']
REQUIRED_FILES = ['lambda_function.py']


def build():
    build_dir = tempfile.mkdtemp(prefix='lambda_package_')
    install_packages(build_dir, REQUIRED_PACKAGES)
    for f in REQUIRED_FILES:
        shutil.copyfile(
            src=os.path.join(module_path, f),
            dst=os.path.join(build_dir, f)
        )
    out_file = 'sqs_s3_logger_lambda_{}.zip'.format(
        datetime.datetime.now().isoformat())
    archive(build_dir, out_file)
    return out_file


def install_packages(dest, packages):
    for p in packages:
        pip.main(['install', '-t', dest, p])


# def archive(srcs, dest, filename='function.zip'):
#     output_path = os.path.join(dest, filename)
#     with zipfile.ZipFile(output_path, 'w', zipfile.ZIP_DEFLATED) as f:
#         for s in srcs:
#             f.write(s)


def archive(src_dir, output_file):
    with zipfile.ZipFile(output_file, 'w', zipfile.ZIP_DEFLATED) as f:
        for root, _, files in os.walk(src_dir):
            for file in files:
                f.write(os.path.join(root, file))

if __name__ == '__main__':
    build()
