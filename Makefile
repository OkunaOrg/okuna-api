makemessages:
	django-admin makemessages --all

compilemessages_en:
	django-admin compilemessages --locale=en

compilemessages_es:
	django-admin compilemessages --locale=es

build_openbook_api:
	docker-compose build

start_openbook_api:
	docker-compose up

stop_openbook_api:
	docker-compose stop

clean_openbook-api:
	docker-compose down -v --rmi local

logs_openbook-api:
	docker-compose logs -f

runserver:
	python manage.py runserver

runserver_public:
	python manage.py runserver 0.0.0.0:8000