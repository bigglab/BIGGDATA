#System Imports
import json
import static
import sys
import os
import time
import random
from shutil import copyfile
import shlex
import validators

from celery import uuid
from celery.result import AsyncResult
from celery.utils.log import get_task_logger

import operator
import ast
from sets import Set
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
    View('Dashboard', 'frontend.analyses'),
        
    Subgroup(
        'Import Data', 
        View('My Files', 'frontend.files'), 
        View('Import File', 'frontend.file_download'),
        View('Import From NCBI', 'frontend.import_sra'), 
        ),
    Subgroup(
        'Manage Data',
        View('Add a Project', 'projects.create_project'),
        View('My Projects', 'projects.manage_projects'),
        View('My Datasets', 'frontend.datasets'),
        # Link('Other Tasks', 'under_construction'), 
        ),
    Subgroup(
        'Run Analysis', 
        View('Run On Dataset', 'frontend.datasets'),
        View('My Analyses', 'frontend.analyses'),
        View('VDJ VIZualizer', 'frontend.vdj_visualizer'),
        # View('Browse Sequences', 'frontend.browse_sequences'),
        # Link('Download Lots of Data', 'under_construction'),
        # Link('Download For Mass Spec', 'under_construction')
        ),
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
    ),
    View('Login', 'frontend.login'),
    ))

nav.register_element('frontend_user', Navbar(
    View('BIGG DATA', 'frontend.index'),
    View('Dashboard', 'frontend.dashboard'),
        
    Subgroup(
        'Import Data', 
        View('My Files', 'frontend.files'), 
        View('Import File', 'frontend.file_download'),
        View('Import From NCBI', 'frontend.import_sra'), 
        ),
    Subgroup(
        'Manage Data',
        View('New Project', 'projects.create_project'),
        View('My Projects', 'projects.manage_projects'),
        View('My Datasets', 'frontend.datasets'),
        # Link('Other Tasks', 'under_construction'), 
        ),
    Subgroup(
        'Run Analysis', 
        View('Create Analysis Pipline', 'frontend.pipeline'),
        View('My Analyses', 'frontend.analyses'),
        View('VDJ VIZualizer', 'frontend.vdj_visualizer'),
        # View('Browse Sequences', 'frontend.browse_sequences'),
        # Link('Download Lots of Data', 'under_construction'),
        # Link('Download For Mass Spec', 'under_construction')
        ),
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
    ),
    View('Logout', 'frontend.logout'),
    ))

@frontend.route('/', methods=['GET', 'POST'])
def index():
    login_form = LoginForm()
    registration_form = RegistrationForm()
    results = db.session.query(User).all()
    return render_template("index.html", results=results, current_user=current_user, login_form = login_form, registration_form = registration_form)

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
                flash('Success: You are logged in!', 'success')

                db.session.refresh(user)

                #if not user.is_migrated:
                #    return migrate_files()

                return redirect(url_for("frontend.dashboard"))
            else: 
                flash("Password doesn't match for " + user.first_name, 'error')
                print "password didnt match for " + user.first_name 
        else: 
            flash("couldn't find that user... try registering a new user", 'normal')
    #also supply create_user_form here for convenience
    registration_form = RegistrationForm()
    return render_template("login.html", login_form=login_form, registration_form=registration_form, current_user=current_user)

@frontend.route("/users/create", methods=["POST"])
def create_user():
    form = RegistrationForm()
    # add some validations / cleansing

    # check to see if that username is already taken
    test_user = db.session.query(User).filter(User.username == form.username.data).first()
    if test_user:
        flash('Error: that username is taken.', 'warning')
        login_form = LoginForm()
        return render_template("login.html", login_form=login_form, create_user_form=form, current_user=current_user)

    user = load_user(form.email.data)
    if user:
        if bcrypt.check_password_hash(user.password_hash, form.password.data):
            login_user(user)
            user.authenticated = True
            db.session.add(user)
            db.session.commit()
        flash('Error: that email has already been registered!', 'error')
        return redirect(url_for(".login"))

    # begin instantiating new user
    new_user = User()
    new_user.first_name = form.first_name.data
    new_user.last_name = form.last_name.data 
    new_user.email = form.email.data
    new_user.username = form.username.data
    new_user.password_hash = bcrypt.generate_password_hash(form.password.data)
    
    # Just authorize automatically, for now
    new_user.authenticated = True 
    new_user.root_path = app.config['USER_ROOT'].replace('<username>', new_user.username)

    #new_user.dropbox_path = '{}/{}{}'.format(app.config['DROPBOX_ROOT'], form.first_name.data, form.last_name.data)
    #new_user.scratch_path = '{}/{}{}'.format(app.config['SCRATCH_ROOT'], form.first_name.data, form.last_name.data)
    db.session.add(new_user)
    db.session.commit()
    login_user(new_user, remember=True)
    flash("Success! New user created and logged in.", 'success')
    #create home and scratch if necessary 
    result = instantiate_user_with_directories.apply_async((new_user.id, ), queue=celery_queue)
    return redirect(url_for("frontend.dashboard"))

# Will not be needed for clean start
# @frontend.route("/users/migrate_files", methods=["GET"])
# @login_required
# def migrate_files():
#
#     if not current_user.is_migrated:
#
#         # update the database with the user root path
#         if not current_user.root_path:
#             current_user.root_path = app.config['USER_ROOT'].replace('<username>', current_user.username)
#             db.session.commit()
#             print 'Updated user root path to : {}'.format(current_user.root_path)
#
#         # migrate files
#         result = migrate_user_files.apply_async(( current_user.id , ), queue=celery_queue)
#     else:
#         flash('Your files have already been migrated.', 'success')
#
#     return redirect(url_for("frontend.index"))

@frontend.route("/logout", methods=["GET"])
def logout():
    """Logout the current user."""
    if current_user.is_authenticated(): 
        user = current_user
        user.authenticated = False
        db.session.add(user)
        db.session.commit()
        logout_user()
        flash('You have been logged out.', 'success')
        return redirect(url_for('.login'))
    else: 
        flash('no user logged in')
        return redirect(url_for('.login'))
        # return render_template("index.html")

@frontend.route('/under_construction', methods=['GET', 'POST'])
def under_construction():
    gif_path=retrieve_golden()
    return render_template("under_construction.html", gif_path=gif_path)

@frontend.route('/dashboard', methods=['GET', 'POST'])
@login_required
def dashboard(status=[]):
    status = request.args.getlist('status')
    analyses = current_user.analyses.all()
    analysis_file_dict = OrderedDict()
    for analysis in sorted(analyses, key=lambda x: x.started, reverse=True): 
        analysis_file_dict[analysis] = analysis.files.all() 
    return render_template("dashboard.html", analyses=analyses, analysis_file_dict=analysis_file_dict, status=status, current_user=current_user)


