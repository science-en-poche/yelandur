# -*- coding: utf-8 -*-

from contextlib import contextmanager
import json
import unittest

from flask import Flask

from . import create_app, create_apizer, helpers
from .models import User, Exp
from .helpers import hexregex


@contextmanager
def client_with_user(app, user):
    with app.test_client() as c:
        if user is not None:
            with c.session_transaction() as session:
                session['user_id'] = user.user_id
        yield c


class UsersTestCase(unittest.TestCase):

    maxDiff = None

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
        self.ruphus_dict_private_with_user_id = self.ruphus_dict_private.copy()
        self.ruphus_dict_private_with_user_id['user_id'] = 'ruphus'
        self.ruphus_dict_private_with_user_id['user_id_is_set'] = True

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

    def tearDown(self):
        with self.app.test_request_context():
            helpers.wipe_test_database()

    def get(self, url, user=None, load_json=True):
        with self.app.test_client_as_user(user) as c:
            resp = c.get(self.apize(url))
            data = json.loads(resp.data) if load_json else resp
            return data, resp.status_code

    def test_root_no_trailing_slash_should_redirect(self):
        resp, status_code = self.get('/users', self.jane, False)
        # Redirects to '/users/'
        self.assertEqual(status_code, 301)
        self.assertRegexpMatches(resp.headers['Location'],
                                 r'{}$'.format(self.apize('/users/')))

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
        # As Jane
        data, status_code = self.get('/users/?access=private',
                                     self.jane)
        self.assertEqual(status_code, 200)
        self.assertEqual(data, {'users': [self.jane_dict_private]})

        # As Ruphus
        data, status_code = self.get('/users/?access=private',
                                     self.ruphus)
        self.assertEqual(status_code, 200)
        self.assertEqual(data, {'users': [self.ruphus_dict_private]})

        # Without authentication
        data, status_code = self.get('/users/?access=private')
        self.assertEqual(status_code, 401)
        self.assertEqual(data, self.error_401_dict)

    def test_root_get_private_collaborators(self):
        # Now creating an experiment with Ruphus as a collaborator for
        # Jane (meaning Ruphus must have his user_id set)
        self.ruphus.set_user_id('ruphus')
        Exp.create('test-exp', self.jane, collaborators=[self.ruphus])
        self.jane_dict_public['n_exps'] = 1
        self.jane_dict_private['n_exps'] = 1
        self.ruphus_dict_public['n_exps'] = 1
        self.ruphus_dict_private['n_exps'] = 1
        self.ruphus_dict_private_with_user_id['n_exps'] = 1

        # Add a user to make sure the following answers aren't just
        # including all available users
        u = User.get_or_create_by_email('temp@example.com')
        u.set_user_id('temp')

        # Jane sees both herself and Ruphus
        data, status_code = self.get('/users/?access=private',
                                     self.jane)
        self.assertEqual(status_code, 200)
        # FIXME: will fail once ordering works
        self.assertIn(self.jane_dict_private, data['users'])
        self.assertIn(self.ruphus_dict_private_with_user_id, data['users'])

        # Ruphus sees both himself and Jane
        data, status_code = self.get('/users/?access=private',
                                     self.ruphus)
        self.assertEqual(status_code, 200)
        # FIXME: will fail once ordering works
        self.assertIn(self.jane_dict_private, data['users'])
        self.assertIn(self.ruphus_dict_private_with_user_id, data['users'])

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

    def test_user_get(self):
        # A user with user_id set
        data, status_code = self.get('/users/jane', self.jane)
        self.assertEqual(status_code, 200)
        self.assertEqual(data, {'user': self.jane_dict_public})

        # A user with user_id not set
        data, status_code = self.get('/users/{}'.format(self.ruphus.user_id),
                                     self.jane)
        self.assertEqual(status_code, 200)
        self.assertEqual(data, {'user': self.ruphus_dict_public})

        # A non-existing user
        data, status_code = self.get('/users/seb', self.jane)
        self.assertEqual(status_code, 404)
        self.assertEqual(data, self.error_404_does_not_exist_dict)

        ## Now without authentication

        # A user with user_id set
        data, status_code = self.get('/users/jane')
        self.assertEqual(status_code, 200)
        self.assertEqual(data, {'user': self.jane_dict_public})

        # A user with user_id not set
        data, status_code = self.get('/users/{}'.format(self.ruphus.user_id))
        self.assertEqual(status_code, 200)
        self.assertEqual(data, {'user': self.ruphus_dict_public})

        # A non-existing user
        data, status_code = self.get('/users/seb')
        self.assertEqual(status_code, 404)
        self.assertEqual(data, self.error_404_does_not_exist_dict)

    def test_user_get_private(self):
        # A user with user_id set
        data, status_code = self.get('/users/jane?access=private', self.jane)
        self.assertEqual(status_code, 200)
        self.assertEqual(data, {'user': self.jane_dict_private})

        # A user with user_id not set
        data, status_code = self.get('/users/{}?access=private'.format(
            self.ruphus.user_id), self.jane)
        self.assertEqual(status_code, 403)
        self.assertEqual(data, self.error_403_unauthorized_dict)

        # A non-existing user
        data, status_code = self.get('/users/seb?access=private',
                                     self.jane)
        self.assertEqual(status_code, 404)
        self.assertEqual(data, self.error_404_does_not_exist_dict)

        ## Now without authentication

        # A user with user_id set
        data, status_code = self.get('/users/jane?access=private')
        self.assertEqual(status_code, 401)
        self.assertEqual(data, self.error_401_dict)

        # A user with user_id not set
        data, status_code = self.get('/users/{}?access=private'.format(
            self.ruphus.user_id))
        self.assertEqual(status_code, 401)
        self.assertEqual(data, self.error_401_dict)

        # A non-existing user
        data, status_code = self.get('/users/seb?access=private')
        self.assertEqual(status_code, 404)
        self.assertEqual(data, self.error_404_does_not_exist_dict)

        ## Finally, an authenticated user has access to his
        ## collaborators

        self.ruphus.set_user_id('ruphus')
        Exp.create('test-exp', self.jane, collaborators=[self.ruphus])
        self.jane_dict_public['n_exps'] = 1
        self.jane_dict_private['n_exps'] = 1
        self.ruphus_dict_public['n_exps'] = 1
        self.ruphus_dict_private['n_exps'] = 1
        self.ruphus_dict_private_with_user_id['n_exps'] = 1

        data, status_code = self.get('/users/ruphus?access=private',
                                     self.jane)
        self.assertEqual(status_code, 200)
        self.assertEqual(data,
                         {'user': self.ruphus_dict_private_with_user_id})

        data, status_code = self.get('/users/jane?access=private',
                                     self.ruphus)
        self.assertEqual(status_code, 200)
        self.assertEqual(data, {'user': self.jane_dict_private})
