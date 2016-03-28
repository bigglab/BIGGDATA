#System Imports
import json
import static
import sys
import os
import time
import random
from shutil import copyfile
import operator
# import urllib
os.environ['http_proxy']=''
import urllib2
import itertools
import subprocess
import boto 
import math 
# from filechunkio import FileChunkIO 
from celery import Celery
from collections import defaultdict, OrderedDict
import collections
#Flask Imports
from werkzeug import secure_filename
from flask import Blueprint, render_template, flash, redirect, url_for
from flask import Flask, Blueprint, make_response, render_template, render_template_string, request, session, flash, redirect, url_for, jsonify, get_flashed_messages, send_from_directory
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
# from render_utils import make_context, smarty_filter, urlencode_filter
import wtforms
from flask_wtf import Form
import random
import jinja2 
from sqlalchemy import create_engine
from sqlalchemy import Table, Column, Integer, String, MetaData, ForeignKey, Boolean
from sqlalchemy.dialects import postgresql
from sqlalchemy.dialects.postgresql import JSON, JSONB, ARRAY, BIT, VARCHAR, INTEGER, FLOAT, NUMERIC, OID, REAL, TEXT, TIME, TIMESTAMP, TSRANGE, UUID, NUMRANGE, DATERANGE
from sqlalchemy.sql import select
from sqlalchemy.orm import sessionmaker, scoped_session
from pymongo import MongoClient
import pymongo
 
#Local Imports 
from forms import *
from functions import * 
from models import * 




app = Flask(__name__, instance_relative_config=True)
app.config.from_pyfile('config.py')
# Initialize extensions
bcrypt = Bcrypt(app)
nav = Nav() 
Bootstrap(app) 

db = SQLAlchemy(app)





# Celery configured for local RabbitMQ 
celery = Celery(app.name, broker='amqp://')
import celery_config 
celery.config_from_object('celery_config')

s3 = boto.connect_s3(app.config['AWSACCESSKEYID'], app.config['AWSSECRETKEY'])
s3_bucket = s3.get_bucket(app.config['S3_BUCKET'])


# Mongo DB for Legacy Sequence Data
mongo_connection_uri = 'mongodb://reader:cdrom@geordbas01.ccbb.utexas.edu:27017/'
login_manager = LoginManager()
login_manager.init_app(app)

# load template environment for cleaner routes 
templateLoader = jinja2.FileSystemLoader( searchpath="{}/templates".format(app.config['HOME']) )
templateEnv = jinja2.Environment( loader=templateLoader, extensions=['jinja2.ext.with_'])

def include_file(name):
    return jinja2.Markup(loader.get_source(env, name)[0])
app.jinja_env.globals['include_file'] = include_file


def round_to_two(flt):
    out = round(flt, 2) 
    return out
app.jinja_env.globals['round_to_two'] = round_to_two



# os.environ['http_proxy'] = app.config['QUOTAGUARD_URL']
proxy = urllib2.ProxyHandler()
opener = urllib2.build_opener(proxy)



def include_external_html(url):
    print 'requesting url: {}'.format(url)
    try: 
        response = opener.open(url)
        # response = urllib2.urlopen(url)
        contents = response.read()
    except urllib2.URLError, error: 
        print "ERROR RETRIEVING: {}".format(error)
        return ''
    return response  

app.jinja_env.globals['include_external_html'] = include_external_html








# Flask-Login use this to reload the user object from the user ID stored in the session
@login_manager.user_loader
def load_user(email):
    user = db.session.query(User).filter_by(email=email).first()
    if user: 
        return user 
    else:
        return None




frontend = Blueprint('frontend', __name__)
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
        View('Import File', '.file_download'), 
        View('Import From NCBI', '.import_sra'), 
        ),
    Subgroup(
        'Run Analysis',
        View('My Datasets', '.datasets'),
        View('My Analyses', '.analyses'),
        View('VDJ VIZualizer', '.vdj_visualizer'),
        Link('Other Tasks', 'under_construction'), 
        ),
    Subgroup(
        'Database', 
        View('Browse Experiments', '.browse_experiments'),
        View('Browse Sequences', '.browse_sequences'),
        Link('Download Lots of Data', 'under_construction'),
        Link('Download For Mass Spec', 'under_construction')
        ),
    View('Dashboard', '.analyses'),
    Subgroup(
        'Documentation', 
        View('BIGG DATA Overview', '.overview'), 
        View('BIGG DB Schema', '.schema'), 
        # Link('Confluence', 'under_construction'), 
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
    Link('Powered by {}'.format('Python and Flask'), 'https://github.com/russelldurrett/BIGGDATA'),
))






@frontend.route('/', methods=['GET', 'POST'])
def index():
    results = db.session.query(User).all()
    return render_template("index.html", results=results, user=current_user)



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
    return render_template("login.html", login_form=login_form, create_user_form=create_user_form, current_user=current_user)


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
    new_user.username = form.username.data
    new_user.password_hash = bcrypt.generate_password_hash(form.password.data)
    # Just authorize automatically, for now
    new_user.authenticated = True 
    new_user.dropbox_path = '{}/{}{}'.format(app.config['DROPBOX_ROOT'], form.first_name.data, form.last_name.data)
    new_user.scratch_path = '{}/{}{}'.format(app.config['SCRATCH_ROOT'], form.first_name.data, form.last_name.data)
    db.session.add(new_user)
    db.session.commit()
    login_user(new_user, remember=True)
    flash("new user created and logged in", 'success')
    #create home and scratch if necessary 
    result = instantiate_user_with_directories.apply_async((new_user.id, ), queue='default')
    return redirect(url_for(".index"))


@celery.task
def instantiate_user_with_directories(new_user_id):
    new_user = db.session.query(User).filter(User.id==new_user_id).first()
    if not os.path.isdir(new_user.dropbox_path):
        os.makedirs(new_user.dropbox_path)
        print 'created new directory at {}'.format(new_user.dropbox_path)
    if not os.path.isdir(new_user.scratch_path):
        os.makedirs(new_user.scratch_path)
        print 'created new directory at {}'.format(new_user.dropbox_path)
    # COPY SOME EXAMPLE FILES TO PLAY WITH
    share_root = app.config['SHARE_ROOT'] 
    files = os.listdir(share_root)
    print 'copying these files to new users dropbox: {}'.format(','.join(files))
    for f in files: 
        fullfilepath = '{}/{}'.format(new_user.dropbox_path, f)
        copyfile('{}/{}'.format(share_root, f), '{}/{}'.format(new_user.dropbox_path, f))
        link_file_to_user(fullfilepath, new_user.id, f)
    return True 





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
        return redirect(url_for('.login'))
    else: 
        flash('no user logged in')
        return redirect(url_for('.login'))
        # return render_template("index.html")


