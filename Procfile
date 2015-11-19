web: gunicorn app:app --log-file=-
celery:  celery -A app.celery worker --loglevel=info
rabbit: rabbitmq-server
