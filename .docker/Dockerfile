FROM python:3.7.3

# Copy any files over
COPY entrypoint.sh /entrypoint.sh

# Install redis
RUN apt update -y && \
    apt install -y redis-server

# Install PIP packages
RUN pip install \
    awscli \
    pipenv

# Change permissions
RUN chmod +x /entrypoint.sh

ENTRYPOINT ["/entrypoint.sh"]

VOLUME ["/opt/openbook-api"]

EXPOSE 80 443

CMD ["pipenv", "run", "python", "manage.py", "runserver"]