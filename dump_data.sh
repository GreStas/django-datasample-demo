#!/usr/bin/env bash
#source ~/.virtualenvs/django-sql-repos-dev/bin/activate && \
python manage.py dumpdata --indent 2 -o example/tests/example_data.json auth example datasamples && \
echo Congratulates! Export data success finished!