def retrieve_golden():
    gifs_dir = '{}/static/goldens'.format(app.config['HOME'])
    gifs = os.listdir(gifs_dir)
    gif = random.choice(gifs)
    gif_path = url_for('static', filename='goldens/{}'.format(gif))
    return gif_path


@frontend.route('/under_construction', methods=['GET', 'POST'])
def under_construction():
    gif_path=retrieve_golden()
    return render_template("under_construction.html", gif_path=gif_path)


@login_manager.unauthorized_handler
def unauthorized():
    gif_path=retrieve_golden()
    return render_template("unauthorized.html", git_path=gif_path)




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
    ext_dict['gtf'] = 'GTF'
    ext_dict['gff'] = 'GFF'
    ext_dict['gff3'] = 'GFF3'
    ext_dict['bed'] = 'BED'
    ext_dict['wig'] = 'WIGGLE'
    ext_dict['py'] = 'PYTHON'
    ext_dict['rb'] = 'RUBY'
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
        file.chain = form.chain.data
        file.paired_partner = form.paired_partner.data 
        file.dataset_id = form.dataset_id.data
        file.path = '{}/{}'.format(current_user.scratch_path, file.name) 
        file.user_id = current_user.id
        print 'Saving uploaded file to {}'.format(file.path)
        request_file.save(file.path)
        file.available = True 
        print 'Saving File Metadata to Postgres: {}'.format(file.__dict__)
        db.session.add(file)
        db.session.commit()
        flash('file uploaded to {}'.format(file.path))
        return redirect(url_for('.files'))
    else:
        dl_form = FileDownloadForm()
        return render_template("file_upload.html", upload_form=form, download_form=dl_form)



@frontend.route('/file_download', methods=['GET', 'POST'])
@login_required
def file_download(status=[], bucket='', key=''):
    bucket = request.args.get('bucket')
    key = request.args.get('key')
    if bucket: 
        status.append('Your file is available for download at the following URL:')
        status.append('https://s3.amazonaws.com/{}/{}'.format(bucket, key))
        form = FileDownloadForm(data={'url':'https://s3.amazonaws.com/{}/{}'.format(bucket, key)})
    else: 
        form = FileDownloadForm()
    if request.method == 'POST':
        file = File()
        file.url = form.url.data.rstrip()
        file.name = file.url.split('/')[-1].split('?')[0]
        file.file_type = parse_file_ext(file.name)
        file.description = form.description.data
        file.chain = form.chain.data
        file.paired_partner = form.paired_partner.data 
        file.dataset_id = form.dataset_id.data
        file.path = '{}/{}'.format(current_user.scratch_path, file.name) 
        file.user_id = current_user.id
        file.available = False 
        file.s3_status = ''
        file.status = ''
        print 'Saving File Metadata to Postgres: {}'.format(file.__dict__)
        db.session.add(file)
        db.session.commit()
        status.append('Started background task to download file from {}'.format(file.url))
        status.append('Saving File To {}'.format(file.path))
        status.append('This file will be visible in "My Files", and available for use after the download completes.')
        print status 
        # result_id NOT WORKING - STILL REDUNDANT IF THEY CLICK TWICE!!
        if not 'async_result_id' in session.__dict__:
            result = download_file.apply_async((file.url, file.path, file.id), queue='default')
            flash('file downloading from {}'.format(file.url))
            session['async_result_id'] = result.id
        time.sleep(1)
        async_result = add.AsyncResult(session['async_result_id'])
        # r = async_result.info
        r = result.__dict__
        r['async_result.info'] = async_result.info 
        db.session.commit()
        flash('file uploaded to {}'.format(file.path))
    else:
        r=''
    return render_template("file_download.html", download_form=form, status=status, r=r)







def parse_name_for_chain_type(name):
    if 'tcra' in name.lower() or 'alpha' in name.lower(): 
        chain = 'TCRA'
    if 'tcrb' in name.lower() or 'beta' in name.lower(): 
        chain = 'TCRB'
    if 'tcra' in name.lower() or 'alpha' in name.lower() and 'tcrb' in name.lower() or 'beta' in name.lower():
        chain = 'TCRA/B'
    if 'igh' in name.lower() or 'heavy' in name.lower(): 
        chain = 'HEAVY'
    if 'igl' in name.lower() or 'igk' in name.lower() or 'light' in name.lower(): 
        chain = 'LIGHT'
    if 'igl' in name.lower() or 'igk' in name.lower() or 'light' in name.lower() and 'igh' in name.lower() or 'heavy' in name.lower(): 
        chain = 'HEAVY/LIGHT'
    try: 
        chain
    except NameError: 
        chain = '' 
    return chain 


def link_file_to_user(path, user_id, name):
    file = File()
    file.name = name 
    file.path = path 
    file.user_id = user_id
    file.description = ''
    file.file_type = parse_file_ext(file.path)
    file.available = True 
    file.s3_status = ''
    file.chain = parse_name_for_chain_type(name)
    db.session.add(file)
    db.session.commit()
    return True


@celery.task
def transfer_file_to_s3(file_id): 
    f = db.session.query(File).filter(File.id==file_id).first()
    if not f: 
        return False 
    else: 
        if f.path:
            if f.s3_path: 
                print 'transferring file from {} to {}'.format(f.path, f.s3_path)
            else: 
                f.s3_path = '{}'.format(f.path)
                print 'transferring file from {} to s3://{}/{}'.format(f.path, app.config['S3_BUCKET'], f.s3_path)
                f.s3_status = 'Staging'
                db.session.commit()
        file_size = os.stat(f.path).st_size
        print 'starting transfer of {} byte file'.format(file_size)
        def cb(complete, total): 
            f.s3_status = 'Transferred {} of {} bytes'.format(complete, total)
            db.session.commit()
        key = s3_bucket.new_key(f.s3_path)
        result = key.set_contents_from_filename(f.path, cb=cb, num_cb=10)
        key.set_canned_acl('public-read')
        f.s3_status = "AVAILABLE"
        db.session.commit()
        print "Transfer complete. {} bytes transferred from {}  to  {}".format(result, f.path, f.s3_path)
        return True 


