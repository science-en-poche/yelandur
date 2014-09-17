# -*- coding: utf-8 -*-

import json
import time

from flask import Blueprint, jsonify, abort, request
from flask.views import MethodView
from flask.ext.login import current_user
from mongoengine.queryset import DoesNotExist

from .cors import cors
from .models import Profile, Result, DataValueError
from .helpers import (dget, jsonb64_load, MalformedSignatureError,
                      BadSignatureError, is_jose_sig_valid, is_jws_sig_valid)


# Maximum delay between signature timestamp and now, in seconds
MAX_AUTH_DELAY = 30


# Create the actual blueprint
results = Blueprint('results', __name__)


class RequestMalformedError(Exception):
    pass


class MissingRequirementError(Exception):
    pass


class TooManySignaturesError(Exception):
    pass


class ProfileError(Exception):

    def __init__(self, presults=None):
        super(ProfileError, self).__init__()
        if presults is not None:
            self.presults = presults


class ProfileNotFoundError(ProfileError):
    pass


class ProfileMismatchError(ProfileError):
    pass


# TODO: test
def validate_data_signature(sdata):
    b64_jpayload = dget(sdata, 'payload', MalformedSignatureError)
    sigs = dget(sdata, 'signatures', MalformedSignatureError)

    # Check the number of signatures
    if not isinstance(sigs, list) or len(sigs) < 1:
        raise MalformedSignatureError
    elif len(sigs) > 1:
        raise TooManySignaturesError

    # Extract the list of posted results
    payload = jsonb64_load(b64_jpayload, MalformedSignatureError)
    if 'result' in payload:
        is_bulk = False
        presults = [payload['result']]
    elif 'results' in payload:
        is_bulk = True
        presults = payload['results']
        if not isinstance(presults, list):
            raise MissingRequirementError
    else:
        raise MissingRequirementError

    # Check all the provided profile_ids are identical
    profile_ids = [dget(pr, 'profile_id', MissingRequirementError)
                   for pr in presults]
    if profile_ids.count(profile_ids[0]) != len(profile_ids):
        raise ProfileMismatchError(presults)

    try:
        profile = Profile.objects.get(profile_id=profile_ids[0])
        profile_vk_pem = profile.vk_pem
    except DoesNotExist:
        raise ProfileNotFoundError(presults)

    return (presults, is_bulk, profile,
            is_jose_sig_valid(b64_jpayload, sigs[0], profile_vk_pem))


# TODO: test
def validate_auth_token(auth_token):
    parts = auth_token.split('.')
    if len(parts) != 3:
        raise MalformedSignatureError

    # Extract parts to check token is well formed
    jheader_b64, jbody_b64, sig_der_b64 = parts
    header = jsonb64_load(jheader_b64, MalformedSignatureError)
    body = jsonb64_load(jbody_b64, MalformedSignatureError)

    if not isinstance(header, dict) or not isinstance(body, dict):
        raise MalformedSignatureError

    if 'id' not in body or 'timestamp' not in body:
        raise MalformedSignatureError

    if abs(body['timestamp'] - time.time()) > MAX_AUTH_DELAY:
        raise MalformedSignatureError

    try:
        profile = Profile.objects.get(profile_id=body['id'])
        profile_vkpem = profile.vk_pem
    except DoesNotExist:
        raise ProfileNotFoundError(body)

    return (profile, is_jws_sig_valid(auth_token, profile_vkpem))


