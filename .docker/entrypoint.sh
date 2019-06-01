#!/bin/bash
set -eo pipefail

redis-server &

exec $@