@frontend.route('/file_upload', methods=['GET', 'POST'])
@login_required
def file_upload():
    form = FileUploadForm()

    # get a list of user datasets for the form
    datasets = Set(current_user.datasets)
    datasets.discard(None)
    datasets.discard(current_user.default_dataset)

    datasets = sorted(datasets, key=lambda x: x.id, reverse=True)
    dataset_tuples = []

    if len(datasets) > 0:
        for dataset in datasets:
            dataset_tuples.append( (str(dataset.id), dataset.name))

        if len(dataset_tuples) > 0:
            #dataset_tuples.append(('new', 'New Dataset'))
            dataset_tuples.insert(0,('new', 'New Dataset'))
            form.dataset.choices = dataset_tuples

    # get a list of user projects for the form
    projects = Set(current_user.projects)
    projects.discard(None)
    projects = sorted(projects, key=lambda x: x.id, reverse=True)
    project_tuples = []

    if len(projects) > 0:
        for project in projects:
            if project.role(current_user) == 'Owner' or project.role(current_user) == 'Editor':
                project_tuples.append( (str(project.id), project.project_name))
        if len(project_tuples) > 0:
            project_tuples.insert(0, ('new', 'New Project'))
            form.project.choices = project_tuples

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
        file.path.replace('//', '') 
 
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
        return render_template("file_upload.html", upload_form=form, download_form=dl_form, current_user=current_user)

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

        # set the dataset options
        datasets = Set(current_user.datasets)
        datasets.discard(None)
        datasets.discard(current_user.default_dataset)

        datasets = sorted(datasets, key=lambda x: x.id, reverse=True)
        dataset_tuples = []

        if len(datasets) > 0:
            for dataset in datasets:
                dataset_tuples.append( (str(dataset.id), dataset.name))

            if len(dataset_tuples) > 0:
                #dataset_tuples.append(('new', 'New Dataset'))
                dataset_tuples.insert(0,('new', 'New Dataset'))
                form.dataset.choices = dataset_tuples

        # get a list of user projects for the form
        projects = Set(current_user.projects)
        projects.discard(None)
        projects = sorted(projects, key=lambda x: x.id, reverse=True)
        project_tuples = []

        if len(projects) > 0:
            for project in projects:
                if project.role(current_user) == 'Owner' or project.role(current_user) == 'Editor':
                    project_tuples.append( (str(project.id), project.project_name))
            if len(project_tuples) > 0:
                project_tuples.insert(0, ('new', 'New Project'))
                form.project.choices = project_tuples

    if request.method == 'POST':
        file = File()
        file.url = form.url.data.rstrip()
        file.name = file.url.split('/')[-1].split('?')[0]
        file.file_type = parse_file_ext(file.name)
        file.description = form.description.data
        file.chain = form.chain.data
        file.paired_partner = form.paired_partner.data 
        file.dataset_id = form.dataset_id.data
        file.path = '{}/{}'.format(current_user.scratch_path.rstrip('/'), file.name)
        file.user_id = current_user.id
        file.available = False 
        file.s3_status = ''
        file.status = ''
        print 'Saving File Metadata to Postgres: {}'.format(file.__dict__)
        db.session.add(file)
        db.session.commit()

#######
        # check if the user has selected the default project (i.e., the user has no projects)
        file_dataset = None
        if form.dataset.data == 'new':
            # create a new dataset here with the name default, add the user and dataset to the new project
            new_dataset = Dataset()
            new_dataset.user_id = current_user.id
            new_dataset.populate_with_defaults(current_user)
            new_dataset.name = 'Dataset'
            db.session.add(new_dataset)
            db.session.flush()
            new_dataset.name = 'Dataset ' + str(new_dataset.id)
            new_dataset.files = [file]
            db.session.commit()
            file_dataset = new_dataset
            flash('New file will be added to dataset "{}".'.format(new_dataset.name), 'success')
        else: # check if the user has selected a project which they have access to
            user_has_permission = False
            for dataset in current_user.datasets:
                if str(dataset.id) == form.dataset.data:
                    dataset.files.append(file)
                    file_dataset = dataset
                    user_has_permission = True

                    # if current_user.default_dataset == None:
                    #     d.cell_types_sequenced = [str(project.cell_types_sequenced)]
                    #     d.species = project.species
            if not user_has_permission:
                flash('Error: you do not have permission to add a file to that dataset.','warning')
        db.session.commit()


        # now do the same with projects, with the qualification that we add the dataset to the project if it's not there already
        # check if the user has selected the default project (i.e., the user has no projects)
        if file_dataset:
            if form.project.data == 'new':
                # create a new project here with the name default, add the user and dataset to the new project
                new_project = Project()
                new_project.user_id = current_user.id
                new_project.project_name = 'Project'
                db.session.add(new_project)
                db.session.flush()
                new_project.project_name = 'Project ' + str(new_project.id)
                new_project.users = [current_user]
                new_project.datasets = [file_dataset]
                new_project.cell_types_sequenced = [str(file_dataset.cell_types_sequenced)]
                new_project.species = file_dataset.species

                db.session.commit()
            else: # check if the user has selected a project which they have access to
                user_has_permission = False
                for project in projects:
                    if str(project.id) == form.project.data:
                        if project.role(current_user) == 'Owner' or project.role(current_user) == 'Editor':
                            # if the dataset is not in the project, add it
                            if file_dataset not in project.datasets:
                                project.datasets.append(file_dataset)
                            user_has_permission = True

                            if current_user.default_dataset == None:
                                file_dataset.cell_types_sequenced = [str(project.cell_types_sequenced)]
                                file_dataset.species = project.species

                            db.session.commit()
                if not user_has_permission:
                    flash('Error: you do not have permission to add a dataset to that project.','warning')
                db.session.commit()        

        # modify the path with the new style, the new hotness if you will
        if file_dataset:
            file.path = '{}/{}/{}'.format(
                current_user.scratch_path.rstrip('/'),
                'Dataset_' + str(file_dataset.id), 
                file.name)

        # check if the file path we settled on is available.
        if os.path.isfile(file.path):
            file.path = os.path.splitext(file.path)[0] + '_1' + os.path.splitext(file.path)[1]
#######

        # Making the status message a single line. 
        status_message = 'Started background task to download file from {}. Saving File To {}. This file will be visible in "My Files", and available for use after the download completes.'.format(file.url, file.path)
        status.append(status_message)
        # status.append('Started background task to download file from {}'.format(file.url))
        # status.append('Saving File To {}'.format(file.path))
        # status.append('This file will be visible in "My Files", and available for use after the download completes.')
        print status 
        
        # result_id NOT WORKING - STILL REDUNDANT IF THEY CLICK TWICE!!
        flash_message = ''
        if not 'async_result_id' in session.__dict__:
            result = download_file.apply_async((file.url, file.path, file.id), {'user_id': current_user.id}, queue=celery_queue)
            #flash_message = 'File downloading from {}. '.format(file.url)
            session['async_result_id'] = result.id
        time.sleep(1)
        
        #async_result = add.AsyncResult(session['async_result_id'])
        # r = async_result.info
        r = result.__dict__
        #r['async_result.info'] = async_result.info 
        r['async_result.info'] = result.info 

        db.session.commit()
        #flash_message = flash_message + 'File uploaded to {}. '.format(file.path)
        #flash(flash_message, 'success')
        return redirect( url_for('frontend.dashboard') )

    else:
        r=''
    return render_template("file_download.html", download_form=form, status=status, r=r, current_user=current_user)

@frontend.route('/files/transfer_to_s3/<int:file_id>', methods=['GET'])
@login_required
def transfer_to_s3(file_id): 
    f = db.session.query(File).filter(File.id==file_id).first()
    if f: 
        f.s3_status = 'Staging On S3'
        db.session.add(f)
        db.session.commit()
        result = transfer_file_to_s3.apply_async((f.id,), queue=celery_queue)
        return redirect(url_for('.files'))

@frontend.route('/files', methods=['GET', 'POST'])
@login_required
def files(status=[], bucket=None, key=None):
    # print request
    db.session.expire_all()
    files = sorted(current_user.files.all(), key=lambda x: x.id, reverse=True)
    dropbox_file_paths = get_dropbox_files(current_user)
    form = Form()

    #creates list of datasets
    projectnames = []
    for x in current_user.projects:
        projectid = str(x.id)
        name = str(x.project_name) 
        projectnames.append(name + ' - ' + projectid)
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
        return render_template("files.html", files=files, dropbox_files=dropbox_file_paths, form=form, current_user=current_user, status=status, projectnames=map(json.dumps, projectnames))
    else: 
        dropbox_file_paths = get_dropbox_files(current_user)
        return render_template("files.html", files=files, dropbox_files=dropbox_file_paths, form=form, current_user=current_user, status=status, projectnames=map(json.dumps, projectnames))

