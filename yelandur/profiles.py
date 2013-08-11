# -*- coding: utf-8 -*-

from flask import Blueprint, jsonify, abort, request
from flask.views import MethodView
from flask.ext.login import current_user

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


profiles.add_url_rule('/', view_func=ProfilesView.as_view('profiles'))


@profiles.errorhandler(401)
@cors()
def unauthenticated(error):
    return jsonify(
        {'error': {'status_code': 401,
                   'type': 'Unauthenticated',
                   'message': 'Request requires authentication'}}), 401
