#System Imports
import json
import static
import sys
import os
import time
import random
from shutil import copyfile
import operator
import urllib
import itertools
import subprocess
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


app = Flask(__name__, instance_relative_config=True)
app.config.from_pyfile('config.py')
# Initialize extensions
bcrypt = Bcrypt(app)
nav = Nav() 
Bootstrap(app) 
# Postgres DB for Admin and File Tracking Purposes 
# override DATABASE URI if environment variable is set: 
#print 'DEBUG ENVIRON keys:'
#for k,v in os.environ.items():
#    print '{} : {}'.format(k,v)


db = SQLAlchemy(app)



# Celery configured for local RabbitMQ 
celery = Celery(app.name, broker='amqp://')
import celery_config 
celery.config_from_object('celery_config')


# Mongo DB for Legacy Sequence Data
mongo_connection_uri = 'mongodb://reader:cdrom@biotseq.icmb.utexas.edu:27017/'
login_manager = LoginManager()
login_manager.init_app(app)

# load template environment for cleaner routes 
templateLoader = jinja2.FileSystemLoader( searchpath="{}/templates".format(app.config['HOME']) )
templateEnv = jinja2.Environment( loader=templateLoader, extensions=['jinja2.ext.with_'])









# MODELS. Not abstracted to make alembic migrations easier 

class User(db.Model):
        __tablename__ = 'user'
        id = db.Column(db.Integer, primary_key=True)
        username = db.Column(db.String(64))
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
        analyses = db.relationship('Analysis', backref='user', lazy='dynamic')
        
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

        def __repr__(self): 
            return "<  User {}: {}  {}  {}  >".format(self.username, self.first_name, self.last_name, self.email)



        def __init__(self): 
            self.user_type = 'researcher'


        def create_resources(self): 
            if self.first_name != None & self.last_name != None: 
                self.dropbox_path = '{}/{}{}'.format(app.config['DROPBOX_ROOT'], self.first_name, self.last_name)
                self.scratch_path = '{}/{}{}'.format(app.config['SCRATCH_ROOT'], self.first_name, self.last_name)
                if not os.path.isdir(self.dropbox_path):
                    os.makedirs(self.dropbox_path)
                    print 'created new directory at {}'.format(self.dropbox_path)
                if not os.path.isdir(self.scratch_path):
                    os.makedirs(self.scratch_path)
                    print 'created new directory at {}'.format(self.dropbox_path)
                return True 
            else: 
                print 'USER FIRST AND LAST NAMES NOT SET!'
                return False 





class File(db.Model):
        __tablename__ = 'file'
        id = db.Column(db.Integer, primary_key=True)
        user_id = db.Column(db.Integer, db.ForeignKey('user.id'))
        dataset_id = db.Column(db.Integer, db.ForeignKey('dataset.id'))
        name = db.Column(db.String(256))
        description =db.Column(db.String(512))
        file_type = db.Column(db.String(128))
        available = db.Column(db.Boolean)
        in_use = db.Column(db.Boolean)
        status = db.Column(db.String(50))
        path = db.Column(db.String(256))
        s3_available = db.Column(db.Boolean)
        s3_status = db.Column(db.String(50))
        s3_path = db.Column(db.String(256))
        chain = db.Column(db.String(128))
        url = db.Column(db.String(256))
        command = db.Column(db.String(1024))
        created = db.Column(db.DateTime, default=db.func.now())
        paired_partner = db.Column(db.Integer, db.ForeignKey('file.id'))
        parent_id = db.Column(db.Integer, db.ForeignKey('file.id'))
        analysis_id = db.Column(db.Integer, db.ForeignKey('analysis.id'))

        sequences = db.relationship('Sequence', backref='file', lazy='dynamic')

        def __repr__(self): 
            if self.paired_partner: 
                p = 'Paired To: {}'.format(str(self.paired_partner))
            else: 
                p = ''
            return "<File {}: _{}_  {}  {}>".format(self.id, self.file_type, self.name, p)


        def pair(self, f): 
            if self.file_type == f.file_type: 
                self.paired_partner = f.id 
                f.paired_partner = self.id 
                if self.dataset_id: 
                    d = self.dataset 
                    d.paired = True 
                return True 
            else: 
                return False


