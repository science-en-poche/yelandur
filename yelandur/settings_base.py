# -*- coding: utf-8 -*-

import os

# API URL
API_VERSION_URL = '/v1'

# Upload options
MAX_CONTENT_LENGTH = 16 * 1024 * 1024

# IP to listen on if standalone server
HOST = '0.0.0.0'

# Logging is always active. If there is no LOG_FILE in the environment,
# logs are directed to stdout.
if 'LOG_FILE' in os.environ:
    LOG_FILE = os.environ['LOG_FILE']
# Default LOG_LEVEL is logging.INFO