@frontend.route('/files/<int:id>', methods=['GET','POST'])
@login_required
def file(id):
    f = db.session.query(File).filter(File.id==id).first()

    # This part is to ensure that you have permissions to look/edit the selected file
    if f.dataset is None:
        flash('There is no dataset on this file', 'warning')
        if f.user_id is current_user.id:
            edit='edit'
        else:
            edit='none'
    else:
        projects = f.dataset.projects
        if f.user_id is current_user.id:
            edit = 'edit'
        else:
            edit = ''
        for project in projects:
            if project.role(f.user_id) is "Owner" or "Editor":
                edit = 'edit'
            elif project.role(f.user_id) is "Read Only" and edit != 'edit':
                edit = 'read'
            elif edit != 'edit' and edit != 'read':
                edit = None

    if edit is 'None':
        flash('You do not have permission to access this file', 'warning')
        return redirect( url_for('files'))
    else:

        editfileform = FileEditForm()
        if f.dataset != None:
            editfileform.paired_partner.choices = [(x.id, x.name) for x in f.dataset.files if ((x.user_id != None) and (x.name != f.name))]
            editfileform.paired_partner.choices.append((0, None))
        else:
            editfileform.paired_partner.choices = [(x.id, x.name) for x in f.user.files if ((x.user_id != None) and (x.dataset == None) and (x.name != f.name))]
            editfileform.paired_partner.choices.append((0, None))

        if editfileform.validate_on_submit():
            f.name = editfileform.name.data
            if f.paired_partner != None:
                f2 = db.session.query(File).filter(File.id==f.paired_partner).first()

                if f2.id == editfileform.paired_partner.id:
                    flash('Edited ' + f.name, 'success')
                elif editfileform.paired_partner.data is 0:
                    f2 = db.session.query(File).filter(File.id==f.paired_partner).first()
                    f2.paired_partner = None
                    f.paired_partner = None
                    flash('Removed partner', 'success')
                else:
                    f.paired_partner = editfileform.paired_partner.data
                    f3 = db.session.query(File).filter(File.id==f.paired_partner).first()
                    f3.paired_partner=f.id
                    f2.paired_partner=None
            else:
                f.paired_partner = editfileform.paired_partner.data
                f2 = db.session.query(File).filter(File.id==f.paired_partner).first()
                f2.paired_partner = f.id

            f.chain = editfileform.chain.data
            db.session.commit()
            flash('Edited ' + f.name, 'success')
        else:
            flash_errors(editfileform)

        return render_template("file.html", file=f, editfileform=editfileform, edit=edit, current_user=current_user)

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
    datasets = [dataset for dataset in datasets if dataset.name != '__default__']
    #datasets = datasets.filter(Dataset.name != '__default__')
    
    datadict = get_user_dataset_dict(current_user)
    form = CreateDatasetForm()

    projects = Set(current_user.projects)
    projects.discard(None)
    projects = sorted(projects, key=lambda x: x.id, reverse=True)
    project_tuples = []

    if len(projects) > 0:
        for project in projects:
            if project.role(current_user) == 'Owner' or project.role(current_user) == 'Editor':
                project_tuples.append( (str(project.id), project.project_name))
        if len(project_tuples) > 0:
            project_tuples.append(('new', 'New Project'))
            form.project.choices = project_tuples

    if request.method == 'POST':
        if form.name.data: 
            d = Dataset()

            # use default values for the new dataset, if given
            if current_user.default_dataset:
                d.populate_with_defaults(current_user)

            d.name = form.name.data

            if d.name == '__default__':
                flash('Error: cannot create a dataset with that name.', 'warning')
                return redirect(url_for('.datasets'))

            d.description = form.description.data
            d.paired = form.paired.data 
            d.ig_type = form.ig_type.data 
            d.user_id = current_user.id

            db.session.add(d)
            db.session.flush()

            # check if the user has selected the default project (i.e., the user has no projects)
            if form.project.data == 'new':
                # create a new project here with the name default, add the user and dataset to the new project
                new_project = Project()
                new_project.user_id = current_user.id
                new_project.project_name = 'Project'
                db.session.add(new_project)
                db.session.flush()
                new_project.project_name = 'Project ' + str(new_project.id)
                new_project.users = [current_user]
                new_project.datasets = [d]
                new_project.cell_types_sequenced = str(dataset.cell_types_sequenced)
                new_project.species = dataset.species

                db.session.commit()
                return redirect(url_for('.datasets'))
            else: # check if the user has selected a project which they have access to
                for project in projects:
                    if str(project.id) == form.project.data:
                        if project.role(current_user) == 'Owner' or project.role(current_user) == 'Editor':
                            project.datasets.append(d)

                            if current_user.default_dataset == None:
                                d.cell_types_sequenced = [str(project.cell_types_sequenced)]
                                d.species = project.species

                            db.session.commit()
                            return redirect(url_for('.datasets'))
                flash('Error: you do not have permission to add a dataset to that project.','warning')
                return redirect(url_for('.datasets'))
            db.session.commit()
            d.directory = current_user.scratch_path + '/dataset_' + d.id 
            db.session.commit()
        return redirect(url_for('.datasets')) # render_template("datasets.html", datadict=datadict, form=Form())
    else: 
        return render_template("datasets.html", datadict=datadict, form=form, current_user=current_user)

@frontend.route('/datasets/<int:id>', methods=['GET', 'POST'])
@login_required
def dataset(id):

    # print request.__dict__
    print 'finding dataset with {}'.format(id)
    dataset = db.session.query(Dataset).filter(Dataset.id==id).first()

    if not dataset:
        flash('Error: Dataset {} not found.'.format(str(id)), 'warning')
        return redirect( url_for('frontend.datasets') )

    if dataset.role(current_user) == None:
        flash('Error: you do not have permission to access that dataset.', 'warning')
        return redirect( url_for('frontend.datasets') )

    if dataset.name == "__default__":
        flash('Error: Please use this form to edit the default dataset settings.'.format(str(id)), 'warning')
        return redirect( url_for('frontend.edit_default_dataset') )

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
        return render_template("dataset.html", datadict=datadict, form=form, id=id, dataset=dataset, current_user=current_user)
    else: 
        return render_template("dataset.html", datadict=datadict, form=form, id=id, dataset=dataset, current_user=current_user)

