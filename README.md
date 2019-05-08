### Install

Install postgresql and start the service.

`./setup.sh`

Add an admin user:

`source venv/bin/activate`

`from app import models, db`

`import datetime`

`date = datetime.datetime.strptime('01/01/1980', '%d/%m/%Y').date()`

`user = models.User(username="admin", email="asdf@asdf.com", password="somepassword", name="Someone", dob=date, roles="admin,coordinator,rider")`

`db.session.add(user)`

`db.session.commit()`

### Run
Source the environment:

`source venv/bin/activate`

Start the server:

`flask run`

Run the tests (in another terminal):

`source venv/bin/activate`

`pytest --disable-pytest-warnings`

### Development
##### Libraries
When you add a new library with `pip install` run:

`pip freeze > requirements.txt`

##### Database changes
When you make changes that require database migrations run:

`flask db migrate -m "message"`
