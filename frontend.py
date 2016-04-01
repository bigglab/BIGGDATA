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

from app import *

# Local Imports 
from forms import *
from functions import * 
from models import * 

# blueprint
frontend = Blueprint('frontend', __name__)

nav.register_element('frontend_top', Navbar(
    View('BIGG DATA', 'frontend.index'),
    View('Home', 'frontend.index'),
    Subgroup(
        'Login',
        View('Login', 'frontend.login'),
        View('Logout', 'frontend.logout'),
        ),
    Subgroup(
        'Files', 
        View('My Files', 'frontend.files'), 
        View('Import File', 'frontend.file_download'), 
        View('Import From NCBI', 'frontend.import_sra'), 
        ),
    Subgroup(
        'Run Analysis',
        View('My Datasets', 'frontend.datasets'),
        View('My Analyses', 'frontend.analyses'),
        View('VDJ VIZualizer', 'frontend.vdj_visualizer'),
        Link('Other Tasks', 'under_construction'), 
        ),
    Subgroup(
        'Database', 
        View('Manage Projects', 'projects.manage_projects'),
        View('Browse Sequences', 'frontend.browse_sequences'),
        Link('Download Lots of Data', 'under_construction'),
        Link('Download For Mass Spec', 'under_construction')
        ),
    View('Dashboard', 'frontend.analyses'),
    Subgroup(
        'Documentation', 
        View('BIGG DATA Overview', 'frontend.overview'), 
        View('BIGG DB Schema', 'frontend.schema'), 
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

@frontend.route('/under_construction', methods=['GET', 'POST'])
def under_construction():
    gif_path=retrieve_golden()
    return render_template("under_construction.html", gif_path=gif_path)

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



