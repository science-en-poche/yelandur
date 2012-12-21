import json

from flask import Blueprint, request, abort
from flask.views import MethodView
from flask.ext.login import login_required, current_user
from mongoengine import NotUniqueError
from mongoengine.queryset import DoesNotExist
import jws
from jws.utils import base64url_decode
from jws.exceptions import SignatureError
from ecdsa import VerifyingKey

from yelandur.helpers import jsonify
from yelandur.models import User, Exp, Device, Result


devices = Blueprint('devices', __name__)


def user_has_device(u, d):
    results = Result.objects(device=d)
    return bool(sum([r.exp.owner == u for r in results]))


def user_devices(u):
    devices = Device.objects()
    return filter(lambda d: user_has_device(u, d), devices)


def user_device_results(u, d):
    results = Result.objects(device=d)
    return filter(lambda r: r.exp.owner == u, results)


def user_device_exps(u, d):
    exps = Exp.objects(owner=u)
    return filter(lambda e: e.has_device(d), exps)


class RootView(MethodView):

    @login_required
    def get(self):
        u = User.objects.get(current_user)
        devices = user_devices(u)
        return jsonify([d.to_jsonable_private() for d in devices])

    def post(self):
        vk_pem = request.json.get('vk_pem')

        if not vk_pem:
            abort(400)

        device = Device.create(vk_pem)
        return jsonify(device.to_jsonable()), 201


devices.add_url_rule('/', view_func=RootView.as_view('root'))


@devices.route('/<device_id>')
@login_required
def device(device_id):
    # No PUT method here since devices can't change
    d = Device.objects.get(device_id=device_id)
    u = User.objects.get(current_user)

    if user_has_device(u, d):
        return jsonify(d.to_jsonable_private())
    else:
        # User doesn't have that device
        abort(404)


@devices.route('/<device_id>/results/')
@login_required
def device_results(device_id):
    # No POST method here since it goes through the /exps/ url
    d = Device.objects.get(device_id=device_id)
    u = User.objects.get(current_user)

    if user_has_device(u, d):
        results = user_device_results(u, d)
        return jsonify([r.to_jsonable_private_exp() for r in results])
    else:
        # User doesn't have that device
        abort(404)


@devices.route('/<device_id>/exps/')
@login_required
def exps(device_id):
    d = Device.objects.get(device_id=device_id)
    u = User.objects.get(current_user)

    if user_has_device(u, d):
        exps = user_device_exps(u, d)
        return jsonify([e.to_jsonable_private() for e in exps])
    else:
        # User doesn't have that device
        abort(404)


@devices.route('/<device_id>/exps/<exp_id>')
@login_required
def exp(device_id, exp_id):
    d = Device.objects.get(device_id=device_id)
    u = User.objects.get(current_user)

    if user_has_device(u, d):
        e = Exp.objects.get(exp_id=exp_id)
        if current_user == e.owner or current_user in e.collaborators:
            if not e.has_device(d):
                # Exp doesn't have that device
                abort(404)
            return jsonify(e.to_jsonable_private())
        else:
            # User doesn't have that exp
            abort(404)
    else:
        # User doesn't have that device
        abort(404)


class ExpResultsView(MethodView):

    @login_required
    def get(self, device_id, exp_id):
        d = Device.objects.get(device_id=device_id)
        u = User.objects.get(current_user)

        if user_has_device(u, d):
            e = Exp.objects.get(exp_id=exp_id)
            if current_user == e.owner or current_user in e.collaborators:
                if not e.has_device(d):
                    # Exp doesn't have that device
                    abort(404)
                return jsonify(e.to_jsonable_private('results'))
            else:
                # User doesn't have that exp
                abort(404)
        else:
            # User doesn't have that device
            abort(404)

    def post(self, device_id, exp_id):
        print 'request.form: ' + str(request.form)

        d = Device.objects.get(device_id=device_id)
        e = Exp.objects.get(exp_id=exp_id)

        jws_data = request.form.get('jws_data')
        if not jws_data:
            abort(400)

        try:
            header_b64, payload_b64, sig = map(str, jws_data.split('.'))
            header, payload = map(base64url_decode, [header_b64, payload_b64])
        except TypeError:
            abort(400)

        vk = VerifyingKey.from_pem(d.vk_pem)

        print 'verifying sig'
        if jws.verify(header, payload, sig, vk, is_json=True):
            print 'sig ok'
            parsed_data = json.loads(payload)
            print 'parsed data: ' + str(parsed_data)
            r = Result.create(e, d, parsed_data)
            print 'result: ' + str(r.to_jsonable_private())
            return jsonify(r.to_jsonable()), 201
        else:
            # Bad signature. This should never execute, since jws.verify
            # raises the exception for us
            print 'bad signature'
            raise SignatureError('bad signature')


devices.add_url_rule('/<device_id>/exps/<exp_id>/results/',
                     view_func=ExpResultsView.as_view('exp_results'))


@devices.route('/<device_id>/exps/<exp_id>/results/<result_id>')
@login_required
def result(device_id, exp_id, result_id):
    d = Device.objects.get(device_id=device_id)
    u = User.objects.get(current_user)

    if user_has_device(u, d):
        e = Exp.objects.get(exp_id=exp_id)
        if current_user == e.owner or current_user in e.collaborators:
            r = Result.objects.get(result_id=result_id)
            if not r.device == d or not r.exp == e:
                # Exp doesn't have that result or device doesn't have that
                # result. This is implied by "exp doesn't have that device".
                abort(404)
            return jsonify(r.to_jsonable_private())
        else:
            # User doesn't have that exp
            abort(404)
    else:
        # User doesn't have that device
        abort(404)


@devices.errorhandler(SignatureError)
def signature_error(error):
    return (jsonify(status='error', type='SignatureError',
                    message=error.message), 403)


@devices.errorhandler(NotUniqueError)
def not_unique_error(error):
    return (jsonify(status='error', type='NotUniqueError',
                    message=error.message), 403)


@devices.errorhandler(DoesNotExist)
def does_not_exist(error):
    abort(404)
