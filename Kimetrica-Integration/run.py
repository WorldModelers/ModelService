#!/usr/bin/env python
import subprocess
import argparse
import boto3
import logging

logger = logging.getLogger()
logger.setLevel(logging.INFO)

def run(model_name, task_name):
    call = ["luigi", 
            "--module", 
            f"models.{model_name}.tasks",
            f"models.{model_name}.tasks.{task_name}",
            "--local-scheduler"]

    subprocess.call(call)

def storeResults(bucket, result_name, key):
   result_path = f'/usr/src/app/output/{result_name}'
   exists = os.path.isfile(result_path)

   if exists:
       s3 = boto3.client('s3')
       s3.meta.client.upload_file(result_path, bucket, key)
       return "SUCCESS"
    else:
        return "FAIL"

if __name__ == "__main__":
    parser = argparse.ArgumentParser()
    parser.add_argument("--bucket", help="S3 Bucket to store results")
    parser.add_argument("--model_name", help="Kimetrica model name")
    parser.add_argument("--task_name", help="Kimetrica task name")
    parser.add_argument("--result_name", help="Expected result file name")
    parser.add_argument("--key", help="Key to store file on S3")
    args = parser.parse_args()

    run(args.model_name, args.task_name)

    run_results = storeResults(args.bucket, args.result_name, args.key)
    
    logger.info(f'Model run: {run_results}')