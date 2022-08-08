# Проект: Yatube Cоциальная сеть 

![example workflow](https://github.com/aVeter77/hw05_final/actions/workflows/main.yml/badge.svg)

Социальная сеть с возможность создать учетную запись, публиковать записи, подписываться на любимых авторов, комментировать и отмечать понравившиеся записи.

Пример работы приложения [http://yatube.aveter77.site/](http://yatube.aveter77.site/)

Образ на [Dockerhub](https://hub.docker.com/r/aveter77/yatube/tags)

## Технологии
- [Python 3.7](https://www.python.org/)
- [Django 2.2.16](https://www.djangoproject.com/)
- [PostgreSQL 13.0](https://www.postgresql.org/)
- [gunicorn 20.0.4](https://pypi.org/project/)
- [nginx 1.21.3](https://nginx.org/ru/)
- [Docker 20.10.17](https://www.docker.com/)
- [Docker Compose 2.9](https://docs.docker.com/compose/)

## Запуск

Установите переменные среды, как в `.env.example`.
### Docker
```
cd infra/
docker-compose up -d
```
После запуска выполните команды:
```
docker-compose exec web python manage.py migrate
docker-compose exec web python manage.py createsuperuser
docker-compose exec web python manage.py collectstatic --no-input 
```

## Заполнение базы начальными данными
```
cd infra/
cat fixtures.json | docker-compose exec -T web python manage.py loaddata --format=json -
docker-compose cp media_fixtures/cache/ web:/app/media/
docker-compose cp media_fixtures/posts/ web:/app/media/
```

## Автор
Александр Николаев

## Лицензия
MIT
