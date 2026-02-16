#!/usr/bin/env bash
export DJANGO_SETTINGS_MODULE=aar_admin.settings_local
cd app
python manage.py migrate
python manage.py runserver 0.0.0.0:8000
