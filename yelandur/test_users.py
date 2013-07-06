# -*- coding: utf-8 -*-

from contextlib import contextmanager
import json
import unittest

from flask import Flask

from . import create_app, create_apizer, helpers
from .models import User
from .helpers import hexregex


@contextmanager
def client_with_user(app, user):
    with app.test_client() as c:
        if user is not None:
            with c.session_transaction() as session:
                session['user_id'] = user.user_id
        yield c


class UsersTestCase(unittest.TestCase):

    def setUp(self):
        self.app = create_app('test')
        self.apize = create_apizer(self.app)

        # Bind our helper client to the app
        self.app.test_client_as_user = client_with_user.__get__(self.app,
                                                                Flask)

        # Two test users to work with
        self.jane = User.get_or_create_by_email('jane@example.com')
        self.jane.set_user_id('jane')
        self.ruphus = User.get_or_create_by_email('ruphus@example.com')

        # Their corresponding dicts
        self.jane_dict_public = {'user_id': 'jane',
                                 'user_id_is_set': True,
                                 'gravatar_id': ('9e26471d35a78862'
                                                 'c17e467d87cddedf'),
                                 'n_profiles': 0,
                                 'n_devices': 0,
                                 'n_exps': 0,
                                 'n_results': 0}
        self.jane_dict_private = self.jane_dict_public.copy()
        self.jane_dict_private['persona_email'] = 'jane@example.com'
        self.ruphus_dict_public = {'user_id': self.ruphus.user_id,
                                   'user_id_is_set': False,
                                   'gravatar_id': ('441d567f9db81987'
                                                   'ca712fed581d17d9'),
                                   'n_profiles': 0,
                                   'n_devices': 0,
                                   'n_exps': 0,
                                   'n_results': 0}
        self.ruphus_dict_private = self.ruphus_dict_public.copy()
        self.ruphus_dict_private['persona_email'] = 'ruphus@example.com'

        # 401 error dict
        self.error_401_dict = {'status': 'error', 'message': '',
                               'type': 'Unauthorized'}

    def tearDown(self):
        with self.app.test_request_context():
            helpers.wipe_test_database()

    def get(self, url, user=None, load_json=True):
        with self.app.test_client_as_user(user) as c:
            resp = c.get(self.apize(url))
            data = json.loads(resp.data) if load_json else resp
            return data, resp.status_code

    def test_above_base_url(self):
        resp, status_code = self.get('/users', self.jane, False)
        # Redirects to '/users/'
        self.assertEqual(status_code, 301)

    def test_root_get(self):
        # A user with his user_id set
        data, status_code = self.get('/users/', self.jane)
        self.assertEqual(status_code, 200)
        # FIXME: will fail once ordering works
        self.assertEqual(data, {'users': [self.jane_dict_public,
                                          self.ruphus_dict_public]})

        # A user with his user_id not set
        data, status_code = self.get('/users/', self.ruphus)
        self.assertEqual(status_code, 200)
            # FIXME: will fail once ordering works
        self.assertEqual(data, {'users': [self.jane_dict_public,
                                          self.ruphus_dict_public]})

        # Without loging in
        data, status_code = self.get('/users/')
        self.assertEqual(status_code, 200)
        # FIXME: will fail once ordering works
        self.assertEqual(data, {'users': [self.jane_dict_public,
                                          self.ruphus_dict_public]})

    def test_root_get_private(self):
        # TODO
        pass

    def test_me_get(self):
        # A user with his user_id set
        data, status_code = self.get('/users/me', self.jane)
        self.assertEqual(status_code, 200)
        self.assertEqual(data, {'user': self.jane_dict_private})

        # A user with his user_id not set
        data, status_code = self.get('/users/me', self.ruphus)
        self.assertEqual(status_code, 200)
        self.assertEqual(data, {'user': self.ruphus_dict_private})
        self.assertEqual(data['user']['user_id'][:7], 'ruphus-')
        self.assertRegexpMatches(data['user']['user_id'][7:], hexregex)

        # Without logging in
        data, status_code = self.get('/users/me')
        self.assertEqual(status_code, 401)
        self.assertEqual(data, self.error_401_dict)
