#System Imports
import json
import static
import os
import time
import random
from celery import Celery
from collections import defaultdict
#Flask Imports
from werkzeug import secure_filename
from flask import Blueprint, render_template, flash, redirect, url_for
from flask import Flask, Blueprint, make_response, render_template, render_template_string, request, session, flash, redirect, url_for, jsonify, get_flashed_messages
from flask.ext.bcrypt import Bcrypt
from flask.ext.login import LoginManager, UserMixin, current_user, login_user, logout_user, login_required
from flask.ext.mail import Mail, Message
from flask.ext.script import Manager
from flask.ext.migrate import Migrate, MigrateCommand
from flask_bootstrap import Bootstrap
from flask_bootstrap import __version__ as FLASK_BOOTSTRAP_VERSION
from flask_nav import Nav 
from flask_nav.elements import Navbar, View, Subgroup, Link, Text, Separator
from flask_sqlalchemy import SQLAlchemy
from markupsafe import escape
from render_utils import make_context, smarty_filter, urlencode_filter
import wtforms
from flask_wtf import Form
import random
import jinja2 
from sqlalchemy import create_engine
from sqlalchemy import Table, Column, Integer, String, MetaData, ForeignKey
from sqlalchemy.sql import select
from sqlalchemy.orm import sessionmaker, scoped_session


#Local Imports 
from forms import *


app = Flask(__name__, instance_relative_config=True)
app.config.from_pyfile('config.py')
# Initialize extensions
bcrypt = Bcrypt(app)
nav = Nav() 
Bootstrap(app) 
# Postgres DB for Admin and File Tracking Purposes 
db = SQLAlchemy(app)
login_manager = LoginManager()
login_manager.init_app(app)

# load template environment for cleaner routes 
templateLoader = jinja2.FileSystemLoader( searchpath="/Users/red/Desktop/GeorgiouProjects/BIGGIG/templates" )
templateEnv = jinja2.Environment( loader=templateLoader, extensions=['jinja2.ext.with_'])



# MODELS. Not abstracted to make alembic migrations easier 

class User(db.Model):
        __tablename__ = 'user'
        id = db.Column(db.Integer, primary_key=True)
        first_name = db.Column(db.String(128))
        last_name = db.Column(db.String(128))
        email = db.Column(db.String(128))
        password_hash = db.Column(db.String(128))
        data = db.Column(db.Text())
        authenticated = db.Column(db.Boolean, default=False)
        user_type = db.Column(db.String(128))
        dropbox_path = db.Column(db.String(256))
        scratch_path = db.Column(db.String(256))
        files = db.relationship('File', backref='user', lazy='dynamic')
        datasets = db.relationship('Dataset', backref='user', lazy='dynamic')

        def get_id(self):
            """Return the email address to satisfy Flask-Login's requirements."""
            return self.email

        def is_active(self):
            """True, as all users are active."""
            return True

        def is_authenticated(self):
            """Return True if the user is authenticated."""
            return self.authenticated

        def is_anonymous(self):
            """False, as anonymous users aren't supported."""
            return False


class File(db.Model):
        __tablename__ = 'file'
        id = db.Column(db.Integer, primary_key=True)
        user_id = db.Column(db.Integer, db.ForeignKey('user.id'))
        dataset_id = db.Column(db.Integer, db.ForeignKey('dataset.id'))
        name = db.Column(db.String(256))
        description =db.Column(db.String(512))
        file_type = db.Column(db.String(128))
        path = db.Column(db.String(256))
        locus = db.Column(db.String(128))
        created = db.Column(db.DateTime, default=db.func.now())
        paired_partner = db.Column(db.Integer, db.ForeignKey('file.id'))
        parent = db.Column(db.Integer, db.ForeignKey('file.id'))



class Dataset(db.Model):
        __tablename__ = 'dataset'
        id = db.Column(db.Integer, primary_key=True)
        user_id = db.Column(db.Integer, db.ForeignKey('user.id'))
        name = db.Column(db.String(256))
        description =db.Column(db.String(512))
        ig_type = db.Column(db.String(128))
        paired = db.Column(db.Boolean, default=False)
        files = db.relationship('File', backref='dataset', lazy='dynamic')





# Flask-Login use this to reload the user object from the user ID stored in the session
@login_manager.user_loader
def load_user(email):
    user = db.session.query(User).filter_by(email=email).first()
    if user: 
        return user 
    else:
        return None


# @login_manager.user_loader
# def load_user(userid):
#     session = settings.Session()
#     user = session.query(models.User).filter(models.User.id == userid).first()
#     session.expunge_all()
#     session.commit()
#     session.close()
#     return user




frontend = Blueprint('frontend', __name__)

