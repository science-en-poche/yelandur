# -*- coding: utf-8 -*-

import json

from flask import Blueprint, jsonify, abort, request
from flask.views import MethodView
from flask.ext.login import current_user
from mongoengine import NotUniqueError
from mongoengine.queryset import DoesNotExist

from .cors import cors
from .models import Exp, Device, Profile, DeviceSetError, DataValueError
from .helpers import (dget, jsonb64_load, MalformedSignatureError,
                      BadSignatureError, is_sig_valid)


# Create the actual blueprint
profiles = Blueprint('profiles', __name__)


class MissingRequirementError(Exception):
    pass


class TooManySignaturesError(Exception):
    pass


class RequestMalformedError(Exception):
    pass


class DeviceNotFoundError(Exception):

    def __init__(self, pprofile=None):
        super(DeviceNotFoundError, self).__init__()
        if pprofile is not None:
            self.pprofile = pprofile


class ExperimentNotFoundError(Exception):
    pass


# TODO: test
def validate_data_signature(sdata, profile=None):
    b64_jpayload = dget(sdata, 'payload', MalformedSignatureError)
    sigs = dget(sdata, 'signatures', MalformedSignatureError)

    if not isinstance(sigs, list) or len(sigs) < 1:
        raise MalformedSignatureError
    elif len(sigs) > 2:
        raise TooManySignaturesError

    payload = jsonb64_load(b64_jpayload, MalformedSignatureError)
    pprofile = dget(payload, 'profile', MissingRequirementError)

    if profile is None:
        # If we have no provided profile, the data comes from a POST
        profile_vk_pem = dget(pprofile, 'vk_pem', MissingRequirementError)
    else:
        # If we have a profile, the data comes from a PUT
        profile_vk_pem = profile.vk_pem

    if len(sigs) == 1:
        # Only one signature, it's necessarily from the profile
        return (pprofile, (profile,),
                is_sig_valid(b64_jpayload, sigs[0], profile_vk_pem))

    else:
        # Two signatures, there should be one from the profile and one from the
        # device
        device_id = dget(pprofile, 'device_id', MissingRequirementError)
        try:
            device = Device.objects.get(device_id=device_id)
            device_vk_pem = device.vk_pem
        except DoesNotExist:
            raise DeviceNotFoundError(pprofile)

        # Make sure we have exactly one and only one valid signature per model
        # type (device, profile)
        profile_sig_valid = False
        device_sig_valid = False
        for sig in sigs:
            if is_sig_valid(b64_jpayload, sig, profile_vk_pem):
                profile_sig_valid = True
            elif is_sig_valid(b64_jpayload, sig, device_vk_pem):
                device_sig_valid = True

        return (pprofile, (profile, device),
                profile_sig_valid and device_sig_valid)


class ProfilesView(MethodView):

    @cors()
    def get(self):
        # Private access
        if request.args.get('access', None) == 'private':
            if not current_user.is_authenticated():
                abort(401)

            if 'ids[]' in request.args:
                ids = request.args.getlist('ids[]')
                rprofiles = Profile.objects(profile_id__in=ids)
                for p in rprofiles:
                    if p.profile_id not in current_user.profile_ids:
                        abort(403)
            else:
                rprofiles = Profile.objects(
                    profile_id__in=current_user.profile_ids)

            filtered_query = Profile.objects.translate_to_jsonable_private(
                request.args)
            rprofiles = rprofiles(**filtered_query)

            return jsonify({'profiles': rprofiles.to_jsonable_private()})

        # Public access
        if 'ids[]' in request.args:
            ids = request.args.getlist('ids[]')
            rprofiles = Profile.objects(profile_id__in=ids)
        else:
            rprofiles = Profile.objects()

        filtered_query = Profile.objects.translate_to_jsonable(request.args)
        rprofiles = rprofiles(**filtered_query)

        return jsonify({'profiles': rprofiles.to_jsonable()})

    @cors()
    def post(self):
        try:
            rdata = json.loads(request.data)
        except ValueError:
            raise RequestMalformedError
        try:
            pprofile, valid_models, sig_valid = validate_data_signature(rdata)
            device_not_found = False
        except DeviceNotFoundError, e:
            # For the sake of error priorities, we delay the sig_valid check
            # and keep the DeviceNotFound to see if there aren't other
            # higher-priority errors (using the extracted payload from the
            # signature). We try, and if nothing is raised before we raise the
            # BadSignatureError or the DeviceNotFound.
            pprofile = e.pprofile
            device_not_found = True

        exp_id = dget(pprofile, 'exp_id', MissingRequirementError)

        # Now raise exceptions if necessary
        if device_not_found:
            raise DeviceNotFoundError
        if not sig_valid:
            raise BadSignatureError

        # Finish extracting the data
        data_dict = pprofile.get('profile_data', {})
        if not isinstance(data_dict, dict):
            raise DataValueError
        try:
            exp = Exp.objects.get(exp_id=exp_id)
        except DoesNotExist:
            raise ExperimentNotFoundError

        device = valid_models[1] if len(valid_models) == 2 else None
        vk_pem = dget(pprofile, 'vk_pem', MissingRequirementError)
        p = Profile.create(vk_pem, exp, data_dict, device)

        return jsonify({'profile': p.to_jsonable_private()}), 201

    @cors()
    def options(self):
        pass


