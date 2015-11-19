import os 
import sys 

if 'RABBITMQ_BIGWIG_URL' in os.environ.keys(): 
	BROKER_URL = os.environ('RABBITMQ_BIGWIG_URL')
else: 
	BROKER_URL = 'amqp://'


CELERY_RESULT_BACKEND = 'rpc://'

CELERY_TASK_SERIALIZER = 'json'
CELERY_RESULT_SERIALIZER = 'json'
CELERY_ACCEPT_CONTENT=['json']
CELERY_TIMEZONE = 'America/Chicago'
CELERY_ENABLE_UTC = True