class Dataset(db.Model):
        __tablename__ = 'dataset'
        id = db.Column(db.Integer, primary_key=True)
        user_id = db.Column(db.Integer, db.ForeignKey('user.id'))
        experiment_id = db.Column(db.Integer, db.ForeignKey('experiment.id'))
        name = db.Column(db.String(256))
        description =db.Column(db.String(512))
        ig_type = db.Column(db.String(128))
        paired = db.Column(db.Boolean, default=False)
        files = db.relationship('File', backref='dataset', lazy='dynamic')
        sequences = db.relationship('Sequence', backref='dataset', lazy='dynamic')
        analyses = db.relationship('Analysis', backref='dataset', lazy='dynamic')
        annotations = db.relationship('Annotation', backref='dataset', lazy='dynamic')
        cell_types_sequenced = db.Column(postgresql.ARRAY(db.String(50)))
        chain_types_sequenced = db.Column(postgresql.ARRAY(db.String(20)))
        primary_data_file_ids = Column(postgresql.ARRAY(db.Integer))


        def __repr__(self): 
            return "<Dataset {} : {} : {}>".format(self.id, self.name, self.description)


class Experiment(db.Model):
        __tablename__ = 'experiment'
        id = db.Column(db.Integer, primary_key=True)
        user_id = db.Column(db.Integer, db.ForeignKey('user.id'))
        project_name = db.Column(db.String(128))
        description = db.Column(db.String(256))
        _id = db.Column(JSON())
        paired = db.Column(db.Boolean, default=False)
        chain_types_sequenced = db.Column(postgresql.ARRAY(db.String(20)))
        owners_of_experiment = db.Column(postgresql.ARRAY(db.String(20)))
        read_access = db.Column(postgresql.ARRAY(db.String(50)))
        cell_types_sequenced = db.Column(postgresql.ARRAY(db.String(50)))
        isotypes_sequenced = db.Column(postgresql.ARRAY(db.String(10)))
        publications = db.Column(postgresql.ARRAY(db.String(256)))
        mid_tag = db.Column(postgresql.ARRAY(db.String(256)))
        filenames = db.Column(postgresql.ARRAY(db.String(256)))
        reverse_primer_used_in_rt_step = db.Column(db.String(128))
        sample_preparation_date = db.Column(db.String(128))
        uploaded_by = db.Column(db.String(128))
        sequencing_platform = db.Column(db.String(128))
        experiment_creation_date = db.Column(db.String(128))
        species = db.Column(db.String(128))
        seq_count = db.Column(db.Integer())
        cell_number = db.Column(db.Integer())
        target_reads = db.Column(db.Integer())
        template_type = db.Column(db.String(128))
        experiment_name = db.Column(db.String(256))
        work_order = db.Column(db.String(128))
        gsaf_sample_name = db.Column(db.String(128))
        lab = db.Column(db.String(128))
        cell_selection_kit_name = db.Column(db.String(128))
        contains_rna_seq_data = db.Column(db.Boolean, default=False)
        curated = db.Column(db.Boolean, default=False)
        gsaf_barcode = db.Column(db.String(20))
        analyses_settings = db.Column(JSON())
        lab_notebook_source = db.Column(db.String(128))
        pairing_technique = db.Column(db.String(128))
        analyses_count = db.Column(JSON())
        person_who_prepared_library = db.Column(db.String(128))
        cell_markers_used = db.Column(postgresql.ARRAY(db.String(100)))
        list_of_polymerases_used = db.Column(postgresql.ARRAY(db.String(100)))
        primer_set_name = db.Column(postgresql.ARRAY(db.String(100)))
        datasets = db.relationship('Dataset', backref='experiment', lazy='dynamic')

        def __repr__(self): 
            return "<  Experiment {}:  {}   :   {}   :   {} >".format(self.id, self.project_name, self.experiment_name, self.seq_count)


def build_exp_from_dict(dict): 
    ex = Experiment()
    for k,v in dict.iteritems():
        vetted_k = ''
        for c in k: 
            if c in ['$']:
                do_nothing = ''
            else: 
                vetted_k = ''.format(vetted_k, c)
        setattr(ex, k.lower(), v)
    return ex






class Sequence(db.Model):  

        id = Column(Integer(), primary_key=True)
        dataset_id = Column(Integer(), ForeignKey('dataset.id'))
        file_id = Column(Integer(), ForeignKey('file.id'))
        header = Column(String(100))
        sequence = Column(String(500))
        quality = Column(String(500))
        annotations = db.relationship('Annotation', backref='sequence', lazy='dynamic')

        def __repr__(self): 
            return "< Sequence {}: {} >".format(self.id, self.header)





