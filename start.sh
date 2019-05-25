#!/bin/bash

# Start Gunicorn processes
echo Starting Gunicorn.
exec gunicorn server3.wsgi:application \
    --bind 0.0.0.0:21720 \
    --workers 3