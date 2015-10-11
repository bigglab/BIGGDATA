# BIGGIG 

# Start Broker 
rabbitmq-server

# Start Celery
celery -A app.celery worker --loglevel=info

# Start Celery Admin 
flower --port=5555  

# Start Web Service 
python app.py 

# Check It Out 

Current functionality only extends to the broader infrastructure. We have the ability to launch async jobs and distribute to the local node, and can easily extend to include other resources. 


# Resources
Props to the NPR apps team and Miguel Grinberg's Flask+Celery tutorials:  
  - Tutorial
    - [How to build a news app that never goes down and costs you practically nothing](http://blog.apps.npr.org/2013/02/14/app-template-redux.html)
    - [Flask + Celery Example - Grinberg ](blog.miguelgrinberg.com/post/using-celery-with-flask)


And a ton of other resources curated here: 
https://github.com/humiaozuzu/awesome-flask