@frontend.route('/files/transfer_to_s3/<int:file_id>', methods=['GET'])
@login_required
def transfer_to_s3(file_id): 
    f = db.session.query(File).filter(File.id==file_id).first()
    if f: 
        f.s3_status = 'Staging On S3'
        db.session.add(f)
        db.session.commit()
        result = transfer_file_to_s3.apply_async((f.id,), queue='default')
        return redirect(url_for('.files'))


@frontend.route('/files', methods=['GET', 'POST'])
@login_required
def files(status=[], bucket=None, key=None):
    # print request
    db.session.expire_all()
    files = sorted(current_user.files.all(), key=lambda x: x.id, reverse=True)
    dropbox_file_paths = get_dropbox_files(current_user)
    form = Form()
    if bucket and key: 
        status.append('https://s3.amazon.com/{}/{}'.format(bucket, key))
    if request.method == 'POST' and os.path.isfile(request.form['submit']):
        file_path = request.form['submit'] 
        file_name = file_path.split('/')[-1]
        if file_path not in [file.path for file in current_user.files]:
            print 'linking new file "{}"  to  {}'.format(file_name, file_path)
            if link_file_to_user(file_path, current_user, file_name):
                flash('linked new file to your user: {}'.format(file_path), 'success')
                dropbox_file_paths = dropbox_file_paths.remove(file_path)
                files = sorted(current_user.files, key=lambda x: x.id, reverse=True)
        else: 
            flash('file metadata already created to your user')
            dropbox_file_paths = get_dropbox_files(current_user)
        return render_template("files.html", files=files, dropbox_files=dropbox_file_paths, form=form, current_user=current_user, status=status)
    else: 
        dropbox_file_paths = get_dropbox_files(current_user)
        return render_template("files.html", files=files, dropbox_files=dropbox_file_paths, form=form, current_user=current_user, status=status)



@frontend.route('/files/<int:id>', methods=['GET'])
@login_required
def file(id):
    f = db.session.query(File).filter(File.id==id).first()
    return render_template("file.html", file=f)



@frontend.route('/files/download/<int:id>')
@login_required
def send_file_from_id(id):
    # print request.__dict__
    files = sorted(current_user.files.all(), key=lambda x: x.id, reverse=True)
    f = db.session.query(File).filter(File.id==id).first()  
    f.dir = '/{}'.format('/'.join(f.path.split('/')[:-1]))
    file_path = f.path
    print 'trying to send {} from {}'.format(f.name, f.dir)
    return send_from_directory(f.dir, f.name, mimetype='text/plain', as_attachment=True)
    # return redirect(url_for('.files'))



def get_user_dataset_dict(user): 
    datadict = OrderedDict()
    for dataset in sorted(user.datasets, key=lambda x: x.id, reverse=True):
        datadict[dataset] = sorted(dataset.files.all(), key=lambda x: x.file_type)
    return datadict



@frontend.route('/datasets', methods=['GET', 'POST'])
@login_required
def datasets():
    # print request.__dict__
    files = current_user.files.all()
    datasets = current_user.datasets.all()
    datadict = get_user_dataset_dict(current_user)
    form = CreateDatasetForm()
    if request.method == 'POST':
        if form.name.data: 
            d = Dataset() 
            d.name = form.name.data 
            d.description = form.description.data
            d.paired = form.paired.data 
            d.ig_type = form.ig_type.data 
            d.user_id = current_user.id 
            db.session.add(d)
            db.session.commit()
        return redirect(url_for('.datasets')) # render_template("datasets.html", datadict=datadict, form=Form())
    else: 
        return render_template("datasets.html", datadict=datadict, form=form)



@frontend.route('/datasets/<int:id>', methods=['GET', 'POST'])
@login_required
def dataset(id):
    # print request.__dict__
    print 'finding dataset with {}'.format(id)
    dataset = db.session.query(Dataset).filter(Dataset.id==id).first()
    form = AssociateFilesToDatasetForm()
    form.dataset_id.data = dataset.id 
    file_choices = [f for f in db.session.query(File).filter(File.user_id==current_user.id).all() if f.dataset_id == None and f.available == True]
    # file_choices = db.session.query(File).filter(File.user_id==6).all()
    print 'choosing from these files: '.format(file_choices)
    form.file_ids.choices = [(f.id, f.name) for f in file_choices]   
    datadict = {dataset : dataset.files.all()}
    if request.method == 'POST' and dataset:
        print 'linking file id {} to dataset {}'.format(form.file_ids.data, dataset.__dict__)
        f = db.session.query(File).filter(File.id==form.file_ids.data).first()
        f.dataset_id = dataset.id 
        db.session.commit()
        flash('dataset saved')
        return render_template("dataset.html", datadict=datadict, form=form, id=id, dataset=dataset)
    else: 
        return render_template("dataset.html", datadict=datadict, form=form, id=id, dataset=dataset)




@frontend.route('/analysis', methods=['GET', 'POST'])
@login_required
def analyses(status=[]):
    status = request.args.getlist('status')
    analyses = current_user.analyses.all()
    analysis_file_dict = OrderedDict()
    for analysis in sorted(analyses, key=lambda x: x.started, reverse=True): 
        analysis_file_dict[analysis] = analysis.files.all() 
    return render_template("analyses.html", analyses=analyses, analysis_file_dict=analysis_file_dict, status=status)





# @frontend.route('/analysis/<int:analysis_id>/export_to_msdb/<string(length=3):ig_type>')
# @login_required
# def export_analysis_to_msdb(analysis_id, ig_type=None):
#     analysis = db.session.query(Analysis).filter(Analysis.id==analysis_id).first()
#     if ig_type: 
#         aa_seqs = db.engine.execute("select  cdr3_aa, count(distinct aa) from annotation a WHERE a.analysis_id = {} GROUP BY cdr3_aa ORDER BY count(aa) DESC;".format(analysis.id)).fetchall()






