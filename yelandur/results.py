# -*- coding: utf-8 -*-

import json

from flask import Blueprint, jsonify, abort, request
from flask.views import MethodView
from flask.ext.login import current_user
from mongoengine.queryset import DoesNotExist

from .cors import cors
from .models import Profile, Result, DataValueError
from .helpers import (JSONSet, dget, jsonb64_load, MalformedSignatureError,
                      BadSignatureError, is_sig_valid)


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
            is_sig_valid(b64_jpayload, sigs[0], profile_vk_pem))


class ResultsView(MethodView):

    @cors()
    def get(self):
        if request.args.get('access', None) == 'private':
            if not current_user.is_authenticated():
                abort(401)
            js_results = JSONSet(Result, current_user.results)
            return jsonify({'results': js_results.to_jsonable_private()})

        return jsonify({'results': Result.objects.to_jsonable()})

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
            data_dicts.append(dget(presult, 'data', MissingRequirementError))

        # Now raise exceptions if necessary
        if profile_error is not None:
            raise profile_error
        if not sig_valid:
            raise BadSignatureError

        results = []
        for (presult, data_dict) in zip(presults, data_dicts):
            results.append(Result.create(profile, data_dict))

        if is_bulk:
            js_results = JSONSet(Result, results)
            return jsonify({'results': js_results.to_jsonable_private()}), 201
        else:
            return jsonify({'result': results[0].to_jsonable_private()}), 201

    @cors()
    def options(self):
        pass


results.add_url_rule('/', view_func=ResultsView.as_view('results'))


class ResultView(MethodView):

    @cors()
    def get(self, result_id):
        r = Result.objects.get(result_id=result_id)

        if request.args.get('access', None) == 'private':
            if not current_user.is_authenticated():
                abort(401)

            if r in current_user.results:
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
