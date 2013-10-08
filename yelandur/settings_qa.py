# -*- coding: utf-8 -*-

import os

# Miscellaneous options
SECRET_KEY = os.environ['FLASK_SECRET_KEY_QA']
DEBUG = True
DEBUG_AUTH = False
TESTING = False

# CORS and BrowserID configurations
CORS_CLIENT_DOMAIN = os.environ['FLASK_CORS_CLIENT_DOMAIN_QA']
BROWSERID_CLIENT_DOMAIN = CORS_CLIENT_DOMAIN

# MongoDB options
if 'MONGOLAB_URI_QA' in os.environ:
    uri = os.environ['MONGOLAB_URI_QA'].split('//')[1]
    username_password_host_port, db = uri.split('/')
    username_password, host_port = username_password_host_port.split('@')
    username, password = username_password.split(':')
    host, port_str = host_port.split(':')

    MONGODB_SETTINGS = {'db': db,
                        'host': host,
                        'port': int(port_str),
                        'username': username,
                        'password': password}
else:
    MONGODB_SETTINGS = {'db': 'yelandur_qa'}