@frontend.route('/analysis/<int:id>', methods=['GET', 'POST'])
@login_required
def analysis(id):
    analysis = db.session.query(Analysis).filter(Analysis.id==id).first()
    cdr3_aa_counts = db.engine.execute("select  cdr3_aa, count(1) from annotation a WHERE a.analysis_id = {} GROUP BY cdr3_aa ORDER BY count(1) DESC;".format(analysis.id)).fetchall()
    v_hit_counts = db.engine.execute("select  v_top_hit, count(1) from annotation a WHERE a.analysis_id = {} GROUP BY v_top_hit ORDER BY count(1) DESC;".format(analysis.id)).fetchall()
    v_hit_loci_counts = db.engine.execute("select  v_top_hit_locus, count(1) from annotation a WHERE a.analysis_id = {} GROUP BY v_top_hit_locus ORDER BY count(1) DESC;".format(analysis.id)).fetchall()
    return render_template("analysis.html", analysis=analysis, cdr3_aa_counts=cdr3_aa_counts, v_hit_counts=v_hit_counts, v_hit_loci_counts=v_hit_loci_counts)
    






@frontend.route('/analysis/mixcr/<int:dataset_id>', methods=['GET', 'POST'])
@login_required
def mixcr(dataset_id, status=[]):
    dataset = db.session.query(Dataset).filter(Dataset.id==dataset_id).first()
    form = CreateMixcrAnalysisForm()
    status = []
    if request.method == 'POST' and dataset:
        status.append('MIXCR Launch Detected')
        result = run_mixcr_with_dataset_id.apply_async((dataset_id, ),  {'analysis_name': form.name.data, 'analysis_description': form.description.data, 'user_id': current_user.id, 'trim': form.trim.data, 'cluster': form.cluster.data}, queue='default')
        status.append(result.__repr__())
        status.append('Background Execution Started To Analyze Dataset {}'.format(dataset.id))
        time.sleep(1)
        # return render_template("mixcr.html", dataset=dataset, form=form, status=status) 
        analyses = current_user.analyses.all()
        analysis_file_dict = OrderedDict()
        for analysis in sorted(analyses, key=lambda x: x.started, reverse=True): 
            analysis_file_dict[analysis] = analysis.files.all() 
        return redirect(url_for('.analyses', status=status))
        # return render_template("analyses.html", analyses=analyses, analysis_file_dict=analysis_file_dict, status=status)
    else: 
        return render_template("mixcr.html", dataset=dataset, form=form, status=status) 




@frontend.route('/analysis/pandaseq/<int:dataset_id>', methods=['GET', 'POST'])
@login_required
def pandaseq(dataset_id, status=[]):
    dataset = db.session.query(Dataset).filter(Dataset.id==dataset_id).first()
    form = CreatePandaseqAnalysisForm()
    status = []
    if request.method == 'POST' and dataset:
        status.append('PANDASEQ Launch Detected')
        result = run_pandaseq_with_dataset_id.apply_async((dataset_id, ),  {'analysis_name': form.name.data, 'analysis_description': form.description.data, 'user_id': current_user.id, 'algorithm': form.algorithm.data}, queue='default')
        status.append(result.__repr__())
        status.append('Background Execution Started To Analyze Dataset {}'.format(dataset.id))
        time.sleep(1)
        # return render_template("mixcr.html", dataset=dataset, form=form, status=status) 
        analyses = current_user.analyses.all()
        analysis_file_dict = OrderedDict()
        for analysis in sorted(analyses, key=lambda x: x.started, reverse=True): 
            analysis_file_dict[analysis] = analysis.files.all() 
        return redirect(url_for('.analyses', status=status))
        # return render_template("analyses.html", analyses=analyses, analysis_file_dict=analysis_file_dict, status=status)
    else: 
        return render_template("pandaseq.html", dataset=dataset, form=form, status=status) 












@frontend.route('/browse_experiments', methods=['GET', 'POST'])
@login_required
def browse_experiments():
    # print request.__dict__
    files = current_user.files.all()
    datasets = current_user.datasets.all()
    datadict = tree()
    for dataset in datasets:
        datadict[dataset] = dataset.files.all()
    form = Form()
    exps = db.session.query(Experiment).order_by(Experiment.curated.desc(), Experiment.experiment_creation_date.desc()).all()
    species_data = sorted(db.engine.execute('select species, count(*) from experiment GROUP BY species;').fetchall(), key=lambda x: x[1], reverse=True)
    chain_data = sorted(db.engine.execute('select chain_types_sequenced, count(*) from experiment GROUP BY chain_types_sequenced;').fetchall(), key=lambda x: x[1], reverse=True)
    cell_data = sorted(db.engine.execute('select cell_types_sequenced, count(*) from experiment GROUP BY cell_types_sequenced;').fetchall(), key=lambda x: x[1], reverse=True)
    primer_data = sorted(db.engine.execute('select primer_set_name, count(*) from experiment GROUP BY primer_set_name;').fetchall(), key=lambda x: x[1], reverse=True)
    cell_marker_data = sorted(db.engine.execute('select cell_markers_used, count(*) from experiment GROUP BY cell_markers_used;').fetchall(), key=lambda x: x[1], reverse=True)
    owner_query_data = sorted(db.engine.execute('select owners_of_experiment, count(*) from experiment GROUP BY owners_of_experiment;').fetchall(), key=lambda x: x[1], reverse=True)
    owners = set(flatten_list([o[0] for o in owner_query_data]))
    owner_data = {}
    for o in owners: 
        owner_data[o] = 0 
    for os,c in owner_query_data: 
        for o in os: 
            owner_data[o] += c 
    owner_data = sorted(owner_data.items(), key=operator.itemgetter(1), reverse=True)
    isotype_query_data = sorted(db.engine.execute('select isotypes_sequenced, count(*) from experiment GROUP BY isotypes_sequenced;').fetchall(), key=lambda x: x[1], reverse=True)
    isotype_data = demultiplex_tuple_counts(isotype_query_data)
    # sorted(isotype_counts.items(), key=operator.itemgetter(0))
    cell_marker_query_data = sorted(db.engine.execute('select cell_markers_used, count(*) from experiment GROUP BY cell_markers_used;').fetchall(), key=lambda x: x[1], reverse=True)
    cell_marker_data=demultiplex_tuple_counts(cell_marker_query_data, index=1, reverse=True)
    # print cell_marker_data 
    golden = retrieve_golden()
    err = False
    return render_template("browse_experiments.html", datadict=datadict, form=form, exps=exps, err=err, gif_path=golden, species_data=species_data, chain_data=chain_data, cell_data=cell_data, cell_marker_data=cell_marker_data, primer_data=primer_data, isotype_data=isotype_data, owner_data=owner_data)




