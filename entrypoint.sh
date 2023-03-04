#!/bin/sh
set -x

flask initdb
flask create-user admin devpassword

# start Nginx
nginx

# Start Gunicorn with 2 Uvicorn workers
gunicorn -w 2 -b 0.0.0.0:8000 keyserver:app