class Annotation(db.Model):  

        id = Column(Integer(), primary_key=True)
        sequence_id = Column(Integer(), ForeignKey('sequence.id'))
        dataset_id = Column(Integer(), ForeignKey('dataset.id'))
        analysis_id = Column(Integer(), ForeignKey('analysis.id'))
        _id = Column(JSON())
        seq_id = Column(JSON())
        exp_id = Column(JSON())
        analysis_name = Column(String())
        recombination_type = Column(String())
        strand = Column(String(10))
        
        productive = Column(db.Boolean)
        productive_comment = Column(String(256))
        recombination_type = Column(String(20))
        chain = Column(String(20))

        locus = Column(String)
        isotype = Column(String)
        isotype_mismatches = Column(Integer)
        isotype_percent_similarity = Column(FLOAT)
        isotype_barcode_direction = Column(String)

        nt = Column(String(600))
        aa = Column(String(200))

        cdr1_aa = Column(String(100))
        cdr1_nt = Column(String(100))
        cdr2_aa = Column(String(100))
        cdr2_nt = Column(String(100))
        cdr3_aa = Column(String(200))
        cdr3_nt = Column(String(400))
        fr1_nt = Column(String(200))
        fr1_aa = Column(String(100))
        fr2_nt = Column(String(100))
        fr2_aa = Column(String(100))
        fr3_nt = Column(String(200))
        fr3_aa = Column(String(200))
        fr4_nt  = Column(String(100))
        fr4_aa = Column(String(100))

        c_top_hit = Column(String) 
        c_top_hit_locus = Column(String)
        v_top_hit = Column(String) 
        v_top_hit_locus = Column(String) 
        d_top_hit = Column(String) 
        d_top_hit_locus = Column(String) 
        j_top_hit = Column(String) 
        j_top_hit_locus = Column(String) 
        
        c_hits = Column(JSON)
        j_hits = Column(JSON)
        d_hits = Column(JSON)
        v_hits = Column(JSON)

        shm_aa = Column(FLOAT())
        shm_nt = Column(FLOAT())
        shm_nt_percent = Column(FLOAT())
        shm_aa_percent = Column(FLOAT())
        v_shm_nt = Column(Integer)
        v_shm_percent = Column(FLOAT)
        j_shm_nt = Column(Integer)
        j_shm_percent = Column(FLOAT)

        full_length = Column(Boolean)
        cdr3_junction_in_frame = Column(Boolean)
        codon_frame = Column(Integer)
        start_codon = Column(Integer)
        stop_codon = Column(Integer)

        def __repr__(self): 
            return "< Annotation {} on Sequence {} : {} >".format(self.id, self.sequence_id, self.analysis_name)

        def __init__(self):
            self.v_hits = OrderedDict()
            self.d_hits = OrderedDict()
            self.j_hits = OrderedDict()
            self.c_hits = OrderedDict()