@frontend.route('/edit_dataset/<int:id>', methods=['GET', 'POST'])
@login_required
def edit_dataset(id):
    # print request.__dict__
    print 'finding dataset with {}'.format(id)
    dataset = db.session.query(Dataset).filter(Dataset.id==id).first()

    if not dataset:
        flash('Error: Dataset {} not found.'.format(str(id)), 'warning')
        return redirect( url_for('frontend.datasets') )

    if dataset.role(current_user) != "Owner":
        flash('Error: You do not have permission to edit Dataset {}.'.format(str(id)), 'warning')
        return redirect( url_for('frontend.datasets') )

    if dataset.name == "__default__":
        flash('Error: Please use this form to edit the default dataset settings.'.format(str(id)), 'warning')
        return redirect( url_for('frontend.edit_default_dataset') )

    edit_dataset_form = EditDatasetForm()
    edit_dataset_form.dataset_id.data = dataset.id

    # for the other version of the form
    form = AssociateFilesToDatasetForm()
    form.dataset_id.data = dataset.id 
    datadict = {dataset : dataset.files.all()}

    if request.method == 'POST':

        if edit_dataset_form.validate_on_submit():

            dataset.name = edit_dataset_form.name.data
            dataset.description = edit_dataset_form.description.data
            dataset.paired = edit_dataset_form.paired.data
            dataset.ig_type = edit_dataset_form.ig_type.data

            # special treatment for arrays
            try: 
                dataset.cell_types_sequenced = ast.literal_eval(edit_dataset_form.cell_types_sequenced.data)
            except:
                dataset.cell_types_sequenced = [edit_dataset_form.cell_types_sequenced.data] 

            try: 
                dataset.chain_types_sequenced = ast.literal_eval(edit_dataset_form.chain_types_sequenced.data)
            except: 
                dataset.chain_types_sequenced = [edit_dataset_form.chain_types_sequenced.data]

            try:
                dataset.primary_data_files_ids = ast.literal_eval(edit_dataset_form.primary_data_files_ids.data)
            except:
                if edit_dataset_form.primary_data_files_ids.data.isdigit():
                    dataset.primary_data_files_ids = [int(edit_dataset_form.primary_data_files_ids.data)]

            dataset.lab_notebook_source = edit_dataset_form.lab_notebook_source.data
            dataset.sequencing_submission_number = edit_dataset_form.sequencing_submission_number.data
            dataset.contains_rna_seq_data = edit_dataset_form.contains_rna_seq_data.data
            dataset.reverse_primer_used_in_rt_step = edit_dataset_form.reverse_primer_used_in_rt_step.data
            dataset.list_of_polymerases_used = edit_dataset_form.list_of_polymerases_used.data
            dataset.sequencing_platform = edit_dataset_form.sequencing_platform.data
            dataset.target_reads = edit_dataset_form.target_reads.data
            dataset.cell_markers_used = edit_dataset_form.cell_markers_used.data
            dataset.read_access = edit_dataset_form.read_access.data
            dataset.owners_of_experiment = edit_dataset_form.owners_of_experiment.data
            dataset.adjuvant = edit_dataset_form.adjuvant.data
            dataset.species = edit_dataset_form.species.data
            dataset.cell_selection_kit_name = edit_dataset_form.cell_selection_kit_name.data
            dataset.isotypes_sequenced = edit_dataset_form.isotypes_sequenced.data
            dataset.post_sequencing_processing_dict = edit_dataset_form.post_sequencing_processing_dict.data
            dataset.sample_preparation_date = edit_dataset_form.sample_preparation_date.data
            dataset.gsaf_barcode = edit_dataset_form.gsaf_barcode.data
            dataset.mid_tag = edit_dataset_form.mid_tag.data
            dataset.cell_number = edit_dataset_form.cell_number.data
            dataset.primer_set_name = edit_dataset_form.primer_set_name.data
            dataset.template_type = edit_dataset_form.template_type.data
            dataset.experiment_name = edit_dataset_form.experiment_name.data
            dataset.person_who_prepared_library = edit_dataset_form.person_who_prepared_library.data
            dataset.pairing_technique = edit_dataset_form.pairing_technique.data
            dataset.json_id = edit_dataset_form.json_id.data

            db.session.commit()
            db.session.refresh(dataset)


            if edit_dataset_form.use_as_default.data == True:
                current_user.change_dataset_defaults(dataset)


            flash('Success! Your dataset has been updated.', 'success')
            return redirect ( url_for( 'frontend.datasets', id = id ) )

        else:
            flash_errors(edit_dataset_form)
            return render_template("edit_dataset.html", 
                datadict=datadict, 
                form=form, 
                id=id, 
                dataset=dataset, 
                edit_dataset_form = edit_dataset_form, 
                current_user=current_user, 
                default_dataset = current_user.default_dataset)

    else: # this is the get method

        # set the form variables appropriately
        edit_dataset_form.name.data = dataset.name
        edit_dataset_form.description.data = dataset.description
        edit_dataset_form.paired.data = dataset.paired
        edit_dataset_form.ig_type.data = dataset.ig_type

        edit_dataset_form.cell_types_sequenced.data = dataset.cell_types_sequenced
        edit_dataset_form.chain_types_sequenced.data = dataset.chain_types_sequenced
        edit_dataset_form.primary_data_files_ids.data = dataset.primary_data_files_ids

        edit_dataset_form.lab_notebook_source.data = dataset.lab_notebook_source
        edit_dataset_form.sequencing_submission_number.data = dataset.sequencing_submission_number
        edit_dataset_form.contains_rna_seq_data.data = dataset.contains_rna_seq_data
        edit_dataset_form.reverse_primer_used_in_rt_step.data = dataset.reverse_primer_used_in_rt_step
        edit_dataset_form.list_of_polymerases_used.data = dataset.list_of_polymerases_used
        edit_dataset_form.sequencing_platform.data = dataset.sequencing_platform
        edit_dataset_form.target_reads.data = dataset.target_reads
        edit_dataset_form.cell_markers_used.data = dataset.cell_markers_used
        edit_dataset_form.read_access.data = dataset.read_access
        edit_dataset_form.owners_of_experiment.data = dataset.owners_of_experiment
        edit_dataset_form.adjuvant.data = dataset.adjuvant
        edit_dataset_form.species.data = dataset.species
        edit_dataset_form.cell_selection_kit_name.data = dataset.cell_selection_kit_name
        edit_dataset_form.isotypes_sequenced.data = dataset.isotypes_sequenced
        edit_dataset_form.post_sequencing_processing_dict.data = dataset.post_sequencing_processing_dict
        edit_dataset_form.sample_preparation_date.data = dataset.sample_preparation_date
        edit_dataset_form.gsaf_barcode.data = dataset.gsaf_barcode
        edit_dataset_form.mid_tag.data = dataset.mid_tag
        edit_dataset_form.cell_number.data = dataset.cell_number
        edit_dataset_form.primer_set_name.data = dataset.primer_set_name
        edit_dataset_form.template_type.data = dataset.template_type
        edit_dataset_form.experiment_name.data = dataset.experiment_name
        edit_dataset_form.person_who_prepared_library.data = dataset.person_who_prepared_library
        edit_dataset_form.pairing_technique.data = dataset.pairing_technique
        edit_dataset_form.json_id.data = dataset.json_id

        return render_template("edit_dataset.html", 
            datadict=datadict, 
            form=form, 
            id=id, 
            dataset=dataset, 
            edit_dataset_form = edit_dataset_form, 
            current_user=current_user, 
            default_dataset = current_user.default_dataset)

@frontend.route('/edit_dataset/default', methods=['GET', 'POST'])
@login_required
def edit_default_dataset():
    
    dataset = db.session.query(Dataset). \
                filter(Dataset.user_id==current_user.id). \
                filter(Dataset.name == '__default__').first()

    # if there isn't a dataset with the name __default__, create one
    if not dataset: 
        dataset = Dataset()
        dataset.name = '__default__'
        dataset.user_id = current_user.id
        db.session.add(dataset)
        db.session.commit()
        db.session.refresh(dataset)
        print 'added default dataset\n\n'

    edit_dataset_form = EditDatasetForm()
    edit_dataset_form.dataset_id.data = dataset.id

    # for the other version of the form
    form = AssociateFilesToDatasetForm()
    form.dataset_id.data = dataset.id 
    datadict = {dataset : dataset.files.all()}

    if request.method == 'POST':

        if edit_dataset_form.validate_on_submit():

            #dataset.name = edit_dataset_form.name.data
            #dataset.description = edit_dataset_form.description.data
            dataset.paired = edit_dataset_form.paired.data
            dataset.ig_type = edit_dataset_form.ig_type.data

            # special treatment for arrays
            try: 
                dataset.cell_types_sequenced = ast.literal_eval(edit_dataset_form.cell_types_sequenced.data)
            except:
                dataset.cell_types_sequenced = [edit_dataset_form.cell_types_sequenced.data] 

            try: 
                dataset.chain_types_sequenced = ast.literal_eval(edit_dataset_form.chain_types_sequenced.data)
            except: 
                dataset.chain_types_sequenced = [edit_dataset_form.chain_types_sequenced.data]

            try:
                dataset.primary_data_files_ids = ast.literal_eval(edit_dataset_form.primary_data_files_ids.data)
            except:
                if edit_dataset_form.primary_data_files_ids.data.isdigit():
                    dataset.primary_data_files_ids = [int(edit_dataset_form.primary_data_files_ids.data)]

            dataset.lab_notebook_source = edit_dataset_form.lab_notebook_source.data
            dataset.sequencing_submission_number = edit_dataset_form.sequencing_submission_number.data
            dataset.contains_rna_seq_data = edit_dataset_form.contains_rna_seq_data.data
            dataset.reverse_primer_used_in_rt_step = edit_dataset_form.reverse_primer_used_in_rt_step.data
            dataset.list_of_polymerases_used = edit_dataset_form.list_of_polymerases_used.data
            dataset.sequencing_platform = edit_dataset_form.sequencing_platform.data
            dataset.target_reads = edit_dataset_form.target_reads.data
            dataset.cell_markers_used = edit_dataset_form.cell_markers_used.data
            dataset.adjuvant = edit_dataset_form.adjuvant.data
            dataset.species = edit_dataset_form.species.data
            dataset.cell_selection_kit_name = edit_dataset_form.cell_selection_kit_name.data
            dataset.isotypes_sequenced = edit_dataset_form.isotypes_sequenced.data
            dataset.post_sequencing_processing_dict = edit_dataset_form.post_sequencing_processing_dict.data
            dataset.mid_tag = edit_dataset_form.mid_tag.data
            dataset.cell_number = edit_dataset_form.cell_number.data
            dataset.primer_set_name = edit_dataset_form.primer_set_name.data
            dataset.template_type = edit_dataset_form.template_type.data
            dataset.experiment_name = edit_dataset_form.experiment_name.data
            dataset.person_who_prepared_library = edit_dataset_form.person_who_prepared_library.data
            dataset.pairing_technique = edit_dataset_form.pairing_technique.data

            db.session.commit()
            flash('Success! Your dataset has been updated.', 'success')
            return redirect ( url_for( 'frontend.datasets', id = id ) )

        else:
            flash_errors(edit_dataset_form)
            return render_template("edit_dataset_defaults.html", datadict=datadict, form=form, id=id, dataset=dataset, edit_dataset_form = edit_dataset_form, current_user=current_user)

    else: # method = GET #

        # set the form variables appropriately
        # edit_dataset_form.description.data = dataset.description
        edit_dataset_form.paired.data = dataset.paired
        edit_dataset_form.ig_type.data = dataset.ig_type

        edit_dataset_form.cell_types_sequenced.data = dataset.cell_types_sequenced
        edit_dataset_form.chain_types_sequenced.data = dataset.chain_types_sequenced
        edit_dataset_form.primary_data_files_ids.data = dataset.primary_data_files_ids

        edit_dataset_form.lab_notebook_source.data = dataset.lab_notebook_source
        edit_dataset_form.sequencing_submission_number.data = dataset.sequencing_submission_number
        edit_dataset_form.contains_rna_seq_data.data = dataset.contains_rna_seq_data
        edit_dataset_form.reverse_primer_used_in_rt_step.data = dataset.reverse_primer_used_in_rt_step
        edit_dataset_form.list_of_polymerases_used.data = dataset.list_of_polymerases_used
        edit_dataset_form.sequencing_platform.data = dataset.sequencing_platform
        edit_dataset_form.target_reads.data = dataset.target_reads
        edit_dataset_form.cell_markers_used.data = dataset.cell_markers_used
        #edit_dataset_form.read_access.data = dataset.read_access
        #edit_dataset_form.owners_of_experiment.data = dataset.owners_of_experiment
        edit_dataset_form.adjuvant.data = dataset.adjuvant
        edit_dataset_form.species.data = dataset.species
        edit_dataset_form.cell_selection_kit_name.data = dataset.cell_selection_kit_name
        edit_dataset_form.isotypes_sequenced.data = dataset.isotypes_sequenced
        edit_dataset_form.post_sequencing_processing_dict.data = dataset.post_sequencing_processing_dict
        #edit_dataset_form.sample_preparation_date.data = dataset.sample_preparation_date
        #edit_dataset_form.gsaf_barcode.data = dataset.gsaf_barcode
        edit_dataset_form.mid_tag.data = dataset.mid_tag
        edit_dataset_form.cell_number.data = dataset.cell_number
        edit_dataset_form.primer_set_name.data = dataset.primer_set_name
        edit_dataset_form.template_type.data = dataset.template_type
        edit_dataset_form.experiment_name.data = dataset.experiment_name
        edit_dataset_form.person_who_prepared_library.data = dataset.person_who_prepared_library
        edit_dataset_form.pairing_technique.data = dataset.pairing_technique
        #edit_dataset_form.json_id.data = dataset.json_id

        return render_template("edit_default_dataset.html", datadict=datadict, form=form, id=id, dataset=dataset, edit_dataset_form = edit_dataset_form, current_user=current_user)


