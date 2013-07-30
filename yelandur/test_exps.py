# -*- coding: utf-8 -*-

from unittest import skip

from .models import User, Exp
from .helpers import APITestCase


# TODO: add CORS test


class ExpsTestCase(APITestCase):

    def setUp(self):
        super(ExpsTestCase, self).setUp()

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
        self.nd_dict = {'exp_id': ('3991cd52745e05f96baff356d82ce3fc'
                                   'a48ee0f640422477676da645142c6153'),
                        'name': 'numerical-distance',
                        'description': ('The numerical distance '
                                        'experiment, on smartphones'),
                        'owner_id': 'jane',
                        'collaborator_ids': ['sophia', 'bill'],
                        'n_results': 0,
                        'n_profiles': 0,
                        'n_devices': 0}
        self.gp_dict = {'exp_id': ('3812bfcf957e8534a683a37ffa3d09a9'
                                   'db9a797317ac20edc87809711e0d47cb'),
                        'name': 'gender-priming',
                        'description': 'Controversial gender priming effects',
                        'owner_id': 'beth',
                        'collaborator_ids': ['william', 'bill'],
                        'n_results': 0,
                        'n_profiles': 0,
                        'n_devices': 0}
        self.ame_dict = {'exp_id': ('b646639945296429f169a4b93829351a'
                                    '70c92f9cf52095b70a17aa6ab1e2432c'),
                         'name': 'motion-after-effect',
                         'description': 'After motion effects on smartphones',
                         'owner_id': "jane",
                         'collaborator_ids': [],
                         'n_results': 0,
                         'n_profiles': 0}

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
        self.assertIn(self.nd_dict, data['exps'])
        self.assertIn(self.gp_dict, data['exps'])

        # As jane
        data, status_code = self.get('/exps/', self.jane)
        self.assertEqual(status_code, 200)
        # FIXME: adapt once ordering works
        self.assertIn(self.nd_dict, data['exps'])
        self.assertIn(self.gp_dict, data['exps'])

        # As jane with ignored 'private' parameter
        data, status_code = self.get('/exps/?access=private', self.jane)
        self.assertEqual(status_code, 200)
        # FIXME: adapt once ordering works
        self.assertIn(self.nd_dict, data['exps'])
        self.assertIn(self.gp_dict, data['exps'])

    @skip('not implemented yet')
    def test_root_post_successful(self):
        data, status_code = self.post('/exps/',
                                      {'exp':
                                       {'owner_id': 'jane',
                                        'name': 'motion-after-effect',
                                        'description': ('After motion effects '
                                                        'on smartphones')}},
                                      self.jane)
        self.assertEqual(status_code, 201)
        self.assertEqual(data, {'exp': self.ame_dict})

        data, status_code = self.get('/exps/{}'.format(
            self.ame_dict['exp_id']))
        self.assertEqual(status_code, 200)
        self.assertEqual(data, {'exp': self.ame_dict})

    @skip('not implemented yet')
    def test_root_post_successful_ignore_additional_data(self):
        pass

    @skip('not implemented yet')
    def test_root_post_successful_complete_optional_missing_data(self):
        pass

    @skip('not implemented yet')
    def test_root_post_no_authentication(self):
        pass

    @skip('not implemented yet')
    def test_root_post_no_authentication_error_priorities(self):
        pass

    @skip('not implemented yet')
    def test_root_post_malformed(self):
        pass

    @skip('not implemented yet')
    def test_root_post_malformed_error_priorities(self):
        pass

    @skip('not implemented yet')
    def test_root_post_owner_mismatch(self):
        pass

    @skip('not implemented yet')
    def test_root_post_owner_mismatch_error_priorities(self):
        pass

    @skip('not implemented yet')
    def test_root_post_missing_required_field(self):
        pass

    @skip('not implemented yet')
    def test_root_post_missing_required_field_error_priorities(self):
        pass

    @skip('not implemented yet')
    def test_root_post_bad_name_syntax(self):
        pass

    @skip('not implemented yet')
    def test_root_post_bad_name_syntax_error_priorities(self):
        pass

    @skip('not implemented yet')
    def test_root_post_name_already_taken(self):
        pass

    @skip('not implemented yet')
    def test_root_post_name_already_taken_error_priorities(self):
        pass

    def test_exp_get(self):
        ## Non-existing experiment
        # As nodbody
        data, status_code = self.get('/exps/{}'.format(self.nd_dict['exp_id']))
        self.assertEqual(status_code, 404)
        self.assertEqual(data, self.error_404_does_not_exist_dict)

        # As jane
        data, status_code = self.get('/exps/{}'.format(self.nd_dict['exp_id']),
                                     self.jane)
        self.assertEqual(status_code, 404)
        self.assertEqual(data, self.error_404_does_not_exist_dict)

        # As jane with ignored 'private' paramter
        data, status_code = self.get('/exps/{}?access=private'.format(
            self.nd_dict['exp_id']), self.jane)
        self.assertEqual(status_code, 404)
        self.assertEqual(data, self.error_404_does_not_exist_dict)

        ## Now with existing experiments
        self.create_exps()

        # As nobody
        data, status_code = self.get('/exps/{}'.format(self.nd_dict['exp_id']))
        self.assertEqual(status_code, 200)
        self.assertEqual(data, {'exp': self.nd_dict})

        data, status_code = self.get('/exps/{}'.format(self.gp_dict['exp_id']))
        self.assertEqual(status_code, 200)
        self.assertEqual(data, {'exp': self.gp_dict})

        # As jane
        data, status_code = self.get('/exps/{}'.format(self.nd_dict['exp_id']),
                                     self.jane)
        self.assertEqual(status_code, 200)
        self.assertEqual(data, {'exp': self.nd_dict})

        data, status_code = self.get('/exps/{}'.format(self.gp_dict['exp_id']),
                                     self.jane)
        self.assertEqual(status_code, 200)
        self.assertEqual(data, {'exp': self.gp_dict})

        # As jane with ignoredd 'private' parameter
        data, status_code = self.get('/exps/{}?access=private'.format(
            self.nd_dict['exp_id']), self.jane)
        self.assertEqual(status_code, 200)
        self.assertEqual(data, {'exp': self.nd_dict})

        data, status_code = self.get('/exps/{}?access=private'.format(
            self.gp_dict['exp_id']), self.jane)
        self.assertEqual(status_code, 200)
        self.assertEqual(data, {'exp': self.gp_dict})
