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
from mongoengine import (IntField, StringField, ListField,
                         ComplexDateTimeField, DateTimeField)
import jws
from jws.utils import base64url_decode, base64url_encode
from ecdsa.util import (sigdecode_der, sigencode_der,
                        sigdecode_string, sigencode_string)
from ecdsa import VerifyingKey


hexregex = r'^[0-9a-f]*$'
nameregex = r'^[a-zA-Z]([a-zA-Z0-9_.-]?[a-zA-Z0-9]+)*$'
iso8601 = r'%Y-%m-%dT%H:%M:%S.%fZ'
iso8601_seconds = r'%Y-%m-%dT%H:%M:%SZ'
dot_code = '&dot;'
and_code = '&and;'


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
def mongo_encode_string(s):
    pres = s.replace('&', and_code)
    return pres.replace('.', dot_code)


# TODO: test
def mongo_encode_list(dlist):
    elist = []
    for ditem in dlist:
        elist.append(mongo_encode(ditem))
    return elist


# TODO: test
def mongo_encode_dict(ddict):
    edict = {}
    for dkey, dvalue in ddict.iteritems():
        if isinstance(dkey, str) or isinstance(dkey, unicode):
            ekey = mongo_encode_string(dkey)
        elif isinstance(dkey, float) or isinstance(dkey, int):
            ekey = dkey
        else:
            raise ValueError("Can not encode dict key: object type "
                             "not supported (key is: {})".format(dkey))
        edict[ekey] = mongo_encode(dvalue)
    return edict


# TODO: test
def mongo_encode(dobject):
    if isinstance(dobject, dict):
        return mongo_encode_dict(dobject)
    elif isinstance(dobject, list):
        return mongo_encode_list(dobject)
    else:
        return dobject


# TODO: test
def mongo_decode_string(s):
    pres = s.replace(dot_code, '.')
    return pres.replace(and_code, '&')


# TODO: test
def mongo_decode_list(elist):
    dlist = []
    for eitem in elist:
        dlist.append(mongo_decode(eitem))
    return dlist


# TODO: test
def mongo_decode_dict(edict):
    ddict = {}
    for ekey, evalue in edict.iteritems():
        if isinstance(ekey, str) or isinstance(ekey, unicode):
            dkey = mongo_decode_string(ekey)
        elif isinstance(ekey, float) or isinstance(ekey, int):
            dkey = ekey
        else:
            raise ValueError("Can not decode dict key: object type "
                             "not supported (key is: {})".format(ekey))
        ddict[dkey] = mongo_decode(evalue)
    return ddict


# TODO: test
def mongo_decode(eobject):
    if isinstance(eobject, dict):
        return mongo_decode_dict(eobject)
    elif isinstance(eobject, list):
        return mongo_decode_list(eobject)
    else:
        return eobject


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
def is_jose_sig_valid(b64_jpayload, jose_sig, vk_pem):
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
def is_jws_sig_valid(b64_jws_sig, vk_pem):
    parts = b64_jws_sig.split('.')
    if len(parts) != 3:
        raise MalformedSignatureError

    # Extract parts to verify signature
    jheader_b64, jbody_b64, sig_der_b64 = parts
    jheader = b64url_dec(jheader_b64)
    jbody = b64url_dec(jbody_b64)
    sig_der = b64url_dec(sig_der_b64)

    vk = VerifyingKey.from_pem(vk_pem)
    vk_order = vk.curve.order
    sig_string_b64 = base64url_encode(sig_der_to_string(sig_der, vk_order))

    try:
        jws.verify(jheader, jbody, sig_string_b64, vk, is_json=True)
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

    def get(self, url, user=None, load_json_resp=True, query_string=None):
        with self.app.test_client_as_user(user) as c:
            resp = c.get(self.apize(url), query_string=query_string)
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

    def _create_auth_token(self, sk, profile):
        jheader = '{"alg": "ES256"}'
        jheader_b64 = base64url_encode(jheader)

        body = {'id': profile.profile_id, 'timestamp': int(time.time())}
        jbody = json.dumps(body)
        jbody_b64 = base64url_encode(jbody)

        sig_string_b64 = jws.sign(jheader, jbody, sk, is_json=True)

        order = sk.curve.order
        sig_string = base64url_decode(sig_string_b64)
        r, s = sigdecode_string(sig_string, order)
        sig_der = sigencode_der(r, s, order)
        sig_der_b64 = base64url_encode(sig_der)

        return '{0}.{1}.{2}'.format(jheader_b64, jbody_b64, sig_der_b64)

    def sget(self, url, sk, profile, load_json_resp=True, query_string=None):
        auth_token = self._create_auth_token(sk, profile)
        if query_string is None:
            query_string = {}
        query_string['auth_token'] = auth_token
        return self.get(url, load_json_resp=load_json_resp,
                        query_string=query_string)

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


