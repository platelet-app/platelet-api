import os
import time

import boto3
import logging
import boto.ec2
from app import app


class AwsStore:
    def __init__(self, bucket_name, max_retries=10):
        self.aws_region = app.config['AWS_DEFAULT_REGION']
        self.aws_access_key_id = app.config['AWS_ACCESS_KEY_ID']
        self.aws_secret_access_key = app.config['AWS_SECRET_ACCESS_KEY']
        self.bucket_name = bucket_name
        self.max_retries = max_retries
        self.endpoint = app.config['AWS_ENDPOINT']

        self.s3 = boto3.Session(aws_access_key_id=self.aws_access_key_id,
                                aws_secret_access_key=self.aws_secret_access_key).resource('s3', endpoint_url=self.endpoint)
        self.s3_client = boto3.client("s3")
        self.bucket_obj = self.s3.Bucket(name=bucket_name)

    def get_object(self, key):
        return self.bucket_obj.Object(key)

    def delete(self, key):
        file = self.get_object(key)
        file.delete()
        logging.info("[AWS]: Deleted key {}.".format(key))

    def upload(self, file_path, target_key, delete_original=False):
        if not os.path.exists(file_path):
            raise IOError("File {} does not exist.".format(file_path))

        for i in range(self.max_retries):
            try:
                self.get_object(target_key).upload_file(file_path)
            except Exception as e:
                if i == self.max_retries:
                    raise
                logging.exception("[AWS]: Failed to upload {}. Reason: {}".format(target_key, e))
                time.sleep(5)
                continue
            break

        if delete_original:
            if os.path.exists(file_path):
                try:
                    os.remove(file_path)
                except Exception as e:
                    logging.exception("[AWS]: Could not delete file {}. Reason:".format(file_path, e))
            else:
                logging.warning("[AWS]: File {} no longer exists and cannot be deleted.".format(file_path))

    def get_presigned_url(self, key):
        return self.s3_client.generate_presigned_url("get_object",
                                              Params={'Bucket': self.bucket_name,
                                                      'Key': key},
                                              ExpiresIn=3600)
