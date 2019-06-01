#!/bin/bash
set -eo pipefail

# start the redis server
redis-server &

cd /opt/openbook-api

# install pip env deps, run migrations, collect media, start the server
pipenv install
pipenv run python manage.py migrate
echo "yes" | pipenv run python manage.py collectmedia
pipenv run python manage.py loaddata circles.json emoji-groups.json emojis.json badges.json categories.json

exec $@