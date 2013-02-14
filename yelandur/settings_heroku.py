import os

# Miscellaneous options
SECRET_KEY = 'UVzIcJsapHkxzH3Ag7zS0kRwmN84zNav9Tw7lFzjWuC4AnxdKFNa2nryNfiWjGT4'
DEBUG = False
TESTING = False
# No HOST option here, we're using a dedicated WSGI server

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
