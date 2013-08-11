# -*- coding: utf-8 -*-

from flask import Blueprint, jsonify, abort, request
from flask.views import MethodView
from flask.ext.login import current_user
from mongoengine.queryset import DoesNotExist

from .cors import cors
from .models import Profile
from .helpers import JSONSet


# Create the actual blueprint
profiles = Blueprint('profiles', __name__)


class ProfilesView(MethodView):

    @cors()
    def get(self):
        if request.args.get('access', None) == 'private':
            if not current_user.is_authenticated():
                abort(401)
            js_profiles = JSONSet(Profile, current_user.profiles)
            return jsonify({'profiles': js_profiles.to_jsonable_private()})

        return jsonify({'profiles': Profile.objects.to_jsonable()})

    #@cors()
    #def post(self):

    #@cors()
    #def options(self):
        #pass


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


profiles.add_url_rule('/<profile_id>',
                      view_func=ProfileView.as_view('profile'))


@profiles.errorhandler(DoesNotExist)
@cors()
def does_not_exist(error):
    return jsonify(
        {'error': {'status_code': 404,
                   'type': 'DoesNotExist',
                   'message': 'Item does not exist'}}), 404


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
