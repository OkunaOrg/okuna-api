#!/bin/bash
set -eo pipefail

redis-server &

cd /opt/openbook-api

pipenv install
pipenv run python manage.py migrate
echo "yes" | pipenv run python manage.py collectmedia
pipenv run python manage.py loaddata circles.json emoji-groups.json emojis.json badges.json categories.json

pipenv run python manage.py runserver 0.0.0.0:80