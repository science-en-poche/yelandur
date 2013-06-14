from datetime import datetime
import json

import mongoengine as mge
from mongoengine.queryset import DoesNotExist

from .auth import BrowserIDUserMixin
from .helpers import (build_gravatar_id, JSONMixin, sha256hex,
                      random_md5hex, hexregex)


class UserIdSetError(Exception):
    pass


class User(mge.Document, BrowserIDUserMixin, JSONMixin):

    meta = {'ordering': ['profiles__count']}

    _jsonable = ['user_id',
                 'user_id_is_set',
                 ('profiles__count', 'n_profiles'),
                 ('devices__count', 'n_devices'),
                 ('exps__count', 'n_exps'),
                 ('results__count', 'n_results'),
                 'gravatar_id']
    _jsonable_private = ['persona_email']

    user_id = mge.StringField(unique=True,
                              regex=r'^[a-zA-Z][a-zA-Z0-9_-]*[a-zA-Z0-9]$')
    user_id_is_set = mge.BooleanField(required=True, default=False)
    gravatar_id = mge.StringField(regex=hexregex, required=True)
    profiles = mge.ListField(mge.ReferenceField('Profile'),
                             required=True, default=[])
    devices = mge.ListField(mge.ReferenceField('Device'), required=True,
                            default=[])
    exps = mge.ListField(mge.ReferenceField('Exp'), required=True,
                         default=[])
    results = mge.ListField(mge.ReferenceField('Result'), required=True,
                            default=[])
    persona_email = mge.EmailField(unique=True, min_length=3, max_length=50)

    def set_user_id(self, user_id):
        if self.user_id_is_set:
            raise UserIdSetError('user_id has already been set')

        self.user_id = user_id
        self.user_id_is_set = True

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


class Exp(mge.Document, JSONMixin):

    meta = {'ordering': ['results__count']}

    _jsonable = ['exp_id',
                 'name',
                 'description',
                 ('owner__user_id', 'owner_id'),
                 ('collaborators__id', 'collaborator_ids'),
                 ('devices__count', 'n_devices'),
                 ('profiles__count', 'n_profiles'),
                 ('results__count', 'n_results')]
    _jsonable_private = []

    exp_id = mge.StringField(unique=True, regex=hexregex)
    name = mge.StringField(unique_with='owner',
                           min_length=3, max_length=50,
                           regex=r'^[a-zA-Z][a-zA-Z0-9_-]*[a-zA-Z0-9]$')
    owner = mge.ReferenceField('User', required=True)
    description = mge.StringField(max_length=300, required=True,
                                  default='')
    collaborators = mge.ListField(mge.ReferenceField('User'),
                                  required=True, default=[])
    devices = mge.ListField(mge.ReferenceField('Device'), required=True,
                            default=[])
    profiles = mge.ListField(mge.ReferenceField('Profile'),
                             required=True, default=[])
    results = mge.ListField(mge.ReferenceField('Result'), required=True,
                            default=[])

    @classmethod
    def build_exp_id(cls, name, owner):
        return sha256hex(owner.user_id + '/' + name)

    @classmethod
    def create(cls, name, owner, description='', collaborators=[]):
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


class Device(mge.Document, JSONMixin):

    meta = {'ordering': ['device_id']}

    _jsonable = ['device_id', 'vk_pem']
    _jsonable_private = []

    device_id = mge.StringField(unique=True, regex=hexregex)
    vk_pem = mge.StringField(required=True, max_length=5000)

    # TODO: add profiles, results, exps

    @classmethod
    def build_device_id(cls, vk_pem):
        return sha256hex(vk_pem)

    @classmethod
    def create(cls, vk_pem):
        device_id = cls.build_device_id(vk_pem)
        d = cls(device_id=device_id, vk_pem=vk_pem)
        d.save()
        return d


class Data(mge.DynamicEmbeddedDocument, JSONMixin):

    _jsonable = []
    _jsonable_private = [(r'/^((?!_)[a-zA-Z0-9_]+)$/', r'\1')]


class DeviceSetError(Exception):
    pass


class Profile(mge.Document, JSONMixin):

    meta = {'ordering': ['results__count']}

    _jsonable = ['profile_id', 'vk_pem']
    _jsonable_private = [('exp__id', 'exp_id'),
                         ('device__id', 'device_id'),
                         ('results__count', 'n_results'),
                         'data']

    device_id = mge.StringField(unique=True, regex=hexregex)
    vk_pem = mge.StringField(required=True, max_length=5000)
    exp = mge.ReferenceField('Exp', required=True)
    data = mge.EmbeddedDocumentField('Data', required=True,
                                     default=Data())
    device = mge.ReferenceField('Device')
    results = mge.ListField(mge.ReferenceField('Result'), required=True,
                            default=[])

    def set_device(self, device):
        try:
            if self.device is not None:
                raise DeviceSetError('Device has already been set')
        except AttributeError:
            pass

        self.device = device
        self.save()

        if device not in self.exp.devices:
            self.exp.devices.append(device)
            self.exp.save()
        if device not in self.exp.owner.devices:
            self.exp.owner.devices.append(device)
            self.exp.owner.save()
        for c in self.exp.collaborators:
            if device not in c.devices:
                c.devices.append(device)
                c.save()

    @classmethod
    def build_profile_id(cls, vk_pem):
        return sha256hex(vk_pem)

    @classmethod
    def create(cls, vk_pem, exp, data={}, device=None):
        profile_id = cls.build_profile_id(vk_pem)
        d = Data(**data)
        p = cls(profile_id=profile_id, vk_pem=vk_pem, exp=exp,
                data=d, device=device)
        p.save()

        exp.profiles.append(p)
        exp.save()
        exp.owner.profiles.append(p)
        exp.owner.save()
        for c in exp.collaborators:
            c.profiles.append(p)
            c.save()

        return p


class Result(mge.Document, JSONMixin):

    meta = {'ordering': ['created_at']}

    _jsonable = ['result_id']
    _jsonable_private = ['device', 'created_at', 'data']

    result_id = mge.StringField(unique=True, regex=hexregex)
    profile = mge.ReferenceField('Profile', required=True)
    exp = mge.ReferenceField('Exp', required=True)
    created_at = mge.DateTimeField(required=True)
    data = mge.EmbeddedDocumentField('Data', required=True)

    @classmethod
    def build_result_id(cls, profile, created_at, data):
        return sha256hex(profile.profile_id + '@' +
                         created_at.isoformat() + '/' +
                         json.dumps(data))

    @classmethod
    def create(cls, profile, exp, data):
        created_at = datetime.utcnow()
        result_id = cls.build_result_id(profile, created_at, data)
        d = Data(**data)
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