class ComputedSaveMixin(object):

    def save(self, *args, **kwargs):
        if hasattr(self, 'computed_lengths'):
            for f, c in self.computed_lengths:
                self.__setattr__(c, len(self.__getattribute__(f)))
        super(ComputedSaveMixin, self).save(*args, **kwargs)


class EmptyJsonableException(BaseException):
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


class QueryTooDeepException(ValueError):
    pass


class UnknownOperator(ValueError):
    pass


class NonQueriableType(ValueError):
    pass


class BadQueryType(ValueError):
    pass


class ParsingError(ValueError):
    pass


class JSONIterableMixin(TypeStringParserMixin):

    mongo_py_type_map = {StringField: str,
                         IntField: int,
                         ListField: list,
                         ComplexDateTimeField: datetime,
                         DateTimeField: datetime}
    general_operators = ['gte', 'gt', 'lte', 'lt']
    string_operators = ['exact', 'iexact', 'contains', 'icontains',
                        'startswith', 'istartswith', 'endswith', 'iendswith']
    queriable_types = [int, str, datetime, list]

    def _to_jsonable(self, pre_type_string):
        res = []

        for item in self.__iter__():
            res.append(item._to_jsonable(pre_type_string))

        return res

    def _parse_query_parts(self, pre_type_string, query_dict):
        type_string = self._find_type_string(pre_type_string, self._document)
        includes = self._get_includes(type_string, self._document)

        if len(includes) == 0:
            raise EmptyJsonableException

        query_parts = {}
        for k, value in query_dict.iteritems():
            parts = k.split('__')
            if len(parts) >= 2:
                subquery = '__' + '__'.join(parts[1:])
            else:
                subquery = ''
            try:
                query_parts[parts[0]].append((subquery, value))
            except KeyError:
                query_parts[parts[0]] = [(subquery, value)]

        return includes, query_parts

    @classmethod
    def _validate_query_item(self, key, value, attr_type, list_attr_type=None):
        # Query deepness
        parts = key.split('__')
        if len(parts) > 2:
            raise QueryTooDeepException

        # Queried field type
        if attr_type not in self.queriable_types:
            raise NonQueriableType
        if attr_type == list:
            if list_attr_type is not None:
                if list_attr_type not in self.queriable_types:
                    raise NonQueriableType

        if len(parts) == 2:
            # We have an operator
            attr_name, op = parts
            if (op not in self.general_operators and
                    op not in self.string_operators):
                raise UnknownOperator("Unknown operator '{}'".format(op))

            # String operator on non-{list of }string field
            if (op in self.string_operators and
                not (attr_type == str or
                     (attr_type == list and
                      (list_attr_type == str or list_attr_type is None)))):
                raise BadQueryType

        # Un-parsable integer
        if attr_type == int or (attr_type == list and list_attr_type == int):
            try:
                int(value)
            except ValueError, msg:
                raise ParsingError(msg)

        # Un-parsable datetime
        if attr_type == datetime or (attr_type == list and
                                     list_attr_type == datetime):
            parsed = False
            try:
                int(value)
                parsed = True
            except ValueError:
                pass
            try:
                float(value)
                parsed = True
            except ValueError:
                pass
            try:
                datetime.strptime(value, iso8601)
                parsed = True
            except ValueError:
                pass
            try:
                datetime.strptime(value, iso8601_seconds)
                parsed = True
            except ValueError:
                pass

            if not parsed:
                raise ParsingError("Couldn't parse timestamp")

    def _validate_query(self, includes, query_parts):
        for preinc in includes:
            inc = self._parse_preinc(preinc)
            if self._is_regex(inc[0]):
                # Don't take queries on regexps
                continue
            if inc[1] in query_parts:
                for subquery, value in query_parts[inc[1]]:
                    # Rebuild original key for validation below
                    orig_k = inc[1] + subquery
                    # Get type of field being queried
                    field = self._document._fields[inc[0]]
                    tipe = self.mongo_py_type_map.get(type(field),
                                                      NonQueriableType)
                    if tipe == list:
                        list_tipe = self.mongo_py_type_map.get(
                            type(field.field), NonQueriableType)
                    else:
                        list_tipe = None
                    # Only bark for an invalid query now that we know
                    # the field is valid
                    self._validate_query_item(orig_k, value, tipe, list_tipe)

    def _translate_to(self, includes, query_parts):
        translated_query = {}
        for preinc in includes:
            inc = self._parse_preinc(preinc)
            if self._is_regex(inc[0]):
                # Don't take queries on regexps
                continue
            if inc[1] in query_parts:
                for subquery, value in query_parts[inc[1]]:
                    # Build the corresponding mongo key
                    k = inc[0] + subquery
                    translated_query[k] = value

        return translated_query

    def _translate_order_to(self, pre_type_string, query_multi_dict):
        type_string = self._find_type_string(pre_type_string, self._document)
        includes = self._get_includes(type_string, self._document)

        if len(includes) == 0:
            raise EmptyJsonableException

        if 'order' not in query_multi_dict:
            return []

        # Break each order query into sign, root, subquery
        order_values_parts = []
        for o in query_multi_dict.getlist('order'):
            parts = o.split('__')
            root = parts[0]
            if root[0] in ('-', '+', ' '):
                sign = root[0].strip()
                root = root[1:]
            else:
                sign = ''
            if len(parts) >= 2:
                subquery = '__' + '__'.join(parts[1:])
            else:
                subquery = ''
            order_values_parts.append((sign, root, subquery))

        # Map inc[1] -> inc[0], excluding regexps
        incmap = {}
        for preinc in includes:
            inc = self._parse_preinc(preinc)
            if self._is_regex(inc[0]):
                # Don't take queries on regexps
                continue
            incmap[inc[1]] = inc[0]

        # Now get order queries to be included, and re-assemble them
        order_values = []
        for sign, root, subquery in order_values_parts:
            if root in incmap:
                # TODO: do same here as in translate_to
                # Only bark for a query too deep now that we know
                # the field is valid
                if subquery.count('__') > 1:
                    raise QueryTooDeepException
                # Store the corresponding mongo key
                order_values.append(sign + incmap[root] + subquery)

        return order_values

    def _build_to_jsonable(self, pre_type_string):
        def to_jsonable(self):
            try:
                return self._to_jsonable(pre_type_string)
            except EmptyJsonableException:
                return None
        # Return bound method
        return to_jsonable.__get__(self, JSONIterableMixin)

    # TODO: test validation here also
    def _build_translate_to(self, pre_type_string):
        def translate_to(self, query_dict):
            try:
                includes, query_parts = self._parse_query_parts(
                    pre_type_string, query_dict)
                self._validate_query(includes, query_parts)
                return self._translate_to(includes, query_parts)
            except EmptyJsonableException:
                return None
        # Return bound method
        return translate_to.__get__(self, JSONDocumentMixin)

    def _build_translate_order_to(self, pre_type_string):
        def translate_order_to(self, query_dict):
            try:
                # TODO: do same as with translate_to
                return self._translate_order_to(pre_type_string, query_dict)
            except EmptyJsonableException:
                return None
        # Return bound method
        return translate_order_to.__get__(self, JSONDocumentMixin)

    def __getattribute__(self, name):
        # Catch 'to_*' and 'translate_to_*' calls
        if name != 'to_mongo' and len(name) >= 4:
            if name[:3] == 'to_' and name[2:] in self._document.__dict__:
                return self._build_to_jsonable(name[2:])
            elif (name[:13] == 'translate_to_'
                  and name[12:] in self._document.__dict__):
                return self._build_translate_to(name[12:])
            elif (name[:19] == 'translate_order_to_'
                  and name[18:] in self._document.__dict__):
                return self._build_translate_order_to(name[18:])
        return object.__getattribute__(self, name)


class JSONQuerySet(JSONIterableMixin, QuerySet):
    pass


# FIXME: unused now, can be deleted
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

        # TODO: test postprocess
        postprocess = getattr(self, 'json_postprocess', lambda x, s: x)

        return postprocess(res, type_string)

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
