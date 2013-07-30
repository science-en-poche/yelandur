# -*- coding: utf-8 -*-

from flask import Flask

from . import create_app, create_apizer, helpers
from .models import User, Exp
from .helpers import APITestCase, client_with_user


# TODO: add CORS test


class ExpsTestCase(APITestCase):

    def setUp(self):
        self.app = create_app('test')
        self.apize = create_apizer(self.app)

        # Bind our helper client to the app
        self.app.test_client_as_user = client_with_user.__get__(self.app,
                                                                Flask)

        # Six test users to work with
        self.jane = User.get_or_create_by_email('jane@example.com')
        self.jane.set_user_id('jane')
        self.sophia = User.get_or_create_by_email('sophia@example.com')
        self.sophia.set_user_id('sophia')
        self.bill = User.get_or_create_by_email('bill@example.com')
        self.bill.set_user_id('bill')
        self.beth = User.get_or_create_by_email('beth@example.com')
        self.beth.set_user_id('beth')
        self.william = User.get_or_create_by_email('william@example.com')
        self.william.set_user_id('william')
        self.ruphus = User.get_or_create_by_email('ruphus@example.com')

        # Experiments to work with
        self.numerical_distance_dict = {
            'exp_id': ('3991cd52745e05f96baff356d82ce3fc'
                       'a48ee0f640422477676da645142c6153'),
            'name': 'numerical-distance',
            'description': 'The numerical distance experiment, on smartphones',
            'owner_id': 'jane',
            'collaborator_ids': ['sophia', 'bill'],
            'n_results': 0,
            'n_profiles': 0,
            'n_devices': 0}
        self.gender_priming_dict = {
            'exp_id': ('3812bfcf957e8534a683a37ffa3d09a9'
                       'db9a797317ac20edc87809711e0d47cb'),
            'name': 'gender-priming',
            'description': 'Controversial gender priming effects',
            'owner_id': 'beth',
            'collaborator_ids': ['william', 'bill'],
            'n_results': 0,
            'n_profiles': 0,
            'n_devices': 0}

    def tearDown(self):
        with self.app.test_request_context():
            helpers.wipe_test_database()

    def create_exps(self):
        Exp.create('numerical-distance', self.jane,
                   'The numerical distance experiment, on smartphones',
                   [self.sophia, self.bill])
        Exp.create('gender-priming', self.beth,
                   'Controversial gender priming effects',
                   [self.william, self.bill])

    def test_root_no_trailing_slash_should_redirect(self):
        resp, status_code = self.get('/exps', self.jane, False)
        # Redirects to '/users/'
        self.assertEqual(status_code, 301)
        self.assertRegexpMatches(resp.headers['Location'],
                                 r'{}$'.format(self.apize('/exps/')))

    def test_root_get(self):
        ## With no exps
        data, status_code = self.get('/exps/')
        self.assertEqual(status_code, 200)
        self.assertEqual([], data['exps'])

        ## Now with some exps
        self.create_exps()

        # As nobody
        data, status_code = self.get('/exps/')
        self.assertEqual(status_code, 200)
        # FIXME: adapt once ordering works
        self.assertIn(self.numerical_distance_dict, data['exps'])
        self.assertIn(self.gender_priming_dict, data['exps'])

        # As jane
        data, status_code = self.get('/exps/', self.jane)
        self.assertEqual(status_code, 200)
        # FIXME: adapt once ordering works
        self.assertIn(self.numerical_distance_dict, data['exps'])
        self.assertIn(self.gender_priming_dict, data['exps'])

        # As jane with ignored 'private' parameter
        data, status_code = self.get('/exps/?access=private', self.jane)
        self.assertEqual(status_code, 200)
        # FIXME: adapt once ordering works
        self.assertIn(self.numerical_distance_dict, data['exps'])
        self.assertIn(self.gender_priming_dict, data['exps'])

    def test_root_post_successful(self):
        pass

    def test_exp_get(self):
        pass
