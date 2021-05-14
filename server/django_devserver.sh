#! /bin/bash
python /sharky/manage.py migrate --noinput
python /sharky/manage.py runserver 0.0.0.0:8000
