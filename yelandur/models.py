from datetime import datetime

import mongoengine as mge
from mongoengine.queryset import DoesNotExist

from .auth import BrowserIDUserMixin
from .helpers import (build_gravatar_id, JSONMixin, sha256hex,
                      random_md5hex, hexregex)


class LoginSetError(Exception):
    pass


class User(mge.Document, BrowserIDUserMixin, JSONMixin):

    meta = {'ordering': ['login']}

    _jsonable = [('user_id', 'id'), 'login', 'login_is_set', 'gravatar_id']
    _jsonable_private = ['email']

    user_id = mge.StringField(unique=True, regex=hexregex)
    email = mge.EmailField(unique=True, min_length=3, max_length=50)
    login = mge.StringField(unique=True, min_length=3, max_length=50,
                            regex=r'^[a-zA-Z][a-zA-Z0-9_-]*[a-zA-Z0-9]$')
    login_is_set = mge.BooleanField(required=True, default=False)
    gravatar_id = mge.StringField(regex=hexregex)

    def update_gravatar_id(self):
        self.gravatar_id = build_gravatar_id(self.email)

    def set_login(self, login):
        if self.login_is_set:
            raise LoginSetError('login has already been set')

        self.login = login
        self.login_is_set = True

    @classmethod
    def build_user_id(cls, email):
        return sha256hex(email)

    @classmethod
    def get(cls, user_id):
        try:
            return User.objects.get(user_id=user_id)
        except DoesNotExist:
            return None

    @classmethod
    def get_by_login(cls, login):
        try:
            return User.objects.get(login=login)
        except DoesNotExist:
            return None

    @classmethod
    def get_by_email(cls, email):
        return cls.get(cls.build_user_id(email))

    @classmethod
    def get_or_create_by_email(cls, email):
        user_id = cls.build_user_id(email)

        found = False
        for i in range(50):
            login = 'a' + random_md5hex()
            if cls.objects(login=login).count() == 0:
                found = True
                break

        if not found:
            raise Exception('could not generate a temporary login string')

        u = User.objects.get_or_create(email=email,
                                       defaults={'user_id': user_id,
                                                 'email': email,
                                                 'login': login},
                                       auto_save=True)[0]

        if not u.gravatar_id:
            u.update_gravatar_id()
            u.save()
        return u


class Exp(mge.Document, JSONMixin):

    meta = {'ordering': ['name']}

    _jsonable = [('exp_id', 'id'), 'name', 'description', 'owner',
                 'collaborators', 'n_results']
    _jsonable_private = []

    exp_id = mge.StringField(unique=True, regex=hexregex)
    name = mge.StringField(unique_with='owner',
                           min_length=3, max_length=50,
                           regex=r'^[a-zA-Z][a-zA-Z0-9_-]*[a-zA-Z0-9]$')
    owner = mge.ReferenceField('User', required=True, dbref=False)
    description = mge.StringField(max_length=300)
    collaborators = mge.ListField(mge.ReferenceField('User', dbref=False))
    results = mge.ListField(mge.ReferenceField('Result', dbref=False))

    def has_device(self, device):
        return device in [r.device for r in self.results]

    @classmethod
    def build_exp_id(cls, name, owner):
        return sha256hex(owner.user_id + '/' + name)

    @classmethod
    def create(cls, name, owner, description=None, collaborators=None):
        exp_id = cls.build_exp_id(name, owner)
        e = cls(exp_id=exp_id, name=name, owner=owner,
                description=description, collaborators=collaborators)
        e.save()
        return e


class Device(mge.Document, JSONMixin):

    meta = {'ordering': ['device_id']}

    _jsonable = [('device_id', 'id')]
    _jsonable_private = []

    device_id = mge.StringField(unique=True, regex=hexregex)
    vk_pem = mge.StringField(required=True, max_length=5000)

    @classmethod
    def build_device_id(cls, vk_pem):
        return sha256hex(vk_pem)

    @classmethod
    def create(cls, vk_pem):
        device_id = cls.build_device_id(vk_pem)
        d = Device(device_id=device_id, vk_pem=vk_pem)
        d.save()
        return d


class ResultData(mge.DynamicEmbeddedDocument, JSONMixin):

    _jsonable = []
    _jsonable_private = [(r'/^((?!_)[a-zA-Z0-9_]+)$/', r'\1')]


class Result(mge.Document, JSONMixin):

    meta = {'ordering': ['created_at']}

    _jsonable = [('result_id', 'id')]
    _jsonable_private = ['device', 'created_at', 'data']
    _jsonable_private_exp = ['exp']

    result_id = mge.StringField(unique=True, regex=hexregex)
    device = mge.ReferenceField('Device', required=True, dbref=False)
    exp = mge.ReferenceField('Exp', required=True, dbref=False)
    created_at = mge.DateTimeField(required=True)
    data = mge.EmbeddedDocumentField('ResultData', required=True)

    @classmethod
    def build_result_id(cls, device, created_at):
        return sha256hex(device.device_id + '@' +
                         created_at.strftime("%d/%m/%Y-%H:%M:%S"))

    @classmethod
    def create(cls, exp, device, data):
        created_at = datetime.now()
        result_id = cls.build_result_id(device, created_at)
        d = ResultData(**data)
        r = cls(result_id=result_id, device=device, exp=exp,
                created_at=created_at, data=d)
        r.save()
        exp.results.append(r)
        exp.save()
        return r
