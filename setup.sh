#!/bin/bash

read -s -p "Please set a password for the admin user: " pswd

if ! systemctl list-units | grep -q -i postgres; then
    echo "Please install and start the postgresql database server (sudo systemctl start postgresql)"
    exit
else
    echo "Postgres found. Creating database. You may need to provide your sudo password."
fi

if ! systemctl list-units | grep -q -i elasticsearch; then
    echo "Elasticsearch service is not running. Search will not be available. You should edit the elasticsearch url 'http://localhost:9200' in config.py to None if you don't intend to use it."
fi

sudo -u postgres createuser "$(whoami)"
sudo -u postgres createdb -O "$(whoami)" bloodbike_dev
sudo -u postgres createdb -O "$(whoami)" bloodbike_test

python3 -m venv venv

source venv/bin/activate

pip install -r requirements.txt

flask db upgrade

python setup.py $pswd

echo "Completed setup"
