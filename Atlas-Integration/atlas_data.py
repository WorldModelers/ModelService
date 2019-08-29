import boto3
import os
import argparse

profile = "wmuser"
bucket_name = "world-modelers"

session = boto3.Session(profile_name=profile)

s3 = session.resource("s3")
s3_client = session.client("s3")

bucket = s3.Bucket(bucket_name)

if __name__ == "__main__":
    parser = argparse.ArgumentParser(description='Atlas.a Data Downloader')
    parser.add_argument('output_directory', type=str,
                        help='Where should Atlas.ai data be downloaded?')
    parser.add_argument('key_file', type=str,
                        help='A text file containing the S3 keys for the Atlas files.')

    args = parser.parse_args()
    output_directory = args.output_directory
    key_file = args.key_file

    keys = [i.split('\n')[0] for i in open(key_file).readlines()]

    # make Atlas.ai data directory
    if not os.path.exists(output_directory):
        os.mkdir(output_directory)

    for k in keys:
        file_name = k.split('/')[-1]
        bucket.download_file(k, f"{output_directory}/{file_name}")
