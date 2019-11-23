FROM python:3.7.3

RUN apt-get -y update && apt-get -y upgrade &&  apt-get install -y ffmpeg

COPY wait-for-it.sh /wait-for-it.sh

# Copy any files over
COPY entrypoint.sh /entrypoint.sh

# Copy any files over
COPY bootstrap_development_data.sh /bootstrap_development_data.sh

# Change permissions
RUN chmod +x /entrypoint.sh
RUN chmod +x /bootstrap_development_data.sh
RUN chmod +x /wait-for-it.sh

ENTRYPOINT ["/entrypoint.sh"]

COPY requirements.txt /requirements.txt

RUN pip install -r /requirements.txt

VOLUME ["/opt/okuna-api"]

EXPOSE 80

CMD ["python", "manage.py", "runserver", "0.0.0.0:80"]
