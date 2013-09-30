# -*- coding: utf-8 -*-

from datetime import datetime
import json

import mongoengine as mge
from mongoengine.queryset import DoesNotExist

from .auth import BrowserIDUserMixin
from .helpers import (build_gravatar_id, JSONDocumentMixin, JSONSet,
                      sha256hex, random_md5hex, hexregex, nameregex, iso8601)


# Often, before modifying a model, you will encounter a model.reload()
# call. This is a workaround for bug
# https://github.com/MongoEngine/mongoengine/issues/237 whose fix
# doesn't seem to be included in our mongoengine 0.8.2. The fix comes
# from
# http://stackoverflow.com/questions/16725340.


# TODO: add a database integrity check function that will be called
# periodically

# TODO: test ordering of results for models


class DatabaseIntegrityError(Exception):
    pass


class UserIdSetError(Exception):
    pass


class OwnerInCollaboratorsError(Exception):
    pass


class DataValueError(ValueError):
    pass


class UserIdReservedError(ValueError):
    pass


class User(mge.Document, BrowserIDUserMixin, JSONDocumentMixin):

    meta = {'ordering': 'profiles__count'}
    reserved_user_ids = ['new', 'settings']

    _jsonable = [('user_id', 'id'),
                 'user_id_is_set',
                 ('exps__exp_id', 'exp_ids'),
                 ('profiles__count', 'n_profiles'),
                 ('devices__count', 'n_devices'),
                 ('results__count', 'n_results'),
                 'gravatar_id']
    _jsonable_private = ['persona_email']

    user_id = mge.StringField(unique=True,
                              regex=nameregex,
                              min_length=2, max_length=50)
    user_id_is_set = mge.BooleanField(required=True, default=False)
    gravatar_id = mge.StringField(regex=hexregex, required=True)
    profiles = mge.ListField(mge.ReferenceField('Profile'))
    devices = mge.ListField(mge.ReferenceField('Device'))
    exps = mge.ListField(mge.ReferenceField('Exp'))
    results = mge.ListField(mge.ReferenceField('Result'))
    persona_email = mge.EmailField(unique=True, min_length=3, max_length=50)

    def set_user_id(self, user_id):
        if self.user_id_is_set:
            raise UserIdSetError('user_id has already been set')
        if user_id in self.reserved_user_ids:
            raise UserIdReservedError("Can't set user_id to any "
                                      'of {}'.format(self.reserved_user_ids))

        self.user_id = user_id
        self.user_id_is_set = True
        self.save()

    def get_collaborators(self):
        collaborators = JSONSet(User)

        for e in self.exps:
            collaborators.add(e.owner)
            collaborators.update(e.collaborators)

        collaborators.discard(self)
        return collaborators

    def has_access_to_user(self, u):
        if u == self:
            return True

        is_collaborator = False
        for e in self.exps:
            if u in e.collaborators or u == e.owner:
                is_collaborator = True
                break

        return is_collaborator

    @classmethod
    def get(cls, user_id):
        try:
            return User.objects.get(user_id=user_id)
        except DoesNotExist:
            return None

    @classmethod
    def get_by_email(cls, email):
        try:
            return User.objects.get(persona_email=email)
        except DoesNotExist:
            return None

    @classmethod
    def get_or_create_by_email(cls, email):
        u = cls.get_by_email(email)

        if u is None:
            pre = email.split('@')[0]
            found = False
            for i in range(50):
                post = random_md5hex()[:3]
                user_id = pre + '-' + post
                if cls.objects(user_id=user_id).count() == 0:
                    found = True
                    break

            if not found:
                raise Exception('Could not generate a temporary user_id '
                                'string')

            gravatar_id = build_gravatar_id(email)
            u = cls(user_id=user_id, gravatar_id=gravatar_id,
                    persona_email=email)
            u.save()

        return u


class Exp(mge.Document, JSONDocumentMixin):

    meta = {'ordering': 'results__count'}

    _jsonable = [('exp_id', 'id'),
                 'name',
                 'description',
                 ('owner__user_id', 'owner_id'),
                 ('collaborators__user_id', 'collaborator_ids'),
                 ('devices__count', 'n_devices'),
                 ('profiles__count', 'n_profiles'),
                 ('results__count', 'n_results')]
    _jsonable_private = []

    exp_id = mge.StringField(unique=True, regex=hexregex)
    name = mge.StringField(unique_with='owner',
                           min_length=3, max_length=50,
                           regex=nameregex)
    owner = mge.ReferenceField('User', required=True)
    description = mge.StringField(max_length=300, default='')
    collaborators = mge.ListField(mge.ReferenceField('User'))
    devices = mge.ListField(mge.ReferenceField('Device'))
    profiles = mge.ListField(mge.ReferenceField('Profile'))
    results = mge.ListField(mge.ReferenceField('Result'))

    @classmethod
    def build_exp_id(cls, name, owner):
        return sha256hex(owner.user_id + '/' + name)

    @classmethod
    def check_owner_collaborators_integrity(self, owner, collaborators):
        if not owner.user_id_is_set:
            raise UserIdSetError("Owner's `user_id` is not set")

        collaborators = collaborators or []
        for c in collaborators:
            if not c.user_id_is_set:
                raise UserIdSetError("A collaborator's `user_id` is not"
                                     ' set')

    @classmethod
    def create(cls, name, owner, description='', collaborators=None):
        if not collaborators:
            collaborators = []

        cls.check_owner_collaborators_integrity(owner, collaborators)

        if owner in collaborators:
            raise OwnerInCollaboratorsError

        exp_id = cls.build_exp_id(name, owner)
        e = cls(exp_id=exp_id, name=name, owner=owner,
                description=description, collaborators=collaborators)
        e.save()

        owner.exps.append(e)
        owner.save()
        for c in collaborators:
            c.exps.append(e)
            c.save()

        return e


