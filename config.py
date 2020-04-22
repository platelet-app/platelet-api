import os
basedir = os.path.abspath(os.path.dirname(__file__))

class Config:
    SECRET_KEY = os.environ.get('SECRET_KEY') or 'you-will-never-guess'

    SQLALCHEMY_DATABASE_URI = os.environ.get('DATABASE_URL') or \
        'postgresql://localhost/bloodbike_dev'
    SQLALCHEMY_TRACK_MODIFICATIONS = False

    JWT_ACCESS_LIFESPAN = {'minutes': 15}

    JWT_REFRESH_LIFESPAN = {'days': 7}

    DEFAULT_DELETE_TIME = 10

    ELASTICSEARCH_URL = None
    #ELASTICSEARCH_URL = os.environ.get('ELASTICSEARCH_URL') or \
    #    'http://localhost:9200'