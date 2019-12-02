FROM python:3.7.3

RUN apt-get -y update && apt-get -y upgrade &&  apt-get install -y ffmpeg  && apt-get install -y supervisor

COPY wait-for-it.sh /wait-for-it.sh

# Copy any files over
COPY entrypoint.sh /entrypoint.sh

COPY supervisord.conf /etc/supervisor/conf.d/supervisord.conf

# Change permissions
RUN chmod +x /entrypoint.sh
RUN chmod +x /wait-for-it.sh

ENTRYPOINT ["/entrypoint.sh"]

COPY requirements.txt /requirements.txt

RUN pip install -r /requirements.txt

VOLUME ["/opt/okuna-api"]

CMD ["/usr/bin/supervisord", "-c", "/etc/supervisor/conf.d/supervisord.conf"]