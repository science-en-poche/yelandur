import os

# Miscellaneous options
SECRET_KEY = os.environ['FLASK_SECRET_KEY']
DEBUG = False
TESTING = False

# CORS and BrowserID configurations
CORS_CLIENT_DOMAIN = 'naja.herokuapp.com'
BROWSERID_CLIENT_DOMAIN = CORS_CLIENT_DOMAIN

# MongoDB options
uri = os.environ['MONGOLAB_URI'].split('//')[1]
username_password_host_port, db = uri.split('/')
username_password, host_port = username_password_host_port.split('@')
username, password = username_password.split(':')
host, port_str = host_port.split(':')

MONGODB_SETTINGS = {'db': db,
                    'host': host,
                    'port': int(port_str),
                    'username': username,
                    'password': password}
