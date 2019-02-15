### Install

`./setup.sh`

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