@frontend.route('/browse_sequences', methods=['GET', 'POST'])
@login_required
def browse_sequences():
    # print request.__dict__
    files = current_user.files.all()
    datasets = current_user.datasets.all()
    datadict = tree()
    for dataset in datasets:
        datadict[dataset] = dataset.files.all()
    seq_count = db.session.query(Sequence).count()
    ann_count = db.session.query(Annotation).count()
    form = Form()
    golden = retrieve_golden()
    err = False
    return render_template("browse_sequences.html", form=form, files=files, datasets=datasets, datadict=datadict, err=err, gif_path=golden, seq_count=seq_count, ann_count=ann_count)


@frontend.route('/developers/schema', methods=['GET'])
def schema():
    schema_url = url_for('static', filename='schema.png')
    return render_template("schema.html", schema_url=schema_url)

@frontend.route('/developers/overview', methods=['GET'])
def overview():
    schema_url = url_for('static', filename='schema.png')
    infrastructure_image_url = url_for('static', filename='bigg_data_infrastructure.png')
    return render_template("infrastructure.html", schema_url=schema_url, infrastructure_image_url=infrastructure_image_url)


@frontend.route('/vdjviz', methods=['GET'])
def vdj_visualizer():
    vdjviz_url = 'http://vdjviz.rsldrt.com:9000/account'
    return render_template("vdjviz.html", vdjviz_url=vdjviz_url)



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









@frontend.route('/files/import_sra', methods=['GET', 'POST'])
@login_required
def import_sra():
    form = ImportSraAsDatasetForm()
    result = None
    status = []
    if request.method == 'POST':
        if 'SRR' in form.accession.data: 
            status.append('Import SRA Started for Accession {}'.format(form.accession.data))
            status.append('Once complete, a dataset named {} will automatically be created containing these single or paired-end read files'.format(form.accession.data))
            result = import_from_sra.apply_async((form.accession.data,), {'name': form.accession.data, 'user_id': current_user.id}, queue='default')
            # status.append(result.__dict__)
        else: 
            status.append('Accession does not start with SRR or ERR?')
    return render_template('sra_import.html', status=status, form=form, result=result)



@celery.task 
def import_from_sra(accession, name=None, user_id=57):
    user = db.session.query(User).filter(User.id==user_id).first()
    if not name: 
        name = accession 
    print 'Fetching SRA data from NCBI {}'.format(accession)
    command = 'fastq-dump --gzip --split-files -T --outdir {} {}'.format(user.scratch_path, accession) 
    response = os.system(command)
    if response == 0: 
        file_paths = []
        dirs = os.listdir('{}/{}'.format(user.scratch_path, accession))
        if dirs == ['1']:
            file_paths = ['{}/{}/1/fastq.gz'.format(user.scratch_path, accession)]
            filename_array = ['{}.fastq.gz'.format(accession)]
        if dirs == ['1','2'] or dirs == ['2','1']:
            file_paths = ['{}/{}/1/fastq.gz'.format(user.scratch_path, accession), '{}/{}/2/fastq.gz'.format(user.scratch_path, accession)]
            filename_array = ['{}.R1.fastq.gz'.format(accession), '{}.R2.fastq.gz'.format(accession)]
        else: 
            print 'Number of files from SRA export not one or two...'
            return False 
    print 'Writing sra output files to {}'.format(user.scratch_path)
    dataset = import_files_as_dataset(file_paths, filename_array=filename_array, user_id=user_id, name=name)
    print 'Dataset from SRA Accession {} created for user {}'.format(accession, user.username) 
    return True







@celery.task 
def import_files_as_dataset(filepath_array, filename_array=None, chain=None, user_id=57, name=None):
    d = Dataset()
    d.user_id = user_id
    d.name = name
    d.description = 'Dataset generated from file import'
    d.chain_types_sequenced = [chain]
    db.session.add(d)
    db.session.commit()
    files = []
    for index, filepath in enumerate(filepath_array):
        f = File()
        f.user_id = user_id 
        if filename_array and len(filename_array) == len(filepath_array):
            f.name = filename_array[index]
        else:
            f.name = filepath.split('/')[-1]
        f.file_type = parse_file_ext(f.name) 
        f.dataset_id = d.id
        # description = 
        f.available = True
        f.in_use = False
        f.status = 'AVAILABLE'
        f.path = filepath
        f.file_size = os.path.getsize(f.path)
        f.s3_available = False
        f.s3_status = ''
        f.s3_path = ''
        f.chain = chain
        # url = db.Column(db.String(256))
        f.command = 'metadata created to link existing file'
        f.created = 'now'
        # paired_partner = db.Column(db.Integer, db.ForeignKey('file.id'))
        # parent_id = db.Column(db.Integer, db.ForeignKey('file.id'))
        # analysis_id = db.Column(db.Integer, db.ForeignKey('analysis.id'))
        files.append(f)
    for f in files: 
        db.session.add(f)
    db.session.commit()
    d.primary_data_files_ids = map(lambda f: f.id, files)
    db.session.commit()
    return True 




@celery.task
def download_file(url, path, file_id):
    print 'urllib2 downloading file from {}'.format(url)
    response = urllib2.urlopen(url)
    CHUNK = 16 * 1024
    with open(path, 'wb') as outfile: 
        while True: 
            chunk = response.read(CHUNK)
            if not chunk: break 
            outfile.write(chunk)
    f = db.session.query(File).filter(File.id==file_id).first()
    f.available = True
    f.file_size = os.path.getsize(f.path)
    db.session.commit()
    return True 



