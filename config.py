import os
basedir = os.path.abspath(os.path.dirname(__file__))


class Config:
    SECRET_KEY = os.environ.get("SECRET_KEY") or "some-key"

    SQLALCHEMY_DATABASE_URI = os.environ.get("DATABASE_URL") or \
        "postgresql://localhost/bloodbike_dev"
    SQLALCHEMY_TRACK_MODIFICATIONS = False

    CLOUD_PLATFORM = os.environ.get("CLOUD_PLATFORM") or "aws"
    AWS_ENDPOINT = os.environ.get("AWS_ENDPOINT") or None
    AWS_ACCESS_KEY_ID = os.environ.get("AWS_ACCESS_KEY_ID") or ""
    AWS_SECRET_ACCESS_KEY = os.environ.get("AWS_SECRET_ACCESS_KEY") or ""
    AWS_DEFAULT_REGION = os.environ.get("AWS_DEFAULT_REGION") or ""
    CLOUD_PROFILE_PICTURE_STORE_NAME = os.environ.get("CLOUD_PROFILE_PICTURE_STORE_NAME") or ""
    PROFILE_PROCESSING_DIRECTORY = os.environ.get("PROFILE_PROCESSING_DIRECTORY") or ""
    DEFAULT_PROFILE_PICTURE_URL = os.environ.get("DEFAULT_PROFILE_PICTURE_URL") or ""

    JWT_ACCESS_LIFESPAN = {"days": 15}

    JWT_REFRESH_LIFESPAN = {"days": 7}

    DEFAULT_DELETE_TIME = 10

    ELASTICSEARCH_URL = None
    #ELASTICSEARCH_URL = os.environ.get("ELASTICSEARCH_URL") or \
    #    "http://localhost:9200"