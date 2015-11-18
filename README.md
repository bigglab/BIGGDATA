# BIGGDATA 

BIGGDATA is a web portal for analyzing IG and TCR repertoire data. 

Users are able to run a variety of analysis programs (MixCR, IgBlast, etc) to annotate reads from Illumina instruments and generate useful insights into repretoire distribution, loci usage and interchain pairing (given interchain paired reads). 

The stack consists of python/flask with celery + rabbitMQ to execute and distribute asynchronous jobs. 

# Start Broker 
rabbitmq-server

# Start Celery
celery -A app.celery worker --loglevel=info

# Start Celery Admin (if you want) 
flower --port=5555  

# Start Web Service 
python manage.py runserver

# Check It Out At 0.0.0.0:5000