profiles.add_url_rule('', view_func=ProfilesView.as_view('profiles'))


class ProfileView(MethodView):

    @cors()
    def get(self, profile_id):
        p = Profile.objects.get(profile_id=profile_id)

        if request.args.get('access', None) == 'private':
            if not current_user.is_authenticated():
                abort(401)

            if p.profile_id in current_user.profile_ids:
                return jsonify({'profile': p.to_jsonable_private()})
            else:
                abort(403)
        else:
            return jsonify({'profile': p.to_jsonable()})

    @cors()
    def put(self, profile_id):
        p = Profile.objects.get(profile_id=profile_id)

        try:
            rdata = json.loads(request.data)
        except ValueError:
            raise RequestMalformedError

        pprofile, valid_models, sig_valid = validate_data_signature(rdata, p)
        if not sig_valid:
            raise BadSignatureError

        # Set the data if asked to
        data_dict = pprofile.get('profile_data')
        if data_dict is not None:
            p.set_data(data_dict)

        # Set the device if asked to
        if len(valid_models) == 2:
            p.set_device(valid_models[1])

        return jsonify({'profile': p.to_jsonable_private()})

    @cors()
    def options(self):
        pass


profiles.add_url_rule('/<profile_id>',
                      view_func=ProfileView.as_view('profile'))


@profiles.errorhandler(DoesNotExist)
@cors()
def does_not_exist(error):
    return jsonify(
        {'error': {'status_code': 404,
                   'type': 'DoesNotExist',
                   'message': 'Item does not exist'}}), 404


@profiles.errorhandler(MalformedSignatureError)
@cors()
def malformed_signature(error):
    return jsonify(
        {'error': {'status_code': 400,
                   'type': 'Malformed',
                   'message': 'Request body is malformed'}}), 400


@profiles.errorhandler(TooManySignaturesError)
@cors()
def too_many_signatures(error):
    return jsonify(
        {'error': {'status_code': 400,
                   'type': 'TooManySignatures',
                   'message': 'Too many signatures provided'}}), 400


@profiles.errorhandler(DeviceNotFoundError)
@cors()
def device_does_not_exist(error):
    return jsonify(
        {'error': {'status_code': 400,
                   'type': 'DeviceNotFound',
                   'message': 'The requested device was not found'}}), 400


@profiles.errorhandler(ExperimentNotFoundError)
@cors()
def experiment_does_not_exist(error):
    return jsonify(
        {'error': {'status_code': 400,
                   'type': 'ExperimentNotFound',
                   'message': 'The requested experiment was not found'}}), 400


@profiles.errorhandler(BadSignatureError)
@cors()
def bad_signature(error):
    return jsonify(
        {'error': {'status_code': 403,
                   'type': 'BadSignature',
                   'message': 'The signature is invalid'}}), 403


@profiles.errorhandler(NotUniqueError)
@cors()
def not_unique_error(error):
    return jsonify(
        {'error': {'status_code': 409,
                   'type': 'FieldConflict',
                   'message': 'The value is already taken'}}), 409


@profiles.errorhandler(400)
@profiles.errorhandler(RequestMalformedError)
@profiles.errorhandler(DataValueError)
@cors()
def malformed(error):
    return jsonify(
        {'error': {'status_code': 400,
                   'type': 'Malformed',
                   'message': 'Request body is malformed'}}), 400


@profiles.errorhandler(MissingRequirementError)
@cors()
def missing_requirement(error):
    return jsonify(
        {'error': {'status_code': 400,
                   'type': 'MissingRequirement',
                   'message': 'One of the required fields is missing'}}), 400


@profiles.errorhandler(DeviceSetError)
@cors()
def device_already_set(error):
    return jsonify(
        {'error': {'status_code': 403,
                   'type': 'DeviceAlreadySet',
                   'message': 'Device is already set'}}), 403


@profiles.errorhandler(401)
@cors()
def unauthenticated(error):
    return jsonify(
        {'error': {'status_code': 401,
                   'type': 'Unauthenticated',
                   'message': 'Request requires authentication'}}), 401


@profiles.errorhandler(403)
@cors()
def unauthorized(error):
    return jsonify(
        {'error': {'status_code': 403,
                   'type': 'Unauthorized',
                   'message': ('You do not have access '
                               'to this resource')}}), 403