class ResultsView(MethodView):

    @cors()
    def get(self):
        # Private access
        if request.args.get('access', None) == 'private':
            authed = None

            # Differentiate user and profile auth. User has priority (set last)
            auth_token = request.args.get('auth_token', None)
            if auth_token is not None:
                profile, valid_profile_sig = validate_auth_token(auth_token)
            if valid_profile_sig:
                authed = profile
            if current_user.is_authenticated():
                authed = current_user

            if authed is None:
                abort(401)

            if 'ids[]' in request.args:
                ids = request.args.getlist('ids[]')
                rresults = Result.objects(result_id__in=ids)
                for r in rresults:
                    if r.result_id not in authed.result_ids:
                        abort(403)
            else:
                rresults = Result.objects(
                    result_id__in=authed.result_ids)

            filtered_query = Result.objects.translate_to_jsonable_private(
                request.args)
            rresults = rresults(**filtered_query)

            return jsonify({'results': rresults.to_jsonable_private()})

        # Public access
        if 'ids[]' in request.args:
            ids = request.args.getlist('ids[]')
            rresults = Result.objects(result_id__in=ids)
        else:
            rresults = Result.objects()

        filtered_query = Result.objects.translate_to_jsonable(request.args)
        rresults = rresults(**filtered_query)

        return jsonify({'results': rresults.to_jsonable()})

    @cors()
    def post(self):
        try:
            rdata = json.loads(request.data)
        except ValueError:
            raise RequestMalformedError

        try:
            presults, is_bulk, profile, sig_valid = validate_data_signature(
                rdata)
            profile_error = None
        except ProfileError, e:
            # For the sake of error priorities, we delay the sig_valid check
            # and keep the ProfileNotFound to see if there aren't other
            # higher-priority errors (using the extracted payload from the
            # signature). We try, and if nothing is raised before we raise the
            # BadSignatureError or the ProfileNotFound.
            presults = e.presults
            profile_error = e

        # Check we have all the data we want
        data_dicts = []
        for presult in presults:
            data_dicts.append(dget(presult, 'result_data',
                                   MissingRequirementError))

        # Now raise exceptions if necessary
        if profile_error is not None:
            raise profile_error
        if not sig_valid:
            raise BadSignatureError

        result_ids = []
        for (presult, data_dict) in zip(presults, data_dicts):
            r = Result.create(profile, data_dict)
            result_ids.append(r.result_id)

        results = Result.objects(result_id__in=result_ids)
        if is_bulk:
            return jsonify({'results': results.to_jsonable_private()}), 201
        else:
            return jsonify({'result': results[0].to_jsonable_private()}), 201

    @cors()
    def options(self):
        pass


results.add_url_rule('', view_func=ResultsView.as_view('results'))


class ResultView(MethodView):

    @cors()
    def get(self, result_id):
        r = Result.objects.get(result_id=result_id)

        if request.args.get('access', None) == 'private':
            if not current_user.is_authenticated():
                abort(401)

            if r.result_id in current_user.result_ids:
                return jsonify({'result': r.to_jsonable_private()})
            else:
                abort(403)
        else:
            return jsonify({'result': r.to_jsonable()})


results.add_url_rule('/<result_id>',
                     view_func=ResultView.as_view('result'))


@results.errorhandler(DoesNotExist)
@cors()
def does_not_exist(error):
    return jsonify(
        {'error': {'status_code': 404,
                   'type': 'DoesNotExist',
                   'message': 'Item does not exist'}}), 404


@results.errorhandler(400)
@results.errorhandler(RequestMalformedError)
@results.errorhandler(DataValueError)
@cors()
def malformed(error):
    return jsonify(
        {'error': {'status_code': 400,
                   'type': 'Malformed',
                   'message': 'Request body is malformed'}}), 400


@results.errorhandler(ProfileMismatchError)
@cors()
def profile_mismatch(error):
    return jsonify(
        {'error': {'status_code': 400,
                   'type': 'ProfileMismatch',
                   'message': ('The provided profiles '
                               'differ from one another')}}), 400


@results.errorhandler(MissingRequirementError)
@cors()
def missing_requirement(error):
    return jsonify(
        {'error': {'status_code': 400,
                   'type': 'MissingRequirement',
                   'message': 'One of the required fields is missing'}}), 400


@results.errorhandler(MalformedSignatureError)
@cors()
def malformed_signature(error):
    return jsonify(
        {'error': {'status_code': 400,
                   'type': 'Malformed',
                   'message': 'Request body is malformed'}}), 400


@results.errorhandler(TooManySignaturesError)
@cors()
def too_many_signatures(error):
    return jsonify(
        {'error': {'status_code': 400,
                   'type': 'TooManySignatures',
                   'message': 'Too many signatures provided'}}), 400


@results.errorhandler(ProfileNotFoundError)
@cors()
def profile_does_not_exist(error):
    return jsonify(
        {'error': {'status_code': 400,
                   'type': 'ProfileNotFound',
                   'message': 'The requested profile was not found'}}), 400


@results.errorhandler(BadSignatureError)
@cors()
def bad_signature(error):
    return jsonify(
        {'error': {'status_code': 403,
                   'type': 'BadSignature',
                   'message': 'The signature is invalid'}}), 403


@results.errorhandler(401)
@cors()
def unauthenticated(error):
    return jsonify(
        {'error': {'status_code': 401,
                   'type': 'Unauthenticated',
                   'message': 'Request requires authentication'}}), 401


@results.errorhandler(403)
@cors()
def unauthorized(error):
    return jsonify(
        {'error': {'status_code': 403,
                   'type': 'Unauthorized',
                   'message': ('You do not have access '
                               'to this resource')}}), 403
