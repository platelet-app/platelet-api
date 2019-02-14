### Install
Create a virtual environment:  
`python3 -m venv venv`

Activate it:  
`. venv/bin/activate`

Install requirements:  
`pip install -r requirements.txt`

Set up database:  
`flask db upgrade`

### Run
Start the server:  
`flask run`

Run the tests:  
`pytest --disable-pytest-warnings`

### Development
##### Libraries
When you add a new library with `pip install` run:  
`pip freeze > requirements.txt`

##### Database changes
When you make changes that require database migrations run:  
`flask db migrate -m "message"`
