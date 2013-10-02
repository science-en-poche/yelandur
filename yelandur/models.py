# -*- coding: utf-8 -*-

from datetime import datetime
import json

import mongoengine as mge
from mongoengine.queryset import DoesNotExist

from .auth import BrowserIDUserMixin
from .helpers import (build_gravatar_id, JSONDocumentMixin, sha256hex,
                      random_md5hex, hexregex, nameregex, iso8601,
                      ComputedSaveMixin)


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


class User(ComputedSaveMixin, mge.Document,
           BrowserIDUserMixin, JSONDocumentMixin):

    meta = {'ordering': 'n_profiles'}
    computed_lengths = [('profile_ids', 'n_profiles'),
                        ('device_ids', 'n_devices'),
                        ('exp_ids', 'n_exps'),
                        ('result_ids', 'n_results')]
    reserved_user_ids = ['new', 'settings']

    _jsonable = [('user_id', 'id'),
                 'user_id_is_set',
                 'exp_ids',
                 'n_exps',
                 'n_profiles',
                 'n_devices',
                 'n_results',
                 'gravatar_id']
    _jsonable_private = ['persona_email']

    user_id = mge.StringField(unique=True,
                              regex=nameregex,
                              min_length=2, max_length=50)
    user_id_is_set = mge.BooleanField(required=True, default=False)
    gravatar_id = mge.StringField(regex=hexregex, required=True)
    profile_ids = mge.ListField(mge.StringField(regex=hexregex))
    n_profiles = mge.IntField(required=True)
    device_ids = mge.ListField(mge.StringField(regex=hexregex))
    n_devices = mge.IntField(required=True)
    exp_ids = mge.ListField(mge.StringField(regex=hexregex))
    n_exps = mge.IntField(required=True)
    result_ids = mge.ListField(mge.StringField(regex=hexregex))
    n_results = mge.IntField(required=True)
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


class Exp(ComputedSaveMixin, mge.Document, JSONDocumentMixin):

    meta = {'ordering': 'n_results'}
    computed_lengths = [('profile_ids', 'n_profiles'),
                        ('device_ids', 'n_devices'),
                        ('result_ids', 'n_results'),
                        ('collaborator_ids', 'n_collaborators')]

    _jsonable = [('exp_id', 'id'),
                 'name',
                 'description',
                 'owner_id',
                 'collaborator_ids',
                 'n_collaborators',
                 'n_devices',
                 'n_profiles',
                 'n_results']
    _jsonable_private = []

    exp_id = mge.StringField(unique=True, regex=hexregex)
    name = mge.StringField(unique_with='owner_id',
                           min_length=3, max_length=50,
                           regex=nameregex)
    owner_id = mge.StringField(required=True, regex=nameregex)
    description = mge.StringField(max_length=300, default='')
    collaborator_ids = mge.ListField(mge.StringField(regex=nameregex))
    n_collaborators = mge.IntField(required=True)
    device_ids = mge.ListField(mge.StringField(regex=hexregex))
    n_devices = mge.IntField(required=True)
    profile_ids = mge.ListField(mge.StringField(regex=hexregex))
    n_profiles = mge.IntField(required=True)
    result_ids = mge.ListField(mge.StringField(regex=hexregex))
    n_results = mge.IntField(required=True)

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
        collaborator_ids = [c.user_id for c in collaborators]
        e = cls(exp_id=exp_id, name=name, owner_id=owner.user_id,
                description=description, collaborator_ids=collaborator_ids)
        e.save()

        owner.exp_ids.append(exp_id)
        owner.save()
        for c in collaborators:
            c.exp_ids.append(exp_id)
            c.save()

        return e


class Device(ComputedSaveMixin, mge.Document, JSONDocumentMixin):

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


class Profile(ComputedSaveMixin, mge.Document, JSONDocumentMixin):

    meta = {'ordering': 'n_results'}
    computed_lengths = [('result_ids', 'n_results')]

    _jsonable = [('profile_id', 'id'), 'vk_pem']
    _jsonable_private = ['exp_id',
                         ('device_id', 'device_id', None),
                         'n_results',
                         'data']

    profile_id = mge.StringField(unique=True, regex=hexregex)
    vk_pem = mge.StringField(required=True, max_length=5000)
    exp_id = mge.StringField(required=True, regex=hexregex)
    data = mge.EmbeddedDocumentField('Data', default=Data)
    device_id = mge.StringField(regex=hexregex)
    result_ids = mge.ListField(mge.StringField(regex=hexregex))
    n_results = mge.IntField(required=True)

    def set_device(self, device):
        try:
            if self.device_id is not None:
                raise DeviceSetError('Device has already been set')
        except AttributeError:
            pass

        self.device_id = device.device_id
        self.save()

        exp = Exp.objects.get(exp_id=self.exp_id)
        if device.device_id not in exp.device_ids:
            exp.device_ids.append(device.device_id)
            exp.save()
        owner = User.objects.get(user_id=exp.owner_id)
        if device.device_id not in owner.device_ids:
            owner.device_ids.append(device.device_id)
            owner.save()
        for c in User.objects(user_id__in=exp.collaborator_ids):
            if device.device_id not in c.device_ids:
                c.device_ids.append(device.device_id)
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
        p = cls(profile_id=profile_id, vk_pem=vk_pem, exp_id=exp.exp_id,
                data=d, device_id=device.device_id if device else None)
        p.save()

        exp.reload()
        exp.profile_ids.append(profile_id)
        if device and (device.device_id not in exp.device_ids):
            exp.device_ids.append(device.device_id)
        exp.save()

        owner = User.objects.get(user_id=exp.owner_id)
        owner.profile_ids.append(profile_id)
        if device and (device.device_id not in owner.device_ids):
            owner.device_ids.append(device.device_id)
        owner.save()

        for c in User.objects(user_id__in=exp.collaborator_ids):
            c.profile_ids.append(profile_id)
            if device and (device.device_id not in c.device_ids):
                c.device_ids.append(device.device_id)
            c.save()

        return p


class Result(ComputedSaveMixin, mge.Document, JSONDocumentMixin):

    meta = {'ordering': 'created_at'}

    _jsonable = [('result_id', 'id')]
    _jsonable_private = ['profile_id',
                         'exp_id',
                         'created_at',
                         'data']

    result_id = mge.StringField(unique=True, regex=hexregex)
    profile_id = mge.StringField(regex=hexregex, required=True)
    exp_id = mge.StringField(regex=hexregex, required=True)
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
        exp = Exp.objects.get(exp_id=profile.exp_id)
        result_id = cls.build_result_id(profile, created_at, data_dict)
        d = Data(**data_dict)
        r = cls(result_id=result_id, profile_id=profile.profile_id,
                exp_id=exp.exp_id, created_at=created_at, data=d)
        r.save()

        exp.result_ids.append(result_id)
        exp.save()
        profile.result_ids.append(result_id)
        profile.save()
        owner = User.objects.get(user_id=exp.owner_id)
        owner.result_ids.append(result_id)
        owner.save()
        for c in User.objects(user_id__in=exp.collaborator_ids):
            c.result_ids.append(result_id)
            c.save()

        return r
