#!/bin/bash
set -eo pipefail

cd /opt/okuna-api

# install pip env deps, run migrations, collect media, start the server
pip install -r requirements.txt

exec $@
