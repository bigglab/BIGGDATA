
import json
# import oauth
import static
import os
import time
import random
from render_utils import make_context, smarty_filter, urlencode_filter
from werkzeug.debug import DebuggedApplication
from flask import Flask, make_response, render_template, render_template_string, request, session, flash, redirect, url_for, jsonify
from flask.ext.login import * 
import wtforms
from forms import LoginForm

# from flask_mail import Mail
from flask.ext.mail import Mail, Message
from flask_sqlalchemy import SQLAlchemy
from flask_user import login_required, SQLAlchemyAdapter, UserManager, UserMixin, roles_required
from celery import Celery


app = Flask(__name__)
import app_config
app.config.from_object(app_config)
#set key for Flask session handler - should be in a more secret place... 
app.secret_key = '\x95\x90+\x1c\xd36\xa3\x94\x99\xaeA\xac\xd3M5\x0b\xc7\xefF\xf3\x08\x05t\xd9'

# Initialize extensions
# Postgres DB for Users 
pgdb = SQLAlchemy(app)
login_manager = LoginManager()
login_manager.init_app(app)

# Celery configured for local RabbitMQ
celery = Celery(app.name, broker='amqp://')
import celery_config 
celery.config_from_object('celery_config')


# should really break out tasks to celery_tasks.py or something 
@celery.task
def add(x, y):
    # some long running task here
    return x + y 


@celery.task
def send_async_email(msg):
    """Background task to send an email with Flask-Mail."""
    with app.app_context():
        mail.send(msg)


@celery.task(bind=True)
def long_task(self):
    """Background task that runs a long function with progress reports."""
    verb = ['Starting up', 'Booting', 'Repairing', 'Loading', 'Checking']
    adjective = ['master', 'radiant', 'silent', 'harmonic', 'fast']
    noun = ['solar array', 'particle reshaper', 'cosmic ray', 'orbiter', 'bit']
    message = ''
    total = random.randint(10, 50)
    for i in range(total):
        if not message or random.random() < 0.25:
            message = '{0} {1} {2}...'.format(random.choice(verb),
                                              random.choice(adjective),
                                              random.choice(noun))
    # total = 100 
    # for i in range(total): 
    #     message = ''
        self.update_state(state='PROGRESS',
                          meta={'current': i, 'total': total,
                                'status': message})
        time.sleep(1)
    return {'current': 100, 'total': 100, 'status': 'Task completed!',
            'result': 42}







# load template environment for cleaner routes 
import jinja2 
templateLoader = jinja2.FileSystemLoader( searchpath="/Users/red/Desktop/BIGGIG/templates" )
templateEnv = jinja2.Environment( loader=templateLoader )



@app.route('/')
# @oauth.oauth_required
def index():
    template = templateEnv.get_template('index.html')
    return template.render(r='r')

@app.route('/login', methods=['GET', 'POST'])
def login():
    # Here we use a class of some kind to represent and validate our
    # client-side form data. For example, WTForms is a library that will
    # handle this for us, and we use a custom LoginForm to validate.
    form = LoginForm()
    if form.validate_on_submit():
        # Login and validate the user.
        # user should be an instance of your `User` class
        login_user(user)

        flask.flash('Logged in successfully.')

        next = flask.request.args.get('next')
        # next_is_valid should check if the user has valid
        # permission to access the `next` url
        if not next_is_valid(next):
            return abort(400)

        return redirect(next or flask.url_for('index'))
    return render_template('login.html', form=form)


@app.route('/igrep')
# @oauth.oauth_required
def igrep():
    template = templateEnv.get_template('igrep.html')
    return template.render(r='r')


@app.route('/add1/<num>')
# @oauth.oauth_required
def add_page(num):
    num = int(num)
    result = add.delay(1,num)
    time.sleep(3)
    async_result = add.AsyncResult(result.id)
    r = async_result.info
    template = templateEnv.get_template('add1.html')
    return template.render(input=num, result=r)

    # return make_response(render_template('index.html'))
    # return '<h4>Hi</h4>'



@app.route('/example', methods=['GET', 'POST'])
def example_index():
    if request.method == 'GET':
        return render_template('example_index.html', email=session.get('email', 'example'))
    email = request.form['email']
    session['email'] = email

    # send the email
    msg = Message('Hello from Flask',
                  recipients=[request.form['email']])
    msg.body = 'This is a test email sent from a background Celery task.'
    if request.form['submit'] == 'Send':
        # send right away
        send_async_email.delay(msg)
        flash('Sending email to {0}'.format(email))
    else:
        # send in one minute
        # send_async_email.apply_async(args=[msg], countdown=60)
        flash('An email will be sent to {0} in one minute'.format(email))

    return redirect(url_for('example_index'))


@app.route('/longtask', methods=['GET', 'POST'])
def longtask():
    task = long_task.apply_async()
    return jsonify({}), 202, {'Location': url_for('taskstatus',
                                                  task_id=task.id)}


@app.route('/status/<task_id>')
def taskstatus(task_id):
    task = long_task.AsyncResult(task_id)
    if task.state == 'PENDING':
        response = {
            'state': task.state,
            'current': 0,
            'total': 1,
            'status': 'Pending...'
        }
    elif task.state != 'FAILURE':
        response = {
            'state': task.state,
            'current': task.info.get('current', 0),
            'total': task.info.get('total', 1),
            'status': task.info.get('status', '')
        }
        if 'result' in task.info:
            response['result'] = task.info['result']
    else:
        # something went wrong in the background job
        response = {
            'state': task.state,
            'current': 1,
            'total': 1,
            'status': str(task.info),  # this is the exception raised
        }
    return jsonify(response)


@app.route('/users', methods=['GET', 'POST'])
def users():
    from sqlalchemy import create_engine
    from sqlalchemy import Table, Column, Integer, String, MetaData, ForeignKey
    engine = create_engine('postgresql://localhost/biggig', echo=True)
    conn = engine.connect()
    from sqlalchemy.sql import select
    metadata = MetaData()
    users = Table('users', metadata, 
        Column('id', Integer, primary_key=True),
        Column('first_name', String),
        Column('last_name', String)
        )
    s = select([users])
    results = conn.execute(s)  
    print 'query results from /users:'
    # for row in results:
    #     print row
    template = templateEnv.get_template('users.html')
    return template.render(results=results)






if __name__ == '__main__':
    app.run(host='0.0.0.0', port=5000, debug=True)


