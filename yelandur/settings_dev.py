# -*- coding: utf-8 -*-

import os

# Miscellaneous options
if 'FLASK_SECRET_KEY_DEV' in os.environ:
    SECRET_KEY = os.environ['FLASK_SECRET_KEY_DEV']
else:
    SECRET_KEY = 'development key'
DEBUG = True
TESTING = False

# CORS and BrowserID configurations
if 'FLASK_CORS_CLIENT_DOMAIN_DEV' in os.environ:
    CORS_CLIENT_DOMAIN = os.environ['FLASK_CORS_CLIENT_DOMAIN_DEV']
else:
    CORS_CLIENT_DOMAIN = 'dev.naja.cc'
BROWSERID_CLIENT_DOMAIN = CORS_CLIENT_DOMAIN

# MongoDB options
MONGODB_SETTINGS = {'db': 'yelandur_dev'}
