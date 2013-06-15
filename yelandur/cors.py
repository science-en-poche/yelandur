# -*- coding: utf-8 -*-

from datetime import timedelta
from functools import update_wrapper

from flask import current_app, request, make_response


def get_client_origin():
    # Build the client_origin
    client_domain = current_app.config['CORS_CLIENT_DOMAIN']
    end_scheme = request.url_root.find('://') + 3
    client_scheme = request.url_root[:end_scheme]
    return client_scheme + client_domain


def add_cors_headers(response):
    # Create the CORS headers.
    cors_headers = {
        'Access-Control-Allow-Origin': get_client_origin(),
        'Access-Control-Allow-Methods': 'HEAD, GET, PUT, POST, OPTIONS',
        'Access-Control-Allow-Credentials': 'true',
        'Access-Control-Max-Age': 21600
    }

    # Add them to the response.
    response.headers.extend(cors_headers)

    return response


def cors(origin_getter=get_client_origin, methods=None, headers=None,
         max_age=21600, attach_to_all=True, automatic_options=True):

    if methods is not None:
        methods = ', '.join(sorted(x.upper() for x in methods))
    if headers is not None and not isinstance(headers, basestring):
        headers = ', '.join(x.upper() for x in headers)
    if isinstance(max_age, timedelta):
        max_age = max_age.total_seconds()

    def get_methods():
        if methods is not None:
            return methods

        options_resp = current_app.make_default_options_response()
        return options_resp.headers['allow']

    def decorator(f):

        def wrapped_function(*args, **kwargs):
            if automatic_options and request.method == 'OPTIONS':
                resp = current_app.make_default_options_response()
            else:
                resp = make_response(f(*args, **kwargs))
            if not attach_to_all and request.method != 'OPTIONS':
                return resp

            h = resp.headers

            h['Access-Control-Allow-Origin'] = origin_getter()
            h['Access-Control-Allow-Methods'] = get_methods()
            h['Access-Control-Allow-Credentials'] = 'true'
            h['Access-Control-Max-Age'] = str(max_age)
            if headers is not None:
                h['Access-Control-Allow-Headers'] = headers
            else:
                h['Access-Control-Allow-Headers'] = 'Content-Type'
            return resp

        f.provide_automatic_options = False
        return update_wrapper(wrapped_function, f)

    return decorator