@frontend.route('/analysis', methods=['GET', 'POST'])
@login_required
def analyses(status=[]):
    status = request.args.getlist('status')
    analyses = current_user.analyses.all()
    analysis_file_dict = OrderedDict()
    for analysis in sorted(analyses, key=lambda x: x.started, reverse=True): 
        analysis_file_dict[analysis] = analysis.files.all() 
    return render_template("analyses.html", analyses=analyses, analysis_file_dict=analysis_file_dict, status=status, current_user=current_user)

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
    # cdr3_aa_counts = db.engine.execute("select  cdr3_aa, count(1) from annotation a WHERE a.analysis_id = {} GROUP BY cdr3_aa ORDER BY count(1) DESC;".format(analysis.id)).fetchall()
    # v_hit_counts = db.engine.execute("select  v_top_hit, count(1) from annotation a WHERE a.analysis_id = {} GROUP BY v_top_hit ORDER BY count(1) DESC;".format(analysis.id)).fetchall()
    # v_hit_loci_counts = db.engine.execute("select  v_top_hit_locus, count(1) from annotation a WHERE a.analysis_id = {} GROUP BY v_top_hit_locus ORDER BY count(1) DESC;".format(analysis.id)).fetchall()
    return render_template("analysis.html", analysis=analysis, current_user=current_user) #, cdr3_aa_counts=cdr3_aa_counts, v_hit_counts=v_hit_counts, v_hit_loci_counts=v_hit_loci_counts)
    
@frontend.route('/analysis/mixcr/<int:dataset_id>', methods=['GET', 'POST'])
@login_required
def mixcr(dataset_id, status=[]):
    dataset = db.session.query(Dataset).filter(Dataset.id==dataset_id).first()

    try:
        if dataset and dataset.name == "__default__":
            flash('Error: that dataset cannot be analyzed','warning')
            return redirect( url_for('frontend.dashboard') )
    except:
        flash('Error: that dataset cannot be analyzed','warning')
        return redirect( url_for('frontend.dashboard') )

    form = CreateMixcrAnalysisForm()
    status = []
    if request.method == 'POST' and dataset:
        status.append('MIXCR Launch Detected')
        result = run_mixcr_with_dataset_id.apply_async( ( ),  
            { 'dataset_id': dataset_id,
            'analysis_name': form.name.data, 
            'analysis_description': form.description.data, 
            'user_id': current_user.id, 
            'trim': form.trim.data, 
            'cluster': form.cluster.data}, queue=celery_queue)
        status.append(result.__repr__())
        status.append('Background Execution Started To Analyze Dataset {}'.format(dataset.id))
        time.sleep(1)
        # return render_template("mixcr.html", dataset=dataset, form=form, status=status) 
        analyses = current_user.analyses.all()
        analysis_file_dict = OrderedDict()
        for analysis in sorted(analyses, key=lambda x: x.started, reverse=True): 
            analysis_file_dict[analysis] = analysis.files.all()

        return redirect(url_for('frontend.dashboard')) 
        #return redirect(url_for('.analyses', status=status))
        # return render_template("analyses.html", analyses=analyses, analysis_file_dict=analysis_file_dict, status=status)
    else: 
        return render_template("mixcr.html", dataset=dataset, form=form, status=status, current_user=current_user) 

@frontend.route('/analysis/pandaseq/<int:dataset_id>', methods=['GET', 'POST'])
@login_required
def pandaseq(dataset_id, status=[]):
    dataset = db.session.query(Dataset).filter(Dataset.id==dataset_id).first()

    try:
        if dataset and dataset.name == "__default__":
            flash('Error: that dataset cannot be analyzed','warning')
            return redirect( url_for('frontend.dashboard') )
    except:
        flash('Error: that dataset cannot be analyzed','warning')
        return redirect( url_for('frontend.dashboard') )

    form = CreatePandaseqAnalysisForm()
    status = []
    if request.method == 'POST' and dataset:
        status.append('PANDASEQ Launch Detected')
        result = run_pandaseq_with_dataset_id.apply_async((dataset_id, ),  {'analysis_name': form.name.data, 'analysis_description': form.description.data, 'user_id': current_user.id, 'algorithm': form.algorithm.data}, queue=celery_queue)
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
        return render_template("pandaseq.html", dataset=dataset, form=form, status=status, current_user=current_user) 


@frontend.route('/analysis/create/<int:dataset_id>', methods=['GET', 'POST'])
@login_required
def create_analysis(dataset_id, status=[]):
    dataset = db.session.query(Dataset).filter(Dataset.id==dataset_id).first()

    try:
        if dataset and dataset.name == "__default__":
            flash('Error: that dataset cannot be analyzed','warning')
            return redirect( url_for('frontend.dashboard') )
    except:
        flash('Error: that dataset cannot be analyzed','warning')
        return redirect( url_for('frontend.dashboard') )

    form = CreateAnalysisForm()
    file_options = map(lambda f: [f.id, f.name], [f for f in dataset.files if 'FASTQ' in f.file_type])
    form.file_ids.choices = file_options
    status = []
    if request.method == 'POST' and dataset:
        status.append('Analysis Launch Detected')
        result = run_analysis.apply_async(
            (None, dataset_id, form.file_ids.data, ),  
                {'analysis_type': 'IGFFT', 
                'analysis_name': form.name.data, 
                'analysis_description': form.description.data, 
                'trim': form.trim.data, 
                'cluster': form.cluster.data, 
                'overlap': form.overlap.data, 
                'paired': form.paired.data,
                'user_id': current_user.id }, 
            queue=celery_queue)
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
        return render_template("create_analysis.html", dataset=dataset, form=form, status=status, current_user=current_user) 


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
    return render_template("browse_sequences.html", form=form, files=files, datasets=datasets, datadict=datadict, err=err, gif_path=golden, seq_count=seq_count, ann_count=ann_count, current_user=current_user)


