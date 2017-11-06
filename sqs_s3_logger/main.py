#!/usr/bin/env python

import argparse
from sqs_s3_logger.environment import Environment
from sqs_s3_logger.lambda_function_builder import build_package, ROLE_NAME, ROLE_POLICY


def get_environment(args):
    f_name = args.function if args.function is not None else\
        '{}-to-{}'.format(args.queue, args.bucket)
    return Environment(
        queue_name=args.queue,
        bucket_name=args.bucket,
        function_name=f_name
    )


def create(args):
    env = get_environment(args)
    package_file = build_package()
    role_arn = env.update_role_policy(ROLE_NAME, ROLE_POLICY)
    env.update_function(role_arn, package_file, schedule=args.schedule)


def purge(args):
    env = get_environment(args)
    env.destroy(delete_function=True)


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument('command', nargs='?', default='create',
                        help='create(default) / purge'),
    parser.add_argument('-b', '--bucket', required=True,
                        help='Name of the bucket to drop logs to')
    parser.add_argument('-q', '--queue',  required=True,
                        help='Name of the queue to be used')
    parser.add_argument('-f', '--function',
                        help='Name of the read/push function - will be replaced if exists')
    parser.add_argument('-s', '--schedule', default='rate(1 day)',
                        help='A cron/rate at which the function will execute.')
    args = parser.parse_args()
    if args.command == 'create':
        create(args)
    elif args.command == 'purge':
        purge(args)


if __name__ == '__main__':
    main()
