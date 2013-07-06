# -*- coding: utf-8 -*-

import unittest
import json

from . import create_app, create_apizer, helpers
from .models import User


class UsersTestCase(unittest.TestCase):

    def setUp(self):
        self.app = create_app('test')
        self.apize = create_apizer(self.app)

        # Two test users to work with
        self.u = User.get_or_create_by_email('jane@example.com')
        self.u.set_user_id('jane')
        self.nu = User.get_or_create_by_email('ruphus@example.com')

    def tearDown(self):
        with self.app.test_request_context():
            helpers.wipe_test_database()

    def test_root(self):
        pass

    def test_me(self):
        with self.app.test_client() as c:
            with c.session_transaction() as session:
                session['user_id'] = self.u.user_id
            resp = c.get(self.apize('/users/me'))
            data = json.loads(resp.data)
            self.assertEqual(data, {'user':
                             {'user_id': 'jane',
                              'user_id_is_set': True,
                              'gravatar_id': ('9e26471d35a78862'
                                              'c17e467d87cddedf'),
                              'n_profiles': 0,
                              'n_devices': 0,
                              'n_exps': 0,
                              'n_results': 0,
                              'persona_email': 'jane@example.com'}})
