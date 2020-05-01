"""Entrypoint for spark-submit. Loaded by EMR from S3 on step execution.

Copyright 2020 Daniel Cortez Stevenson

Licensed under the Apache License, Version 2.0 (the "License");
you may not use this file except in compliance with the License.
You may obtain a copy of the License at

    https://www.apache.org/licenses/LICENSE-2.0

Unless required by applicable law or agreed to in writing, software
distributed under the License is distributed on an "AS IS" BASIS,
WITHOUT WARRANTIES OR CONDITIONS OF ANY KIND, either express or implied.
See the License for the specific language governing permissions and
limitations under the License.
"""
import argparse
import datetime
import importlib
import logging
import os


logger = logging.getLogger(__name__)


try:
    from pyspark.sql import SparkSession
    spark = SparkSession \
        .builder \
        .appName(__name__) \
        .master('local[*]') \
        .enableHiveSupport() \
        .getOrCreate()
except ImportError:
    msg = 'Install pyspark to your Python environment to test locally.'
    logger.error(msg)


def main():
    parser = argparse.ArgumentParser(description='Run a PySpark job via spark-submit.')
    parser.add_argument('--job-name', type=str, required=True, dest='job_name',
                        help='The name of the job module you want to run. (ex: `--job-name example_one` will run main() in job.example_one module)')
    parser.add_argument('--job-kwargs', nargs='*',
                        help='Extra keyword-arguments to send to main() of the job module (ex: `--job-kwargs bat=baz foo=bar`')
    args = parser.parse_args()

    logging.info('Called with arguments:', args)

    os.environ.update({
        'PYSPARK_JOB_ARGS': ' '.join(args.job_kwargs) if args.job_kwargs else ''
    })
    logging.info(f'OS environment:\n{os.environ}')

    job_kwargs = dict()
    if args.job_kwargs:
        for kwarg in args.job_kwargs:
            kw, arg = kwarg.split('=', 1)
            job_kwargs[kw] = arg
    logger.info(f'event: submit job "{args.job_name}" with kwargs: {job_kwargs}')

    try:
        job_module = importlib.import_module(f'pyogo.job.{args.job_name}')
        logger.info(f'Imported {args.job_name} sucessfully.')
    except ImportError:
        logger.error('______________ Abrupt Exit ______________')
        logger.error(f'Failed to import {args.job_name}. Exiting.')
        raise

    start = datetime.datetime.now()
    try:
        job_module.main(**job_kwargs)
    except Exception:
        logger.error('______________ Abrupt Exit ______________')
        raise
    finally:
        end = datetime.datetime.now()
        duration = end - start
        execution_mins = round(duration.seconds / 60., 2)
        logger.info(f'Execution of job {args.job_name} took {execution_mins} minutes')
    logger.info(f'Finished running pyspark_entrypoint for job {args.job_name}')


if __name__ == '__main__':
    main()