#System Imports
import json
import static
import sys
import os
import time
import random
from shutil import copyfile
import shlex

try:
    from shlex import quote as cmd_quote
except ImportError:
    from pipes import quote as cmd_quote

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
from flask import Flask, Blueprint, Markup, make_response, render_template, render_template_string, request, session, flash, redirect, url_for, jsonify, get_flashed_messages, send_from_directory
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
from sqlalchemy import create_engine, func
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

#Nav for Unauthenticated public 
nav.register_element('frontend_top', Navbar(
    View('BIGG DATA', 'frontend.index'),
    View('Login', 'frontend.login'),
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
    ))

nav.register_element('frontend_user', Navbar(
    View('BIGG DATA', 'frontend.index'),
    View('Dashboard', 'frontend.dashboard'),
    Subgroup(
        'Files', 
        View('My Files', 'frontend.files'), 
        View('Import File', 'frontend.file_download'),
        View('Import From NCBI', 'frontend.import_sra'), 
        View('Import From GSAF', 'frontend.import_gsaf')
        ),
    Subgroup(
        'Manage Data',
        View('My Projects', 'projects.manage_projects'),
        View('My Datasets', 'frontend.datasets'),
        View('New Project', 'projects.create_project'),
        ),
    Subgroup(
        'Run Analysis', 
        View('Previous Analyses', 'frontend.analyses'),
        View('VDJ Annotation Pipline', 'frontend.pipeline'),
        View('Create MSDB from Annotations', 'frontend.msdb'),
        View('Pair VH/VL Annotations', 'frontend.pair_vhvl'),
        View('VDJ VIZualizer', 'frontend.vdj_visualizer'),
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
        return render_template("login.html", login_form=login_form, registration_form=form, current_user=current_user)

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

    db.session.add(new_user)
    db.session.commit()
    login_user(new_user, remember=True)
    flash("Success! New user created and logged in.", 'success')
    #create home and scratch if necessary 
    result = instantiate_user_with_directories.apply_async((new_user.id, ), queue=celery_queue)
    return redirect(url_for("frontend.dashboard"))

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

@frontend.route('/file_upload', methods=['POST'])
@login_required
def file_upload():
    upload_form = FileUploadForm()

    # get a list of user projects
    projects = Set(current_user.projects)
    projects.discard(None)
    projects = sorted(projects, key=lambda x: x.id, reverse=True)

    form_valid = True
    new_files = []
    if upload_form.file_pairing.data == 'none':
        try:
            request_file_1 = request.files['file_1']
        except:
            flash('Error: unable to upload file.','warning')
            form_valid = False
        else:
            file_1 = File(user_id = current_user.id)
            if upload_form.file_1_name.data == '':
                file_1.name = cmd_quote(request_file_1.filename)
            else:
                file_1.name = cmd_quote(upload_form.file_1_name.data)

            file_1.file_type = parse_file_ext(file_1.name)
            #file_1.description = upload_form.description.data
            #file_1.dataset_id = int(upload_form.dataset.data) set later
            file_1.path = '{}/{}'.format(current_user.path.rstrip('/'), file_1.name)
            file_1.path = file_1.path.replace('//', '') 
            file_1.user_id = current_user.id

            if file_1.exists():
                file_1.change_name_to_available()

            print 'Saving uploaded file to {}'.format(file_1.path)
            request_file_1.save(file_1.path)
            file_1.available = True 
            db.session.add(file_1)
            file_1.validate()
            db.session.commit()
            db.session.refresh(file_1)
            new_files.append(file_1)

            flash('New file uploaded with file id {}.'.format( file_1.id ), 'success' )

    else:
        try:
            request_file_1 = request.files['file_1']
            request_file_2 = request.files['file_2']
        except:
            flash('Error: unable to upload files.','warning')
            form_valid = False
        else:
            # First Download File
            file_1 = File(user_id = current_user.id)
            if upload_form.file_1_name.data == '':
                file_1.name = cmd_quote(request_file_1.filename)
            else:
                file_1.name = cmd_quote(upload_form.file_1_name.data)

            file_1.file_type = parse_file_ext(file_1.name)
            #file_1.description = upload_form.description.data
            file_1.path = '{}/{}'.format(current_user.path.rstrip('/'), file_1.name)
            file_1.path = file_1.path.replace('//', '') 
            file_1.user_id = current_user.id

            print "This: {}".format(file_1.user_id)
            #file_1.dataset_id = int(upload_form.dataset.data)
            # NOT SET file.chain = upload_form.chain.data
            # NOT SET file.paired_partner = upload_form.paired_partner.data 

            if file_1.exists():
                file_1.change_name_to_available()                    

            print "This: {}".format(file_1.user_id)

            
            print 'Saving uploaded file to {}'.format(file_1.path)
            request_file_1.save(file_1.path)
            file_1.available = True

            # Second Download File
            file_2 = File(user_id = current_user.id)
            if upload_form.file_2_name.data == '':
                file_2.name = cmd_quote(request_file_2.filename)
            else:
                file_2.name = cmd_quote(upload_form.file_2_name.data)

            file_2.user_id = current_user.id
            file_2.file_type = parse_file_ext(file_2.name)
            file_2.description = upload_form.description.data
            file_2.path = '{}/{}'.format(current_user.path.rstrip('/'), file_2.name)
            file_2.path = file_2.path.replace('//', '') 
            #file_2.dataset_id = int(upload_form.dataset.data)
            # NOT SET file.chain = upload_form.chain.data
            # NOT SET file.paired_partner = upload_form.paired_partner.data 
            if file_2.exists():
                file_2.change_name_to_available()                    
     
            print 'Saving uploaded file to {}'.format(file_2.path)
            request_file_2.save(file_2.path)
            file_2.available = True 
            db.session.add(file_1)
            db.session.add(file_2)
            file_1.validate()
            file_2.validate()
            db.session.commit()
            db.session.refresh(file_1)
            db.session.refresh(file_2)
            new_files.append(file_1)
            new_files.append(file_2)

            vhvl_paired = False
            if upload_form.file_pairing.data == 'vhvl': vhvl_paired = True

            if not file_1.pair(file_2, vhvl_paired = vhvl_paired):
                flash('Unable to pair different file types. Submitted files had types "{}" and "{}".'.format(file_1.file_type, file_2.file_type), 'warning' )

            flash('New files uploaded with file ids {} and {}.'.format( file_1.id, file_2.id ), 'success' )

# check if the user has selected the default project (i.e., the user has no projects)
    output_file_dataset = None
    if upload_form.dataset.data == 'new' and new_files != [] and form_valid:
        # create a new dataset here with the name default, add the user and dataset to the new project
        new_dataset = Dataset()
        new_dataset.user_id = current_user.id
        new_dataset.populate_with_defaults(current_user)
        new_dataset.name = 'Dataset'
        db.session.add(new_dataset)
        db.session.flush()
        new_dataset.name = 'Dataset ' + str(new_dataset.id)
        new_dataset.directory = "{}/Dataset_{}".format(current_user.path.rstrip('/') , new_dataset.id)

        upload_form.dataset.choices.append( ( str(new_dataset.id), new_dataset.name ) )
        db.session.commit()

        if not os.path.isdir(new_dataset.directory):
            os.makedirs(new_dataset.directory)
            print 'Created new directory at {}'.format(new_dataset.directory)

        output_file_dataset = new_dataset
        #flash('New files will be added to dataset "{}".'.format(new_dataset.name), 'success')

    else: # check if the user has selected a project which they have access to
        user_has_permission = False
        for dataset in current_user.datasets:
            if str(dataset.id) == upload_form.dataset.data:
                #####dataset.files.append(file)
                user_has_permission = True
                output_file_dataset = dataset

        if not user_has_permission:
            flash('Error: you do not have permission to add a file to that dataset.','warning')
            if first_error_item == None : first_error_item = 3
            form_valid = False

    if new_files != []:
        selected_files = []
        file_id_dict = {}

        for file in new_files:
            if not os.path.isfile(file.path):
                print 'Unable to find file {}'.format(file.path)
            else:
                print 'Moving {} to {}/{}'.format(file.path, output_file_dataset.directory, file.name)

            file.move( output_file_dataset.directory )
            #os.rename(file.path, '{}/{}'.format( output_file_dataset.directory, file.name) )
            file.path = '{}/{}'.format( output_file_dataset.directory, file.name)
            file.dataset_id = output_file_dataset.id
            selected_files.append( str(file.id) )
            file_id_dict[ str(file.id) ] = file.name
            output_file_dataset.files.append(file)

    db.session.commit()

    if form_valid:

        # now do the same with projects, with the qualification that we add the dataset to the project if it's not there already
        # check if the user has selected the default project (i.e., the user has no projects)
        if output_file_dataset:

            if upload_form.project.data == 'new':
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
                    if str(project.id) == upload_form.project.data:
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

    return redirect( url_for('frontend.dashboard') )

@frontend.route('/file_download', methods=['GET', 'POST'])
@login_required
def file_download(status=[], bucket='', key=''):

    form = FileDownloadForm()
    upload_form = FileUploadForm()

    form.dataset.choices = get_dataset_choices(current_user, new = True)
    form.project.choices = get_project_choices(current_user, new = True)
    upload_form.dataset.choices = form.dataset.choices
    upload_form.project.choices = form.project.choices

    # get a list of user projects for user later
    projects = Set(current_user.projects)
    projects.discard(None)
    projects = sorted(projects, key=lambda x: x.id, reverse=True)

    if request.method == 'POST':
        file = File()
        file.url = form.url.data.rstrip()
        file.name = file.url.split('/')[-1].split('?')[0]
        file.file_type = parse_file_ext(file.name)
        file.description = form.description.data
        file.chain = form.chain.data
        file.paired_partner = form.paired_partner.data 
        file.dataset_id = form.dataset_id.data
        file.path = '{}/{}'.format(current_user.path.rstrip('/'), file.name)
        file.user_id = current_user.id
        file.available = False 
        file.status = ''
        print 'Saving File Metadata to Postgres: {}'.format(file.__dict__)
        db.session.add(file)
        db.session.commit()

        #######
        # check if the user has selected the default project (i.e., the user has no projects)
        file_dataset = None
        if form.dataset.data == 'new':
            # create a new dataset here with the name default, add the user and dataset to the new project
            file_dataset = generate_new_dataset(current_user)
            flash('New file will be added to dataset "{}".'.format(file_dataset.name), 'success')
        else: # check if the user has selected a project which they have access to
            user_has_permission = False
            for dataset in current_user.datasets:
                if str(dataset.id) == form.dataset.data:
                    dataset.files.append(file)
                    file_dataset = dataset
                    user_has_permission = True

            if not user_has_permission:
                flash('Error: you do not have permission to add a file to that dataset.','warning')
        db.session.commit()


        # now do the same with projects, with the qualification that we add the dataset to the project if it's not there already
        # check if the user has selected the default project (i.e., the user has no projects)
        if file_dataset:
            if form.project.data == 'new':
                new_project = generate_new_project(user = current_user, dataset = file_dataset)
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
                current_user.path.rstrip('/'),
                'Dataset_' + str(file_dataset.id), 
                file.name)

        # check if the file path we settled on is available.
        if os.path.isfile(file.path):
            file.path = os.path.splitext(file.path)[0] + '_1' + os.path.splitext(file.path)[1]
        #######

        db.session.commit()
        download_file.apply_async((file.url, file.path, file.id), {'user_id' : current_user.id})

        return redirect( url_for('frontend.dashboard') )

    return render_template("file_download.html", download_form=form, upload_form = upload_form, current_user=current_user)


##### Download the file here #####
@frontend.route('/download/<int:file_id>', methods=['GET', 'POST'])
def download(file_id):

    file = db.session.query(File).get(file_id)

    if file:

        return send_from_directory(directory=file.directory, filename=file.name)

    else:
        return redirect( request.referrer )

@frontend.route('/files', methods=['GET', 'POST'])
@login_required
def files(status=[], bucket=None, key=None):
    # print request
    db.session.expire_all()
    files = sorted(current_user.files.all(), key=lambda x: x.id, reverse=True)
    paths = get_dropbox_files(current_user)
    form = Form()

    #creates list of datasets
    projectnames = []
    for x in current_user.projects:
        projectid = str(x.id)
        name = str(x.project_name) 
        projectnames.append(name + ' - ' + projectid)

    if request.method == 'POST' and os.path.isfile(request.form['submit']):
        file_path = request.form['submit'] 
        file_name = file_path.split('/')[-1]
        if file_path not in [file.path for file in current_user.files]:
            print 'linking new file "{}"  to  {}'.format(file_name, file_path)
            file = File(name = file_name, path = file_path, user_id = current_user.id,
                    check_name = False)
            file.validate()
            db.session.add(file)
            db.session.commit()

            flash('linked new file to your user: {}'.format(file_path), 'success')
            paths = paths.remove(file_path)
            files = sorted(current_user.files, key=lambda x: x.id, reverse=True)
        else: 
            flash('file metadata already created to your user')
            paths = get_dropbox_files(current_user)
        return render_template("files.html", files=files, dropbox_files=paths, form=form, current_user=current_user)
    else: 
        paths = get_dropbox_files(current_user)
        return render_template("files.html", files=files, dropbox_files=paths, form=form, current_user=current_user)

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
    files = current_user.files.all()
    datasets = current_user.datasets.all()
    datasets = [dataset for dataset in datasets if dataset.name != '__default__']
    
    datadict = get_user_dataset_dict(current_user)

    form = CreateDatasetForm()
    form.project.choices = get_project_choices(current_user, new = True)

    projects = Set(current_user.projects)
    projects.discard(None)
    projects = sorted(projects, key=lambda x: x.id, reverse=True)
    project_tuples = []

    if request.method == 'POST':
        if form.name.data: 
            d = generate_new_dataset(current_user)

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
                new_project.cell_types_sequenced = str(d.cell_types_sequenced)
                new_project.species = d.species
                d.project_id = new_project.id

                db.session.commit()
                return redirect(url_for('.datasets'))
            else: # check if the user has selected a project which they have access to
                for project in projects:
                    if str(project.id) == form.project.data:
                        print "project.role(current_user): {}".format(project.role(current_user) )
                        if project.role(current_user) == 'Owner' or project.role(current_user) == 'Editor':
                            project.datasets.append(d)
                            d.project_id = project.id

                            if current_user.default_dataset == None:
                                d.cell_types_sequenced = [str(project.cell_types_sequenced)]
                                d.species = project.species

                            db.session.commit()
                            return redirect(url_for('.datasets'))
                flash('Error: you do not have permission to add a dataset to that project.','warning')
                return redirect(url_for('.datasets'))
            db.session.commit()
            d.directory = current_user.path.rstrip('/') + '/dataset_' + d.id 
            db.session.commit()
        return redirect(url_for('.datasets')) # render_template("datasets.html", datadict=datadict, form=Form())
    else: 
        return render_template("datasets.html", datadict=datadict, form=form, current_user=current_user)

@frontend.route('/datasets/<int:id>', methods=['GET', 'POST'])
@login_required
def dataset(id):

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


@frontend.route('/analysis/<int:id>', methods=['GET', 'POST'])
@login_required
def analysis(id):
    analysis = db.session.query(Analysis).filter(Analysis.id==id).first()        
    return render_template("analysis.html", analysis=analysis, current_user=current_user) #, cdr3_aa_counts=cdr3_aa_counts, v_hit_counts=v_hit_counts, v_hit_loci_counts=v_hit_loci_counts)

# Call a celery task to zip all the files and download them
@frontend.route('/analysis/<int:id>/download', methods=['GET', 'POST'])
@login_required
def analysis_download(id):
    analysis = db.session.query(Analysis).filter(Analysis.id==id).first()

    if analysis.zip_file_id != None:
        if analysis.zip_file.status == 'COMPRESSING':
            flash('Error: a compressed file for that analysis is being created.', 'warning ')
        else:
            flash('Error: a compressed file for that analysis has been/is being created.', 'warning ')
        return redirect( url_for('frontend.analyses') )


    if analysis.files.count() > 0:
        result = create_analysis_zip_file.apply_async( ( ),  
            { 
                'analysis_id': analysis.id,
                'user_id': current_user.id 
            }, queue=celery_queue)

    else:
        flash('Analysis {} has no files to compress.'.format(analysis.id) , 'warning')

    return redirect( url_for('frontend.analyses') )
    
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
    file_options = map(lambda f: [f.id, f.name], [f for f in dataset.files if 'FASTQ' in f.file_type])
    form.file_ids.choices = file_options

    if request.method == 'POST' and dataset:
        flash('PANDASEQ Launch Detected', 'success')
        if len(form.file_ids.data) != 2: 
            flash('Should select two files for consensus alignment', 'warning')
        result = run_pandaseq_with_dataset_id.apply_async((dataset_id, ),  {'analysis_name': form.name.data, 'analysis_description': form.description.data, 'file_ids': form.file_ids.data, 'user_id': current_user.id, 'algorithm': form.algorithm.data, 'minimum_overlap': form.minimum_overlap.data, 'minimum_length': form.minimum_length.data}, queue=celery_queue)
        return redirect(url_for('frontend.dashboard'))
    else: 
        form.name.data = dataset.name
        return render_template("pandaseq.html", dataset=dataset, form=form, current_user=current_user) 


@frontend.route('/test/', methods=['GET', 'POST'])
@login_required
def test():

    print db.session.query(func.max(File.id)).first()[0]


    message = Markup('<a href="{}">Test Again</a>.'.format( url_for('frontend.test') ) )
    flash(message , 'success' )

    return redirect( url_for('frontend.dashboard') )


@frontend.route('/analysis/pair_vhvl/', methods=['GET', 'POST'])
@login_required
def pair_vhvl(status=[]):

    pair_vhvl_form = CreateVHVLPairingAnalysisForm()

    # get a list of datasets and projects
    datasets = current_user.get_ordered_datasets()
    projects = current_user.get_ordered_projects()
    project_tuples = []

    dataset = None


    status = []
    if request.method == 'POST':

        # Check the submitted name, use default if possible
        current_analysis_id = db.session.query(func.max(File.id)).first()[0]
        if current_analysis_id:
            next_analysis_id = int(current_analysis_id) + 1
        else:
            next_analysis_id = 1

        if pair_vhvl_form.name.data == 'Pairing Analysis {}'.format( str(next_analysis_id) ):
            pair_vhvl_form.name.data = ''

        file_ids_to_pair = []

        if len(pair_vhvl_form.dataset_ids.data) == 1:
            output_dataset_id = int(pair_vhvl_form.dataset_ids.data[0])
        else: # This mvoes the output director up to /user.path/Pairing_Analysis_#
            output_dataset_id = None

        for dataset in current_user.datasets:
            if str(dataset.id) in pair_vhvl_form.dataset_ids.data:
                for file in dataset.files:
                    if str(file.id) in pair_vhvl_form.file_ids.data:
                        file_ids_to_pair.append(file.id)

        if file_ids_to_pair != []:

            result = run_pair_vhvl_with_dataset_id.apply_async( ( ), 
                    { 
                        'user_id' : current_user.id, 
                        'dataset_id' : output_dataset_id, 
                        'analysis_id' : None,
                        'analysis_name' : pair_vhvl_form.name.data,
                        'analysis_description' : pair_vhvl_form.description.data,
                        'file_ids' : file_ids_to_pair, 
                        'vhvl_min' : float( pair_vhvl_form.vhvl_min.data ), 
                        'vhvl_max' : float( pair_vhvl_form.vhvl_max.data ), 
                        'vhvl_step' : float( pair_vhvl_form.vhvl_step.data ) }, 
                    queue=celery_queue )

            return redirect( url_for('frontend.dashboard') )
        else:
            flash('No files selected for analysis.', 'warning')

    else: # request.method == 'GET'
        # Check the submitted name, use default if possible
        current_analysis_id = db.session.query(func.max(File.id)).first()[0]
        if current_analysis_id:
            next_analysis_id = int(current_analysis_id) + 1
        else:
            next_analysis_id = 1
        pair_vhvl_form.name.data = 'Pairing Analysis {}'.format( str(next_analysis_id) )

    # Fall through to this point if the method if 'GET'
    dataset_choices = []
    file_choices = []
    dataset_file_dict = {}

    # build choices for the file_ids and dataset_ids
    # only include files which are annotation files
    for dataset in current_user.datasets:

        dataset_added = False

        for file in dataset.files:

            if file.file_type == 'IGFFT_ANNOTATION':

                if dataset_added == False:
                    # Add the dataset as an option
                    dataset_added = True
                    dataset_choices.append( (str(dataset.id), dataset.name) )
                    dataset_file_dict[str(dataset.id)] = []

                # Add the file to the list of options
                file_choices.append( (str(file.id), file.name) )
                dataset_file_dict[str(dataset.id)].append( str(file.id) )

                # Use description to associate datasets/files


    pair_vhvl_form.dataset_ids.choices = dataset_choices
    pair_vhvl_form.file_ids.choices = file_choices

    return render_template("pair_vhvl.html", dataset=dataset, pair_vhvl_form=pair_vhvl_form, status=status, current_user=current_user, dataset_file_dict = dataset_file_dict) 

@frontend.route('/analysis/msdb/', methods=['GET', 'POST'])
@login_required
def msdb(status=[]):

    msdb_form = CreateMSDBAnalysisForm()

    # get a list of datasets and projects
    datasets = current_user.get_ordered_datasets()
    projects = current_user.get_ordered_projects()
    project_tuples = []

    dataset = None

    status = []
    if request.method == 'POST':

        must_be_present=['CDR3']
        if msdb_form.require_cdr1.data: must_be_present.append('CDR1')
        if msdb_form.require_cdr2.data: must_be_present.append('CDR2')

        file_ids_to_pair = []

        # Check the submitted name, use default if possible
        next_analysis_id = int(db.session.query(func.max(File.id)).first()[0]) + 1
        if msdb_form.name.data == 'MSDB Analysis {}'.format( str(next_analysis_id) ):
            msdb_form.name.data = ''


        if len(msdb_form.dataset_ids.data) == 1:
            output_dataset_id = int(msdb_form.dataset_ids.data[0])
        else: # This mvoes the output director up to /user.path/Pairing_Analysis_#
            output_dataset_id = None

        for dataset in current_user.datasets:
            if str(dataset.id) in msdb_form.dataset_ids.data:
                for file in dataset.files:
                    if str(file.id) in msdb_form.file_ids.data:
                        file_ids_to_pair.append(file.id)

        if file_ids_to_pair != []:

            result = run_msdb_with_dataset_id.apply_async( ( ), 
                    { 
                        'user_id' : current_user.id, 
                        'dataset_id' : output_dataset_id, 
                        'analysis_id' : None, 
                        'analysis_name' : msdb_form.name.data,
                        'analysis_description' : msdb_form.description.data,
                        'file_ids' : file_ids_to_pair, 
                        'cluster_percent' : float(msdb_form.msdb_cluster_percent.data), 
                        'must_be_present' : must_be_present
                     }, queue=celery_queue )

            return redirect( url_for('frontend.dashboard') )
        else:
            flash('No files selected for analysis.', 'warning')

    else: # request.method == 'GET'
        current_analysis_id = db.session.query(func.max(File.id)).first()[0]
        if current_analysis_id:
            next_analysis_id = int(current_analysis_id) + 1
        else:
            next_analysis_id = 1

        msdb_form.name.data = 'MSDB Analysis {}'.format( str(next_analysis_id) )

    # Fall through to this point if the method if 'GET'
    dataset_choices = []
    file_choices = []
    dataset_file_dict = {}

    # build choices for the file_ids and dataset_ids
    # only include files which are annotation files
    for dataset in current_user.datasets:

        dataset_added = False

        for file in dataset.files:

            if file.file_type == 'IGFFT_ANNOTATION':

                if dataset_added == False:
                    # Add the dataset as an option
                    dataset_added = True
                    dataset_choices.append( (str(dataset.id), dataset.name) )
                    dataset_file_dict[str(dataset.id)] = []

                # Add the file to the list of options
                file_choices.append( (str(file.id), file.name) )
                dataset_file_dict[str(dataset.id)].append( str(file.id) )

                # Use description to associate datasets/files

    msdb_form.dataset_ids.choices = dataset_choices
    msdb_form.file_ids.choices = file_choices

    if not dataset:
        dataset = None

    return render_template("msdb.html", dataset=dataset, msdb_form=msdb_form, status=status, current_user=current_user, dataset_file_dict = dataset_file_dict) 

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
    form.dataset.choices = get_dataset_choices(current_user, new = True)
    form.project.choices = get_project_choices(current_user, new = True)

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


@frontend.route('/files/import_gsaf', methods=['GET', 'POST'])
@login_required
def import_gsaf():
    form = GsafDownloadForm()
    if request.method == 'POST':
        url = form.url.data
        req = urllib2.Request(url)
        try:
            response = urllib2.urlopen(req)
            # do stuff...
        except urllib2.HTTPError as err:
            error = ['URL Unreachable...', err]
            flash('URL is unreachable...', 'error')
            flash(err, 'error')
            return render_template('import_gsaf.html', form=form)
        else: 
            error = None
            parse_gsaf_response_into_datasets.apply_async((url,), {'user_id':current_user.id}, queue=celery_queue)
            return redirect(url_for('frontend.dashboard'))
             # render_template('sra_import.html', status=status, form=form, result=result, current_user=current_user)

    return render_template('import_gsaf.html', form=form)


@frontend.route('/delete_task/<task_id>', methods=['GET', 'POST'])
@login_required
def delete_task(task_id):
    tasks = Set(current_user.celery_tasks)
    tasks.discard(None)
    tasks = Set( sorted(tasks, key=lambda x: x.id, reverse=True) )

    discard_task = ''

    for task in tasks:
        if str(task.id) == task_id:

            logfile = '{}/{}.log'.format( current_user.path.rstrip('/') , task.async_task_id )

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

            logfile = '{}/{}.log'.format( current_user.path.rstrip('/') , task.async_task_id )

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

            ##### Set task heading here #####
            if task.status == 'SUCCESS': 
                pass # task_heading_color = 'green'
            elif task.status == 'FAILURE':
                pass # task_heading_color = 'red'


            task_analysis_link = ''
            if task.status == 'SUCCESS' or task.status == 'FAILURE' or task.status == 'COMPLETE':    
                if task.analysis_id:
                    task_analysis_link = ' <a href="{1}">Click Here</a><font color="{0}"> to view the analysis results.</color>'.format(task_heading_color, url_for('frontend.analysis', id = task.analysis_id))
                elif task.name == 'create_analysis_zip_file':
                    pattern = re.compile('(.+)file (\d+)')
                    pattern_match =  pattern.match(task.result)


                    if pattern_match:
                        file_id = int(pattern_match.group(2))
                        file = db.session.query(File).get(file_id)
                        if file and file.available:
                            task_analysis_link = ' <a href="{1}" onclick="document.someForm.submit();" download="{2}">Click Here</a><font color="{0}"> to download the file.</color>'.format(task_heading_color, url_for('frontend.download', file_id = file_id), file.name)

            entry = """
            <table width="100%">
                <tbody>
                    <tr>
                        <td><font color="{0}">[Task {1} ({2}) - {3}] {4}</font> {7}<br>
                        {5}{6}</td>
                        <td align="right" valign="top">
                        <span class="pencil glyphicon glyphicon-remove" style="margin-right: 3px; color:black; cursor: pointer; cursor: hand;" onclick=delete_task('{8}')></span>

                        </td>
                    </tr>
                </tbody>
            </table>
            <br>""".format( task_heading_color , task.id, task.name , task.status, task_message , log_entries, async_task_progress , task_analysis_link, url_for( 'frontend.delete_task', task_id = task.id )  )

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
        interval = 5000

    response = {
        'message': message,
        'interval': interval,
        'current': 1,
        'total': 1,
     }  # this is the exception raised

    return jsonify( response )

@frontend.route('/zip_file_status_json', methods=['GET', 'POST'])
@login_required
def zip_file_status_json():
 # For determining whether to allow downloads or not for an analysis
    analysis_status = {}
    zip_file_names = {}

    for analysis in current_user.analyses:

        # Update the status of each analysis here
        if analysis.status != 'SUCCESS' and analysis.status != 'FAILURE' and analysis.status != 'COMPLETE':

            if not analysis.async_task_id: 
                if analysis.status == 'QUEUED':
                    analysis.status = 'COMPLETE'
                if not analysis.status and analysis.files.count() == 0:
                    analysis.status = 'FAILURE'

                db.session.commit()

        if analysis.files.count() != 0:

            if analysis.status != 'SUCCESS' and analysis.status != 'FAILURE' and analysis.status != 'COMPLETE':    
                analysis_status[analysis.id] = 'RUNNING'
            elif not analysis.zip_file:
                analysis_status[analysis.id] = 'NONE'
            elif analysis.zip_file.status == 'COMPRESSING':
                analysis_status[analysis.id] = 'COMPRESSING'
            elif analysis.zip_file.available:
                analysis_status[analysis.id] = str(analysis.zip_file.id)
                zip_file_names[analysis.id] = analysis.zip_file.name
            else:
                analysis_status[analysis.id] = 'NONE'

    response = {
        'analysis_status': analysis_status,
        'zip_file_names': zip_file_names
    }

    return jsonify( response )


@frontend.route('/pipeline', methods=['GET', 'POST'])
@login_required
def pipeline(selected_dataset=None):

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
            for file in [file for file in dataset.files if 'FASTQ' in file.file_type]:
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
        build_pipeline_form.output_project.choices = [ ('new', 'New Project') ]

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

        elif build_pipeline_form.file_source.data == 'file_url':

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

        elif build_pipeline_form.file_source.data == 'file_upload':

            new_files = []

            if build_pipeline_form.file_pairing.data == 'none':
                try:
                    request_file_1 = request.files['file_1']
                except:
                    flash('Error: unable to upload file.','warning')
                    runtime_attributes.append(('input[id=file_1]', 'style', form_warning_style))   
                    first_error_item = 0
                    form_valid = False
                else:
                    file_1 = File()
                    if build_pipeline_form.file_1_name.data == '':
                        file_1.name = cmd_quote(request_file_1.filename)
                    else:
                        file_1.name = cmd_quote(build_pipeline_form.file_1_name.data)

                    file_1.file_type = parse_file_ext(file_1.name)
                    file_1.description = build_pipeline_form.description.data
                    #file_1.dataset_id = int(build_pipeline_form.dataset.data) set later
                    file_1.path = '{}/{}'.format(current_user.path.rstrip('/'), file_1.name)
                    file_1.path = file_1.path.replace('//', '') 
                    file_1.user_id = current_user.id

                    if file_1.exists():
                        file_1.change_name_to_available()

                    print 'Saving uploaded file to {}'.format(file_1.path)
                    request_file_1.save(file_1.path)
                    file_1.available = True 
                    db.session.add(file_1)
                    file_1.validate()
                    db.session.commit()
                    db.session.refresh(file_1)
                    new_files.append(file_1)

            else:
                try:
                    request_file_1 = request.files['file_1']
                    request_file_2 = request.files['file_2']
                except:
                    flash('Error: unable to upload files.','warning')
                    runtime_attributes.append(('input[id=file_1_name]', 'style', form_warning_style))   
                    runtime_attributes.append(('input[id=file_2_name]', 'style', form_warning_style))   
                    first_error_item = 0
                    form_valid = False
                else:
                    # First Download File
                    file_1 = File()
                    if build_pipeline_form.file_1_name.data == '':
                        file_1.name = cmd_quote(request_file_1.filename)
                    else:
                        file_1.name = cmd_quote(build_pipeline_form.file_1_name.data)

                    file_1.file_type = parse_file_ext(file_1.name)
                    file_1.description = build_pipeline_form.description.data
                    file_1.path = '{}/{}'.format(current_user.path.rstrip('/'), file_1.name)
                    file_1.path = file_1.path.replace('//', '') 
                    file_1.user_id = current_user.id
                    #file_1.dataset_id = int(build_pipeline_form.dataset.data)
                    # NOT SET file.chain = build_pipeline_form.chain.data
                    # NOT SET file.paired_partner = build_pipeline_form.paired_partner.data 

                    if file_1.exists():
                        file_1.change_name_to_available()                    
                    
                    print 'Saving uploaded file to {}'.format(file_1.path)
                    request_file_1.save(file_1.path)
                    file_1.available = True

                    # Second Download File
                    file_2 = File()
                    if build_pipeline_form.file_2_name.data == '':
                        file_2.name = cmd_quote(request_file_2.filename)
                    else:
                        file_2.name = cmd_quote(build_pipeline_form.file_2_name.data)

                    file_2.user_id = current_user.id
                    file_2.file_type = parse_file_ext(file_2.name)
                    file_2.description = build_pipeline_form.description.data
                    file_2.path = '{}/{}'.format(current_user.path.rstrip('/'), file_2.name)
                    file_2.path = file_2.path.replace('//', '') 
                    #file_2.dataset_id = int(build_pipeline_form.dataset.data)
                    # NOT SET file.chain = build_pipeline_form.chain.data
                    # NOT SET file.paired_partner = build_pipeline_form.paired_partner.data 
                    if file_2.exists():
                        file_2.change_name_to_available()                    
             
                    print 'Saving uploaded file to {}'.format(file_2.path)
                    request_file_2.save(file_2.path)
                    file_2.available = True 
                    db.session.add(file_1)
                    db.session.add(file_2)
                    file_1.validate()
                    file_2.validate()
                    db.session.commit()
                    db.session.refresh(file_1)
                    db.session.refresh(file_2)
                    new_files.append(file_1)
                    new_files.append(file_2)

                    vhvl_paired = False
                    if build_pipeline_form.file_pairing.data == 'vhvl': vhvl_paired = True

                    if not file_1.pair(file_2, vhvl_paired = vhvl_paired):
                        flash('Unable to pair different file types. Submitted files had types "{}" and "{}".'.format(file_1.file_type, file_2.file_type), 'warning' )

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
            
                if build_pipeline_form.trim_slidingwindow_size.data and not int(build_pipeline_form.trim_slidingwindow_size.data) > 0: # must be positive integer
                    flash('Error: if trimming is selected, you must choose a valid sliding window size.','warning')
                    runtime_attributes.append(('input[id=trim_slidingwindow_size]', 'style', form_warning_style))                                   
                    if first_error_item == None: first_error_item = 1
                    form_valid = False

                if build_pipeline_form.trim_slidingwindow_quality.data and not int(build_pipeline_form.trim_slidingwindow_quality.data) > 0: # must be positive integer
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
        if form_valid or (build_pipeline_form.file_source.data == 'file_upload' and new_files != []):

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
                new_dataset.directory = "{}/Dataset_{}".format(current_user.path.rstrip('/') , new_dataset.id)
                dataset_file_dict[ str(new_dataset.id) ] = []

                build_pipeline_form.dataset.choices.append( ( str(new_dataset.id), new_dataset.name ) )
                db.session.commit()

                if not os.path.isdir(new_dataset.directory):
                    os.makedirs(new_dataset.directory)
                    print 'Created new directory at {}'.format(new_dataset.directory)

                output_file_dataset = new_dataset
                #flash('New files will be added to dataset "{}".'.format(new_dataset.name), 'success')

                # used to pass the dataset selection to the celery task
                build_pipeline_form.output_dataset.data = str(output_file_dataset.id)
            else: # check if the user has selected a project which they have access to
                user_has_permission = False
                for dataset in current_user.datasets:
                    if str(dataset.id) == build_pipeline_form.output_dataset.data:
                        #####dataset.files.append(file)
                        user_has_permission = True
                        output_file_dataset = dataset

                if not user_has_permission:
                    flash('Error: you do not have permission to add a file to that dataset.','warning')
                    if first_error_item == None : first_error_item = 3
                    form_valid = False

            if build_pipeline_form.file_source.data == 'file_upload' and new_files != []:
                selected_files = []
                file_id_dict = {}

                for file in new_files:
                    if not os.path.isfile(file.path):
                        print 'Unable to find file {}'.format(file.path)
                    else:
                        print 'Moving {} to {}/{}'.format(file.path, output_file_dataset.directory, file.name)

                    file.move( output_file_dataset.directory )
                    #os.rename(file.path, '{}/{}'.format( output_file_dataset.directory, file.name) )
                    file.path = '{}/{}'.format( output_file_dataset.directory, file.name)
                    file.dataset_id = output_file_dataset.id
                    selected_files.append( str(file.id) )
                    file_id_dict[ str(file.id) ] = file.name
                    output_file_dataset.files.append(file)
                    build_pipeline_form.dataset_files.choices.append( ( str(file.id), file.name ) ) 

                # If new files are created and the form is invalid, this passes those files back into the form
                # and automatically selects those files from the multiple select
                dataset_file_dict[ str(output_file_dataset.id) ] = file_id_dict
                build_pipeline_form.file_source.data = 'file_dataset'
                build_pipeline_form.dataset_files.data = selected_files
                build_pipeline_form.dataset.data = str(output_file_dataset.id)

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
                        if str(project.id) == build_pipeline_form.output_project.data:
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

            if len(new_files) != 0:
                build_pipeline_form.dataset_files.default = build_pipeline_form.dataset_files.data

            if len(new_files) == 1:
                # Flash this only if the rest of the form submission is unsuccessful 
                flash('New files uploaded to {} in dataset {}'.format(new_files[0].path, output_file_dataset.name), 'success')
            elif len(new_files) == 2:
                # Flash this only if the rest of the form submission is unsuccessful 
                flash('New files uploaded to {} {} in dataset {}'.format(file_1.path, file_1.path, output_file_dataset.name), 'success')

            # set attributes to render the form correctly
            if build_pipeline_form.file_source.data != 'None':
                runtime_attributes.append(('input[value={}]'.format(build_pipeline_form.file_source.data), 'checked', 'checked'))
            if build_pipeline_form.analysis_type.data != 'None':
                runtime_attributes.append(('input[value={}]'.format(build_pipeline_form.analysis_type.data), 'checked', 'checked'))


            return render_template( "pipeline.html", build_pipeline_form = build_pipeline_form, dataset_file_dict = dataset_file_dict, dataset_project_dict = dataset_project_dict, runtime_attributes = runtime_attributes, first_error_item = first_error_item )

        if form_valid: 

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
                'cluster' : build_pipeline_form.cluster.data,
                'species' : build_pipeline_form.species.data,
                'loci': build_pipeline_form.loci.data,
                'generate_msdb' : build_pipeline_form.generate_msdb.data,
                'pair_vhvl' : build_pipeline_form.pair_vhvl.data,
                'msdb_cluster_percent' : str(build_pipeline_form.msdb_cluster_percent.data),
                'require_cdr1' : build_pipeline_form.require_cdr1.data,
                'require_cdr2' : build_pipeline_form.require_cdr2.data,
                'require_cdr3' : build_pipeline_form.require_cdr3.data,
                'vhvl_min' : str(build_pipeline_form.vhvl_min.data),
                'vhvl_max' : str(build_pipeline_form.vhvl_max.data),
                'vhvl_step' : str(build_pipeline_form.vhvl_step.data)
            }

            result = run_analysis_pipeline.apply_async( (), form_output_dict, queue=celery_queue)
            return redirect(url_for("frontend.dashboard"))

        ##### End Form Validation #####

    else: # request.method == 'GET'
        build_pipeline_form.trim_slidingwindow.data = True
        build_pipeline_form.trim_illumina_adapters.data = True
        build_pipeline_form.trim_slidingwindow_size.data = 4
        build_pipeline_form.trim_slidingwindow_quality.data = 15
        

    return render_template( "pipeline.html", build_pipeline_form = build_pipeline_form, dataset_file_dict = dataset_file_dict, dataset_project_dict = dataset_project_dict, runtime_attributes = runtime_attributes, first_error_item = first_error_item )


 

