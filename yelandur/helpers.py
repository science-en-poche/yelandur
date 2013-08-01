# -*- coding: utf-8 -*-

import re
from collections import MutableSet
from datetime import datetime
from hashlib import md5, sha256
import random
import time
import json
from contextlib import contextmanager
import unittest

from flask import Flask, current_app
from mongoengine.queryset import QuerySet
from ecdsa.util import sigdecode_der, sigencode_string


hexregex = r'^[0-9a-f]*$'
iso8601 = r'%Y-%m-%dT%H:%M:%S.%f'


def md5hex(s):
    return md5(s).hexdigest()


def sha256hex(s):
    return sha256(s).hexdigest()


def random_md5hex():
    random.seed(time.time())
    return md5hex(str(random.random()))


def random_sha256hex():
    random.seed(time.time())
    return sha256hex(str(random.random()))


def sig_der_to_string(sig, order):
    r, s = sigdecode_der(sig, order)
    return sigencode_string(r, s, order)


def build_gravatar_id(email):
    return md5hex(email)


def wipe_test_database(*collections):
    if not current_app.config['TESTING']:
        raise ValueError('TESTING mode not activated for the app.'
                         " I won't risk wiping a production database.")

    if not current_app.config['MONGODB_SETTINGS']['db'][-5:] == '_test':
        raise ValueError("MONGODB_SETTINGS['db'] does not end with '_test'."
                         " I won't risk wiping a production database.")

    from .models import User, Exp, Device, Profile, Result
    User.drop_collection()
    User.ensure_indexes()
    Exp.drop_collection()
    Exp.ensure_indexes()
    Device.drop_collection()
    Device.ensure_indexes()
    Profile.drop_collection()
    Profile.ensure_indexes()
    Result.drop_collection()
    Result.ensure_indexes()

    for collection in collections:
        collection.drop_collection()
        collection.ensure_indexes()


# Untested
@contextmanager
def client_with_user(app, user):
    with app.test_client() as c:
        if user is not None:
            with c.session_transaction() as session:
                session['user_id'] = user.user_id
        yield c


# Untested
class APITestCase(unittest.TestCase):

    def setUp(self):
        from . import create_app, create_apizer

        self.app = create_app('test')
        self.apize = create_apizer(self.app)

        # Bind our helper client to the app
        self.app.test_client_as_user = client_with_user.__get__(self.app,
                                                                Flask)

        # Malformed JSON or does not respect rules
        self.error_400_malformed_dict = {
            'error': {'status_code': 400,
                      'type': 'Malformed',
                      'message': 'Request body is malformed'}}

        # Missing required field
        self.error_400_missing_requirement_dict = {
            'error': {'status_code': 400,
                      'type': 'MissingRequirement',
                      'message': 'One of the required fields is missing'}}

        # Bad field syntax
        self.error_400_bad_syntax_dict = {
            'error': {'status_code': 400,
                      'type': 'BadSyntax',
                      'message': ('A field does not fulfill '
                                  'the required syntax')}}

        # 401 error dict
        self.error_401_dict = {
            'error': {'status_code': 401,
                      'type': 'Unauthenticated',
                      'message': 'Request requires authentication'}}

        # DoesNotExist error dict
        self.error_404_does_not_exist_dict = {
            'error': {'status_code': 404,
                      'type': 'DoesNotExist',
                      'message': 'Item does not exist'}}

        # 403 unauthorized error dict
        self.error_403_unauthorized_dict = {
            'error': {'status_code': 403,
                      'type': 'Unauthorized',
                      'message': ('You do not have access to this '
                                  'resource')}}

        # 403 owner user_id not set dict
        self.error_403_owner_user_id_not_set_dict = {
            'error': {'status_code': 403,
                      'type': 'OwnerUserIdNotSet',
                      'message': "Owner's user_id is not set"}}

        # 409 conflit
        self.error_409_field_conflict_dict = {
            'error': {'status_code': 409,
                      'type': 'FieldConflict',
                      'message': 'The value is already taken'}}

    def tearDown(self):
        with self.app.test_request_context():
            wipe_test_database()

    def get(self, url, user=None, load_json_resp=True):
        with self.app.test_client_as_user(user) as c:
            resp = c.get(self.apize(url))
            data = json.loads(resp.data) if load_json_resp else resp
            return data, resp.status_code

    def put(self, url, pdata, user=None, mime='application/json',
            dump_json_data=True, load_json_resp=True):
        with self.app.test_client_as_user(user) as c:
            pdata = json.dumps(pdata) if dump_json_data else pdata
            resp = c.put(path=self.apize(url), data=pdata,
                         content_type=mime)
            rdata = json.loads(resp.data) if load_json_resp else resp
            return rdata, resp.status_code

    def post(self, url, pdata, user=None, mime='application/json',
             dump_json_data=True, load_json_resp=True):
        with self.app.test_client_as_user(user) as c:
            pdata = json.dumps(pdata) if dump_json_data else pdata
            resp = c.post(path=self.apize(url), data=pdata,
                          content_type=mime)
            rdata = json.loads(resp.data) if load_json_resp else resp
            return rdata, resp.status_code


class EmptyJsonableException(BaseException):
    pass


