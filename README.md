## Install
##### Install needed packages:
`sudo apt install postgresql postgresql-server-dev-10 python3-virtualenv python3-dev`

##### Install elasticsearch:
`sudo apt install apt-transport-https`

`wget -qO - https://artifacts.elastic.co/GPG-KEY-elasticsearch | sudo apt-key add -`

`sudo add-apt-repository "deb https://artifacts.elastic.co/packages/7.x/apt stable main"`

`sudo apt update`

`sudo apt install elasticsearch`

##### Configure postgresql:
`sudo nano /etc/postgresql/10/main/pg_hba.conf`

Edit the line:
```
# IPv4 local connections:
host    all             all             127.0.0.1/32            md5
```
to:
```
# IPv4 local connections:
host    all             all             127.0.0.1/32            trust
```
**This will allow unauthenticated connections on localhost**

##### Start the services:
`sudo systemctl start postgresql && sudo systemctl start elasticsearch`

##### Run the setup script:
`./setup.sh`

Optionally input a json file with premade data to insert into the database.

`./setup.sh dev_data.json`


## Run

### API

##### Make sure the services are active:
`sudo systemctl start postgresql && sudo systemctl start elasticsearch`

##### Source the environment:
`source venv/bin/activate`

##### Start the server:
`flask run`

##### Run the tests (in another terminal):
`source venv/bin/activate`

`pytest --disable-pytest-warnings`

##### Visit root to see the swagger API documentation:
http://localhost:5000

### React

cd into the react_app directory.

`cd react_app`

Install packages.

`npm install`

Start the React development server.

`npm start`

It'll likely load up the page in your default browser. If not, navigate to http://localhost:3000

## Development
##### Libraries
When you add a new library with `pip install` run:  
`pip freeze > requirements.txt`

##### Database changes
When you make changes that require database migrations run:  
`flask db migrate -m "message"`