def build_annotation_from_mongo_dict(d): 
    d = flatten_dictionary(d)
    nd = {}
    for k,v in d.iteritems(): 
        nd[k.lower()] = v 
    d = nd 
    ann = Annotation() 
    if d['analysis_name'] == 'IMGT': 
        print 'interpreting IMGT Annotation Record from flattened mongo sequence document' 
        print d
        ann.v_hits = OrderedDict()
        ann.d_hits = OrderedDict()
        ann.j_hits = OrderedDict()
        ann.c_hits = OrderedDict()
        for k,v in d.iteritems(): 
            if "_id" == k: ann._id = v
            if "seq_id" == k: ann.seq_id = v
            if "exp_id" == k: ann.exp_id = v
            if "analysis_name" == k: ann.analysis_name = v
            if "recombination_type" == k: ann.recombination_type = v
            if "data.cdr3.aa" == k: ann.cdr3_aa = v
            if "data.cdr3.nt" == k: ann.cdr3_nt = v
            if "data.jregion.fr4.aa" == k: ann.fr4_aa = v            
            if "data.jregion.fr4.nt" == k: ann.fr4_nt = v
            # if "data.notes" == k: ann.notes = v
            if "data.predicted_ab_seq.aa" == k: ann.aa = v
            if "data.predicted_ab_seq.nt" == k: ann.nt = v
            if "data.strand" == k: ann.strand = v
            if "data.vregion.cdr1.aa" == k: ann.cdr1_aa = v
            if "data.vregion.cdr1.nt" == k: ann.cdr1_nt = v
            if "data.vregion.cdr2.aa" == k: ann.cdr2_aa = v
            if "data.vregion.cdr2.nt" == k: ann.cdr2_nt = v
            if "data.vregion.fr1.aa" == k: ann.fr1_aa = v
            if "data.vregion.fr1.nt" == k: ann.fr1_nt = v
            if "data.vregion.fr2.aa" == k: ann.fr2_aa = v
            if "data.vregion.fr2.nt" == k: ann.fr2_nt = v
            if "data.vregion.fr3.aa" == k: ann.fr3_aa = v
            if "data.vregion.fr3.nt" == k: ann.fr3_nt = v
            if "data.vregion.shm.aa" == k: ann.shm_aa = v
            if "data.vregion.shm.nt" == k: ann.shm_nt = v
            # if "date_updated" == k: ann.date_updated = v
            # if "settings" == k: ann.settings = v

            if "data.vregion.vgenes" == k: 
                if "data.vregion.vgene_scores" in d: 
                    if len(v) == len(d["data.vregion.vgene_scores"]):
                        for i in range(0,len(v)):
                            ann.v_hits[v[i]] = d["data.vregion.vgene_scores"][i]
                    else: 
                        for i in range(0,len(v)):
                            ann.v_hits[v[i]] = d["data.vregion.vgene_scores"][0]
                else: 
                    for i in range(0,len(v)):
                        ann.v_hits[v[i]] 
                if len(ann.v_hits) > 0: 
                    ann.v_top_hit = ann.v_top_hit_locus = sorted(ann.v_hits, key=operator.itemgetter(1))[-1]
                    ann.v_top_hit_locus= trim_ig_locus_name(ann.v_top_hit_locus)
            if "data.dregion.dgenes" == k: 
                if "data.dregion.dgene_scores" in d: 
                    for i in range(0,len(v)):
                        ann.d_hits[v[i]] = d["data.dregion.dgene_scores"][i]
                else: 
                    for i in range(0,len(v)):
                        ann.d_hits[v[i]] = True 
                if len(ann.d_hits) > 0 : 
                    if ann.d_hits.values() == [True]: 
                        ann.d_top_hit = ann.d_top_hit_locus = ann.d_hits.keys()[0]
                    else: 
                        ann.d_top_hit = ann.d_top_hit_locus = sorted(ann.d_hits, key=operator.itemgetter(1))[-1]
                        ann.d_top_hit_locus= trim_ig_locus_name(ann.d_top_hit_locus)
            if "data.jregion.jgenes" == k: 
                if "data.jregion.jgene_scores" in d: 
                    if len(v) == len(d["data.jregion.jgene_scores"]):
                        for i in range(0,len(v)):
                            ann.j_hits[v[i]] = d["data.jregion.jgene_scores"][i]
                    else: 
                        for i in range(0,len(v)):
                            ann.j_hits[v[i]] = d["data.jregion.jgene_scores"][0]
                else: 
                    for i in range(0,len(v)):
                        if 'LESS' not in v[i]:
                            ann.j_hits[v[i]] = True 
                if len(ann.j_hits) > 0: 
                    ann.j_top_hit = ann.j_top_hit_locus = sorted(ann.j_hits, key=operator.itemgetter(1))[-1]
                    ann.j_top_hit_locus= trim_ig_locus_name(ann.j_top_hit_locus)
            # CONSTANT REGION FROM IMGT? 
            # if "data.cregion.cgenes" == k: 
            #     if "data.cregion.cgene_scores" in d: 
            #         for i in range(0,len(v)):
            #             ann.c_hits[v[i]] = d["data.cregion.cgene_scores"][i]
            #     else: 
            #         for i in range(0,len(v)):
            #             ann.c_hits[v[i]] 
                # if len(ann.c_hits) > 0: 
                #     ann.c_top_hit = sorted(ann.c_hits, key=operator.itemgetter(1))[-1][0]
                #     ann.c_top_hit_locus = ann.c_top_hit.split('-')[0].split('*')[0].split('.')[0]

            if "data.productive" == k: 
                if 'PRODUCTIVE' in v: 
                    ann.productive = True
                else: 
                    ann.productive = False 

        return ann 
    else: 
        print 'CAN NOT INTERPRET NON-IMGT DOCUMENTS (yet)'
        return False