# We're adding a navbar as well through flask-navbar. In our example, the
# navbar has an usual amount of Link-Elements, more commonly you will have a
# lot more View instances.
nav.register_element('frontend_top', Navbar(
    View('BIGG DATA', '.index'),
    View('Home', '.index'),
    Subgroup(
        'Login',
        View('Login', '.login'),
        View('Logout', '.logout'),
        ),
    Subgroup(
        'Files', 
        View('My Files', '.files'), 
        View('My Datasets', '.datasets'),
        View('Upload File', '.file_upload'), 
        Link('Share Files', 'under_construction'),
        ),
    Subgroup(
        'Pipelines', 
        Link('My Pipelines', 'under_construction'), 
        Link('Public Pipelines', 'under_construction'), 
        Link('Create New From Base', 'under_construction')
        ),
    Subgroup(
        'Jobs',
        Link('Dashboard', 'under_construction'), 
        Link('My Jobs', 'under_construction'),
        Link('My Tasks', 'under_construction'), 
        ),
    Subgroup(
        'Database', 
        Link('Browse', 'under_construction'),
        Link('Download', 'under_construction'),
        Link('Mass Spec', 'under_construction')
        ),
    Link('Dashboard', 'under_construction'),
    Subgroup(
        'Documentation', 
        Link('Confluence', 'under_construction'), 
        Link('How To Write A Pipeline', 'under_construction'),
        Separator(),
        Text('External Docs'),
        Link('Flask-Bootstrap', 'http://pythonhosted.org/Flask-Bootstrap'),
        Link('Flask-AppConfig', 'https://github.com/mbr/flask-appconfig'),
        Link('Flask-Debug', 'https://github.com/mbr/flask-debug'),
        Separator(),
        Text('Bootstrap'),
        Link('Getting started', 'http://getbootstrap.com/getting-started/'),
        Link('CSS', 'http://getbootstrap.com/css/'),
        Link('Components', 'http://getbootstrap.com/components/'),
        Link('Javascript', 'http://getbootstrap.com/javascript/'),
        Link('Customize', 'http://getbootstrap.com/customize/'),
    ),
    Text('Powered by {}'.format('Python and Flask')),
))






@frontend.route('/', methods=['GET', 'POST'])
def index():
    results = db.session.query(User).all()
    return render_template("users.html", results=results)


@frontend.route("/login", methods=["GET", "POST"])
def login():
    login_form = LoginForm()
    if login_form.validate_on_submit():
        user = load_user(login_form.email.data)
        if user:
            print "found user" + user.first_name  
            if bcrypt.check_password_hash(user.password_hash, login_form.password.data):
                user.authenticated = True
                db.session.add(user)
                db.session.commit()
                login_user(user, remember=True)
                flash('logged in!', 'success')
                return redirect(url_for(".index"))
            else: 
                flash("Password doesn't match for " + user.first_name, 'error')
                print "password didnt match for " + user.first_name 
        else: 
            flash("couldn't find that user... try registering a new user", 'normal')
    #also supply create_user_form here for convenience
    create_user_form = RegistrationForm()
    return render_template("login.html", login_form=login_form, create_user_form=create_user_form)


@frontend.route("/users/create", methods=["POST"])
def create_user():
    form = RegistrationForm()
    # add some validations / cleansing 
    user = load_user(form.email.data)
    if user:
        if bcrypt.check_password_hash(user.password_hash, form.password.data):
            login_user(user)
            user.authenticated = True
            db.session.add(user)
            db.session.commit()
        flash('email already exists!', 'error')
        return redirect(url_for(".login"))
    new_user = User()
    new_user.first_name = form.first_name.data
    new_user.last_name = form.last_name.data 
    new_user.email = form.email.data
    new_user.password_hash = bcrypt.generate_password_hash(form.password.data)
    new_user.dropbox_path = '{}/{}{}'.format(app.config['DROPBOX_ROOT'], form.first_name.data, form.last_name.data)
    new_user.scratch_path = '{}/{}{}'.format(app.config['SCRATCH_ROOT'], form.first_name.data, form.last_name.data)
    db.session.add(new_user)
    db.session.commit()
    login_user(new_user, remember=True)
    flash("new user created and logged in", 'success')
    #create home and scratch if necessary 
    if not os.path.isdir(new_user.dropbox_path):
        os.makedirs(new_user.dropbox_path)
        print 'created new directory at {}'.format(new_user.dropbox_path)
    if not os.path.isdir(new_user.scratch_path):
        os.makedirs(new_user.scratch_path)
        print 'created new directory at {}'.format(new_user.dropbox_path)
    # return redirect(url_for("index"))
    return render_template("index.html")


@frontend.route("/logout", methods=["GET"])
def logout():
    """Logout the current user."""
    if current_user.is_authenticated(): 
        user = current_user
        user.authenticated = False
        db.session.add(user)
        db.session.commit()
        logout_user()
        flash('you have been logged out', 'success')
        return redirect(url_for('.index'))
    else: 
        flash('no user logged in')
        return redirect(url_for('.index'))
        # return render_template("index.html")


@frontend.route('/under_construction', methods=['GET', 'POST'])
def under_construction():
    gifs_dir = '/Users/red/Desktop/GeorgiouProjects/BIGGIG/static/goldens'
    gifs = os.listdir(gifs_dir)
    gif = random.choice(gifs)
    gif_path = url_for('static', filename='goldens/{}'.format(gif))
    return render_template("under_construction.html", gif_path=gif_path)





