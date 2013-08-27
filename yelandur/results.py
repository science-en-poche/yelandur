# -*- coding: utf-8 -*-

from flask import Blueprint, jsonify, abort, request
from flask.views import MethodView
from flask.ext.login import current_user
from mongoengine.queryset import DoesNotExist

from .cors import cors
from .models import Result
from .helpers import JSONSet


# Create the actual blueprint
results = Blueprint('results', __name__)


class ResultsView(MethodView):

    @cors()
    def get(self):
        if request.args.get('access', None) == 'private':
            if not current_user.is_authenticated():
                abort(401)
            js_results = JSONSet(Result, current_user.results)
            return jsonify({'results': js_results.to_jsonable_private()})

        return jsonify({'results': Result.objects.to_jsonable()})

    #@cors()
    #def post(self):
        #pass

    #@cors()
    #def options(self):
        #pass


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
