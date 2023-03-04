FROM python:3.9-slim

WORKDIR /app

RUN apt-get update && apt-get install -y build-essential && apt clean

COPY requirements.txt requirements.txt

RUN pip3 install -r requirements.txt gunicorn

COPY . .
COPY keyserv/config.docker.py keyserv/config.py

ENV FLASK_APP=keyserver.py
ENV SECRET_KEY=this_key_server_is_secure

RUN apt-get update && apt-get install -y nginx && apt-get clean
COPY nginx.conf /etc/nginx/nginx.conf
COPY entrypoint.sh /app/entrypoint.sh
RUN chmod +x /app/entrypoint.sh

CMD ["/app/entrypoint.sh"]
