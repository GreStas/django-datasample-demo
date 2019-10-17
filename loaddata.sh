#!/usr/bin/env bash
#source ~/.virtualenvs/django-sql-repos-dev/bin/activate && \
#python manage.py flush && \
#bin/rm_migrations.sh && \
#python manage.py makemigrations && \
#python manage.py migrate && \
python manage.py loaddata example/tests/example_data.json && \
echo Congratulates! Import data success finished!