@frontend.route('/developers/schema', methods=['GET'])
def schema():
    schema_url = url_for('static', filename='schema.png')
    return render_template("schema.html", schema_url=schema_url, current_user=current_user)

@frontend.route('/developers/overview', methods=['GET'])
def overview():
    schema_url = url_for('static', filename='schema.png')
    infrastructure_image_url = url_for('static', filename='bigg_data_infrastructure.png')
    return render_template("infrastructure.html", schema_url=schema_url, infrastructure_image_url=infrastructure_image_url, current_user=current_user)


@frontend.route('/vdjviz', methods=['GET'])
def vdj_visualizer():
    vdjviz_url = 'http://vdjviz.rsldrt.com:9000/account'
    return render_template("vdjviz.html", vdjviz_url=vdjviz_url, current_user=current_user)



@frontend.route('/add1/<num>')
# @oauth.oauth_required
def add_page(num):
    num = int(num)
    result = add.delay(1,num)
    time.sleep(3)
    async_result = add.AsyncResult(result.id)
    r = async_result.info
    template = templateEnv.get_template('add1.html')
    return template.render(input=num, result=r, current_user=current_user)

    # return make_response(render_template('index.html'))
    # return '<h4>Hi</h4>'



@frontend.route('/example', methods=['GET', 'POST'])
def example_index():
    if request.method == 'GET':
        return render_template('example_index.html', email=session.get('email', 'example'), current_user=current_user)
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



@frontend.route('/files/import_sra', methods=['GET', 'POST'])
@login_required
def import_sra():
    form = ImportSraAsDatasetForm()

    # set the dataset options
    datasets = Set(current_user.datasets)
    datasets.discard(None)
    datasets.discard(current_user.default_dataset)

    datasets = sorted(datasets, key=lambda x: x.id, reverse=True)
    dataset_tuples = []

    if len(datasets) > 0:
        for dataset in datasets:
            dataset_tuples.append( (str(dataset.id), dataset.name))

        if len(dataset_tuples) > 0:
            #dataset_tuples.append(('new', 'New Dataset'))
            dataset_tuples.insert(0,('new', 'New Dataset'))
            form.dataset.choices = dataset_tuples
    else:
        form.dataset.choices = [ ('new', 'New Dataset') ]


    # get a list of user projects for the form
    projects = Set(current_user.projects)
    projects.discard(None)
    projects = sorted(projects, key=lambda x: x.id, reverse=True)
    project_tuples = []

    if len(projects) > 0:
        for project in projects:
            if project.role(current_user) == 'Owner' or project.role(current_user) == 'Editor':
                project_tuples.append( (str(project.id), project.project_name))
        if len(project_tuples) > 0:
            project_tuples.insert(0, ('new', 'New Project'))
            form.project.choices = project_tuples
    else:
        form.project.choices = [('new', 'New Project')]

    result = None
    status = []
    if request.method == 'POST':
        if 'SRR' in form.accession.data: 
            status.append('Import SRA Started for Accession {}'.format(form.accession.data))
            status.append('Once complete, a dataset named {} will automatically be created containing these single or paired-end read files'.format(form.accession.data))
            result = import_from_sra.apply_async((form.accession.data,), {'name': form.accession.data, 'user_id': current_user.id, 'chain':form.chain.data, 'project_selection':form.project.data , 'dataset_selection':form.dataset.data}, queue=celery_queue)
            return redirect( url_for('frontend.dashboard') )
        else: 
            status.append('Accession does not start with SRR or ERR?')
            return render_template('sra_import.html', status=status, form=form, result=result, current_user=current_user)

    return render_template('sra_import.html', status=status, form=form, result=result, current_user=current_user)

@frontend.route('/delete_task/<task_id>', methods=['GET', 'POST'])
@login_required
def delete_task(task_id):
    tasks = Set(current_user.celery_tasks)
    tasks.discard(None)
    tasks = Set( sorted(tasks, key=lambda x: x.id, reverse=True) )

    discard_task = ''

    for task in tasks:
        if str(task.id) == task_id:

            logfile = '{}/{}.log'.format( current_user.scratch_path.rstrip('/') , task.async_task_id )

            print "Deleting {}...".format( logfile )
            try:
                os.remove( logfile )
            except:
                pass
            discard_task = task

    tasks.discard( discard_task )
    current_user.celery_tasks = tasks
    db.session.commit()

    return json_celery_log()
    #return redirect( url_for('frontend.dashboard') )

@frontend.route('/json_celery_log', methods=['GET', 'POST'])
@login_required
def json_celery_log():


    interval = 60000
    tasks = Set(current_user.celery_tasks)
    tasks.discard(None)
    tasks = sorted(tasks, key=lambda x: x.id, reverse=True)

    tasks_pending = False

    message = ''

    if len(tasks) > 0:

        for task in tasks:
            entry = ''

            async_task_result = celery.AsyncResult(task.async_task_id)

            if task.result:
                task_message = task.result
            else:
                task_message = ""

            if task.status == 'STARTED':
                task_heading_color = 'green'
                tasks_pending = True
            elif task.status == 'SUCCESS': 
                task_heading_color = 'green'
            elif task.status == 'FAILURE':
                task_heading_color = 'red'
            else:
                task_heading_color = 'green'

            log_entries = ''

            logfile = '{}/{}.log'.format( current_user.scratch_path.rstrip('/') , task.async_task_id )

            async_task_progress = ''

            try:
                with open(logfile) as file:
                    for line in file:
                        color = 'black'
                        if 'WARNING' in line:
                            color = 'orange'
                        elif 'ERROR' in line:
                            color = 'red'

                        # Progress can be passed in the logfile as a 'progress' line    
                        if 'PROGRESS' in line:
                            line_parts = tuple(line.strip().split(']'))
                            progress_info = tuple(line_parts[1].strip().split(','))

                            try:
                                async_task_state = 'PROGRESS'
                                async_task_status = progress_info[1]
                                async_task_current = progress_info[2]
                                async_task_total = progress_info[3]
                                async_task_units = progress_info[4]
                            except Exception, message:
                                print "Error: {}".format(message)
                            else:
                                if async_task_units == '%':
                                    progress_message = '{} {} %'.format(async_task_status, async_task_current)
                                else:
                                    progress_message = '{} {}/{} {}'.format(async_task_status, async_task_current, async_task_total, async_task_units)

                                try:
                                    percent = int( float( int(async_task_current) ) / float( int(async_task_total) ) * 100 )
                                except:
                                    percent = 0

                                if percent == 100:
                                    async_task_state = ''
                                    async_task_current = 0
                                    async_task_total = 0
                                    async_task_status = ''
                                    async_task_units = ''
                                    async_task_progress = ''
                                else:
                                    async_task_progress = """
                                        <div class="progress" style="position: relative;">
                                            <div class="progress-bar progress-bar-info" role="progressbar" aria-valuenow="{0}" aria-valuemin="0" aria-valuemax="{1}" style="width:{2}%;"></div>
                                           <span class = "progress-value" style="position:absolute; right:0; left:0; width:100%; text-align:center; z-index:2; color:black;">{3}</span>
                                        </div>
                                    """.format(  async_task_current, async_task_total, percent, progress_message)

                        else:
                            log_entries = log_entries + '<font color="{}">{}</font><br>\n'.format( color , line )
            except:
                pass

            if log_entries == '':
                log_entries = '<br>\n'

            # Check for any ongoing progress from a task via the AMPQ server
            # If there is progress, add a progress bar! If there is a status, post a status message

            if async_task_progress == '' and task.status != 'DOWNLOADING' and task.status != 'SUCCESS' and task.status != 'FAILURE' and async_task_result.state == 'PROGRESS':
                try:
                    async_task_state = async_task_result.state
                    async_task_current = async_task_result.info.get('current')
                    async_task_total = async_task_result.info.get('total')
                    async_task_status = async_task_result.info.get('status')
                    async_task_units = async_task_result.info.get('units')

                except Exception, exception: 
                    print 'There was an error in getting the task progress: {}'.format(exception)
                else:
                    #async_task_progress = """[{}] {}: {}/{} {}<br>\n""".format( async_task_state, async_task_status, async_task_current, async_task_total, async_task_units)
                    if async_task_units == '%':
                        progress_message = '{} {} %'.format(async_task_status, async_task_current)
                    else:
                        progress_message = '{} {}/{} {}'.format(async_task_status, async_task_current, async_task_total, async_task_units)

                    try:
                        percent = int( float( int(async_task_current) ) / float( int(async_task_total) ) * 100 )
                    except:
                        percent = 0

                    async_task_progress = """
                        <div class="progress" style="position: relative;">
                            <div class="progress-bar progress-bar-info" role="progressbar" aria-valuenow="{0}" aria-valuemin="0" aria-valuemax="{1}" style="width:{2}%;"></div>
                           <span class = "progress-value" style="position:absolute; right:0; left:0; width:100%; text-align:center; z-index:2; color:black;">{3}</span>
                        </div>
                    """.format(  async_task_current, async_task_total, percent, progress_message)

            if async_task_progress == '' and task.status != 'DOWNLOADING' and task.status != 'SUCCESS' and task.status != 'FAILURE' and async_task_result.state == 'STATUS':
                try:
                    async_task_state = async_task_result.state
                    async_task_status = async_task_result.info.get('status')
                except Exception, exception: 
                    print 'There was an error in getting the task progress: {}'.format(exception)
                else:
                    async_task_progress = """
                    {}<br>
                    """.format(  async_task_status )

            entry = """
            <table width="100%">
                <tbody>
                    <tr>
                        <td><font color="{}">[Task {} ({}) - {}] {}</font><br>
                        {}{}</td>
                        <td align="right" valign="top">
                        <span class="pencil glyphicon glyphicon-remove" style="margin-right: 3px; color:black; cursor: pointer; cursor: hand;" onclick=delete_task('{}')></span>

                        </td>
                    </tr>
                </tbody>
            </table>
            <br>""".format( task_heading_color , task.id, task.name , task.status, task_message , log_entries, async_task_progress , url_for( 'frontend.delete_task', task_id = task.id )  )

            message = message + entry

    else:
        message = """
            <table width="100%">
                <tbody>
                    <tr>
                        <td>There are no tasks running at this time. (Checking again in <span id="interval">60</span> s...)</td>
                        
                    </tr>
                </tbody>
            </table>
            <br>"""

        ""
        interval = 60000

    if tasks_pending:
        interval = 2500

    response = {
        'message': message,
        'interval': interval,
        'current': 1,
        'total': 1
     }  # this is the exception raised



    return jsonify( response )

