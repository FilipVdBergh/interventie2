#!/bin/sh
gunicorn app:app --workers 5 --timeout 600 --bind 0.0.0.0:443 
# --worker-class gevent