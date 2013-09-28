# -*- coding: utf-8 -*-

import re
from collections import MutableSet
from functools import partial
from datetime import datetime
from hashlib import md5, sha256
import random
import time
import json
from contextlib import contextmanager
import unittest

from flask import Flask, current_app
from mongoengine.queryset import QuerySet
import jws
from jws.utils import base64url_decode, base64url_encode
from ecdsa.util import (sigdecode_der, sigencode_der,
                        sigdecode_string, sigencode_string)
from ecdsa import VerifyingKey


hexregex = r'^[0-9a-f]*$'
nameregex = r'^[a-zA-Z][a-zA-Z0-9_-]*[a-zA-Z0-9]$'
iso8601 = r'%Y-%m-%dT%H:%M:%S.%fZ'


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


class MalformedSignatureError(Exception):
    pass


class BadSignatureError(Exception):
    pass


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

    def _sign(self, pdata, sks, dump_json_data):
        if not isinstance(sks, list):
            sks = [sks]

        jheader = '{"alg": "ES256"}'
        jheader_b64 = base64url_encode(jheader)

        jpayload = json.dumps(pdata) if dump_json_data else pdata
        jpayload_b64 = base64url_encode(jpayload)

        pdata_sig = {'payload': jpayload_b64,
                     'signatures': []}

        for sk in sks:
            sig_string_b64 = jws.sign(jheader, jpayload, sk, is_json=True)

            order = sk.curve.order
            sig_string = base64url_decode(sig_string_b64)
            r, s = sigdecode_string(sig_string, order)
            sig_der = sigencode_der(r, s, order)
            sig_der_b64 = base64url_encode(sig_der)

            pdata_sig['signatures'].append({'protected': jheader_b64,
                                            'signature': sig_der_b64})

        return pdata_sig

    def sput(self, url, pdata, sks, user=None, mime='application/jose+json',
             dump_json_data=True, load_json_resp=True):
        return self.put(url, self._sign(pdata, sks, dump_json_data), user,
                        mime=mime, dump_json_data=True,
                        load_json_resp=load_json_resp)

    def spost(self, url, pdata, sks, user=None, mime='application/jose+json',
              dump_json_data=True, load_json_resp=True):
        return self.post(url, self._sign(pdata, sks, dump_json_data), user,
                         mime=mime, dump_json_data=True,
                         load_json_resp=load_json_resp)


class EmptyJsonableException(BaseException):
    pass


class QueryTooDeepError(ValueError):
    pass


class TypeStringParserMixin(object):

    @classmethod
    def _is_regex(cls, s):
        return len(s) >= 3 and s[0] == '/' and s[-1] == '/'

    @classmethod
    def _get_regex_string(cls, s):
        if not cls._is_regex(s):
            raise ValueError('string does not represent a regex')
        return s[1:-1]

    @classmethod
    def _parse_preinc(cls, preinc):
        return preinc if isinstance(preinc, tuple) else (preinc, preinc)

    @classmethod
    def _parse_deep_attr_name(cls, attr_name):
        parts = attr_name.split('__')
        if len(parts) > 2:
            raise ValueError("Can't go deeper than one level in attributes")
        return parts

    def _get_includes(self, type_string, search_object=None):
        if not re.search('^(_[a-zA-Z][a-zA-Z0-9]*)+$', type_string):
            raise ValueError('bad type_string format')

        if search_object is None:
            attr_getter = self.__getattribute__
        else:
            attr_getter = partial(object.__getattribute__, search_object)

        parts = type_string.split('_')
        includes = []
        for i in xrange(2, len(parts) + 1):
            current = '_'.join(parts[:i])
            try:
                includes.extend(attr_getter(current))
            except AttributeError:
                continue
        return includes

    def _find_type_string(self, pre_type_string, search_object=None):
        if search_object is None:
            attr_getter = self.__getattribute__
        else:
            attr_getter = partial(object.__getattribute__, search_object)

        parts = pre_type_string.split('_')
        for i in reversed(xrange(2, len(parts) + 1)):
            current = '_'.join(parts[:i])
            try:
                attr_getter(current)
                return current
            except AttributeError:
                continue
        raise AttributeError(
            "no parent found for '{}'".format(pre_type_string))


