FROM python:3.7.3

RUN apt-get -y update && apt-get -y upgrade &&  apt-get install -y ffmpeg && apt-get install -y supervisor

RUN mkdir -p /var/log/supervisor

VOLUME ["/opt/okuna-api"]

# Copy any files over
COPY entrypoint.sh /entrypoint.sh
COPY supervisord.conf /etc/supervisor/conf.d/supervisord.conf

# Change permissions
RUN chmod +x /entrypoint.sh

ENTRYPOINT ["/entrypoint.sh"]

CMD ["/usr/bin/supervisord", "-c", "/etc/supervisor/conf.d/supervisord.conf"]