#!/bin/bash

if [[ $1 ]];
then
  if [[ -e $1 ]];
  then
    echo "Data found and exists."
  else
    echo "$1 does not exist."
    exit 1
  fi
fi

read -s -p "Please set a password for the admin user: " pswd

if [[ $2 -eq "db_local" ]];
then
  if ! pg_isready -h "localhost";
  then
    echo "Could not connect to local database. Please make sure postgresql is running."
    exit 1
  else
    sudo -u postgres createuser "$(whoami)"
    sudo -u postgres createdb -O "$(whoami)" platelet_dev
    sudo -u postgres createdb -O "$(whoami)" platelet_test
  fi
    
else
  echo ""
  db_array=(${SQLALCHEMY_DATABASE_URI//\//})
  db_url_name=$(cut -d"@" -f2 <<< $SQLALCHEMY_DATABASE_URI)
  db_host="$(cut -d'/' -f1 <<< $db_url_name)"
  db_name="$(cut -d'/' -f2 <<< $db_url_name)"
  db_first_half="$(cut -d"@" -f1 <<< $SQLALCHEMY_DATABASE_URI)"
  db_user_pass="${db_first_half#*//}"
  db_username="$(cut -d":" -f1 <<< $db_user_pass)"
  
  echo "Found database $db_name on host $db_host with username $db_username"
  
  if ! pg_isready -d $db_name -h $db_host -p 5432 -U $db_username; then
    echo "Could not connect to provided database. Please make sure postgresql is running."
    exit 1
  else
    echo "Postgres found and ready."
  fi
fi

el_host_port=${ELASTICSEARCH_URL#*//}
if [[ -z $ELASTICSEARCH_URL ]];
then
  echo "Elasticsearch not configured, skipping"
else
  el_host="$(cut -d":" -f1 <<< $el_host_port)"
  el_port="$(cut -d":" -f2 <<< $el_host_port)"
  if ! nc -vz $el_host $el_port; then
    echo "Elasticsearch service is not running or not configured. Search will not be available."
  fi
fi


python3 -m venv venv

source venv/bin/activate

pip install -r requirements.txt

if [[ $2 -eq "db_local" ]]
then
  SQLALCHEMY_DATABASE_URI=postgresql://localhost/platelet_dev
  echo "Use export SQLALCHEMY_DATABASE_URI=$SQLALCHEMY_DATABASE_URI to use the local database"
fi

flask db upgrade

python setup.py $pswd $1

echo "Completed setup"