def get_filepaths(directory_path):
    file_paths = []
    for root, directories, files in os.walk(directory_path):
        for filename in files:
            filepath = os.path.join(root, filename)
            file_paths.append(filepath)
    return file_paths 

def get_dropbox_files(user):
    dropbox_path = user.dropbox_path
    dropbox_file_paths = get_filepaths(dropbox_path)
    dropbox_file_paths = [file_path for file_path in dropbox_file_paths if file_path not in [file.path for file in user.files]]
    return dropbox_file_paths

def tree(): return defaultdict(tree)

def parse_file_ext(path):

    if path.split('.')[-1] == 'gz':
        gzipped = True
    else:
        gzipped = False
    if gzipped: 
        ext = path.split('.')[-2]
    else:
        ext = path.split('.')[-1]
    ext_dict = tree()
    ext_dict['fastq'] = 'FASTQ'
    ext_dict['fq'] = 'FASTQ'
    ext_dict['fa'] = 'FASTA'
    ext_dict['fasta'] = 'FASTA'
    ext_dict['txt'] = 'TEXT'
    ext_dict['json'] = 'JSON'
    ext_dict['tab'] = 'TAB'
    ext_dict['csv'] = 'CSV'
    ext_dict['yaml'] = 'YAML'
    ext_dict['pileup'] = 'PILEUP'
    ext_dict['sam'] = 'SAM'
    ext_dict['bam'] = 'BAM'
    ext_dict['imgt'] = 'IMGT'
    file_type = ext_dict[ext]
    if isinstance(file_type, defaultdict):
        return None
    else:
        if gzipped: 
            return 'GZIPPED_{}'.format(file_type)
        else: 
            return file_type




@frontend.route('/file_upload', methods=['GET', 'POST'])
@login_required
def file_upload():
    form = FileUploadForm()
    if request.method == 'POST':
        request_file = request.files['file']
        print 'request file: '
        print request_file.__dict__
        file = File()
        file.name = request_file.filename
        file.file_type = parse_file_ext(file.name)
        file.description = form.description.data
        file.locus = form.locus.data
        file.paired_partner = form.paired_partner.data 
        file.dataset_id = form.dataset_id.data
        file.path = '{}/{}'.format(current_user.scratch_path, file.name) 
        file.user_id = current_user.id
        print 'Saving uploaded file to {}'.format(file.path)
        request_file.save(file.path)
        print 'Saving File Metadata to Postgres: {}'.format(file.__dict__)
        db.session.add(file)
        db.session.commit()
        flash('file uploaded to {}'.format(file.path))
        return redirect(url_for('.files'))
    else:
        return render_template("file_upload.html", form=form)



def link_file_to_user(path, user, name):
    file = File()
    file.name = name 
    file.path = path 
    file.user_id = user.id
    file.description = ''
    file.file_type = parse_file_ext(file.path)
    db.session.add(file)
    db.session.commit()
    return True


@frontend.route('/files', methods=['GET', 'POST'])
@login_required
def files():
    print request
    files = current_user.files.all()
    dropbox_file_paths = get_dropbox_files(current_user)
    form = Form()
    if request.method == 'POST' and os.path.isfile(request.form['submit']):
        file_path = request.form['submit'] 
        file_name = file_path.split('/')[-1]
        if file_path not in [file.path for file in current_user.files]:
            print 'linking new file "{}"  to  {}'.format(file_name, file_path)
            if link_file_to_user(file_path, current_user, file_name):
                flash('linked new file to your user: {}'.format(file_path), 'success')
                dropbox_file_paths = dropbox_file_paths.remove(file_path)
                files = current_user.files
        else: 
            flash('file metadata already created to your user')
            dropbox_file_paths = get_dropbox_files(current_user)
        return render_template("files.html", files=files, dropbox_files=dropbox_file_paths, form=form)
    else: 
        dropbox_file_paths = get_dropbox_files(current_user)
        return render_template("files.html", files=files, dropbox_files=dropbox_file_paths, form=form)



@frontend.route('/datasets', methods=['GET', 'POST'])
@login_required
def datasets():
    print request.__dict__
    files = current_user.files.all()
    datasets = current_user.datasets.all()
    datadict = tree()
    for dataset in datasets:
        datadict[dataset] = dataset.files.all()
    form = Form()
    if request.method == 'POST' and os.path.isfile(request.form['submit']):
        do_nothing = ''
    else: 
        return render_template("datasets.html", datadict=datadict, form=form)







@frontend.route('/add1/<num>')
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



@frontend.route('/example', methods=['GET', 'POST'])
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


@frontend.route('/longtask', methods=['GET', 'POST'])
def longtask():
    task = long_task.apply_async()
    return jsonify({}), 202, {'Location': url_for('taskstatus',
                                                  task_id=task.id)}


@frontend.route('/status/<task_id>')
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



app.register_blueprint(frontend)
nav.init_app(app)



















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