@celery.task
def run_mixcr_with_dataset_id(dataset_id, analysis_name='', analysis_description='', user_id=6, trim=False, cluster=False):
    dataset = db.session.query(Dataset).filter(Dataset.id==dataset_id).first()
    print 'RUNNING MIXCR ON DATASET ID# {}: {}'.format(dataset_id, repr(dataset.__dict__))
    analysis = Analysis()
    analysis.db_status = 'WAITING'
    analysis.name = analysis_name
    analysis.description = analysis_description
    analysis.user_id = user_id
    analysis.dataset_id = dataset.id
    analysis.program = 'mixcr'
    analysis.started = 'now'
    analysis.params = {}
    analysis.status = 'QUEUED'
    analysis.responses = []
    analysis.available = False
    analysis.inserted_into_db = False
    db.session.add(analysis)
    db.session.commit()
    data_files_by_chain = {}
    for key, values in itertools.groupby(dataset.primary_data_files(), lambda x: x.chain): 
        data_files_by_chain[key] = list(values)
    print "Running mixcr in these batches of files (sorted by file.chain): {}".format(data_files_by_chain)
    for chain, files in data_files_by_chain.items(): 
        if trim: 
            print 'Running Trim on Files in Analysis {} before executing MixCR'.format(analysis.id)
            files = run_trim_analysis_with_files(analysis, files)
        print 'ABOUT TO RUN MIXCR ANAYSIS {} ON FILES FROM CHAIN {}'.format(repr(analysis), chain)
        run_mixcr_analysis_id_with_files(analysis.id, files)
        if cluster: 
            print 'Clustering Output Files'
            for file in files: 
                result = run_usearch_cluster_fast_on_analysis_file(analysis, file, identity=0.9)
    return True 



@celery.task
def run_mixcr_analysis_id_with_files(analysis_id, files):
    analysis = db.session.query(Analysis).filter(Analysis.id==analysis_id).first()
    dataset = analysis.dataset
    files_to_execute = []
    print 'RUNNING MIXCR ON THESE FILES: {}'.format(files)
    scratch_path = '/{}'.format('/'.join(files[0].path.split('/')[:-1]))
    basename = files[0].path.split('/')[-1].split('.')[0]
    basepath = '{}/{}'.format(scratch_path, basename)
    print 'Writing output files to base name: {}'.format(basepath)
    output_files = []
    # Instantiate Source Files
    alignment_file = File()
    alignment_file.path = '{}.aln.vdjca'.format(basepath)
    alignment_file.name = "{}.aln.vdjca".format(basename)
    # MIGHT NEED TO ADD THIS ARGUMENT to align   -OjParameters.parameters.mapperMaxSeedsDistance=5
    alignment_file.command = 'mixcr align --save-description -f {} {}'.format(' '.join([f.path for f in files]), alignment_file.path)
    alignment_file.file_type = 'MIXCR_ALIGNMENTS'
    files_to_execute.append(alignment_file)
    clone_file = File()
    clone_file.file_type = 'MIXCR_CLONES'
    clone_file.path = '{}.aln.clns'.format(basepath)
    clone_file.name = '{}.aln.clns'.format(basename)
    clone_file.command = 'mixcr assemble -f {} {}'.format(alignment_file.path, clone_file.path)
    files_to_execute.append(clone_file)
    db.session.add(alignment_file)
    db.session.add(clone_file)
    db.session.commit()
    # Commit To Get Parent IDs
    clone_output_file = File()
    clone_output_file.parent_id = clone_file.id 
    clone_output_file.path = '{}.txt'.format(clone_file.path)
    clone_output_file.file_type = 'MIXCR_CLONES_TEXT'
    clone_output_file.name = '{}.txt'.format(clone_file.name)
    clone_output_file.command = 'mixcr exportClones {} {}'.format(clone_file.path, clone_output_file.path)
    files_to_execute.append(clone_output_file)
    alignment_output_file = File()
    alignment_output_file.parent_id = alignment_file.id
    alignment_output_file.path = '{}.txt'.format(alignment_file.path)
    alignment_output_file.file_type = 'MIXCR_ALIGNMENT_TEXT'
    alignment_output_file.name = '{}.txt'.format(alignment_file.name)
    alignment_output_file.command = 'mixcr exportAlignments  -readId -descrR1 --preset full  {} {}'.format(alignment_file.path, alignment_output_file.path)
    files_to_execute.append(alignment_output_file)
    pretty_alignment_file = File()
    pretty_alignment_file.parent_id = alignment_file.id 
    pretty_alignment_file.path = '{}.pretty.txt'.format(alignment_file.path)
    pretty_alignment_file.file_type = 'MIXCR_PRETTY_ALIGNMENT_TEXT'
    pretty_alignment_file.name =  '{}.pretty.txt'.format(alignment_file.name)
    pretty_alignment_file.command = 'mixcr exportAlignmentsPretty {} {}'.format(alignment_file.path, pretty_alignment_file.path)
    files_to_execute.append(pretty_alignment_file)
    analysis.status = 'EXECUTING'
    db.session.commit()
    for f in files_to_execute:
        f.command = f.command.encode('ascii')
        f.dataset_id = analysis.dataset_id 
        f.analysis_id = analysis.id 
        f.chain = files[0].chain
        print 'Executing: {}'.format(f.command)
        analysis.active_command = f.command
        f.in_use = True 
        db.session.add(f)
        db.session.commit()
        # MAKE THE CALL 
        response = os.system(f.command)
        print 'Response: {}'.format(response)
        if response == 0: 
            f.available = True 
            f.file_size = os.path.getsize(f.path)
            db.session.commit()
        else:
            f.available = False
            analysis.status = 'FAILED'
            db.session.commit()
    print 'All commands in analysis {} have been executed.'.format(analysis)
    if set(map(lambda f: f.available, files_to_execute)) == {True}:
        analysis.status = 'SUCCESS'
        analysis.available = True
    if not analysis.status == 'FAILED': analysis.status = 'SUCCESS'
    analysis.active_command = ''
    analysis.finished = 'now'
    db.session.commit()
    # KICK OFF ASYNC DB INSERTS FROM OUTPUT FILES
    parseable_mixcr_alignments_file_path = alignment_output_file.path
    # PARSE WITH parse_and_insert_mixcr_annotation_dataframe_from_file_path to speed up? 
    if not analysis.status == 'FAILED': result = parse_and_insert_mixcr_annotations_from_file_path(parseable_mixcr_alignments_file_path, dataset_id=analysis.dataset.id, analysis_id=analysis.id)
    return True 