def trim_ig_allele_name(long_name): 
    if long_name == None: return ''
    if '*' in long_name: long_name = [l for l in long_name.split('*') if 'IG' in l or 'TR' in l][0]
    return long_name

def trim_ig_locus_name(long_name): 
    # print 'trimming long name: {}'.format(long_name)
    if long_name == None: return ''
    if long_name == '*': return ''
    if long_name == '.': return ''
    if long_name == 'P': return ''
    if long_name == '-': return ''
    if long_name == ' ': return ''
    if '-' in long_name: long_name = [l for l in long_name.split('-') if 'IG' in l or 'TR' in l][0]
    if '*' in long_name: long_name = [l for l in long_name.split('*') if 'IG' in l or 'TR' in l][0]
    if '.' in long_name: long_name = [l for l in long_name.split('.') if 'IG' in l or 'TR' in l][0]
    if 'P' in long_name: long_name = [l for l in long_name.split('P') if 'IG' in l or 'TR' in l][0]
    if ' ' in long_name: long_name = [l for l in long_name.split(' ') if 'IG' in l or 'TR' in l][0]
    return long_name



def parse_alignments_from_mixcr_hits(hits): 
    score_dict = OrderedDict()
    hs = hits.split(',')
    if len(hs) == 0: 
        return score_dict
    for h in hs: 
        if len(h.split('(')) != 2: 
            # print '!!!!!!! Empty h?:  {}'.format(h)
            continue
        gene,score = h.split('(')
        # short_gene = trim_ig_locus_name(gene)
        score = int(score.replace(')',''))
        score_dict[gene] = score 
    return score_dict 



def build_annotations_from_mixcr_file(file_path, dataset_id=None, analysis_id=None): 
    f = open(file_path)
    headers = f.readline().split('\t')
    annotations = []
    for line in f.readlines():
        fields = line.split('\t')
        ann = Annotation() 
        ann.analysis_name = 'MIXCR'
        if dataset_id: ann.dataset_id = dataset_id 
        if analysis_id: ann.analysis_id = analysis_id
        for i,k in enumerate(headers): 

            # COULD USE THIS TO BUILD SEQUENCE DOCUMENTS
            # if "Read(s) sequence" == k: ann.   = fields[i]
            # if "Read(s) sequence qualities" == k: ann.   = fields[i]
            if "All V hits" == k: ann.v_hits  = parse_alignments_from_mixcr_hits(fields[i])
            if "All D hits" == k: ann.d_hits  = parse_alignments_from_mixcr_hits(fields[i])
            if "All J hits" == k: ann.j_hits  = parse_alignments_from_mixcr_hits(fields[i])
            if "All C hits" == k: ann.c_hits  = parse_alignments_from_mixcr_hits(fields[i])
            if len(ann.v_hits): ann.v_top_hit = trim_ig_allele_name(sorted(ann.v_hits.items(), key=lambda x: x[1], reverse=True)[0][0])
            if len(ann.v_hits): ann.v_top_hit_locus = trim_ig_locus_name(ann.v_top_hit)
            if len(ann.d_hits): ann.d_top_hit = trim_ig_allele_name(sorted(ann.d_hits.items(), key=lambda x: x[1], reverse=True)[0][0])
            if len(ann.d_hits): ann.d_top_hit_locus = trim_ig_locus_name(ann.d_top_hit)
            if len(ann.j_hits): ann.j_top_hit = trim_ig_allele_name(sorted(ann.j_hits.items(), key=lambda x: x[1], reverse=True)[0][0])
            if len(ann.j_hits): ann.j_top_hit_locus = trim_ig_locus_name(ann.j_top_hit)
            if len(ann.c_hits): ann.c_top_hit = trim_ig_allele_name(sorted(ann.c_hits.items(), key=lambda x: x[1], reverse=True)[0][0])
            if len(ann.c_hits): ann.c_top_hit_locus = trim_ig_locus_name(ann.c_top_hit)
            # if "All V alignments" == k: ann.   = fields[i]
            # if "All D alignments" == k: ann.   = fields[i]
            # if "All J alignments" == k: ann.   = fields[i]
            # if "All C alignments" == k: ann.   = fields[i]
            if "N. Seq. FR1" == k: ann.fr1_nt   = fields[i]
            # if "Min. qual. FR1" == k: ann.   = fields[i]
            if "N. Seq. CDR1" == k: ann.cdr1_nt   = fields[i]
            # if "Min. qual. CDR1" == k: ann.   = fields[i]
            if "N. Seq. FR2" == k: ann.fr2_nt   = fields[i]
            # if "Min. qual. FR2" == k: ann.   = fields[i]
            if "N. Seq. CDR2" == k: ann.cdr2_nt   = fields[i]
            # if "Min. qual. CDR2" == k: ann.   = fields[i]
            if "N. Seq. FR3" == k: ann.fr3_nt   = fields[i]
            # if "Min. qual. FR3" == k: ann.   = fields[i]
            if "N. Seq. CDR3" == k: ann.cdr3_nt   = fields[i]
            # if "Min. qual. CDR3" == k: ann.   = fields[i]
            if "N. Seq. FR4" == k: ann.fr4_nt   = fields[i]
            # if "Min. qual. FR4" == k: ann.   = fields[i]
            if "AA. Seq. FR1" == k: ann.fr1_aa   = fields[i]
            if "AA. Seq. CDR1" == k: ann.cdr1_aa   = fields[i]
            if "AA. Seq. FR2" == k: ann.fr2_aa   = fields[i]
            if "AA. Seq. CDR2" == k: ann.cdr2_aa   = fields[i]
            if "AA. Seq. FR3" == k: ann.fr3_aa   = fields[i]
            if "AA. Seq. CDR3" == k: ann.cdr3_aa   = fields[i]
            if "AA. Seq. FR4" == k: ann.fr4_aa   = fields[i]
            # if "Ref. points" == k: ann.   = fields[i]


            # if "data.productive" == k: 
            #     if 'PRODUCTIVE' in v: 
            #         ann.productive = True
            #     else: 
            #         ann.productive = False 

        annotations.append(ann)
    return annotations










