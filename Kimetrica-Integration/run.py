#!/usr/bin/env python
import shutil
import subprocess
import argparse
import boto3
import logging
import os
import glob

def run(model_name, task_name, params):
    call = ["luigi", 
            "--module", 
            f"models.{model_name}.tasks",
            f"models.{model_name}.tasks.{task_name}"]

    # Add model specific tunable params to command line call
    for p in params:
         call.append("--" + p)
         call.append(params[p])

    call.append("--local-scheduler")

    return subprocess.call(call)

def storeResults(model_name, bucket, result_name, key):
    if model_name == "malnutrition_model":
        # we need to zip the results since there will be one .tiff per month covered
        # by the malnutrition model
        result_path = glob.glob(f'/usr/src/app/output/{result_name}')[0]
        if not os.path.exists(f'/usr/src/app/output/results/{model_name}'):
            os.makedirs(f'/usr/src/app/output/results/{model_name}')
        shutil.copy(result_path, f'/usr/src/app/output/{key}')
        logging.info(f"{model_name} output path is: {result_path}")

    elif model_name == "population_model":
        result_path = glob.glob(f'/usr/src/app/output/{result_name}')[0]
        if not os.path.exists(f'/usr/src/app/output/results/{model_name}'):
            os.makedirs(f'/usr/src/app/output/results/{model_name}')
        shutil.copy(result_path, f'/usr/src/app/output/{key}')
        logging.info(f"{model_name} output path is: {result_path}")

    exists = os.path.isfile(result_path)

    if exists:
        session = boto3.Session()
        s3 = session.client("s3")
        s3.upload_file(result_path, bucket, key, ExtraArgs={'ACL':'public-read'})
        logging.info(f'Results stored at : https://s3.amazonaws.com/world-modelers/{key}')
        # Remove all output for now and handle caching at the service level.  Look into this again later.
        shutil.rmtree('/usr/src/app/output/intermediate')
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
    parser.add_argument("--params", help="Model parameters")
    args = parser.parse_args()

    # Sort of sloppy but basically read model specific tunable params and values and form a dict
    param_dict = {}
    if args.params:
        for i,k in enumerate(args.params.split("|")):
            if i % 2 == 0:
                param_dict[k] = args.params.split("|")[i+1]
    
    logging.basicConfig(level=logging.INFO)

    logging.info(f'Running model: {args.model_name}')
    logging.info(f'Running task: {args.task_name}')

    run = run(args.model_name, args.task_name, param_dict)
    run_results = storeResults(args.model_name, args.bucket, args.result_name, args.key)
    logging.info('Model run complete')
    logging.info(f'Model run: {run_results}')
