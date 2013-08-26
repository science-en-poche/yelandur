# -*- coding: utf-8 -*-

import json

from flask import Blueprint, jsonify, abort, request
from flask.views import MethodView
from flask.ext.login import current_user
from mongoengine.queryset import DoesNotExist
from jws.utils import base64url_decode, base64url_encode
import jws
from ecdsa import VerifyingKey

from .cors import cors
from .models import Exp, Device, Profile
from .helpers import JSONSet, sig_der_to_string


# Create the actual blueprint
profiles = Blueprint('profiles', __name__)


class MalformedSignatureError(Exception):
    pass


class BadSignatureError(Exception):
    pass


class MissingRequirementError(Exception):
    pass


class TooManySignaturesError(Exception):
    pass


class RequestMalformedError(Exception):
    pass


class DeviceNotFoundError(Exception):

    def __init__(self, pdata=None):
        super(DeviceNotFoundError, self).__init__()
        if pdata is not None:
            self.pdata = pdata


# TODO: test
def dget(d, k, e):
    try:
        return d[k]
    except KeyError:
        raise e


# TODO: test
def b64url_dec(b64url, e=None):
    try:
        # Adding `str` wrapper here avoids a TypeError
        return base64url_decode(str(b64url))
    except TypeError, msg:
        if e is None:
            raise TypeError(msg)
        else:
            raise e


# TODO: test
def jsonb64_load(j64, e=None):
    j = b64url_dec(j64, e)
    try:
        return json.loads(j)
    except ValueError, msg:
        if e is None:
            raise ValueError(msg)
        else:
            raise e


# TODO: test
def is_sig_valid(b64_jpayload, jose_sig, vk_pem):
    jpayload = b64url_dec(b64_jpayload, MalformedSignatureError)

    b64_jheader = dget(jose_sig, 'protected', MalformedSignatureError)
    jheader = b64url_dec(b64_jheader, MalformedSignatureError)

    b64_sig = dget(jose_sig, 'signature', MalformedSignatureError)
    sig_der = b64url_dec(b64_sig, MalformedSignatureError)

    vk = VerifyingKey.from_pem(vk_pem)
    vk_order = vk.curve.order
    b64_sig_string = base64url_encode(sig_der_to_string(sig_der, vk_order))

    try:
        jws.verify(jheader, jpayload, b64_sig_string, vk, is_json=True)
        return True
    except jws.SignatureError:
        return False


# TODO: test
# FIXME: what happens if a profile and a device have the same public key, or if
# a signature is valid for both the profile and the device?
def validate_data_signature(sdata, profile_id=None):
    b64_jpayload = dget(sdata, 'payload', MalformedSignatureError)
    sigs = dget(sdata, 'signatures', MalformedSignatureError)

    if not isinstance(sigs, list) or len(sigs) < 1:
        raise MalformedSignatureError
    elif len(sigs) > 2:
        raise TooManySignaturesError

    payload = jsonb64_load(b64_jpayload, MalformedSignatureError)
    profile = dget(payload, 'profile', MissingRequirementError)

    if profile_id is None:
        # If we have no profile_id, the data comes from a POST
        profile_vk_pem = dget(profile, 'vk_pem', MissingRequirementError)
    else:
        # If we have a profile_id, the data comes from a PUT
        profile_vk_pem = Profile.objects.get(profile_id=profile_id).vk_pem

    if len(sigs) == 1:
        # Only one signature, it's necessarily from the profile
        return payload, 1, is_sig_valid(b64_jpayload, sigs[0], profile_vk_pem)

    else:
        # Two signatures, there should be one from the profile and one from the
        # device
        device_id = dget(profile, 'device_id', MissingRequirementError)
        try:
            device_vk_pem = Device.objects.get(device_id=device_id).vk_pem
        except DoesNotExist:
            raise DeviceNotFoundError(payload)

        # Make sure we have exactly one and only one valid signature per model
        # type (device, profile)
        profile_sig_valid = False
        device_sig_valid = False
        for sig in sigs:
            if is_sig_valid(b64_jpayload, sig, profile_vk_pem):
                profile_sig_valid = True
            elif is_sig_valid(b64_jpayload, sig, device_vk_pem):
                device_sig_valid = True

        return payload, 2, profile_sig_valid and device_sig_valid


class ProfilesView(MethodView):

    @cors()
    def get(self):
        if request.args.get('access', None) == 'private':
            if not current_user.is_authenticated():
                abort(401)
            js_profiles = JSONSet(Profile, current_user.profiles)
            return jsonify({'profiles': js_profiles.to_jsonable_private()})

        return jsonify({'profiles': Profile.objects.to_jsonable()})

    @cors()
    def post(self):
        try:
            rdata = json.loads(request.data)
        except ValueError:
            raise RequestMalformedError
        try:
            pdata, n_sigs, sig_valid = validate_data_signature(rdata)
            device_not_found = False
        except DeviceNotFoundError, e:
            # For the sake of error priorities, we delay the sig_valid check
            # and keep the DeviceNotFound to see if there aren't other
            # higher-priority errors (using the extracted payload from the
            # signature). We try, and if nothing is raised before we raise the
            # BadSignatureError or the DeviceNotFound.
            pdata = e.pdata
            device_not_found = True

        pprofile = dget(pdata, 'profile', MissingRequirementError)
        vk_pem = dget(pprofile, 'vk_pem', MissingRequirementError)
        exp_id = dget(pprofile, 'exp_id', MissingRequirementError)

        # Now raise exceptions if necessary
        if device_not_found:
            raise DeviceNotFoundError
        if not sig_valid:
            raise BadSignatureError

        # Finish extracting the data
        exp = Exp.objects.get(exp_id=exp_id)
        data_dict = pprofile.get('data', {})
        if n_sigs == 2:
            device_id = dget(pprofile, 'device_id', MissingRequirementError)
            device = Device.objects.get(device_id=device_id)
        else:
            device = None

        p = Profile.create(vk_pem, exp, data_dict, device)

        return jsonify({'profile': p.to_jsonable_private()}), 201

    @cors()
    def options(self):
        pass


profiles.add_url_rule('/', view_func=ProfilesView.as_view('profiles'))


class ProfileView(MethodView):

    @cors()
    def get(self, profile_id):
        p = Profile.objects.get(profile_id=profile_id)

        if request.args.get('access', None) == 'private':
            if not current_user.is_authenticated():
                abort(401)

            if p in current_user.profiles:
                return jsonify({'profile': p.to_jsonable_private()})
            else:
                abort(403)
        else:
            return jsonify({'profile': p.to_jsonable()})

    #@cors()
    #def post(self):

    #@cors()
    #def options(self):
        #pass


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


@profiles.errorhandler(400)
@profiles.errorhandler(RequestMalformedError)
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
