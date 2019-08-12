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

load_fixtures: load_circles_fixtures load_emoji_fixtures load_badges_fixtures load_categories_fixtures load_languages_fixtures

load_circles_fixtures:
	python manage.py loaddata circles.json

load_emoji_fixtures:
	python manage.py loaddata emoji-groups.json
	python manage.py loaddata emojis.json

load_badges_fixtures:
	python manage.py loaddata badges.json

load_categories_fixtures:
	python manage.py loaddata categories.json
	python manage.py loaddata moderation_categories.json

load_languages_fixtures:
	python manage.py loaddata languages.json
