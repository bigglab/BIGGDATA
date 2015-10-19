"""Database models for the BIGGIG application."""

import json
import static
import os
import time
import random
from render_utils import make_context, smarty_filter, urlencode_filter
from werkzeug.debug import DebuggedApplication
from flask import Flask, make_response, render_template, render_template_string, request, session, flash, redirect, url_for, jsonify, get_flashed_messages
from flask.ext.login import LoginManager, UserMixin, current_user, login_user, logout_user
import wtforms
from forms import LoginForm
from flask.ext.mail import Mail, Message
from flask_sqlalchemy import SQLAlchemy
from flask_user import login_required, SQLAlchemyAdapter, UserManager, UserMixin, roles_required
from celery import Celery
from flask.ext.bcrypt import Bcrypt

import datetime
from flask.ext.sqlalchemy import SQLAlchemy


db = SQLAlchemy()
# # Initialize extensions
# bcrypt = Bcrypt(app)

class User(db.Model):
    __tablename__ = 'user'
    id = db.Column(db.Integer, primary_key=True)
    first_name = db.Column(db.String(128))
    last_name = db.Column(db.String(128))
    email = db.Column(db.String(128))
    password_hash = db.Column(db.String(128))
    data = db.Column(db.Text())
    authenticated = db.Column(db.Boolean, default=False)

    # @classmethod
    # def find_by_email(self, email):
    #     unvalidated_response = db.session.query(User).filter_by(email=email).all()
    #     return unvalidated_response[0]

    def is_active(self):
        """True, as all users are active."""
        return True

    def get_id(self):
        """Return the email address to satisfy Flask-Login's requirements."""
        return self.email

    def is_authenticated(self):
        """Return True if the user is authenticated."""
        return self.authenticated

    def is_anonymous(self):
        """False, as anonymous users aren't supported."""
        return False

