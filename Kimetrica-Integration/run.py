#!/usr/bin/env python
import subprocess
import argparse
import boto3
import logging
import os

def run(model_name, task_name):
    call = ["luigi", 
            "--module", 
            f"models.{model_name}.tasks",
            f"models.{model_name}.tasks.{task_name}",
            "--local-scheduler"]

    return subprocess.call(call)

def storeResults(bucket, result_name, key):
    result_path = f'/usr/src/app/output/{result_name}'
    logging.info(result_path)

    exists = os.path.isfile(result_path)
    

    if exists:
        s3 = boto3.client('s3')
        s3.upload_file(result_path, bucket, key, ExtraArgs={'ACL':'public-read'})
        logging.info(f'Results stored at : https://s3.amazonaws.com/world-modelers/{key}')
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
    
    logging.basicConfig(level=logging.INFO)

    logging.info(f'Running model: {args.model_name}')
    logging.info(f'Running task: {args.task_name}')

    run = run(args.model_name, args.task_name)

    logging.info('Model run complete')

    run_results = storeResults(args.bucket, args.result_name, args.key)
    
    logging.info(f'Model run: {run_results}')