@celery.task
def parse_and_insert_mixcr_annotations_from_file_path(file_path, dataset_id=None, analysis_id=None):
    print 'Building annotations from mixcr output at {}, then inserting into postgres in batches'.format(file_path)
    if analysis_id: 
        analysis = db.session.query(Analysis).filter(Analysis.id==analysis_id).first()
    else: 
        analysis = None 
    if analysis: analysis.db_status = 'BUILDING ANNOTATIONS'
    if analysis: analysis.status = 'INSERTING TO DB'
    db.session.commit()
    annotations = build_annotations_from_mixcr_file(file_path, dataset_id=dataset_id, analysis_id=analysis_id)
    total_count = len(annotations) 
    if analysis: analysis.total_count = total_count
    db.session.commit()
    for i,a in enumerate(annotations): 
        db.session.add(a)
        if i % 1000 == 0:
            print "Inserting # {} and the previous 1000 annotations to postgres. Here's what it looks like: {}".format(i, a.__dict__)
            percent_done = float(i) / float(total_count)
            if analysis: analysis.db_status = '{} Annotations Inserted in DB,  {} Percent Done'.format(i, int(percent_done * 100))
            db.session.commit()
    if analysis: 
        analysis.db_status = 'Finished. {} Annotations Inserted'.format(len(annotations))
    db.session.commit()
    result = annotate_analysis_from_db.apply_async((analysis.id, ), queue='default')
    return len(annotations)


@celery.task
def parse_and_insert_mixcr_annotation_dataframe_from_file_path(file_path, dataset_id=None, analysis_id=None):
    print 'Building annotation dataframe from mixcr output at {}, then inserting into postgres'.format(file_path)
    if analysis_id: 
        analysis = db.session.query(Analysis).filter(Analysis.id==analysis_id).first()
    else: 
        analysis = None 
    if analysis: analysis.db_status = 'BUILDING ANNOTATIONS'
    if analysis: analysis.status = 'BUILDING DATABASE'
    db.session.commit()
    annotation_df = build_annotation_dataframe_from_mixcr_file(file_path, dataset_id=dataset_id, analysis_id=analysis_id)
    print "Inserting annotation dataframe to postgres"
    if analysis: analysis.total_count = len(annotation_df)
    if analysis: analysis.db_status = 'INSERTING'
    if analysis: analysis.status = 'INSERTING TO DB'
    db.session.commit()
    engine = create_engine(app.config['SQLALCHEMY_DATABASE_URI'])
    annotation_df.to_sql('annotation', engine, if_exists='append')
    if analysis: 
        analysis.db_status = 'Finished. {} Annotations Inserted'.format(len(annotation_df))
    db.session.commit()
    result = annotate_analysis_from_db.apply_async((analysis.id, ), queue='default')
    return True



@celery.task
def annotate_analysis_from_db(analysis_id): 
    analysis = db.session.query(Analysis).filter(Analysis.id==analysis_id).first()
    if not analysis: 
        return False 
    else: 
        analysis.vdj_count = 0
        analysis.vj_count = 0
        analysis.tcra_count = 0
        analysis.tcrb_count = 0
        analysis.status = 'FINISHED'
        analysis.db_status = 'Inserted and Re-analyzed'
        analysis.available = True 
        db.session.commit()





@celery.task
def run_pandaseq_with_dataset_id(dataset_id, analysis_name='', analysis_description='', user_id=6, algorithm='pear'):
    dataset = db.session.query(Dataset).filter(Dataset.id==dataset_id).first()
    print 'RUNNING MIXCR ON DATASET ID# {}: {}'.format(dataset_id, repr(dataset.__dict__))
    analysis = Analysis()
    analysis.db_status = "We dont currently import raw or pandaseq'd FASTQ Data"
    analysis.name = analysis_name
    analysis.description = analysis_description
    analysis.user_id = user_id
    analysis.dataset_id = dataset.id
    analysis.program = 'pandaseq'
    analysis.started = 'now'
    analysis.params = {}
    analysis.status = 'QUEUED'
    analysis.responses = []
    analysis.available = False
    analysis.inserted_into_db = False
    db.session.add(analysis)
    db.session.commit()
    data_files_by_chain = {}
    for key, values in itertools.groupby(dataset.primary_data_files(), lambda x: x.chain): 
        data_files_by_chain[key] = list(values)
    print "Running pandaseq in these batches of files (sorted by file.chain): {}".format(data_files_by_chain)
    for chain, files in data_files_by_chain.items(): 
        if len(files) == 2: 
            print 'ABOUT TO RUN PANDASEQ CONCATENATION ON {} FILES FROM CHAIN {}'.format(len(files), chain)
            run_pandaseq_analysis_with_files(analysis, files, algorithm=algorithm)
        else: 
            print 'bad request for pandaseq alignment of only {} files'.format(len(files))
    return True 



@celery.task
def run_pandaseq_analysis_with_files(analysis, files, algorithm='pear'):
    dataset = analysis.dataset
    files_to_execute = []
    print 'RUNNING PANDASEQ ON THESE FILES: {}'.format(files)
    scratch_path = '/{}'.format('/'.join(files[0].path.split('/')[:-1]))
    basename = files[0].path.split('/')[-1].split('.')[0]
    basepath = '{}/{}'.format(scratch_path, basename)
    print 'Writing output files to base name: {}'.format(basepath)
    output_files = []
    # Instantiate Source Files
    alignment_file = File()
    alignment_file.path = '{}.pandaseq_{}.fastq'.format(basepath, algorithm)
    alignment_file.name = "{}.pandaseq_{}.fastq".format(basename, algorithm)
    alignment_file.command = 'pandaseq -f {} -r {} -F -T 4 -A {} -w {} 2> {}.log'.format(files[0].path, files[1].path, algorithm, alignment_file.path, alignment_file.path)
    alignment_file.file_type = 'PANDASEQ_ALIGNED_FASTQ'
    files_to_execute.append(alignment_file)
    analysis.status = 'EXECUTING'
    db.session.commit()
    for f in files_to_execute:
        f.command = f.command.encode('ascii')
        f.dataset_id = analysis.dataset_id 
        f.analysis_id = analysis.id 
        f.chain = files[0].chain
        print 'Executing: {}'.format(f.command)
        analysis.active_command = f.command
        f.in_use = True 
        db.session.add(f)
        db.session.commit()
        # MAKE THE CALL 
        response = os.system(f.command)
        print 'Response: {}'.format(response)
        if response == 0: 
            f.available = True 
            f.file_size = os.path.getsize(f.path)
            db.session.commit()
        else:
            f.available = False
            analysis.status = 'FAILED'
            db.session.commit()
    print 'All commands in analysis {} have been executed.'.format(analysis)
    if set(map(lambda f: f.available, files_to_execute)) == {True}:
        analysis.status = 'SUCCESS'
        analysis.available = True
    if not analysis.status == 'FAILED': analysis.status = 'SUCCESS'
    analysis.active_command = ''
    analysis.finished = 'now'
    db.session.commit()
    # Make PandaSeq Alignment Primary Dataset Data Files! Currently done in dataset.primary_data_files() 
    return True 






