#!/bin/bash
set -eo pipefail

# Create Okuna user for RabbitMQ
( rabbitmqctl wait --timeout 60 /var/lib/rabbitmq/mnesia/rabbitmq; \
rabbitmqctl add_user $RABBITMQ_USERNAME $RABBITMQ_PASSWORD 2>/dev/null; \
rabbitmqctl add_vhost okuna; \
rabbitmqctl set_permissions -p okuna $RABBITMQ_USERNAME ".*" ".*" ".*"; \
echo "Initial okuna user created successfully. You may authenticate now.") &

rabbitmq-server $@
