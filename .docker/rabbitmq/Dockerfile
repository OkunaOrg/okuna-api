FROM rabbitmq:3.9-management

ENV RABBITMQ_PID_FILE /var/lib/rabbitmq/mnesia/rabbitmq

COPY entrypoint.sh /entrypoint.sh
RUN chmod +x /entrypoint.sh

EXPOSE 15672
ENTRYPOINT ["/entrypoint.sh"]
