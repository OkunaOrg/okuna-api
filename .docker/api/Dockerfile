FROM python:3.7.3

RUN apt-get -y update && apt-get -y upgrade &&  apt-get install -y ffmpeg

# Copy any files over
COPY entrypoint.sh /entrypoint.sh

# Change permissions
RUN chmod +x /entrypoint.sh

ENTRYPOINT ["/entrypoint.sh"]

COPY requirements.txt /requirements.txt

RUN pip install -r /requirements.txt

VOLUME ["/opt/okuna-api"]

EXPOSE 80

CMD ["python", "manage.py", "runserver", "0.0.0.0:80"]
