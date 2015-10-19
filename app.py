
import json
import static
import os
import time
import random
from render_utils import make_context, smarty_filter, urlencode_filter
# from werkzeug.debug import DebuggedApplication
from flask import Flask, make_response, render_template, render_template_string, request, session, flash, redirect, url_for, jsonify, get_flashed_messages
from flask.ext.login import LoginManager, UserMixin, current_user, login_user, logout_user
import wtforms
from flask.ext.mail import Mail, Message
from flask_sqlalchemy import SQLAlchemy
from flask_user import login_required, SQLAlchemyAdapter, UserManager, UserMixin, roles_required
from celery import Celery
from flask.ext.bcrypt import Bcrypt

from forms import LoginForm


app = Flask(__name__, instance_relative_config=True)
# Load the configuration from the instance folder
app.config.from_pyfile('config.py')
# Initialize extensions
bcrypt = Bcrypt(app)


# Postgres DB for Admin Purposes 
db = SQLAlchemy(app)
from sqlalchemy import create_engine
from sqlalchemy import Table, Column, Integer, String, MetaData, ForeignKey
from sqlalchemy.sql import select
from sqlalchemy.orm import sessionmaker, scoped_session

from models import User 
login_manager = LoginManager()
login_manager.init_app(app)



# load template environment for cleaner routes 
import jinja2 
templateLoader = jinja2.FileSystemLoader( searchpath="/Users/red/Desktop/BIGGIG/templates" )
templateEnv = jinja2.Environment( loader=templateLoader )



# Flask-Login use this to reload the user object from the user ID stored in the session
@login_manager.user_loader
def load_user(email):
    result = db.session.query(User).filter_by(email=email).all()
    return result[0]



@app.route('/', methods=['GET', 'POST'])
def index():
    results = db.session.query(User).all()
    template = templateEnv.get_template('users.html')
    return template.render(results=results, current_user=current_user)


@app.route("/login", methods=["GET", "POST"])
def login():
    form = LoginForm()
    if form.validate_on_submit():
        user = load_user(form.email.data)
        print user.first_name 

        if user:
            if user.password_hash == form.password.data:
                user.authenticated = True
                db.session.add(user)
                db.session.commit()
                login_user(user, remember=True)
                return redirect(url_for("index"))
        # if user:
        #     if bcrypt.check_password_hash(user.password_hash, form.password.data):
        #         user.authenticated = True
        #         db.session.add(user)
        #         db.session.commit()
        #         login_user(user, remember=True)
        #         return redirect(url_for("app.example"))
    return render_template("login.html", form=form)


@app.route("/logout", methods=["GET"])
@login_required
def logout():
    """Logout the current user."""
    user = current_user
    user.authenticated = False
    db.session.add(user)
    db.session.commit()
    logout_user()
    return render_template("logout.html")




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








if __name__ == '__main__':
    print 'Running application on port 5000......'
    app.run(host='0.0.0.0', port=5000, debug=True)


