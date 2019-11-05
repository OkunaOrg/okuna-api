#!/bin/bash
set -eo pipefail

cd /opt/okuna-api

# install pip env deps, run migrations, collect media, start the server
pip install -r requirements.txt
python manage.py migrate
echo "yes" | python manage.py collectmedia
python manage.py loaddata circles.json emoji-groups.json emojis.json badges.json categories.json languages.json

exec $@