def run_trim_analysis_with_files(analysis, files):
    dataset = analysis.dataset
    files_to_execute = []
    print 'RUNNING TRIMMAMATIC ON THESE FILES: {}'.format(files)
    scratch_path = '/{}'.format('/'.join(files[0].path.split('/')[:-1]))
    basename = files[0].path.split('/')[-1].split('.')[0]
    basepath = '{}/{}'.format(scratch_path, basename)
    print 'Writing output files to base name: {}'.format(basepath)
    output_files = []
    # Instantiate Source Files
    if len(files) == 1: 
        output_file = File()
        output_file.path = '{}.trimmed.fastq'.format(basepath)
        output_file.name = "{}.trimmed.fastq".format(basename)
        output_file.command = '{} SE -phred33 -threads 4 {} {} ILLUMINACLIP:{}/TruSeq3-SE.fa:2:30:10 LEADING:3 TRAILING:3 SLIDINGWINDOW:4:15 MINLEN:50'.format(app.config['TRIMMAMATIC'], files[0].path, output_file.path, app.config['TRIMMAMATIC_ADAPTERS'])
        output_file.file_type = 'TRIMMED_FASTQ'
        files_to_execute.append(output_file)
    if len(files) == 2: 
        r1_output_file = File()
        r1_output_file.path = '{}.R1.trimmed.fastq'.format(basepath)
        r1_output_file.name = "{}.R2.trimmed.fastq".format(basename)
        r1_output_file.file_type = 'TRIMMED_FASTQ'
        r2_output_file = File()
        r2_output_file.path = '{}.R1.trimmed.fastq'.format(basepath)
        r2_output_file.name = "{}.R2.trimmed.fastq".format(basename)
        r2_output_file.file_type = 'TRIMMED_FASTQ'
        r1_output_file.command = '{} PE -phred33 -threads 4 {} {} {} {} {} {} ILLUMINACLIP:{}/TruSeq3-PE.fa:2:30:10 LEADING:3 TRAILING:3 SLIDINGWINDOW:4:15 MINLEN:50'.format(app.config['TRIMMAMATIC'], files[0].path, files[1].path, r1_output_file.path, '/dev/null', r2_output_file.path, '/dev/null', app.config['TRIMMAMATIC_ADAPTERS'])
        r2_output_file.command = ''
        files_to_execute.append(r1_output_file)
        files_to_execute.append(r2_output_file)
    analysis.status = 'EXECUTING TRIM'
    db.session.commit()
    for f in files_to_execute:
        f.command = f.command.encode('ascii')
        f.dataset_id = analysis.dataset_id 
        f.analysis_id = analysis.id 
        f.chain = files[0].chain
        print 'Executing: {}'.format(f.command)
        analysis.active_command = f.command
        f.in_use = True 
        db.session.add(f)
        db.session.commit()
        # MAKE THE CALL 
        response = os.system(f.command)
        print 'Response: {}'.format(response)
        if response == 0: 
            f.available = True 
            f.in_use = False
            f.file_size = os.path.getsize(f.path)
            db.session.commit()
        else:
            f.available = False
            f.in_use = False 
            analysis.status = 'FAILED'
            db.session.commit()
    print 'Trim job for analysis {} has been executed.'.format(analysis)
    return files 






def run_usearch_cluster_fast_on_analysis_file(analysis, file, identity=0.9):
    dataset = analysis.dataset
    files_to_execute = []
    print 'RUNNING USEARCH CLUSTERING ON THIS FILE: {}'.format(file)
    scratch_path = '/{}'.format('/'.join(file.path.split('/')[:-1]))
    basename = file.path.split('/')[-1].split('.')[0]
    basepath = '{}/{}'.format(scratch_path, basename)
    print 'Writing output files to base name: {}'.format(basepath)
    output_files = []
    # Instantiate Source Files
    consensus_output_file = File()
    consensus_output_file.path = '{}.uclust_consensus.fasta'.format(basepath)
    consensus_output_file.name = "{}.uclust_consensus.fasta".format(basename)
    consensus_output_file.command = ""
    consensus_output_file.file_type = 'CLUSTERED_CONSENSUS_FASTA'
    uclust_output_file = File()
    uclust_output_file.path = '{}.uclust.tab'.format(basepath)
    uclust_output_file.name = "{}.uclust.tab".format(basename)
    uclust_output_file.command = ""
    uclust_output_file.file_type = 'UCLUST_OUTPUT_TAB_TEXT'
    centroid_output_file = File()
    centroid_output_file.path = '{}.uclust_centroids.fasta'.format(basepath)
    centroid_output_file.name = "{}.uclust_centroids.fasta".format(basename)
    centroid_output_file.file_type = 'CLUSTERED_CENTROIDS_FASTA'
    centroid_output_file.command = "usearch -cluster_fast {} -id {} -centroids {} -consout {} -uc {}".format(file.path, identity, centroid_output_file.path, consensus_output_file.path, uclust_output_file.path)
    files_to_execute.append(centroid_output_file)
    files_to_execute.append(consensus_output_file)
    files_to_execute.append(uclust_output_file)
    analysis.status = 'EXECUTING USEARCH'
    db.session.commit()
    for f in files_to_execute:
        f.command = f.command.encode('ascii')
        f.dataset_id = analysis.dataset_id 
        f.analysis_id = analysis.id 
        f.chain = file.chain
        print 'Executing: {}'.format(f.command)
        analysis.active_command = f.command
        f.in_use = True 
        db.session.add(f)
        db.session.commit()
        # MAKE THE CALL 
        response = os.system(f.command)
        print 'Response: {}'.format(response)
        if response == 0: 
            f.available = True 
            f.in_use = False
            f.file_size = os.path.getsize(f.path)
            db.session.commit()
        else:
            f.available = False
            f.in_use = False 
            analysis.status = 'FAILED'
            db.session.commit()
    print 'Uclust job for analysis {} has been executed.'.format(analysis)
    return files_to_execute














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






app.register_blueprint(frontend)
nav.init_app(app)



if __name__ == '__main__':
    print 'Running application on port 5000......'
    app.run(host='0.0.0.0', port=5000, debug=True)


