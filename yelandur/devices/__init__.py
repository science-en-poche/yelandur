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


class RootView(MethodView):

    def get(self):
        return jsonify(Device.objects.to_jsonable())

    def post(self):
        pubkey_ec = request.json.get('pubkey_ec')

        if not pubkey_ec:
            abort(400)

        device = Device.create(pubkey_ec)
        return jsonify(device.to_jsonable()), 201


devices.add_url_rule('/', view_func=RootView.as_view('root'))


@devices.route('/<device_id>')
def device(device_id):
    # No PUT method here since devices can't change
    d = Device.objects.get(device_id=device_id)
    return jsonify(d.to_jsonable())


@devices.route('/<device_id>/results/')
@login_required
def device_results(device_id):
    # No POST method here since it goes through the /exps/ url
    d = Device.objects.get(device_id=device_id)
    u = User.objects.get(current_user)
    results = Result.objects(device=d)
    results = filter(lambda r: u == r.exp.owner, results)
    return jsonify([r.to_jsonable_private_exp() for r in results])


@devices.route('/<device_id>/exps/')
@login_required
def exps(device_id):
    d = Device.objects.get(device_id=device_id)
    u = User.objects.get(current_user)
    exps = Exp.objects(owner=u)
    exps = filter(lambda e: d in [r.device for r in e.results], exps)
    return jsonify([e.to_jsonable_private() for e in exps])


@devices.route('/<device_id>/exps/<exp_id>')
@login_required
def exp(device_id, exp_id):
    d = Device.objects.get(device_id=device_id)
    e = Exp.objects.get(exp_id=exp_id)

    if current_user == e.owner or current_user in e.collaborators:
        if not d in [r.device for r in e.results]:
            abort(404)
        return jsonify(e.to_jsonable_private())
    else:
        # User not authorized
        abort(403)


class ExpResultsView(MethodView):

    @login_required
    def get(self, device_id, exp_id):
        d = Device.objects.get(device_id=device_id)
        e = Exp.objects.get(exp_id=exp_id)

        if current_user == e.owner or current_user in e.collaborators:
            if not d in [r.device for r in e.results]:
                abort(404)
            return jsonify(e.to_jsonable_private('results'))
        else:
            # User not authorized
            abort(403)

    def post(self, device_id, exp_id):
        print 'request.form: ' + str(request.form)

        d = Device.objects.get(device_id=device_id)
        e = Exp.objects.get(exp_id=exp_id)

        data = request.form.get('data')
        if not data:
            abort(400)

        try:
            header, payload, sig = map(base64url_decode, data.split('.'))
        except TypeError:
            abort(400)
        vk = VerifyingKey.from_pem(d.pubkey_ec)

        if jws.verify(header, payload, sig, vk):
            parsed_data = json.loads(payload)
            r = Result.create(e, d, parsed_data)
            return jsonify(r.to_jsonable()), 201
        else:
            # Bad signature. This should never execute, since jws.verify
            # raises the exception for us
            raise SignatureError('bad signature')


devices.add_url_rule('/<device_id>/exps/<exp_id>/results/',
                     view_func=ExpResultsView.as_view('exp_results'))


@devices.route('/<device_id>/exps/<exp_id>/results/<result_id>')
@login_required
def result(device_id, exp_id, result_id):
    d = Device.objects.get(device_id=device_id)
    e = Exp.objects.get(exp_id=exp_id)
    r = Result.objects.get(result_id=result_id)

    if current_user == e.owner or current_user in e.collaborators:
        if not r.device == d or not r.exp == e:
            abort(404)
        return jsonify(r.to_jsonable_private())
    else:
        # User not authorized
        abort(403)


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
