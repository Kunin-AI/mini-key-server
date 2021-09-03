# syntax=docker/dockerfile:1

FROM python:3.9-slim

WORKDIR /app

RUN apt-get update && apt-get install -y build-essential && apt clean

COPY requirements.txt requirements.txt

RUN pip3 install -r requirements.txt

COPY . .

ENV FLASK_APP=keyserver.py

ENTRYPOINT /app/entrypoint.sh

CMD ["python3", "-m" , "flask", "run", "--host=0.0.0.0"]
