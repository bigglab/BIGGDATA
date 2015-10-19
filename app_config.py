#!/usr/bin/env python

"""
Project-wide application configuration.

DO NOT STORE SECRETS, PASSWORDS, ETC. IN THIS FILE.
They will be exposed to users. Use environment variables instead.
See get_secrets() below for a fast way to access them.
"""

import os
import sys

SQLALCHEMY_DATABASE_URI = "postgresql://localhost/biggig"


# These variables will be set at runtime. See configure_targets() below
S3_BUCKET = 's3://biggig'
DEBUG = True

# """
# OAUTH
# """

# GOOGLE_OAUTH_CREDENTIALS_PATH = '~/.google_oauth_credentials'

# authomatic_config = {
#     'google': {
#         'id': 1,
#         'class_': oauth2.Google,
#         'consumer_key': os.environ.get('GOOGLE_OAUTH_CLIENT_ID'),
#         'consumer_secret': os.environ.get('GOOGLE_OAUTH_CONSUMER_SECRET'),
#         'scope': ['https://www.googleapis.com/auth/drive', 'https://www.googleapis.com/auth/userinfo.email'],
#         'offline': True,
#     },
# authomatic = Authomatic(authomatic_config, os.environ.get('AUTHOMATIC_SALT'))


"""
Utilities
"""
def get_secrets():
    """
    A method for accessing our secrets.
    """
    secrets_dict = {}

    for k,v in os.environ.items():
        if k.startswith(PROJECT_SLUG):
            k = k[len(PROJECT_SLUG) + 1:]
            secrets_dict[k] = v

    return secrets_dict

