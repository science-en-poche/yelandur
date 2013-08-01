# -*- coding: utf-8 -*-

from flask import Blueprint, jsonify, abort, request
from flask.views import MethodView
from flask.ext.login import current_user
from mongoengine import NotUniqueError, ValidationError
from mongoengine.queryset import DoesNotExist

from .cors import cors
from .models import User, Exp


# Create the actual blueprint
exps = Blueprint('exps', __name__)


class OwnerMismatchError(Exception):
    pass


class MissingRequirementError(Exception):
    pass


class RequestMalformedError(Exception):
    pass


class OwnerUserIdNotSetError(Exception):
    pass


class ExpsView(MethodView):

    @cors()
    def get(self):
        return jsonify({'exps': Exp.objects.to_jsonable()})

    @cors()
    def post(self):
        if not current_user.is_authenticated():
            abort(401)

        exp_dict = request.json.get('exp', None)
        if exp_dict is None:
            raise RequestMalformedError

        owner_id = exp_dict.get('owner_id', None)
        if owner_id is None:
            raise MissingRequirementError

        if owner_id != current_user.user_id:
            raise OwnerMismatchError

        u = User.get(user_id=owner_id)
        if not u.user_id_is_set:
            raise OwnerUserIdNotSetError

        name = exp_dict.get('name', None)
        if name is None:
            raise MissingRequirementError

        collaborators = [User.get(user_id=cid) for cid
                         in exp_dict.get('collaborator_ids', [])]

        e = Exp.create(name, u, exp_dict.get('description', ''),
                       collaborators)

        return jsonify({'exp': e.to_jsonable()}), 201

    @cors()
    def options(self):
        pass


exps.add_url_rule('/', view_func=ExpsView.as_view('exps'))


class ExpView(MethodView):

    @cors()
    def get(self, exp_id):
        e = Exp.objects.get(exp_id=exp_id)
        return jsonify({'exp': e.to_jsonable()})

    #@cors()
    #@login_required
    #def put(self, login, name):
        #u = User.objects.get(login=login)
        #e = Exp.objects(owner=u).get(name=name)

        #if current_user == e.owner or current_user in e.collaborators:
            #if name != request.json['name']:
                #abort(400)
            #e.description = request.json['description']
            #e.save()
            #return jsonify(e.to_jsonable_private())
        #else:
            ## User not authorized
            #abort(403)

    #@cors()
    #def options(self, login, name):
        #pass


exps.add_url_rule('/<exp_id>', view_func=ExpView.as_view('exp'))


#@users.route('/<login>/exps/<name>/results/')
#@cors()
#@login_required
#def results(login, name):
    ## No POST method here since results are added by devices only
    #u = User.objects.get(login=login)
    #e = Exp.objects(owner=u).get(name=name)

    #if current_user == e.owner or current_user in e.collaborators:
        #return jsonify(e.to_jsonable_private('results'))
    #else:
        #abort(403)


@exps.errorhandler(ValidationError)
@cors()
def validation_error(error):
    return jsonify(
        {'error': {'status_code': 400,
                   'type': 'BadSyntax',
                   'message': ('A field does not fulfill '
                               'the required syntax')}}), 400


@exps.errorhandler(MissingRequirementError)
@cors()
def missing_requirement(error):
    return jsonify(
        {'error': {'status_code': 400,
                   'type': 'MissingRequirement',
                   'message': 'One of the required fields is missing'}}), 400


@exps.errorhandler(OwnerUserIdNotSetError)
@cors()
def owner_user_id_not_set(error):
    return jsonify(
        {'error': {'status_code': 403,
                   'type': 'OwnerUserIdNotSet',
                   'message': "Owner's user_id is not set"}}), 403


@exps.errorhandler(OwnerMismatchError)
@cors()
def owner_mismatch(error):
    return jsonify(
        {'error': {'status_code': 403,
                   'type': 'OwnerMismatch',
                   'message': ('Authenticated user does not match '
                               'provided owner user_id')}}), 403


@exps.errorhandler(400)
@exps.errorhandler(RequestMalformedError)
@cors()
def malformed(error):
    return jsonify(
        {'error': {'status_code': 400,
                   'type': 'Malformed',
                   'message': 'Request body is malformed'}}), 400


@exps.errorhandler(401)
@cors()
def unauthenticated(error):
    return jsonify(
        {'error': {'status_code': 401,
                   'type': 'Unauthenticated',
                   'message': 'Request requires authentication'}}), 401


@exps.errorhandler(DoesNotExist)
@cors()
def does_not_exist(error):
    return jsonify(
        {'error': {'status_code': 404,
                   'type': 'DoesNotExist',
                   'message': 'Item does not exist'}}), 404