class Analysis(db.Model):  

        id = Column(Integer(), primary_key=True)
        user_id = Column(Integer(), ForeignKey('user.id'))
        dataset_id = Column(Integer(), ForeignKey('dataset.id'))
        name = Column(String())
        description = Column(String(256))
        program = Column(String())
        started = Column(TIMESTAMP)
        finished = Column(TIMESTAMP)
        params = Column(JSON)
        commands = Column(postgresql.ARRAY(String(1024)))
        responses = Column(postgresql.ARRAY(Integer))
        vdj_count = Column(Integer)
        vj_count = Column(Integer)
        tcra_count = Column(Integer)
        tcrb_count = Column(Integer)
        total_count = Column(Integer)
        active_command = Column(String(512))
        status = Column(String(256))
        db_status = Column(String(256))
        notes = Column(String(1000))
        available = Column(Boolean)
        inserted_into_db = Column(Boolean)

        annotations = db.relationship('Annotation', backref='analysis', lazy='dynamic')
        files = db.relationship('File', backref='analysis', lazy='dynamic')

        def __repr__(self): 
            return "< Analysis {}: {} : {} : {}>".format(self.id, self.program, self.name, self.started)

        def __init__(self):
            self.available = False






























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
        View('Import File', '.file_download'), 
        Link('Share Files', 'under_construction'),
        ),
    Subgroup(
        'Run Analysis',
        View('My Datasets', '.datasets'),
        View('Launch Analysis', '.datasets'),
        Link('Other Tasks', 'under_construction'), 
        ),
    Subgroup(
        'Database', 
        View('Browse Experiments', '.browse_experiments'),
        View('Browse Sequences', '.browse_sequences'),
        Link('Download', 'under_construction'),
        Link('Mass Spec', 'under_construction')
        ),
    View('Dashboard', '.analyses'),
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
    result = instantiate_user_with_directories.delay(new_user.id)
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
        copyfile('{}/{}'.format(share_root, f), '{}/{}'.format(new_user.dropbox_path, f))
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
        return redirect(url_for('.index'))
    else: 
        flash('no user logged in')
        return redirect(url_for('.index'))
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
        file.locus = form.locus.data
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
def file_download():
    form = FileDownloadForm()
    if request.method == 'POST':
        file = File()
        file.url = form.url.data
        file.name = file.url.split('/')[-1].split('?')[0]
        file.file_type = parse_file_ext(file.name)
        file.description = form.description.data
        file.locus = form.locus.data
        file.paired_partner = form.paired_partner.data 
        file.dataset_id = form.dataset_id.data
        file.path = '{}/{}'.format(current_user.scratch_path, file.name) 
        file.user_id = current_user.id
        file.available = False 
        print 'Saving File Metadata to Postgres: {}'.format(file.__dict__)
        db.session.add(file)
        db.session.commit()
        status = ['Started background task to download file from {}'.format(file.url),
        'Saving File To {}'.format(file.path),
        'This file will be visible in "My Files", and available for use after the download completes.']
        print status 
        # result_id NOT WORKING - STILL REDUNDANT IF THEY CLICK TWICE!!
        if not 'async_result_id' in session.__dict__:
            result = download_file.delay(file.url, file.path, file.id)
            flash('file downloading from {}'.format(file.url))
            session['async_result_id'] = result.id
        time.sleep(1)
        async_result = add.AsyncResult(session['async_result_id'])
        # r = async_result.info
        r = result.__dict__
        r['async_result.info'] = async_result.info 

        db.session.commit()
        flash('file uploaded to {}'.format(file.path))
        return render_template("file_download.html", download_form=form, status=status, r=r)
        # return redirect(url_for('.files'))
    else:
        status = ''
        r=''
        return render_template("file_download.html", download_form=form, status=status, r=r)




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
    files = sorted(current_user.files.all(), key=lambda x: x.id, reverse=True)
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
                files = sorted(current_user.files, key=lambda x: x.id, reverse=True)
        else: 
            flash('file metadata already created to your user')
            dropbox_file_paths = get_dropbox_files(current_user)
        return render_template("files.html", files=files, dropbox_files=dropbox_file_paths, form=form)
    else: 
        dropbox_file_paths = get_dropbox_files(current_user)
        return render_template("files.html", files=files, dropbox_files=dropbox_file_paths, form=form)



