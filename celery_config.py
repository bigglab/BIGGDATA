import os
import sys 
from kombu import Exchange, Queue
from kombu.common import Broadcast






CELERY_TASK_SERIALIZER = 'json'
CELERY_RESULT_SERIALIZER = 'json'
CELERY_ACCEPT_CONTENT=['json']
CELERY_TIMEZONE = 'America/Chicago'
CELERY_ENABLE_UTC = True

CELERY_RESULT_BACKEND = 'rpc'
CELERY_RESULT_PERSISTENT = True





default_exchange = Exchange('default', type='direct')

CELERY_DEFAULT_QUEUE = 'default'
CELERY_QUEUES = (
	Broadcast('broadcast_tasks'),
  Queue('default', default_exchange, routing_key='default'),
)


class TaskRouter(object):

    def route_for_task(self, task, args=None, kwargs=None):
        if 'queue' in kwargs.keys(): 
					queue = kwargs['queue'] 
					return {'exchange': 'default',
					        'exchange_type': 'direct',
					        'routing_key': queue}
        # else: 
        # 	return {'exchange': 'default'
        # 					'exchange_type': 'default'
        # 					'routing_key': 'default'
        # 	}
        return None



CELERY_ROUTES = (
	TaskRouter(), 
)





if 'RABBITMQ_BIGWIG_URL' in os.environ.keys(): # On Heroku = Sender Queue: 
	BROKER_URL = os.environ['RABBITMQ_BIGWIG_TX_URL']
if 'LESSOPEN' in os.environ.keys(): # AWS Processor = Reciever RX Queue: 
	BROKER_URL="amqp://Sq_rhK2z:sGYEo2JbO0z3JpXh8YJq58NuMbvbM2Su@leaping-pipkin-62.bigwig.lshift.net:10919/thzgJ-IWDfsZ"
else: # Web Server Fired Anywhere Else: Sender Queue 
	BROKER_URL = 'amqp://Sq_rhK2z:sGYEo2JbO0z3JpXh8YJq58NuMbvbM2Su@leaping-pipkin-62.bigwig.lshift.net:10918/thzgJ-IWDfsZ'

