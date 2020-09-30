from app import app
from app.cloud import AwsStore


def get_cloud_store(bucket_name):
    if app.config['CLOUD_PLATFORM'] == "aws":
        return AwsStore(bucket_name=bucket_name)