@frontend.route('/files/<int:id>', methods=['GET'])
@login_required
def file(id):
    f = db.session.query(File).filter(File.id==id).first()
    return render_template("file.html", file=f)



@frontend.route('/files/download/<int:id>')
@login_required
def send_file_from_id(id):
    print request.__dict__
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
    print request.__dict__
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
    print request.__dict__
    print 'finding dataset with {}'.format(id)
    dataset = db.session.query(Dataset).filter(Dataset.id==id).first()
    form = AssociateFilesToDatasetForm()
    form.dataset_id.data = dataset.id 
    file_choices = [f for f in db.session.query(File).filter(File.user_id==current_user.id).all() if f.dataset_id == None]
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
        result = run_mixcr_with_dataset_id.delay(dataset_id, analysis_name=form.name.data, analysis_description=form.description.data, user_id=current_user.id)
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
























@celery.task
def download_file(url, path, file_id):
    url_opener = urllib.URLopener()
    url_opener.retrieve(url, path)
    f = db.session.query(File).filter(File.id==file_id).first()
    f.available = True
    db.session.commit()
    return True 


@celery.task
def run_mixcr_with_dataset_id(dataset_id, analysis_name='', analysis_description='', user_id=6):
    analysis = Analysis()
    analysis.db_status = 'WAITING'
    analysis.name = analysis_name
    analysis.user_id = user_id
    analysis.description = analysis_description
    dataset = db.session.query(Dataset).filter(Dataset.id==dataset_id).first()
    print 'RUNNING MIXCR ON DATASET ID# {}: {}'.format(dataset_id, repr(dataset.__dict__))
    gzipped_fastqs = [f for f in dataset.files.all() if f.file_type=='GZIPPED_FASTQ']
    fastqs = [f for f in dataset.files.all() if f.file_type=='FASTQ']
    print 'FOUND THESE FASTQ FILES: GZIPPED_FASTQ: {} {}  FASTQ: {} {}'.format(len(gzipped_fastqs), gzipped_fastqs, len(fastqs), fastqs)
    if len(fastqs) == 0 and len(gzipped_fastqs) == 0: 
        print 'NO FASTQ DATA ASSOCIATED WITH DATASET'
        return False 
    if len(fastqs) == 0 and len(gzipped_fastqs) != 0: 
        print 'PLEASE DECOMPRESS FASTQ.GZ AND RESUBMIT JOB'
        return False
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
    if len(fastqs) != 0: 
        fastqs_by_locus = {}
        for key, values in itertools.groupby(fastqs, lambda x: x.locus): 
            fastqs_by_locus[key] = list(values)
        print fastqs_by_locus
        for locus, fastqs in fastqs_by_locus.items(): 
            print 'ABOUT TO RUN MIXCR ANAYSIS {} ON FILES FROM LOCUS {}'.format(repr(analysis), locus)
            run_mixcr_analysis_id_with_files(analysis.id, fastqs)
        return True 
    # db.session.commit()
    return False 




