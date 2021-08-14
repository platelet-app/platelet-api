# syntax=docker/dockerfile:1

FROM python:3.9.6

WORKDIR /app

COPY requirements.txt requirements.txt

RUN pip3 install -r requirements.txt
RUN mkdir /tmp/profilepics

COPY . .
CMD [ "python3", "app.py", "--host=0.0.0.0" ]
