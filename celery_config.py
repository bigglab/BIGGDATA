import os
import sys
import logging 
from kombu import Exchange, Queue
#from kombu.common import Broadcast

# @Dave - to see all configuration options, see http://docs.celeryproject.org/en/latest/configuration.html


CELERY_TASK_SERIALIZER = 'json'
CELERY_RESULT_SERIALIZER = 'json'
CELERY_ACCEPT_CONTENT=['json']
CELERY_TIMEZONE = 'America/Chicago'
CELERY_ENABLE_UTC = True

CELERY_RESULT_BACKEND = 'rpc'
CELERY_RESULT_PERSISTENT = True

default_exchange = Exchange('default', type='direct')
ut_exchange = Exchange('ut', type='direct')
aws_exchange = Exchange('aws', type='direct')
dev_exchange = Exchange('dev', type='direct')


CELERY_DEFAULT_QUEUE = 'default'
CELERY_QUEUES = (
	#Broadcast('broadcast'),
  Queue('default', default_exchange, routing_key='default'),
  Queue('ut', ut_exchange, routing_key='ut'),
  Queue('aws', aws_exchange, routing_key='aws'),
  Queue('dev', dev_exchange, routing_key='dev'),

)


class TaskRouter(object):

    def route_for_task(self, task, args=None, kwargs=None):
			print 'figuring out how to parse: {}'.format(task.__dict__)
			if 'queue' in kwargs.keys(): 
				queue = kwargs['queue'] 
				return {'exchange': queue,
								'exchange_type': 'direct',
								'routing_key': queue}
			# else: 
			# 	return {'exchange': 'default'
			# 					'exchange_type': 'default'
			# 					'routing_key': 'default'
			# 	}
			# CELERYD_LOG_FILE = "/path/to/file.log"
			return None

CELERY_ROUTES = (
	TaskRouter(), 
)

# Configure the Celery Logger
# CELERYD_LOG_FORMAT
# Default is [%(asctime)s: %(levelname)s/%(processName)s] %(message)s

# CELERYD_TASK_LOG_FORMAT
# Default is: [%(asctime)s: %(levelname)s/%(processName)s] [%(task_name)s(%(task_id)s)] %(message)s

#CELERY_REDIRECT_STDOUTS
# If enabled stdout and stderr will be redirected to the current logger.
# Enabled by default. Used by celery worker and celery beat.

CELERY_REDIRECT_STDOUTS_LEVEL = 'INFO'

if 'RABBITMQ_BIGWIG_URL' in os.environ.keys(): # On Heroku = Sender Queue: 
	BROKER_URL = os.environ['RABBITMQ_BIGWIG_TX_URL']
if 'LESSOPEN' in os.environ.keys(): # AWS Processor = Reciever RX Queue: 
	BROKER_URL="amqp://Sq_rhK2z:sGYEo2JbO0z3JpXh8YJq58NuMbvbM2Su@leaping-pipkin-62.bigwig.lshift.net:10919/thzgJ-IWDfsZ"
else: # Web Server Fired Anywhere Else: Sender Queue 
	BROKER_URL = 'amqp://Sq_rhK2z:sGYEo2JbO0z3JpXh8YJq58NuMbvbM2Su@leaping-pipkin-62.bigwig.lshift.net:10918/thzgJ-IWDfsZ'

CELERY_RESULT_BACKEND = BROKER_URL


# Set config based on computer name
# Development only
import subprocess
import shlex

daves_machine = False

try:
	command_line_args = shlex.split('scutil --get LocalHostName')
	command_line_process = subprocess.Popen( command_line_args , stdout=subprocess.PIPE, stderr=subprocess.STDOUT)
	response, error = command_line_process.communicate()
	if 'Davids-MacBook-Air' in response:
		daves_machine = True
except subprocess.CalledProcessError as error:
    error = error.output

if daves_machine:
	BROKER_URL = 'amqp://guest:guest@localhost:5672//'