@celery.task
def run_mixcr_analysis_id_with_files(analysis_id, files):
    analysis = db.session.query(Analysis).filter(Analysis.id==analysis_id).first()
    print 'RUNNING MIXCR ON THESE FILES: {}'.format(files)
    scratch_path = '/{}'.format('/'.join(files[0].path.split('/')[:-1]))
    basename = files[0].path.split('/')[-1].split('.')[0]
    basepath = '{}/{}'.format(scratch_path, basename)
    print 'Writing output files to base name: {}'.format(basepath)
    commands = []
    output_files = []
    alignment_file = File()
    alignment_file.path = '{}.aln.vdjca'.format(basepath)
    alignment_file.name = "{}.aln.vdjca".format(basename)
    alignment_file.command = 'mixcr align -f {} {}'.format(' '.join([f.path for f in files]), alignment_file.path)
    alignment_file.file_type = 'MIXCR_ALIGNMENTS'
    commands.append(alignment_file.command) 
    output_files.append(alignment_file)
    clone_file = File()
    clone_file.file_type = 'MIXCR_CLONES'
    clone_file.path = '{}.aln.clns'.format(basepath)
    clone_file.name = '{}.aln.clns'.format(basename)
    clone_file.command = 'mixcr assemble -f {} {}'.format(alignment_file.path, clone_file.path)
    commands.append(clone_file.command)
    output_files.append(clone_file)
    clone_output_file = File()
    clone_output_file.path = '{}.txt'.format(clone_file.path)
    clone_output_file.file_type = 'MIXCR_CLONES_TEXT'
    clone_output_file.name = '{}.txt'.format(clone_file.name)
    clone_output_file.command = 'mixcr exportClones {} {}'.format(clone_file.path, clone_output_file.path)
    commands.append(clone_output_file.command) 
    output_files.append(clone_output_file)
    alignment_output_file = File()
    alignment_output_file.path = '{}.txt'.format(alignment_file.path)
    alignment_output_file.file_type = 'MIXCR_ALIGNMENT_TEXT'
    alignment_output_file.name = '{}.txt'.format(alignment_file.name)
    alignment_output_file.command = 'mixcr exportAlignments {} {}'.format(alignment_file.path, alignment_output_file.path)
    commands.append(alignment_output_file.command) 
    output_files.append(alignment_output_file)
    # pretty_alignment_file = File()
    # pretty_alignment_file.path = '{}.pretty.txt'.format(alignment_file.path)
    # pretty_alignment_file.file_type = 'MIXCR_PRETTY_ALIGNMENT_TEXT'
    # pretty_alignment_file.name =  '{}.pretty.txt'.format(alignment_file.name)
    # pretty_alignment_file.command = 'mixcr exportAlignmentsPretty {} {}'.format(alignment_file.path, pretty_alignment_file.path)
    # commands.append(pretty_alignment_file.command)
    # output_files.append(pretty_alignment_file)
    print 'running these commands:'
    print '\n'.join(commands)
    analysis.commands = commands 
    analysis.status = 'EXECUTING'
    db.session.commit()
    for f in output_files:
        f.command = f.command.encode('ascii')
        # f.command = str(f.command)
        f.dataset_id = analysis.dataset_id 
        f.analysis_id = analysis.id 
        f.locus = files[0].locus 
        db.session.add(f)
        print 'Executing: {}'.format(f.command)
        analysis.active_command = f.command
        db.session.commit()
        response = os.system(f.command)
        responses = analysis.responses
        responses.append(response)
        analysis.responses = responses 
        db.session.commit()
        print 'Response: {}'.format(response)
        if response == 0: 
            f.available = True 
            db.session.commit()
        else:
            f.available = False
            analysis.status = 'FAILED'
            db.session.commit()
    print 'All commands in analysis {} have been executed.'.format(analysis)
    if set(responses) == [0]:
        analysis.status = 'SUCCESS'
        analysis.available = True
    if not analysis.status == 'FAILED': analysis.status = 'SUCCESS'
    analysis.active_command = ''
    analysis.finished = 'now'
    db.session.commit()
    # KICK OFF ASYNC DB INSERTS FROM OUTPUT FILES
    parseable_mixcr_alignments_file_path = alignment_output_file.path
    db.session.commit()
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
    result = annotate_analysis_from_db.delay(analysis.id)
    return len(annotations)





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


