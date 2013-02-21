from flask import current_app, request


def get_client_url():
    # Build the client_url
    client_domain = current_app.config['CORS_CLIENT_DOMAIN']
    end_scheme = request.url_root.find('://') + 3
    client_scheme = request.url_root[:end_scheme]
    return client_scheme + client_domain


def add_cors_headers(response):
    # Create the CORS headers.
    cors_headers = {
        'Access-Control-Allow-Origin': get_client_url(),
        'Access-Control-Allow-Methods': 'HEAD, GET, PUT, POST, OPTIONS',
        'Access-Control-Allow-Credentials': 'true',
        'Access-Control-Max-Age': 21600
    }

    # Add them to the response.
    response.headers.extend(cors_headers)

    return response