class JSONIterableMixin(object):

    def _to_jsonable(self, pre_type_string):
        res = []

        for item in self.__iter__():
            res.append(item._to_jsonable(pre_type_string))

        return res

    def _build_to_jsonable(self, pre_type_string):
        def to_jsonable(self):
            try:
                return self._to_jsonable(pre_type_string)
            except EmptyJsonableException:
                return None
        # Return bound method
        return to_jsonable.__get__(self, JSONIterableMixin)

    def __getattribute__(self, name):
        # Catch 'to_*' calls
        if (name != 'to_mongo' and len(name) >= 4 and name[:3] == 'to_'
                and name[2:] in self._document.__dict__):
            return self._build_to_jsonable(name[2:])
        else:
            return object.__getattribute__(self, name)


class JSONQuerySet(JSONIterableMixin, QuerySet):
    pass


class JSONSet(JSONIterableMixin, MutableSet):

    def __init__(self, document_type, init_set=None):
        self._document = document_type
        if init_set is None:
            init_set = set([])
        self._set = init_set

    def __contains__(self, item):
        return self._set.__contains__(item)

    def __iter__(self):
        return self._set.__iter__()

    def __len__(self):
        return self._set.__len__()

    def add(self, item):
        return self._set.add(item)

    def update(self, items):
        return self._set.update(items)

    def discard(self, item):
        return self._set.discard(item)


class JSONDocumentMixin(object):

    meta = {'queryset_class': JSONQuerySet}

    def _is_regex(self, s):
        return len(s) >= 3 and s[0] == '/' and s[-1] == '/'

    def _get_regex_string(self, s):
        if not self._is_regex(s):
            raise ValueError('string does not represent a regex')
        return s[1:-1]

    def _get_includes(self, type_string):
        if not re.search('^(_[a-zA-Z][a-zA-Z0-9]*)+$', type_string):
            raise ValueError('bad type_string format')

        parts = type_string.split('_')
        includes = []
        for i in xrange(2, len(parts) + 1):
            current = '_'.join(parts[:i])
            try:
                includes.extend(self.__getattribute__(current))
            except AttributeError:
                continue
        return includes

    @classmethod
    def _parse_preinc(cls, preinc):
        return preinc if isinstance(preinc, tuple) else (preinc, preinc)

    def _find_type_string(self, pre_type_string):
        parts = pre_type_string.split('_')
        for i in reversed(xrange(2, len(parts) + 1)):
            current = '_'.join(parts[:i])
            try:
                self.__getattribute__(current)
                return current
            except AttributeError:
                continue
        raise AttributeError(
            "no parent found for '{}'".format(pre_type_string))

    def _insert_jsonable(self, type_string, res, inc):
        try:
            res[inc[1]] = self._jsonablize(type_string, inc[0])
        except EmptyJsonableException:
            pass

    def _insert_regex(self, type_string, res, inc):
        regex = self._get_regex_string(inc[0])

        for attr_name in self.__dict__.iterkeys():
            r = re.search(regex, attr_name)
            if r:
                self._insert_jsonable(type_string, res,
                                      (attr_name, r.expand(inc[1])))

    def _to_jsonable(self, pre_type_string):
        res = {}
        type_string = self._find_type_string(pre_type_string)
        includes = self._get_includes(type_string)

        if len(includes) == 0:
            raise EmptyJsonableException

        for preinc in includes:

            inc = self._parse_preinc(preinc)
            if self._is_regex(inc[0]):
                self._insert_regex(type_string, res, inc)
            else:
                self._insert_jsonable(type_string, res, inc)

        return res

    def _parse_deep_attr_name(self, attr_name):
        parts = attr_name.split('__')
        if len(parts) > 2:
            raise ValueError("Can't go deeper than one level in attributes")
        return parts

    def _jsonablize(self, type_string, attr_or_name, is_attr_name=True):
        if is_attr_name:
            parts = self._parse_deep_attr_name(attr_or_name)
            attr = self.__getattribute__(parts[0])
            if len(parts) == 2:
                if isinstance(attr, list):
                    if parts[1] == 'count':
                        return len(attr)
                    else:
                        return [self._jsonablize(type_string,
                                                 item.__getattribute__(
                                                     parts[1]),
                                                 is_attr_name=False)
                                for item in attr]
                else:
                    return self._jsonablize(type_string,
                                            attr.__getattribute__(parts[1]),
                                            is_attr_name=False)
        else:
            attr = attr_or_name

        if isinstance(attr, JSONDocumentMixin):
            return attr._to_jsonable(type_string)
        elif isinstance(attr, list):
            return [self._jsonablize(type_string, item, is_attr_name=False)
                    for item in attr]
        elif isinstance(attr, datetime):
            return attr.strftime(iso8601)
        else:
            return attr

    def __getattribute__(self, name):
        # Catch 'to_*' calls
        if (name != 'to_mongo' and len(name) >= 4 and name[:3] == 'to_'
                and name[2:] in self.__class__.__dict__):
            return self._build_to_jsonable(name[2:])
        else:
            return object.__getattribute__(self, name)

    def _build_to_jsonable(self, pre_type_string):
        def to_jsonable(self, attr_name=None):
            try:
                if attr_name is None:
                    return self._to_jsonable(pre_type_string)
                else:
                    return self._jsonablize(pre_type_string, attr_name)
            except EmptyJsonableException:
                return None
        # Return bound method
        return to_jsonable.__get__(self, JSONDocumentMixin)
