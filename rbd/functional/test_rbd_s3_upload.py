import argparse
import logging
import os
import sys

import boto3

log = logging.getLogger()

# sys.path.append(os.path.abspath(os.path.join(__file__, "../../../")))

if __name__ == "__main__":

    log.info("Executing prepare rbd image as s3 object")

    parser = argparse.ArgumentParser(description="Prepare rbd image s3 object")
    parser.add_argument("--rgw-node", dest="rgw_node")
    parser.add_argument("--file-name", dest="file_name")
    args = parser.parse_args()
    rgw_node = args.rgw_node

    rgw = boto3.client(
        "s3",
        aws_access_key_id="test_rbd",
        aws_secret_access_key="test_rbd",
        endpoint_url=f"http://{rgw_node}:80",
        use_ssl=False,
    )
    rgw.create_bucket(Bucket="rbd")
    rgw.upload_file(f"{args.file_name}", "rbd", f"{args.file_name.split('.')[0][-2:]}")
