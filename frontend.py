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
from sqlalchemy.orm import sessionmaker, scoped_session, subqueryload, load_only
from pymongo import MongoClient
import pymongo

from app import *

# Local Imports 
from forms import *
from functions import * 
from models import * 



# blueprint
frontend = Blueprint('frontend', __name__)


nav = Nav()

#Nav for Unauthenticated public 
nav.register_element('frontend_top', Navbar(
    View('BIGG DATA', 'frontend.index'),
    View('Login', 'frontend.login'),
    Subgroup(
        'Database',
        View('Germline Allele DB', 'frontend.alleledb'),
        #Link('Metabase DB Browser', 'http://geordbas01.ccbb.utexas.edu:3000/'),
    ),
    Subgroup(
        'Documentation',
        View('About BIGG DATA', 'frontend.about'),
        Link('BIGG DATA GitHub', 'https://github.com/bigglab/BIGGDATA'),
        #View('BIGG DATA Overview', 'frontend.overview'),
        #View('BIGG DB Schema', 'frontend.schema'),
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
        'Manage Data',
        View('Import Files', 'frontend.import_files'), 
        View('My Projects', 'frontend.projects'),
        View('My Datasets', 'frontend.datasets'),
        View('All My Files', 'frontend.files'),
        #View('Create Project', 'frontend.create_project'),
        ),
    Subgroup(
        'Run Analysis', 
        View('VDJ Annotation Pipline', 'frontend.pipeline'),
        View('Cluster Annotations / Create MSDB', 'frontend.msdb'),
        View('VDJ VIZualizer', 'frontend.vdj_visualizer'),
        ),
    Subgroup(
        'Monitor',
        View('Analyses Dashboard', 'frontend.analyses'),
        View('Celery Task Monitor', 'frontend.celery_monitor'),
        View('RabbitMQ Monitor', 'frontend.rabbitmq_monitor'),
    ),
    Subgroup(
        'Database',
        View('Germline Allele DB', 'frontend.alleledb'),
        Link('Metabase DB Browser', 'http://geordbas01.ccbb.utexas.edu:3000/'),
        ),
    Subgroup(
        'Documentation',
        View('About BIGG DATA' , 'frontend.about'),
        Link('BIGG DATA GitHub', 'https://github.com/bigglab/BIGGDATA'),
        #View('BIGG DB Schema', 'frontend.schema'),
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
            if user.authorized == True:
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
            elif user.authorized == False: 
                flash('User is not yet authorized for access to BIGGDATA. Contact Russell Durrett for more info.')
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

    # Authorized = False to verify each user manually as Georgiou / UT 
    new_user.authorized = False 

    #Just default to yes for now - more with login than manual authorization 
    new_user.authenticated = True 

    new_user.root_path = app.config['USER_ROOT'].replace('<username>', new_user.username)

    db.session.add(new_user)
    db.session.commit()

    msg = Message('New User Request', sender=['BIGGDATA.io', 'admin@biggdata.io'], recipients=['russdurrett@utexas.edu'])
    msg.body = 'New User {}, id {} has requested an account on BIGGDATA. Please go to the DB and change "authorized" to TRUE for this user.'.format(new_user.username, new_user.id)
    mail.send(msg)

    # login_user(new_user, remember=True)
    # flash("Success! New user created and logged in.", 'success')
    flash("Success! New user requested and will be verified within 24 hours.", 'success')
    #create home and scratch if necessary 
    result = instantiate_user_with_directories.apply_async((new_user.id, ), queue=celery_queue)
    return redirect(url_for("frontend.index"))


# Dashboard To Verify Users - Currently Manual
# @frontend.route("/verify_user", methods=["GET", "POST"])
# def verify_user():
#     unverified_users = db.session.query(User).filter(User.username == form.username.data).all()



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



@frontend.route('/import_files', methods=['GET', 'POST'])
@login_required
def import_files():

    # print '######### request values #########'
    # print request.values 
    # print '#############'
    form = ImportFilesForm()

    if request.method == 'POST':
        # file_upload has to be handled by the request processor - cant send to celery as async task 
        if form.file_source.data == 'file_upload': 
            print 'attempt to upload files from local computer detected'
            print '######### request files #########'
            print request.files 
            print '#############'

            add_to_project=False
            if form.output_dataset.data == 'new': 
                dataset = generate_new_dataset(user = current_user, name=form.dataset_name.data, description=form.dataset_description.data, session=db.session)
                add_to_project=True
            else: 
                dataset = db.session.query(Dataset).get(int(form.output_dataset.data))

            if form.output_project.data == 'new':
                project = generate_new_project(user = current_user, datasets = dataset, name=form.project_name.data, description=form.project_description.data, session = db.session)
            else: 
                project = db.session.query(Project).get(int(form.output_project.data))
                if add_to_project==True: 
                    project.datasets.append(dataset)

            new_files = []
            try:
                request_file_1 = request.files['local_file_1']
            except:
                flash('Error: unable to upload even the first file.','warning')
                form_valid = False
            else:
                # First Download File
                file_1 = File(user_id = current_user.id)
                file_1.name = cmd_quote(request_file_1.filename)
                file_1.file_type = parse_file_ext(file_1.name)
                file_1.path = '{}/{}'.format(dataset.directory.rstrip('/'), file_1.name).replace('//', '') 
                file_1.dataset_id = dataset.id

                print 'Saving uploaded file to {}'.format(file_1.path)
                request_file_1.save(file_1.path)
                file_1.available = True
                db.session.add(file_1)
                file_1.validate()
                db.session.commit()
                db.session.refresh(file_1)
                new_files.append(file_1)


            if form.file_pairing.data != 'none': # more than one file expected 
                try:
                    request_file_2 = request.files['local_file_2']
                except:
                    flash('Error: unable to upload second file. Expected two files since pairing was set.','warning')
                    form_valid = False
                else:

                    # Second Download File
                    file_2 = File(user_id = current_user.id)
                    file_2.name = cmd_quote(request_file_2.filename)
                    file_2.file_type = parse_file_ext(file_2.name)
                    file_2.path = '{}/{}'.format(dataset.directory.rstrip('/'), file_2.name).replace('//', '') 
                    file_2.dataset_id = dataset.id 
             
                    print 'Saving uploaded file to {}'.format(file_2.path)
                    request_file_2.save(file_2.path)
                    file_2.available = True 

                    db.session.add(file_2)
                    file_2.validate()
                    db.session.commit()
                    db.session.refresh(file_2)
                    new_files.append(file_2)

                vhvl_paired = False
                if form.file_pairing.data == 'vhvl': vhvl_paired = True

                if not file_1.pair(file_2, vhvl_paired = vhvl_paired):
                    flash('Unable to pair different file types. Submitted files had types "{}" and "{}".'.format(file_1.file_type, file_2.file_type), 'warning' )

                flash('New files {} & {} uploaded and saved to Dataset {}.'.format( file_1.id, file_2.id, dataset.id ), 'success' )
            else: 
                flash('New file {} uploaded and saved to Dataset {}.'.format( file_1.id, dataset.id ), 'success' )
                
            return redirect(url_for('frontend.datasets'))


        elif form.file_source.data == 'file_gsaf': 
            url = form.gsaf_url.data
            req = urllib2.Request(url)
            try:
                response = urllib2.urlopen(req)
                # response successful? 
            except urllib2.HTTPError as err:
                flash('Supplied GSAF URL is unreachable...', 'error')
                form.output_dataset.choices = get_dataset_choices(current_user, new = True)
                form.output_project.choices = get_project_choices(current_user, new = True)
                return render_template('import_files.html', form=form)
            else: 
                if form.output_project.data == 'new':
                    project = generate_new_project(user = current_user, name=form.project_name.data, description=form.project_description.data, session = db.session)
                else: 
                    project = db.session.query(Project).get(int(form.output_project.data))

                parse_gsaf_response_into_datasets.apply_async((url,), {'user_id':current_user.id, 'project_id':project.id}, queue=celery_queue)
                return redirect(url_for('frontend.dashboard'))
                 # render_template('sra_import.html', status=status, form=form, result=result, current_user=current_user)


        elif form.file_source.data == 'file_ncbi':

            return_value = import_from_sra.apply_async((), {'accession': form.ncbi_accession.data, 'name':form.ncbi_accession.data, 'user_id':current_user.id, 'project_selection': form.output_project.data, 'project_name': form.project_name.data, 'project_description':form.project_description.data, 'dataset_selection': form.output_dataset.data}, queue=celery_queue)
            return redirect(url_for('frontend.dashboard'))


        elif form.file_source.data =='file_url':

            add_to_project=False
            if form.output_dataset.data == 'new': 
                dataset = generate_new_dataset(user = current_user, name=form.dataset_name.data, description=form.dataset_description.data, session=db.session)
                add_to_project=True
            else: 
                dataset = db.session.query(Dataset).get(int(form.output_dataset.data))

            if form.output_project.data == 'new':
                project = generate_new_project(user = current_user, datasets = dataset, name=form.project_name.data, description=form.project_description.data, session = db.session)
            else: 
                project = db.session.query(Project).get(int(form.output_project.data))
                if add_to_project==True: 
                    project.datasets.append(dataset)

            new_file_ids = []
            for download_url in [url for url in [form.download_url_1.data, form.download_url_2.data] if url != None and url != '']: 
                # first create a new db file to place the download in
                new_file = File()
                new_file.url = download_url.rstrip()
                new_file.name = new_file.url.split('/')[-1].split('?')[0]
                new_file.file_type = parse_file_ext(new_file.name)
                new_file.dataset_id = dataset.id
                new_file.path = '{}/{}'.format(dataset.directory.rstrip('/'), new_file.name)
                new_file.user_id = current_user.id 
                new_file.available = False 
                new_file.status = ''

                if 'gz' in new_file.file_type.lower():
                    new_file.file_type = 'GZIPPED_FASTQ'

                db.session.add(new_file)
                db.session.commit()
                db.session.refresh( new_file )
                new_file_ids.append( new_file.id )
                # add the new file to the dataset
                dataset.files.append(new_file)

                download_file.apply_async((new_file.url, new_file.path, new_file.id), {'user_id' : current_user.id})

            flash('File(s) {} being downloaded and saved to Dataset {}'.format(','.join([str(i) for i in new_file_ids]), dataset.name), 'success')
            return redirect( url_for('frontend.dashboard') )


        elif form.file_source.data =='file_server':

            add_to_project=False
            if form.output_dataset.data == 'new': 
                dataset = generate_new_dataset(user = current_user, name=form.dataset_name.data, description=form.dataset_description.data, session=db.session)
                add_to_project=True
            else: 
                dataset = db.session.query(Dataset).get(int(form.output_dataset.data))

            if form.output_project.data == 'new':
                project = generate_new_project(user = current_user, datasets = dataset, name=form.project_name.data, description=form.project_description.data, session = db.session)
            else: 
                project = db.session.query(Project).get(int(form.output_project.data))
                if add_to_project==True: 
                    project.datasets.append(dataset)

            new_file_ids = [] 
            for path in [path for path in [form.server_file_1.data, form.server_file_2.data] if path != None and path != '']: 
                if os.path.isfile(path):
                    print 'Importing file {} and linking to dataset {}'.format(path, dataset.name)
                    file_name = path.split('/')[-1]
                    new_path = dataset.directory + '/' + file_name
                    file = File(name = file_name, path = new_path, user_id = current_user.id, dataset_id=dataset.id, check_name = False)
                    file.validate()
                    db.session.add(file)
                    print 'Copying file {} to new dataset path: {}'.format(file.name, file.path)
                    from shutil import copyfile
                    copyfile(path, new_path)
                    # os.rename(path, new_path) # would move file, removing old path
                    file.validate()
                    db.session.commit()
                    new_file_ids.append(file.id)
                    flash('File {} Successfully Imported, Linked to Dataset {}'.format(file.name, dataset.name), 'success')
                else: 
                    flash("File path {} doesn't seem to exist. Make sure it's right and permissions are open".format(path), 'warning')

            if len(new_file_ids)>0: 
                return redirect(url_for('frontend.datasets'))
            else: 
                dropbox_files = get_dropbox_files(current_user)
                form.output_dataset.choices = get_dataset_choices(current_user, new = True)
                form.output_project.choices = get_project_choices(current_user, new = True)
                return render_template("import_files.html", form=form, current_user=current_user, dropbox_files=dropbox_files)


        else: 
            flash('Did not understand POST request file_source....', 'warning')

            dropbox_files = get_dropbox_files(current_user)
            form.output_dataset.choices = get_dataset_choices(current_user, new = True)
            form.output_project.choices = get_project_choices(current_user, new = True)

            return render_template("import_files.html", form=form, current_user=current_user, dropbox_files=dropbox_files)

    else: # Finish GET : 
        
        dropbox_files = get_dropbox_files(current_user)
        form.output_dataset.choices = get_dataset_choices(current_user, new = True)
        form.output_project.choices = get_project_choices(current_user, new = True)

        return render_template("import_files.html", form=form, current_user=current_user, dropbox_files=dropbox_files)



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
    return render_template("files.html", files=files, current_user=current_user)

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

        file_types = ['FASTQ', 'GZIPPED_FASTQ', 'FASTA', 'GZIPPED_FASTA', 'IGFFT_ANNOTATION', 'MIXCR_ANNOTATION']
        if f.file_type not in file_types: 
            file_types.append(f.file_type)

        editfileform.file_type.choices = [(x, x) for x in file_types]

        if editfileform.validate_on_submit():
            f.name = editfileform.name.data
            f.file_type = editfileform.file_type.data
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
            elif editfileform.paired_partner.data != 0:
                f.paired_partner = editfileform.paired_partner.data
                f2 = db.session.query(File).filter(File.id==f.paired_partner).first()
                f2.paired_partner = f.id

            f.chain = editfileform.chain.data
            db.session.commit()
            flash('Edited ' + f.name, 'success')
        else:
            flash_errors(editfileform)

        return render_template("file.html", file=f, editfileform=editfileform, edit=edit, current_user=current_user)


@frontend.route('/delete_file/<int:id>')
@login_required
def delete_file(id):
    file = db.session.query(File).get(id)
    if current_user==file.user: 
        path = file.path
        db.session.delete(file)
        db.session.commit()
        flash('File {}, {} Deleted'.format(id, path), 'success')
        return redirect ( url_for( 'frontend.files') )
    else: 
        flash('You dont have permission to delete that file :(' ) 
        return redirect ( url_for( 'frontend.files' ) )



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
    pretime = time.time()
    datadict = get_user_dataset_dict(current_user)
    print "time to get datadict: {}".format(time.time()-pretime)
    return render_template("datasets.html", datadict=datadict, current_user=current_user)


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
        if current_user.dropbox_path in f.path: 
            new_path = dataset.directory + '/' + f.path.split('/')[-1]
            print 'moving dropbox file to new dataset path: {}'.format(new_path)
            os.rename(f.path, new_path)
            f.path = new_path
            flash('Dropbox file {} moved to Dataset directory: {}'.format(f.name, f.path), 'success')
        db.session.commit()
        flash('Dataset Successfully Edited', 'success')
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

    if not dataset.user_has_write_access(current_user):
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

@frontend.route('/delete_dataset/<int:id>')
@login_required
def delete_dataset(id):
    dataset = db.session.query(Dataset).filter(Dataset.id==id).first()
    if current_user==dataset.user: 
        db.session.delete(dataset)
        db.session.commit()
        flash('Dataset {} Deleted'.format(id), 'success')
        return redirect ( url_for( 'frontend.datasets') )
    else: 
        flash('You dont have permission to delete that dataset :(' ) 
        return redirect ( url_for( 'frontend.datasets' ) )


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





@frontend.route('/projects', methods=['GET', 'POST'])
@login_required
def projects():


    # all_projects = current_user.get_ordered_projects()

    projects = current_user.projects
    # shared_projects = current_user.shared_projects
    projects = sorted(projects, key=lambda x: x.id, reverse=True)
    print 'projects'
    print projects


    # print 'shared projects'
    # print shared_projects
    # shared_projects = all_projects.remove(projects)
    # projects = sorted(projects, key=lambda p: p.role(current_user))
    # projects = sum([[p for p in projects if p.role(current_user) == 'Editor'],[p for p in projects if p.role(current_user) == 'Owner']])
    return render_template("projects.html", shared_projects=None, projects = projects, current_user=current_user)





@frontend.route('/create_project', methods=['GET', 'POST'])
@login_required
def create_project():
    create_project_form = CreateProjectForm()

    # also need to wrap this with some exception handling in case this query fails
    users = Set(db.session.query(User).filter(User.id != current_user.id))
    users.discard(None)
    users = sorted(users, key=lambda x: x.last_name, reverse=False)
    user_choices = [(str(user.id), user.name) for user in users]
    create_project_form.editors.choices = user_choices # choices should be a tuple (str(id), username)
    create_project_form.viewers.choices = user_choices 

    datasets = Set(current_user.datasets)
    datasets.discard(None)
    datasets.discard(current_user.default_dataset)
    datasets = sorted(datasets, key=lambda x: x.id, reverse=False)
    dataset_choices = [(str(dataset.id), dataset.name + ' (' + str(dataset.id) + ')' ) for dataset in datasets]
    create_project_form.datasets.choices = dataset_choices # choices should be a tuple (id, username)

    if create_project_form.validate_on_submit():

        # Still need to test for duplicate names
        new_project = Project(
                            user_id = current_user.id,
                            name = create_project_form.name.data,
                            description = create_project_form.description.data,
                            cell_types_sequenced = create_project_form.cell_types_sequenced.data,
                            publications = create_project_form.publications.data,
                            species = create_project_form.species.data,
                            lab = create_project_form.lab.data
                        )

        # Get a list of users who can edit
        user_access_list = []
        user_read_list = []

        # The current user can of course access their own file
        user_access_list.append(current_user)

        # Add a list of users who can access the project
        for user in users:
            if str(user.id) not in create_project_form.editors.data:
                user_access_list.append(user)
            else:
                if str(user.id) not in create_project_form.viewers.data:
                    user_access_list.append(user)
                    user_read_list.append(user)

        # user editor list is now a list of editors and viewers, so set the association proxy accordingly
        new_project.users = user_access_list

        # add selected datasets to the project
        dataset_selection = []
        for dataset in datasets:
            if str(dataset.id) not in create_project_form.datasets.data:
                dataset_selection.append(dataset)

        if current_user.default_dataset:
            dataset_selection.append(current_user.default_dataset) 

        new_project.datasets = dataset_selection

        db.session.add(new_project)
        db.session.flush()
        
        # if the owner set read-only access for users, then we have to update the read-only setting in the association table manually
        if len(user_read_list) > 0:
            db.session.refresh(new_project)
            for user in user_read_list:
                try: 
                    read_only_user_project = db.session.query(UserProjects). \
                        filter(UserProjects.user_id == user.id). \
                        filter(UserProjects.project_id == new_project.id)
                    read_only_user_project[0].read_only = True
                except:
                    print "Error setting read_only attribute for {}".format(user)

        # determine if a JSON was submitted to be added to the project
        try:
            if request.files['file'].filename != '':
                db.session.refresh(new_project)

                request_file = request.files['file']
                json_string = request_file.read()

                # if this function returns a string, it describes the error
                error = create_datasets_from_JSON_string(json_string, new_project)
                if error:
                    flash(error, 'warning')            
        except:
            flash('There was an error in uploading your JSON file.','warning')

        db.session.commit()

        flash('Your new project has been created.', 'success')
        return redirect( url_for('frontend.projects') )

    else:
        flash_errors(create_project_form)

    defaults = [(str(user.id)) for user in users]
    create_project_form.editors.data = defaults # defaults should be a list [str(id)]
    create_project_form.viewers.data = defaults 
    dataset_defaults = [(str(dataset.id)) for dataset in datasets]
    create_project_form.datasets.data = dataset_defaults 

    return render_template("create_project.html", create_project_form = create_project_form, current_user=current_user)




@frontend.route('/edit_project/<project_id>', methods=['GET','POST'])
@login_required
def edit_project(project_id):
    edit_project_form = CreateProjectForm()

    project = db.session.query(Project).get(project_id)
        
    if not project:
        flash('Error: there was an error attempting to edit that project.', 'warning')
        return redirect( url_for('.projects') )

    if not project or current_user in project.readers or (current_user != project.owner and current_user not in project.editors):
        flash('Error: you do not have permission to edit that project.', 'warning')
        return redirect( url_for('.projects') )        

    editor_defaults = []
    viewer_defaults = []

    # Set of users, not including current user or project owner
    users = Set(db.session.query(User). \
            filter(User.id != current_user.id). \
            filter(User.id != project.user_id))
    users.discard(None)
    users = sorted(users, key=lambda x: x.last_name, reverse=False)

    user_choices = [(str(user.id), user.name) for user in users]
    edit_project_form.editors.choices = user_choices # choices should be a tuple (id, username)
    edit_project_form.viewers.choices = user_choices # choices should be a tuple (id, username)

    datasets = Set(current_user.datasets)
    datasets.discard(None)
    datasets.discard(current_user.default_dataset)
    datasets = sorted(datasets, key=lambda x: x.id, reverse=False)

    dataset_choices = [(str(dataset.id), dataset.name + ' (' + str(dataset.id) + ')' ) for dataset in datasets]
    edit_project_form.datasets.choices = dataset_choices # choices should be a tuple (id, username)

    owner = None

    if project:
        owner = project.owner.name
        
        if request.method == 'GET':
            for user in users:
                if user not in project.read_only_users:
                    viewer_defaults.append(str(user.id))
                else: # the user is in the read_only list, so they have to be taken off the editor list
                    editor_defaults.append(str(user.id))

                if user not in project.users:
                    editor_defaults.append(str(user.id))
            
            # this places datasets not attached to the current project on the right side of the multiselect
            edit_project_form.datasets.data = []
            for dataset in datasets:
                if dataset not in project.datasets:
                    edit_project_form.datasets.data.append(str(dataset.id))
            print "hey"
            print edit_project_form.datasets.data

            # populate select fields with user names
            edit_project_form.editors.data = editor_defaults # default should be a list of ids NOT SELECTED
            edit_project_form.viewers.data = viewer_defaults # default should be a list of ids NOT SELECTED

            # prepopulate the form with data from the database                
            edit_project_form.name.data = project.name
            edit_project_form.description.data = project.description
            edit_project_form.cell_types_sequenced.data = project.cell_types_sequenced
            edit_project_form.publications.data = project.publications
            edit_project_form.species.data = project.species
            edit_project_form.lab.data = project.lab 
            return render_template("edit_project.html", edit_project_form = edit_project_form, project_id = project_id, owner = owner, current_user=current_user)

        else:
            if edit_project_form.validate_on_submit():

                # Get a list of users who can edit
                user_access_list = []
                user_read_list = []

                # determine which users are selected as editors or readers (editor selection trumps reader selection)
                for user in users:
                    if str(user.id) not in edit_project_form.editors.data:
                        user_access_list.append(user)
                    else:
                        if str(user.id) not in edit_project_form.viewers.data:
                            user_access_list.append(user)
                            user_read_list.append(user)

                # user editor list is now a list of editors and viewers, so set the association proxy accordingly, not forgetting current user!
                user_access_list.append(current_user)
                if current_user.id != project.user_id:
                    for user in project.users:
                        if user.id == project.user_id:
                            user_access_list.append(user)

                project.users = user_access_list

                # Change the read only setting for selected read only users
                for user in user_read_list:
                    try: 
                        read_only_user_project = db.session.query(UserProjects). \
                            filter(UserProjects.user_id == user.id). \
                            filter(UserProjects.project_id == project.id)
                        read_only_user_project[0].read_only = True
                    except:
                        print "Error setting read_only attribute for {}".format(user)

                # Detmine which datasets are selected and add them to the databse
                dataset_selection = []

                # first, if another user has their datasets in the project, keep them there!
                project_datasets = Set(project.datasets)
                project_datasets.discard(None)
                for dataset in project_datasets:
                    if dataset.user_id != current_user.id:
                        dataset_selection.append(dataset)

                # now, add the datasets selected by the user
                for dataset in datasets:
                    if str(dataset.id) not in edit_project_form.datasets.data:
                        dataset_selection.append(dataset)
                project.datasets = dataset_selection

                # Still need to test for duplicate names
                # update the database with the data, then redirect
                project.name = edit_project_form.name.data
                project.description = edit_project_form.description.data
                project.cell_types_sequenced = edit_project_form.cell_types_sequenced.data
                project.publications = edit_project_form.publications.data
                project.species = edit_project_form.species.data
                project.lab = edit_project_form.lab.data

                db.session.commit()

                # determine if a JSON was submitted to be added to the project
                # try:
                #     if request.files['file'].filename != '':

                #         request_file = request.files['file']
                #         json_string = request_file.read()

                #         # if this function returns a string, it describes the error
                #         error = create_datasets_from_JSON_string(json_string, project)
                #         if error:
                #             flash(error, 'warning')    
                #         else:
                #             # now, we need to update the list of datasets in the project
                #             db.session.commit()
                #             flash('Success!!! Your new project has been updated.', 'success')
                #             return redirect( url_for('projects.edit_project', project_id = project.id) )
                # except:
                #     flash('There was an error in uploading your JSON file.','warning')
                
                flash('Success!!! Your new project has been updated.', 'success')

                # painfully redundant, but this will clean up and form issues where there is a double viewer/editor selection:
                for user in users:
                    if user not in project.read_only_users:
                        viewer_defaults.append(str(user.id))

                # populate select fields with user names
                edit_project_form.viewers.data = viewer_defaults # default should be a list of ids NOT SELECTED

            else:
                flash_errors(edit_project_form)

            # return render_template("edit_project.html", edit_project_form = edit_project_form, project_id = project_id, owner = owner, current_user=current_user)
            # return redirect(url_for('.show_project')) #, project.id)
            return redirect(url_for('.projects'))

    else:
        flash('Error: the project was not found or you do not have permission to edit the project.', 'warning')
        return redirect( url_for('.projects') )

    return render_template("edit_project.html", edit_project_form = edit_project_form, project_id = project_id, current_user=current_user)



@frontend.route('/project/<project_id>', methods=['GET', 'POST'])
@login_required
def show_project(project_id):

    show_project_form = CreateProjectForm()

    # first, make sure the user has access to the project
    try:
        project_query = db.session.query(Project). \
                            filter(Project.id == project_id). \
                            filter(Project.users.contains(current_user))
    except:
        flash('Error: there was an error attempting to view that project.','warning')
        return redirect( url_for('.projects') )

    if project_query and project_query.count() > 0:
        project = project_query[0]
    else:
        flash('Error: there was an error attempting to view that project.','warning')
        return redirect( url_for('.projects') )

    read_only = current_user in project.read_only_users

    show_project_form.name.data = project.name
    show_project_form.description.data = project.description
    show_project_form.cell_types_sequenced.data = project.cell_types_sequenced
    show_project_form.publications.data = project.publications
    show_project_form.species.data = project.species
    show_project_form.lab.data = project.lab
    creation_date = project.date_string()

    owner = project.owner.name
    write_user_list = [user.name for user in sorted(project.editors, key=lambda x: x.last_name, reverse=False)]
    read_only_list = [user.name for user in sorted(project.readers, key=lambda x: x.last_name, reverse=False)]



    datadict = OrderedDict()
    for dataset in sorted(project.datasets, key=lambda x: x.id, reverse=True):
        datadict[dataset] = sorted(dataset.files.all(), key=lambda x: x.id, reverse=True)



    datasets = Set(project.datasets)
    datasets.discard(None)
    datasets = sorted(datasets, key=lambda x: x.id, reverse=False)

    dataset_list = [(dataset.name + ' (' + str(dataset.id) + ')', dataset.owner.name, dataset.id) for dataset in datasets]

    return render_template("project.html", 
        show_project_form = show_project_form, 
        read_only_list = read_only_list,
        write_user_list = write_user_list,
        datadict = datadict, 
        dataset_list = dataset_list,
        current_user=current_user,
        datasets = datasets,
        project = project)




@frontend.route('/about', methods=['GET', 'POST'])
@login_required
def about():
    return render_template("about.html")


@frontend.route('/analysis', methods=['GET', 'POST'])
@login_required
def analyses(status=[]):
    status = request.args.getlist('status')
    analyses = current_user.analyses.all()[-50:]
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




@frontend.route('/analysis/msdb/', methods=['GET', 'POST'])
@login_required
def msdb(status=[]):

    msdb_form = CreateMSDBAnalysisForm()

    if request.method == 'POST':
        print request.__dict__

        if msdb_form.file_ids.data != [] and msdb_form.file_ids.data != '':
            result = run_msdb.apply_async( ( ),
                    { 
                        'user_id' : current_user.id, 
                        'file_ids' : msdb_form.file_ids.data,
                        # 'dataset_id' : output_dataset_id,
                        'analysis_id' : None, 
                        'analysis_name' : msdb_form.name.data,
                        'analysis_description' : msdb_form.description.data,
                        'error_correct_cluster_on': msdb_form.error_correct_cluster_on.data,
                        'error_correct_cluster_percent' : float(msdb_form.error_correct_cluster_percent.data),
                        'error_correct_cluster_algorithm': msdb_form.error_correct_cluster_algorithm.data,
                        'error_correct_read_cutoff': msdb_form.error_correct_read_cutoff.data,
                        'error_correct_max_sequences_per_cluster_to_report': msdb_form.error_correct_max_sequences_per_cluster_to_report.data,
                        'clonotyping_cluster_on': msdb_form.clonotyping_cluster_on.data,
                        'clonotyping_cluster_percent' : float(msdb_form.clonotyping_cluster_percent.data),
                        'clonotyping_cluster_algorithm': msdb_form.clonotyping_cluster_algorithm.data,
                        'clonotyping_read_cutoff': msdb_form.clonotyping_read_cutoff.data,
                        'clonotyping_max_sequences_per_cluster_to_report': msdb_form.clonotyping_max_sequences_per_cluster_to_report.data,
                        'clonotyping_cluster_linkage': msdb_form.clonotyping_cluster_linkage.data,
                        'require_annotations' : msdb_form.require_annotations.data,
                        'generate_fasta_file': msdb_form.generate_fasta_file.data,
                        'append_cterm_peptides': msdb_form.append_cterm_peptides.data,
                        'rescue_n_terminal_peptides': msdb_form.rescue_n_terminal_peptides.data,
                        'rescue_c_terminal_peptides': msdb_form.rescue_c_terminal_peptides.data,
                        'confirm_isotype_calls': msdb_form.confirm_isotype_calls.data,
                    }, queue=celery_queue )

            return redirect( url_for('frontend.dashboard') )
        else:
            flash('No files selected for analysis.', 'warning')
            return redirect(url_for('frontend.msdb'))

    else: # request.method == 'GET'

        current_analysis_id = db.session.query(func.max(File.id)).first()[0]
        if current_analysis_id:
            next_analysis_id = int(current_analysis_id) + 1
        else:
            next_analysis_id = 1

        msdb_form.name.data = 'Post-Annotation Analysis {}'.format( str(next_analysis_id) )

        datasets = current_user.get_ordered_datasets()
        dataset_file_dict = {}

        dataset_ids = tuple(map(lambda d: d.id, datasets))
        files = db.session.query(File).filter(File.dataset_id.in_(dataset_ids)).filter(File.file_type.in_(('ANNOTATION', 'BIGG_ANNOTATION', 'MIXCR_ANNOTATION', 'IGREP_ANNOTATION', 'IGFFT_ANNOTATION'))).filter(File.available==True).all()
        # files = [file for file in files if 'paired' not in file.name] #eliminate paired files? No! Need to support them.
        sorted_files = sorted(files, key=lambda f: f.dataset_id, reverse=True)
        grouped_files = itertools.groupby(sorted_files, key=lambda f: f.dataset_id)
        for dataset_id, files in grouped_files: 
            dataset = [dataset for dataset in datasets if dataset.id==dataset_id][0]
            dataset_file_dict[dataset] = [] 
            for file in files: 
                #only show files on local system
                if os.path.isfile(file.path):
                    dataset_file_dict[dataset].append(file)

        dataset_file_dict = {k:v for k, v in dataset_file_dict.items() if v != []}

        if len(datasets) == 0: 
            flash('You have no datasets with annotation files available for analysis', 'warning')

        return render_template("msdb.html", msdb_form=msdb_form, wtf=wtforms, status=status, current_user=current_user, dataset_file_dict = dataset_file_dict)






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
    err = False
    return render_template("browse_sequences.html", form=form, files=files, datasets=datasets, datadict=datadict, err=err, seq_count=seq_count, ann_count=ann_count, current_user=current_user)


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



@frontend.route('/celery_monitor', methods=['GET'])
def celery_monitor():
    return render_template("celery_monitor.html", current_user=current_user)


@frontend.route('/rabbitmq_monitor', methods=['GET'])
def rabbitmq_monitor():
    return render_template("rabbitmq_monitor.html", current_user=current_user)


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
    tasks = sorted(tasks, key=lambda x: x.id, reverse=True)[0:3]

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

            logfile = '{}/{}.log'.format( current_user.log_path.rstrip('/') , task.async_task_id )

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

            if async_task_progress == ''  and async_task_result.state == 'PROGRESS' and task.status not in ['DOWNLOADING', 'SUCCESS', 'FAILURE']:
                try:
                    async_task_state = async_task_result.state
                    async_task_current = async_task_result.info.get('current')
                    async_task_total = async_task_result.info.get('total')
                    async_task_status = async_task_result.info.get('status')
                    async_task_units = async_task_result.info.get('units')
                except Exception, exception: 
                    print 'There was an error in getting the task progress: {}'.format(exception)
                else:
                    if async_task_units == '%':
                        progress_message = '{} {} %'.format(async_task_status, async_task_current)
                    else:
                        progress_message = '{} {}/{} {}'.format(async_task_status, async_task_current, async_task_total, async_task_units)

                    try:
                        percent = int( float( int(async_task_current) ) / float( int(async_task_total) ) * 100 )
                    except:
                        percent = 0

                    if percent != 100: 
                        async_task_progress = """
                            <div class="progress" style="position: relative;">
                                <div class="progress-bar progress-bar-info" role="progressbar" aria-valuenow="{0}" aria-valuemin="0" aria-valuemax="{1}" style="width:{2}%;"></div>
                               <span class = "progress-value" style="position:absolute; right:0; left:0; width:100%; text-align:center; z-index:2; color:black;">{3}</span>
                            </div>
                        """.format(  async_task_current, async_task_total, percent, progress_message)
                    else: 
                        async_task_progress = '' 

            if async_task_progress == '' and async_task_result.state == 'RUNNING' and task.status not in ['DOWNLOADING', 'SUCCESS', 'FAILURE']:
                try:
                    async_task_state = async_task_result.state
                    async_task_status = async_task_result.info.get('status')
                except Exception, exception: 
                    print 'There was an error in getting the task progress: {}'.format(exception)
                else:
                    async_task_progress = '<div align="center"><b>{}...</b></div><br>'.format(  async_task_status )

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



@frontend.route('/alleledb', methods=['GET','POST'])
# @login_required
def alleledb():
    class AlleleForm(Form):
        locus_type_selector = SelectField(u'Species', choices=())
        locus_selector = SelectField(u'Locus', choices=())
        species_selector = SelectField(u'Species', choices=())
        gene_selector = SelectField(u'Species', choices=())
        source_selector = SelectField(u'Source', choices=())

        sequence_type_selector = SelectField(u'Sequence Type', choices=([('spliced nucleotide', 'spliced nucleotide'), ('gene', 'gene'), ('protein', 'protein'), ('default', 'default')]))
        distance_metric_selector = SelectField(u'Distance Metric', choices=([('hamming','hamming'), ('levenshtein','levenshtein'),('damerau_levenshtein','damerau_levenshtein'), ('jaro','jaro')]), default='hamming')
        weight_size_by_selector = SelectField(u'Weight Size By', choices=())
        color_by_selector = SelectField(u'Color By', choices=([('gene', 'gene'), ('organism', 'organism')]))
        linkage_threshold = FloatField(u'Linkage Threshold')


    form = AlleleForm()


    return render_template('alleledb.html', form=form)




@frontend.route('/alleledb_json', methods=['GET', 'POST'])
# @login_required
def alleledb_json():

    print request.args.__dict__

    source = request.args.get('source', None, type=str)
    species = request.args.get('species', None, type=str)
    locus_type = request.args.get('locus_type', None, type=str)
    locus = request.args.get('locus', None, type=str)
    gene = request.args.get('gene', None, type=str)
    sequence_type = request.args.get('sequence_type', None, type=str)

    print "alleledb query: species {} locus_type {} locus {} gene {}".format(species, locus_type, locus, gene)

    from collections import defaultdict

    j = defaultdict(lambda: '')
    allele_query = db.session.query(Allele)
    locus_name_query = db.session.query(Locus.name).join(Allele)
    locus_type_query = db.session.query(Locus.type).join(Allele)
    species_query = db.session.query(Species.name).join(Allele)
    if source:
        allele_query = allele_query.join(Source).filter(Source.name==source)
        locus_name_query = locus_name_query.join(Source).filter(Source.name == source)
        locus_type_query = locus_type_query.join(Source).filter(Source.name == source)
        species_query = species_query.join(Source).filter(Source.name==source)
    if species:
        allele_query = allele_query.join(Species).filter(Species.name==species)
        locus_name_query = locus_name_query.join(Species).filter(Species.name == species)
        locus_type_query = locus_type_query.join(Species).filter(Species.name == species)
    if gene:
        allele_query = allele_query.join(Gene).filter(Gene.name==gene)
    if locus_type:
        if locus:
            species_query = species_query.join(Locus).filter(Locus.type == locus_type, Locus.name == locus)
            allele_query = allele_query.join(Locus).filter(Locus.name == locus)
            j['gene_options'] = sorted([x[0] for x in set(db.session.query(Gene.name).join(Locus).filter(Locus.name == locus).all())])
        else:
            species_query = species_query.join(Locus).filter(Locus.type == locus_type)
            allele_query = allele_query.join(Locus).filter(Locus.type==locus_type)
            j['gene_options'] = sorted([x[0] for x in set(db.session.query(Gene.name).join(Locus).filter(Locus.type==locus_type).all())])
            # gene_ids = sorted([x[0] for x inset(map(lambda a: a.gene_id, alleles))
        j['locus_options'] = sorted([x[0] for x in set(db.session.query(Locus.name).filter(Locus.type==locus_type).all())])
    elif locus:
        species_query = species_query.join(Locus).filter(Locus.name==locus)
        allele_query = allele_query.join(Locus).filter(Locus.name == locus)
        j['gene_options'] = sorted([x[0] for x in set(db.session.query(Gene.name).join(Locus).filter(Locus.name == locus).all())])
    else:
        gene_ids = []
    if sequence_type:
        if sequence_type=='nuc' or sequence_type=='nucleotide' or sequence_type=='rna' or sequence_type=='spliced nucleotide' or sequence_type=='mrna':
            j['allele_sequence_type_status']+= "{} alleles have {} sequences".format(allele_query.filter(Allele.sequence_nuc != None).count(), sequence_type)
        elif sequence_type == 'prot' or sequence_type=='protein':
            j['allele_sequence_type_status']+="{} alleles have {} sequences".format(allele_query.filter(Allele.sequence_prot != None).count(), sequence_type)
        elif sequence_type=='gene':
            j['allele_sequence_type_status']+="{} alleles have {} sequences".format(allele_query.filter(Allele.sequence_gene != None).count(), sequence_type)
            # allele_query = allele_query.filter(Allele.sequence_gene  != None)
        elif sequence_type=='default':
            j['allele_sequence_type_status']+="{} alleles have {} sequences".format(allele_query.filter(Allele.sequence != None).count(), sequence_type)
    print allele_query
    alleles = allele_query.distinct().all()
    print "{} alleles found".format(len(alleles))


    j['species_options'] = [s.name for s in species_query.distinct().all()]

    j['source_options'] = sorted([x[0] for x in db.session.query(Source.name).distinct().all()])
    if 'locus_options' not in j.keys(): j['locus_options'] = sorted([l.name for l in locus_name_query.distinct().all()])
    if 'locus_type_options' not in j.keys(): j['locus_type_options'] = sorted([l.type for l in locus_type_query.distinct().all()])
    if 'gene_options' not in j.keys():
        gene_ids = set(map(lambda a: a.gene_id, alleles))
        j['gene_options'] = sorted([x[0] for x in db.session.query(Gene.name).filter(Gene.id.in_(gene_ids)).distinct().all()])
    j['allele_status'] += "{} Alleles Match Filters".format(len(alleles))

    print j
    return jsonify( j )



@frontend.route('/alleledb_network_json', methods=['GET', 'POST'])
# @login_required
def alleledb_network_json():

    source = request.args.get('source', None, type=str)
    species = request.args.get('species', None, type=str)
    locus_type = request.args.get('locus_type', None, type=str)
    locus = request.args.get('locus', None, type=str)
    gene = request.args.get('gene', None, type=str)

    sequence_type = request.args.get('sequence_type', None, type=str)
    distance_metric = request.args.get('distance_metric', None, type=str)
    weight_size_by = request.args.get('weight_size_by', None, type=str)
    color_by = request.args.get('color_by', None, type=str)
    linkage_threshold = request.args.get('linkage_threshold', None, type=float)


    print "alleledb network query: species {} locus_type {} locus {} gene {}".format(species, locus_type, locus, gene)

    allele_query = db.session.query(Allele)
    if source:
        allele_query = allele_query.join(Source).filter(Source.name == source)
    if species:
        allele_query = allele_query.join(Species).filter(Species.name == species)
    if gene:
        allele_query = allele_query.join(Gene).filter(Gene.name == gene)
    if locus:
        allele_query = allele_query.join(Locus).filter(Locus.name == locus)
    elif locus_type:
        allele_query = allele_query.join(Locus).filter(Locus.type == locus_type)
    if sequence_type:
        if sequence_type == 'nuc' or sequence_type=='nucleotide' or sequence_type=='spliced nuclotide' or sequence_type=='rna' or sequence_type=='mrna':
            allele_query = allele_query.filter(Allele.sequence_nuc != None)
        elif sequence_type == 'prot' or sequence_type=='protein':
            allele_query = allele_query.filter(Allele.sequence_prot != None)
        elif sequence_type == 'gene':
            allele_query = allele_query.filter(Allele.sequence_gene != None)
        elif sequence_type == 'default':
            allele_query = allele_query.filter(Allele.sequence != None)
    print allele_query
    alleles = allele_query.distinct().all()
    print "{} alleles found".format(len(alleles))


    #
    # # some names and sequences might by identical!
    # names = set(map(lambda a: a.name, alleles))
    # new_alleles = []
    # for name in names:
    #     new_alleles.append([a for a in alleles if a.name == name][0])
    # alleles = new_alleles
    #

    allele_network_dict = {}
    nodes = []
    for i, allele in enumerate(alleles):
        nodes.append({"id": allele.id, "group": allele.gene.name, "name": allele.name})
    allele_network_dict['nodes']=nodes


    print "building network json on {} alleles: sequence_type {} distance_metric {} weight_size_by {} color_by {} linkage_threshold {}".format(len(alleles), sequence_type, distance_metric, weight_size_by, color_by, linkage_threshold)
    import jellyfish
    import editdistance
    links = []
    comparisons_done = [] # tuples of sorted((allele1 identifier, allele2 identifier))
    for allele_i in alleles:
        for allele_j in alleles:
            identifier = tuple(sorted((allele_i.id, allele_j.id)))
            if identifier not in comparisons_done:
                # print 'running comparison of {}'.format(identifier)
                # print "sequence 1: {}".format(allele_i.sequence_by_type(seq_type=sequence_type))
                # print "sequence 2: {}".format(allele_j.sequence_by_type(seq_type=sequence_type))
                # distance = jellyfish.hamming_distance(unicode(allele_i.sequence_by_type(seq_type=sequence_type)), unicode(allele_j.sequence_by_type(seq_type=sequence_type)))
                distance = allele_i.distance_to(allele_j, method=distance_metric) # jellyfish.hamming_distance(unicode(allele_i.sequence), unicode(allele_j.sequence))
                if distance <= linkage_threshold:
                    links.append({"source":allele_i.id, "target":allele_j.id, 'value':distance})
                comparisons_done.append(identifier)
    allele_network_dict['links']=links

    return jsonify ( allele_network_dict )






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





@frontend.route('/project_dataset_options', methods=['GET', 'POST'])
@login_required
def project_dataset_options():

    assert current_user, 'no current_user object identified... exiting'
    if 'file_types' in request.args.keys():
        file_types = request.args.get('file_types', [], type=list)
        return_value = current_user.get_projects_datasets_files(file_types=file_types)
    else:
        return_value = current_user.get_projects_datasets_files()

    print return_value
    if type(return_value)==type(OrderedDict()) or type(return_value)==type(dict()) or type(return_value)==list:
        return json.dumps ( return_value )
        # return jsonify ( return_value )
    else:
        'project_dataset_options route did not return a dict...'
        return json.dumps( None )
        # return jsonify ( None )




import time


@frontend.route('/pipeline', methods=['GET', 'POST'])
@login_required
def pipeline(selected_dataset=None):

    build_pipeline_form = BuildPipelineForm(request.form)

    pipeline_request_start = time.time()

    if request.method == 'POST':

        #should check arguments first...
        form_valid = True 
        if form_valid: 

            # put the form contents into a format that can be serialized and sent to a celery task
            form_output_dict = {
                'user_id' : current_user.id,    
                'file_source' : build_pipeline_form.file_source.data,
                'dataset' : build_pipeline_form.dataset.data,
                'dataset_files' : build_pipeline_form.dataset_files.data,
                'name' : build_pipeline_form.name.data,
                'description' : build_pipeline_form.description.data,
                'split_pacbio': build_pipeline_form.split_pacbio.data,
                'split_pacbio_use_concatemers': build_pipeline_form.split_pacbio_use_concatemers.data,
                'trim' : build_pipeline_form.trim.data,
                'trim_slidingwindow' : build_pipeline_form.trim_slidingwindow.data,
                'trim_slidingwindow_size' : build_pipeline_form.trim_slidingwindow_size.data,
                'trim_slidingwindow_quality' : build_pipeline_form.trim_slidingwindow_quality.data,
                'trim_illumina_adapters' : build_pipeline_form.trim_illumina_adapters.data,
                'filter' : build_pipeline_form.filter.data, 
                'filter_quality' : build_pipeline_form.filter_quality.data, 
                'filter_percentage' : build_pipeline_form.filter_percentage.data, 
                'pandaseq' : build_pipeline_form.pandaseq.data,
                'pandaseq_algorithm' : build_pipeline_form.pandaseq_algorithm.data,
                'pandaseq_minimum_overlap' : build_pipeline_form.pandaseq_minimum_overlap.data, 
                'pandaseq_minimum_length': build_pipeline_form.pandaseq_minimum_length.data, 
                'analysis_type' : build_pipeline_form.analysis_type.data,
                'species' : build_pipeline_form.species.data,
                'loci': build_pipeline_form.loci.data,
                'standardize_outputs': build_pipeline_form.standardize_outputs.data,
                'require_annotations': build_pipeline_form.require_annotations.data,
                'append_cterm_peptides': build_pipeline_form.append_cterm_peptides.data,
                'remove_seqs_with_indels': build_pipeline_form.remove_seqs_with_indels.data,
                'pair_vhvl' : build_pipeline_form.pair_vhvl.data,
                'cluster' : build_pipeline_form.cluster.data,
                'cluster_algorithm' : str(build_pipeline_form.cluster_algorithm.data),
                'cluster_linkage' : str(build_pipeline_form.cluster_linkage.data),
                'cluster_percent': str(build_pipeline_form.cluster_percent.data),
            }

            result = run_analysis_pipeline.apply_async( (), form_output_dict, queue=celery_queue)
            return redirect(url_for("frontend.dashboard"))


    else: # If request is a GET


        # get a list of user projects - relational includes those they own and those shared with them
        # projects = current_user.get_ordered_projects()
        # get datasets from owned and shared projects
        datasets = current_user.get_ordered_datasets()

        pipeline_request_fetched_datasets = time.time()
        print("Dataset Fetching took {} seconds.".format(pipeline_request_fetched_datasets - pipeline_request_start))


        if len(datasets) > 0: 

            dataset_tuples = []
            for dataset in datasets: 
                dataset_tuples.append((str(dataset.id), str(dataset.name)))
            dataset_file_dict = {}
            dataset_project_dict = {}

            dataset_ids = tuple(map(lambda d: d.id, datasets))
            files = db.session.query(File).filter(File.dataset_id.in_(dataset_ids)).filter(File.file_type.in_(('FASTQ', 'GZIPPED_FASTQ', 'FASTA', 'GZIPPED_FASTA', 'SAM', 'BAM', 'SPLIT_FASTQ'))).all()
            sorted_files = sorted(files, key=lambda f: f.dataset_id, reverse=True)
            grouped_files = itertools.groupby(sorted_files, key=lambda f: f.dataset_id)
            files_by_dataset_id = OrderedDict()

            pipeline_request_preloop = time.time()
            print("Preloop took {} seconds.".format(pipeline_request_preloop - pipeline_request_start))

            for dataset_id, files in grouped_files: 
                files_by_dataset_id[str(dataset_id)] = {}
                file_names_by_id = {}
                for file in files: 
                    #only show files on local system
                    if os.path.isfile(file.path):
                        files_by_dataset_id[str(dataset_id)][str(file.id)] = str(file.name)

            dataset_file_dict = {k:v for k, v in files_by_dataset_id.items() if v != {}}

            pipeline_request_postloop = time.time()
            print("Postloop took {} seconds.".format(pipeline_request_postloop - pipeline_request_start))

            # This form does not need a new dataset option
            build_pipeline_form.dataset.choices = [tup for tup in dataset_tuples if tup[0] in dataset_file_dict.keys()]

        # ROUTINE attempt to speed it up - never could get it to connect json to render groups / drag and drop etc
        # projects_datasets_files = current_user.get_projects_datasets_files(file_types=['FASTQ', 'GZIPPED_FASTQ', 'FASTA', 'SAM', 'BAM', 'SPLIT_FASTQ'])
        # projects_datasets_files_formatted =  json.dumps ({'id':'node1', 'level':1, 'title':'placeholder', 'has_children':True, 'children': projects_datasets_files})
        # for pdf in projects_datasets_files:
        #     projects_datasets_files_formatted += json.dumps ( pdf )

        # list of tuples to set arbitrary HTML tag attributes
        # passed to JQUERY to set attributes
        # ('selector' , 'attribute' , 'attribute value')
        runtime_attributes = []
        form_warning_style = 'border: 2px solid #d66; border-radius: 7px; box-shadow: 0 0 10px #d66;'

        pipeline_request_end = time.time()
        print("Pipeline Full Request took {} seconds.".format(pipeline_request_end - pipeline_request_start))

        return render_template( "pipeline.html", build_pipeline_form = build_pipeline_form, dataset_file_dict = dataset_file_dict, dataset_project_dict = dataset_project_dict, runtime_attributes = runtime_attributes ) # projects_datasets_files=projects_datasets_files_formatted,




