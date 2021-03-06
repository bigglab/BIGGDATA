import os
import sys
import logging 
from kombu import Exchange, Queue
#from kombu.common import Broadcast







CELERY_SEND_TASK_ERROR_EMAILS = True
SERVER_EMAIL = 'celery@example.org'
ADMINS = [
        ('BIGG Webmaster', 'russdurrett@utexas.edu')
]
EMAIL_USE_TLS = True
EMAIL_PORT = 587
EMAIL_TIMEOUT = 10
EMAIL_HOST = 'smtp.gmail.com'
EMAIL_HOST_USER = 'biggdata.io@gmail.com'
EMAIL_HOST_PASSWORD = 'rag1rag2'



BROKER_URL = 'amqp://guest:guest@localhost:5672//'
CELERY_RESULT_BACKEND = 'rpc://'
CELERY_RESULT_PERSISTENT = False
# CELERY_TASK_RESULT_EXPIRES = 3600 # defaults to one day

CELERYD_PREFETCH_MULTIPLIER = 1  #limit tasks per process to 1 at a time

CELERY_ACCEPT_CONTENT = ['json']
CELERY_TASK_SERIALIZER = 'json'
CELERY_RESULT_SERIALIZER = 'json'
CELERY_ACCEPT_CONTENT=['json']
CELERY_TIMEZONE = 'America/Chicago'
CELERY_ENABLE_UTC = True


default_exchange = Exchange('default', type='direct')

CELERY_DEFAULT_QUEUE = 'default'
CELERY_QUEUES = (
  Queue('default', default_exchange, routing_key='default'),
)

#
# class TaskRouter(object):
#
#     def route_for_task(self, task, args=None, kwargs=None):
# 			print 'figuring out how to parse: {}'.format(task.__dict__)
# 			if 'queue' in kwargs.keys():
# 				queue = kwargs['queue']
# 				return {'exchange': queue,
# 								'exchange_type': 'direct',
# 								'routing_key': queue}
# 			# else:
# 			# 	return {'exchange': 'default'
# 			# 					'exchange_type': 'default'
# 			# 					'routing_key': 'default'
# 			# 	}
# 			# CELERYD_LOG_FILE = "/path/to/file.log"
# 			return None
#
# CELERY_ROUTES = (
# 	TaskRouter(),
# )

# Configure the Celery Logger
# CELERYD_LOG_FORMAT = "[{}: {} {}] {}".format(asctime, levelname, processName, message)

# [%(asctime)s: %(levelname)s/%(processName)s] %(message)s
# Default is [%(asctime)s: %(levelname)s/%(processName)s] %(message)s

# CELERYD_TASK_LOG_FORMAT
# Default is: [%(asctime)s: %(levelname)s/%(processName)s] [%(task_name)s(%(task_id)s)] %(message)s


CELERYD_TASK_LOG_FORMAT= "[%(processName)s  %(funcName)s %(levelname)s] [%(task_name)s(%(task_id)s)] %(message)s"


#CELERY_REDIRECT_STDOUTS
# If enabled stdout and stderr will be redirected to the current logger.
# Enabled by default. Used by celery worker and celery beat.
CELERY_REDIRECT_STDOUTS_LEVEL = 'INFO'

# if 'RABBITMQ_BIGWIG_URL' in os.environ.keys(): # On Heroku = Sender Queue: 
# 	BROKER_URL = os.environ['RABBITMQ_BIGWIG_TX_URL']
# if 'LESSOPEN' in os.environ.keys(): # AWS Processor = Reciever RX Queue: 
# 	BROKER_URL="amqp://Sq_rhK2z:sGYEo2JbO0z3JpXh8YJq58NuMbvbM2Su@leaping-pipkin-62.bigwig.lshift.net:10919/thzgJ-IWDfsZ"
# else: # Web Server Fired Anywhere Else: Sender Queue 
# 	BROKER_URL = 'amqp://Sq_rhK2z:sGYEo2JbO0z3JpXh8YJq58NuMbvbM2Su@leaping-pipkin-62.bigwig.lshift.net:10918/thzgJ-IWDfsZ'
