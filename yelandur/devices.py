# -*- coding: utf-8 -*-

from flask import Blueprint, jsonify, request
from flask.views import MethodView
from mongoengine import NotUniqueError
from mongoengine.queryset import DoesNotExist

from .cors import cors
from .models import Device


devices = Blueprint('devices', __name__)


class RequestMalformedError(Exception):
    pass


class DevicesView(MethodView):

    @cors()
    def get(self):
        ids = request.args.getlist('ids[]')
        if len(ids) != 0:
            rdevices = Device.objects(device_id__in=ids)
        else:
            rdevices = Device.objects()

        filtered_query = Device.objects.translate_to_jsonable(request.args)
        rdevices = rdevices(**filtered_query)

        return jsonify({'devices': rdevices.to_jsonable()})

    @cors()
    def post(self):
        device_dict = request.json.get('device', None)
        if device_dict is None:
            raise RequestMalformedError

        vk_pem = device_dict.get('vk_pem', None)
        if vk_pem is None:
            raise RequestMalformedError

        d = Device.create(vk_pem)
        return jsonify({'device': d.to_jsonable()}), 201

    @cors()
    def options(self):
        pass


devices.add_url_rule('', view_func=DevicesView.as_view('devices'))


class DeviceView(MethodView):

    @cors()
    def get(self, device_id):
        d = Device.objects.get(device_id=device_id)
        return jsonify({'device': d.to_jsonable()})

    @cors()
    def options(self):
        pass


devices.add_url_rule('/<device_id>',
                     view_func=DeviceView.as_view('device'))


@devices.errorhandler(400)
@devices.errorhandler(RequestMalformedError)
@cors()
def malformed(error):
    return jsonify(
        {'error': {'status_code': 400,
                   'type': 'Malformed',
                   'message': 'Request body is malformed'}}), 400


@devices.errorhandler(NotUniqueError)
@cors()
def not_unique_error(error):
    return jsonify(
        {'error': {'status_code': 409,
                   'type': 'FieldConflict',
                   'message': 'The value is already taken'}}), 409


@devices.errorhandler(DoesNotExist)
@cors()
def does_not_exist(error):
    return jsonify(
        {'error': {'status_code': 404,
                   'type': 'DoesNotExist',
                   'message': 'Item does not exist'}}), 404
