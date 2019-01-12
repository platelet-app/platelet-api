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