class Device(mge.Document, JSONDocumentMixin):

    meta = {'ordering': 'device_id'}

    _jsonable = [('device_id', 'id'), 'vk_pem']
    _jsonable_private = []

    device_id = mge.StringField(unique=True, regex=hexregex)
    vk_pem = mge.StringField(required=True, max_length=5000)

    # TODO: add profiles (count), results (count), exps (id list) in the
    # API and here

    @classmethod
    def build_device_id(cls, vk_pem):
        return sha256hex(vk_pem)

    @classmethod
    def create(cls, vk_pem):
        device_id = cls.build_device_id(vk_pem)
        d = cls(device_id=device_id, vk_pem=vk_pem)
        d.save()
        return d


class Data(mge.DynamicEmbeddedDocument, JSONDocumentMixin):

    _jsonable = []
    _jsonable_private = [(r'/^((?!_)[a-zA-Z0-9_]+)$/', r'\1')]


class DeviceSetError(Exception):
    pass


class Profile(mge.Document, JSONDocumentMixin):

    meta = {'ordering': 'results__count'}

    _jsonable = [('profile_id', 'id'), 'vk_pem']
    _jsonable_private = [('exp__exp_id', 'exp_id'),
                         ('device__device_id', 'device_id', None),
                         ('results__count', 'n_results'),
                         'data']

    profile_id = mge.StringField(unique=True, regex=hexregex)
    vk_pem = mge.StringField(required=True, max_length=5000)
    exp = mge.ReferenceField('Exp', required=True)
    data = mge.EmbeddedDocumentField('Data', default=Data)
    device = mge.ReferenceField('Device')
    results = mge.ListField(mge.ReferenceField('Result'))

    def set_device(self, device):
        try:
            if self.device is not None:
                raise DeviceSetError('Device has already been set')
        except AttributeError:
            pass

        self.device = device
        self.save()

        if device not in self.exp.devices:
            self.exp.reload()
            self.exp.devices.append(device)
            self.exp.save()
        if device not in self.exp.owner.devices:
            self.exp.owner.devices.append(device)
            self.exp.owner.save()
        for c in self.exp.collaborators:
            if device not in c.devices:
                c.devices.append(device)
                c.save()

    def set_data(self, data_dict):
        if not isinstance(data_dict, dict):
            raise DataValueError('Can only initialize with a dict')
        self.data = Data(**data_dict)
        self.save()

    @classmethod
    def build_profile_id(cls, vk_pem):
        return sha256hex(vk_pem)

    @classmethod
    def create(cls, vk_pem, exp, data_dict=None, device=None):
        if data_dict is not None and not isinstance(data_dict, dict):
            raise DataValueError('Can only initialize with a dict')

        profile_id = cls.build_profile_id(vk_pem)
        d = Data(**(data_dict or {}))
        p = cls(profile_id=profile_id, vk_pem=vk_pem, exp=exp,
                data=d, device=device)
        p.save()

        exp.reload()
        exp.profiles.append(p)
        if device and (device not in exp.devices):
            exp.devices.append(device)
        exp.save()

        exp.owner.profiles.append(p)
        if device and (device not in exp.owner.devices):
            exp.owner.devices.append(device)
        exp.owner.save()

        for c in exp.collaborators:
            c.profiles.append(p)
            if device and (device not in c.devices):
                c.devices.append(device)
            c.save()

        return p


class Result(mge.Document, JSONDocumentMixin):

    meta = {'ordering': 'created_at'}

    _jsonable = [('result_id', 'id')]
    _jsonable_private = [('profile__profile_id', 'profile_id'),
                         ('exp__exp_id', 'exp_id'),
                         'created_at',
                         'data']

    result_id = mge.StringField(unique=True, regex=hexregex)
    profile = mge.ReferenceField('Profile', required=True)
    exp = mge.ReferenceField('Exp', required=True)
    created_at = mge.ComplexDateTimeField(required=True)
    data = mge.EmbeddedDocumentField('Data', required=True)

    @classmethod
    def build_result_id(cls, profile, created_at, data_dict):
        # The datetime.isoformat() method does not append the 'Z' for GMT+0, so
        # we add it manually
        return sha256hex(profile.profile_id + '@' +
                         created_at.strftime(iso8601) + '/' +
                         json.dumps(data_dict, separators=(',', ':')))

    @classmethod
    def create(cls, profile, data_dict):
        if not isinstance(data_dict, dict):
            raise DataValueError('Can only initialize with a dict')

        created_at = datetime.utcnow()
        exp = profile.exp
        result_id = cls.build_result_id(profile, created_at, data_dict)
        d = Data(**data_dict)
        r = cls(result_id=result_id, profile=profile, exp=exp,
                created_at=created_at, data=d)
        r.save()

        exp.results.append(r)
        exp.save()
        profile.results.append(r)
        profile.save()
        exp.owner.results.append(r)
        exp.owner.save()
        for c in exp.collaborators:
            c.results.append(r)
            c.save()

        return r
