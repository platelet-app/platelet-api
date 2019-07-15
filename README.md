### Install

Install postgresql and elasticsearch.

`sudo apt install postgresql elasticsearch postgresql-server-dev-9.5`

`sudo nano /etc/postgresql/9.5/main/pg_hba.conf`

Edit the line:

`# IPv4 local connections:`

`host    all             all             127.0.0.1/32            md5`

to:

`# IPv4 local connections:`

`host    all             all             127.0.0.1/32            trust`

##### This will allow unauthenticated connections on localhost

`sudo systemctl start postgresql && sudo systemctl start elasticsearch`

Run the setup script:

`./setup.sh`

### Run
Source the environment:

`source venv/bin/activate`

Start the server:

`flask run`

Run the tests (in another terminal):

`source venv/bin/activate`

`pytest --disable-pytest-warnings`

Visit root to see swagger documentation:

http://localhost:5000/

### Development
##### Libraries
When you add a new library with `pip install` run:

`pip freeze > requirements.txt`

##### Database changes
When you make changes that require database migrations run:

`flask db migrate -m "message"`