class JSONIterableMixin(TypeStringParserMixin):

    def _to_jsonable(self, pre_type_string):
        res = []

        for item in self.__iter__():
            res.append(item._to_jsonable(pre_type_string))

        return res

    def _translate_to(self, pre_type_string, query_dict):
        type_string = self._find_type_string(pre_type_string, self._document)
        includes = self._get_includes(type_string, self._document)

        if len(includes) == 0:
            raise EmptyJsonableException

        query_key_parts = {}
        for k in query_dict.iterkeys():
            parts = k.split('__')
            if len(parts) >= 2:
                query_key_parts[parts[0]] = '__' + '__'.join(parts[1:])
            else:
                query_key_parts[parts[0]] = ''

        translated_query = {}
        for preinc in includes:
            inc = self._parse_preinc(preinc)
            if self._is_regex(inc[0]):
                # Don't take queries on regexps
                continue
            if inc[1] in query_key_parts:
                # Rebuild original key to go fetch the query value in
                # query_dict
                orig_k = inc[1] + query_key_parts[inc[1]]
                # Build the corresponding mongo key
                k = inc[0] + query_key_parts[inc[1]]
                translated_query[k] = query_dict[orig_k]

        return translated_query

    def _build_to_jsonable(self, pre_type_string):
        def to_jsonable(self):
            try:
                return self._to_jsonable(pre_type_string)
            except EmptyJsonableException:
                return None
        # Return bound method
        return to_jsonable.__get__(self, JSONIterableMixin)

    def _build_translate_to(self, pre_type_string):
        def translate_to(self, query_dict):
            return self._translate_to(pre_type_string, query_dict)
        # Return bound method
        return translate_to.__get__(self, JSONDocumentMixin)

    def __getattribute__(self, name):
        # Catch 'to_*' and 'translate_to_*' calls
        if name != 'to_mongo' and len(name) >= 4:
            if name[:3] == 'to_' and name[2:] in self._document.__dict__:
                return self._build_to_jsonable(name[2:])
            elif (name[:13] == 'translate_to_'
                  and name[12:] in self._document.__dict__):
                return self._build_translate_to(name[12:])
        return object.__getattribute__(self, name)


class JSONQuerySet(JSONIterableMixin, QuerySet):
    pass


class JSONSet(JSONIterableMixin, MutableSet):

    def __init__(self, document_type, init_set=None):
        self._document = document_type
        if init_set is None:
            init_set = set([])
        self._set = set(init_set)

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


class JSONDocumentMixin(TypeStringParserMixin):

    meta = {'queryset_class': JSONQuerySet}

    def _insert_jsonable(self, type_string, res, inc):
        try:
            has_default = (len(inc) == 3)
            default = inc[2] if has_default else None
            res[inc[1]] = self._jsonablize(type_string, inc[0],
                                           has_default=has_default,
                                           default=default)
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

    def _jsonablize(self, type_string, attr_or_name, is_attr_name=True,
                    has_default=False, default=None):
        if is_attr_name:
            parts = self._parse_deep_attr_name(attr_or_name)

            # Default-filling block
            try:
                attr = self.__getattribute__(parts[0])
            except AttributeError, msg:
                if has_default:
                    if default is None:
                        raise EmptyJsonableException
                    else:
                        attr = default
                else:
                    raise AttributeError(msg)

            if len(parts) == 2:
                if isinstance(attr, list):
                    if parts[1] == 'count':
                        return len(attr)
                    else:
                        out = []
                        for item in attr:
                            # New default-filling block
                            try:
                                sub_attr = item.__getattribute__(parts[1])
                                out.append(
                                    self._jsonablize(type_string,
                                                     sub_attr,
                                                     is_attr_name=False))
                            except AttributeError, msg:
                                if has_default:
                                    if default is None:
                                        continue
                                    else:
                                        out.append(default)
                                else:
                                    raise AttributeError(msg)
                        return out
                else:
                    # Another default-filling block
                    try:
                        sub_attr = attr.__getattribute__(parts[1])
                        return self._jsonablize(type_string, sub_attr,
                                                is_attr_name=False)
                    except AttributeError, msg:
                        if has_default:
                            if default is None:
                                raise EmptyJsonableException
                            else:
                                return default
                        else:
                            raise AttributeError(msg)

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