from flask import Markup
@frontend.route('/test_celery_log', methods=['GET', 'POST'])
@login_required
def test_celery_log():

    result = output_celery_log.apply_async( (), { 'user_id': current_user.id, }, queue=celery_queue )

    message = Markup('<a href="{}">Test Again</a>.'.format( url_for('frontend.test_celery_log') ) )
    flash(message , 'success' )

    time.sleep(3)    
    return redirect( url_for('frontend.dashboard') )

    # Here in task:
    self.update_state(state='PROGRESS',
                        meta={ 'current': i, 'total': total, 'status': message} )


@frontend.route('/pipeline', methods=['GET', 'POST'])
@login_required
def pipeline():

    build_pipeline_form = BuildPipelineForm(request.form)

    # set the dataset options
    datasets = Set(current_user.datasets)
    datasets.discard(None)
    datasets.discard(current_user.default_dataset)

    datasets = sorted(datasets, key=lambda x: x.id, reverse=True)
    dataset_tuples = []
    new_tuples = []

    dataset_file_dict = {}
    dataset_project_dict = {}

    # get a list of user projects for the form
    projects = Set(current_user.projects)
    projects.discard(None)
    projects = sorted(projects, key=lambda x: x.id, reverse=True)
    project_tuples = []

    # Create form choices for datasets and files
    if len(datasets) > 0:
        for dataset in datasets:
            dataset_tuples.append( (str(dataset.id), dataset.name))
            new_tuples.append( (str(dataset.id), dataset.name))

            # build a dictionary indicating a project to which each dataset belongs
            if len(dataset.projects) > 0 and dataset.projects[0] != None:
                dataset_project_dict[str(dataset.id)] = str(dataset.projects[0].id)
            else:
                dataset_project_dict[str(dataset.id)] = 'new'

            # build a dictionary entry indicating the files in each dataset ('dataset_id':{'file_id':'file_name'})
            file_id_dict = {}
            for file in dataset.files:
                file_id_dict[ str(file.id) ] = file.name 

            dataset_file_dict[ str(dataset.id) ] = file_id_dict

        # This form does not need a new dataset option
        build_pipeline_form.dataset.choices = dataset_tuples

        # Other forms have the option to insert a new dataset
        if len(dataset_tuples) > 0:
            #dataset_tuples.append(('new', 'New Dataset'))
            #new_tuples = dataset_tuples
            new_tuples.insert(0,('new', 'New Dataset'))
            build_pipeline_form.output_dataset.choices = new_tuples
    else:
        build_pipeline_form.output_dataset.choices = [ ('new', 'New Dataset') ]

    # Create form choices for projects
    if len(projects) > 0:
        for project in projects:
            if project.role(current_user) == 'Owner' or project.role(current_user) == 'Editor':
                project_tuples.append( (str(project.id), project.project_name))
        if len(project_tuples) > 0:
            project_tuples.insert(0, ('new', 'New Project'))
            build_pipeline_form.output_project.choices = project_tuples
    else:
        build_pipeline_form.output_project.choices = [ ('new', 'New Dataset') ]

    # list of tuples to set arbitrary HTML tag attributes
    # passed to JQUERY to set attributes
    # ('selector' , 'attribute' , 'attribute value')
    runtime_attributes = []
    form_warning_style = 'border: 2px solid #d66; border-radius: 7px; box-shadow: 0 0 10px #d66;'

    # used to scroll carousel to first error on form
    first_error_item = None


    if request.method == 'POST':

        ##### Validate the Form #####
        form_valid = True

        if build_pipeline_form.file_source.data == 'file_dataset': 

            if build_pipeline_form.dataset_files.data == []:
                flash('Error: you must select one or more files to analyze.','warning')
                runtime_attributes.append(('select[id=dataset_files]', 'style', form_warning_style))                                   
                form_valid = False
                first_error_item = 0
            else:
                file_ids = build_pipeline_form.dataset_files.data

                for file_id in file_ids:
                    print file_id
                    file = db.session.query(File).get(file_id)
                    if not file:
                        flash('Error: file {} not found.'.format(file.id),'warning')
                        runtime_attributes.append(('select[id=dataset_files]', 'style', form_warning_style))                                           
                        form_valid = False
                        first_error_item = 0

                    elif file.user_id != current_user.id:
                        flash('Error: you do not have permission to analyze this file: {}'.format(file.name),'warning')
                        runtime_attributes.append(('select[id=dataset_files]', 'style', form_warning_style))                   
                        form_valid = False
                        first_error_item = 0

        elif build_pipeline_form.file_source.data == 'file_gsaf':
 
            if build_pipeline_form.gsaf_url.data == '':
                flash('Error: you must provide a valid GSAF URL to upload a file, or choose another file source.','warning')
                runtime_attributes.append(('input[id=gsaf_url]', 'style', form_warning_style))                   
                form_valid = False
                first_error_item = 0
            elif not validators.url(build_pipeline_form.gsaf_url.data):
                flash('Error: you must provide a valid GSAF URL to upload a file, or choose another file source.','warning')
                runtime_attributes.append(('input[id=gsaf_url]', 'style', form_warning_style))                   
                first_error_item = 0
                form_valid = False

        elif build_pipeline_form.file_source.data == 'file_upload':

            if build_pipeline_form.download_url.data == '':
                flash('Error: you must provide a URL to upload a file, or choose another file source.','warning')
                runtime_attributes.append(('input[id=download_url]', 'style', form_warning_style))   
                first_error_item = 0
                form_valid = False
            elif not validators.url(build_pipeline_form.download_url.data):
                flash('Error: you must provide a valid URL to upload a file, or choose another file source.','warning')
                runtime_attributes.append(('input[id=download_url]', 'style', form_warning_style))   
                first_error_item = 0
                form_valid = False

        elif build_pipeline_form.file_source.data == 'file_ncbi': 

            if build_pipeline_form.ncbi_accession.data == '':
                flash('Error: you must choose an NCBI accession, or choose another file source.','warning')
                runtime_attributes.append(('input[id=ncbi_accession]', 'style', form_warning_style))   
                first_error_item = 0
                form_valid = False

        else: # file_source.data == 'None':
            flash('Error: you must select a file source.','warning')
            runtime_attributes.append(('div[name=file_source]', 'style', form_warning_style))   
            first_error_item = 0
            form_valid = False

        if build_pipeline_form.trim.data:

            if build_pipeline_form.trim_slidingwindow.data:
            
                if build_pipeline_form.trim_slidingwindow_size.data and not build_pipeline_form.trim_slidingwindow_size.data > 0: # must be positive integer
                    flash('Error: if trimming is selected, you must choose a valid sliding window size.','warning')
                    runtime_attributes.append(('input[id=trim_slidingwindow_size]', 'style', form_warning_style))                                   
                    if first_error_item == None: first_error_item = 1
                    form_valid = False

                if build_pipeline_form.trim_slidingwindow_quality.data and not build_pipeline_form.trim_slidingwindow_quality.data > 0: # must be positive integer
                    flash('Error: if trimming is selected, you must choose a valid sliding window quality.','warning')
                    runtime_attributes.append(('input[id=trim_slidingwindow_quality]', 'style', form_warning_style))                                   
                    if first_error_item == None: first_error_item = 1
                    form_valid = False

        if build_pipeline_form.analysis_type.data == 'None': # cannot be none
            flash('Error: you must select an analysis method.','warning')
            runtime_attributes.append(('div[name=analysis_type]', 'style', form_warning_style))   
            if first_error_item == None: first_error_item = 2
            form_valid = False


        ##### Check output dataset and project #####
        if form_valid:

            # check if the user has selected the default project (i.e., the user has no projects)
            output_file_dataset = None
            if build_pipeline_form.output_dataset.data == 'new':
                # create a new dataset here with the name default, add the user and dataset to the new project
                new_dataset = Dataset()
                new_dataset.user_id = current_user.id
                new_dataset.populate_with_defaults(current_user)
                new_dataset.name = 'Dataset'
                db.session.add(new_dataset)
                db.session.flush()
                new_dataset.name = 'Dataset ' + str(new_dataset.id)
                #####new_dataset.files = [file]
                db.session.commit()
                output_file_dataset = new_dataset
                flash('New files will be added to dataset "{}".'.format(new_dataset.name), 'success')

                # used to pass the dataset selection to the celery task
                build_pipeline_form.output_dataset.data = str(output_file_dataset.id)
            else: # check if the user has selected a project which they have access to
                user_has_permission = False
                for dataset in current_user.datasets:
                    if str(dataset.id) == build_pipeline_form.output_dataset.data:
                        #####dataset.files.append(file)
                        file_dataset = dataset
                        user_has_permission = True

                        # if current_user.default_dataset == None:
                        #     d.cell_types_sequenced = [str(project.cell_types_sequenced)]
                        #     d.species = project.species
                if not user_has_permission:
                    flash('Error: you do not have permission to add a file to that dataset.','warning')
                    if first_error_item == None : first_error_item = 3
                    form_valid = False

            db.session.commit()

        if form_valid:

            # now do the same with projects, with the qualification that we add the dataset to the project if it's not there already
            # check if the user has selected the default project (i.e., the user has no projects)
            if output_file_dataset:

                if build_pipeline_form.output_project.data == 'new':
                    # create a new project here with the name default, add the user and dataset to the new project
                    new_project = Project()
                    new_project.user_id = current_user.id
                    new_project.project_name = 'Project'
                    db.session.add(new_project)
                    db.session.flush()
                    new_project.project_name = 'Project ' + str(new_project.id)
                    new_project.users = [current_user]
                    new_project.datasets = [output_file_dataset]
                    new_project.cell_types_sequenced = [str(output_file_dataset.cell_types_sequenced)]
                    new_project.species = output_file_dataset.species

                    db.session.commit()
                else: # check if the user has selected a project which they have access to
                    user_has_permission = False
                    for project in projects:
                        if str(project.id) == form.output_project.data:
                            if project.role(current_user) == 'Owner' or project.role(current_user) == 'Editor':
                                # if the dataset is not in the project, add it
                                if output_file_dataset not in project.datasets:
                                    project.datasets.append(output_file_dataset)
                                user_has_permission = True

                                if current_user.default_dataset == None:
                                    output_file_dataset.cell_types_sequenced = [str(project.cell_types_sequenced)]
                                    output_file_dataset.species = project.species

                                db.session.commit()
                    if not user_has_permission:
                        flash('Error: you do not have permission to add a dataset to that project.','warning')
                    db.session.commit()        

        ##### End check of output dataset and project #####


        if not form_valid:

            # set attributes to render the form correctly
            if build_pipeline_form.file_source.data != 'None':
                runtime_attributes.append(('input[value={}]'.format(build_pipeline_form.file_source.data), 'checked', 'checked'))
            if build_pipeline_form.analysis_type.data != 'None':
                runtime_attributes.append(('input[value={}]'.format(build_pipeline_form.analysis_type.data), 'checked', 'checked'))

            build_pipeline_form.dataset_files.default = build_pipeline_form.dataset_files.data

            return render_template( "pipeline.html", build_pipeline_form = build_pipeline_form, dataset_file_dict = dataset_file_dict, dataset_project_dict = dataset_project_dict, runtime_attributes = runtime_attributes, first_error_item = first_error_item )

        else:

            # put the form contents into a format that can be serialized and sent to a celery task
            form_output_dict = {
                'user_id' : current_user.id,    
                'file_source' : build_pipeline_form.file_source.data,
                'dataset' : build_pipeline_form.dataset.data,
                'dataset_files' : build_pipeline_form.dataset_files.data,
                'description' : build_pipeline_form.description.data,
                'name' : build_pipeline_form.name.data,
                'output_dataset' : build_pipeline_form.output_dataset.data,
                'output_project' : build_pipeline_form.output_project.data,
                'ncbi_accession' : build_pipeline_form.ncbi_accession.data,
                'ncbi_chain' : build_pipeline_form.ncbi_chain.data,
                'download_url' : build_pipeline_form.download_url.data,
                'download_chain' : build_pipeline_form.download_chain.data,
                'gsaf_url' : build_pipeline_form.gsaf_url.data,
                'gsaf_chain' : build_pipeline_form.gsaf_chain.data,
                'trim' : build_pipeline_form.trim.data,
                'trim_slidingwindow' : build_pipeline_form.trim_slidingwindow.data,
                'trim_slidingwindow_size' : build_pipeline_form.trim_slidingwindow_size.data,
                'trim_slidingwindow_quality' : build_pipeline_form.trim_slidingwindow_quality.data,
                'trim_illumina_adapters' : build_pipeline_form.trim_illumina_adapters.data,
                'pandaseq' : build_pipeline_form.pandaseq.data,
                'analysis_type' : build_pipeline_form.analysis_type.data,
                'description' : build_pipeline_form.description.data,
                'pandaseq_algorithm' : build_pipeline_form.pandaseq_algorithm.data,
                'cluster' : build_pipeline_form.cluster.data
            }

            result = run_analysis_pipeline.apply_async( (), form_output_dict, queue=celery_queue)
            return redirect(url_for("frontend.dashboard"))

        ##### End Form Validation #####

    else: # request.method == 'GET'
        pass

    return render_template( "pipeline.html", build_pipeline_form = build_pipeline_form, dataset_file_dict = dataset_file_dict, dataset_project_dict = dataset_project_dict, runtime_attributes = runtime_attributes, first_error_item = first_error_item )


 

