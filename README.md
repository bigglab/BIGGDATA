# BIGGIG 

# Start Broker 
rabbitmq-server

# Start Celery
celery -A app.celery worker --loglevel=info

# Start Celery Admin 
flower --port=5555  

# Start Web Service 
python app.py 

