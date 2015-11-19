import os
import sys 

if 'RABBITMQ_BIGWIG_URL' in os.environ.keys(): # On Heroku = Sender Queue: 
	BROKER_URL = os.environ['RABBITMQ_BIGWIG_TX_URL']
if 'LESSOPEN' in os.environ.keys(): # AWS Processor = Reciever RX Queue: 
	BROKER_URL="amqp://Sq_rhK2z:sGYEo2JbO0z3JpXh8YJq58NuMbvbM2Su@leaping-pipkin-62.bigwig.lshift.net:10919/thzgJ-IWDfsZ"
else: # Web Server Fired Anywhere Else: Sender Queue 
	BROKER_URL = 'amqp://Sq_rhK2z:sGYEo2JbO0z3JpXh8YJq58NuMbvbM2Su@leaping-pipkin-62.bigwig.lshift.net:10918/thzgJ-IWDfsZ'


CELERY_TASK_SERIALIZER = 'json'
CELERY_RESULT_SERIALIZER = 'json'
CELERY_ACCEPT_CONTENT=['json']
CELERY_TIMEZONE = 'America/Chicago'
CELERY_ENABLE_UTC = True

CELERY_RESULT_BACKEND = 'rpc'
CELERY_RESULT_PERSISTENT = True

