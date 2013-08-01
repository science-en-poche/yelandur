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
        self.mae_dict = {'exp_id': ('b646639945296429f169a4b93829351a'
                                    '70c92f9cf52095b70a17aa6ab1e2432c'),
                         'name': 'motion-after-effect',
                         'description': 'After motion effects on smartphones',
                         'owner_id': 'jane',
                         'collaborator_ids': ['beth', 'william'],
                         'n_results': 0,
                         'n_profiles': 0,
                         'n_devices': 0}
        self.mae_completed_defaults_dict = self.mae_dict.copy()
        self.mae_completed_defaults_dict['description'] = ''
        self.mae_completed_defaults_dict['collaborator_ids'] = []

        # 403 owner mismatch dict
        self.error_403_owner_mismatch = {
            'error': {'status_code': 403,
                      'type': 'OwnerMismatch',
                      'message': ('Authenticated user does not match '
                                  'provided owner user_id')}}

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

    def _test_post_successful(self, pexp_dict, rexp_dict, user):
        data, status_code = self.post('/exps/', pexp_dict, user)
        self.assertEqual(status_code, 201)
        self.assertEqual(data, {'exp': rexp_dict})

        data, status_code = self.get('/exps/{}'.format(
            pexp_dict['exp_id']))
        self.assertEqual(status_code, 200)
        self.assertEqual(data, {'exp': rexp_dict})

    @skip('not implemented yet')
    def test_root_post_successful(self):
        self._test_post_mae_successful(
            {'exp':
             {'owner_id': 'jane',
              'name': 'motion-after-effect',
              'description': ('After motion effects '
                              'on smartphones'),
              'collaborator_ids': ['beth', 'william']}},
            self.mae_dict, self.jane)

    @skip('not implemented yet')
    def test_root_post_successful_ignore_additional_data(self):
        self._test_post_mae_successful(
            {'exp':
             {'owner_id': 'jane',
              'name': 'motion-after-effect',
              'description': ('After motion effects '
                              'on smartphones'),
              'collaborator_ids': ['beth', 'william'],
              'something-else': 1234},
             'more-stuff': 'not included'},
            self.mae_dict, self.jane)

    @skip('not implemented yet')
    def test_root_post_successful_complete_optional_missing_data(self):
        self._test_post_mae_successful(
            {'exp':
             {'owner_id': 'jane',
              'name': 'motion-after-effect'}},
            self.mae_completed_defaults, self.jane)

    @skip('not implemented yet')
    def test_root_post_no_authentication(self):
        data, status_code = self.post(
            '/exps/',
            {'exp':
             {'owner_id': 'jane',
              'name': 'motion-after-effect',
              'description': ('After motion effects '
                              'on smartphones'),
              'collaborator_ids': ['beth', 'william']}})
        self.assertEqual(status_code, 401)
        self.assertEqual(data, self.error_401_dict)

    @skip('not implemented yet')
    def test_root_post_no_authentication_error_priorities(self):
        # Malformed JSON
        data, status_code = self.post('/exps/',
                                      '{"Malformed JSON": "bla"',
                                      dump_json_data=False)
        self.assertEqual(status_code, 401)
        self.assertEqual(data, self.error_401_dict)

        # Owner mismatch makes no sense without authentication

        # Owner user_id not set, missing required field (name), unexisting
        # collaborator, collaborator user_id not set, owner in collaborators
        data, status_code = self.post(
            '/exps/',
            {'exp':
             {'owner_id': self.ruphus.user_id,
              'description': ('After motion effects '
                              'on smartphones'),
              'collaborator_ids': ['non-existing', self.ruphus.user_id]}})
        self.assertEqual(status_code, 401)
        self.assertEqual(data, self.error_401_dict)

        # Owner user_id not set, bad name syntax, unexisting collaborator,
        # collaborator user_id not set, owner in collaborators
        data, status_code = self.post(
            '/exps/',
            {'exp':
             {'owner_id': self.ruphus.user_id,
              'name': '-motion-after-effect',
              'description': ('After motion effects '
                              'on smartphones'),
              'collaborator_ids': ['non-existing', self.ruphus.user_id]}})
        self.assertEqual(status_code, 401)
        self.assertEqual(data, self.error_401_dict)

        # Owner user_id not set, name already taken, unexisting collaborator,
        # collaborator user_id not set, owner in collaborators
        self.post('/exps/',
                  {'exp': {'owner': 'jane', 'name': 'taken-name'}},
                  self.jane)
        data, status_code = self.post(
            '/exps/',
            {'exp':
             {'owner_id': self.ruphus.user_id,
              'name': 'taken-name',
              'description': ('After motion effects '
                              'on smartphones'),
              'collaborator_ids': ['non-existing', self.ruphus.user_id]}})
        self.assertEqual(status_code, 401)
        self.assertEqual(data, self.error_401_dict)

        # Missing required field (owner), bad name syntax, unexisting
        # collaborator, collaborator user_id not set (no owner in collaborators
        # since there is no owner)
        data, status_code = self.post(
            '/exps/',
            {'exp':
             {'name': '-motion-after-effect',
              'description': ('After motion effects '
                              'on smartphones'),
              'collaborator_ids': ['non-existing', self.ruphus.user_id]}})
        self.assertEqual(status_code, 401)
        self.assertEqual(data, self.error_401_dict)

        # Missing required field (owner), name already taken, unexisting
        # collaborator, collaborator user_id not set (no owner in collaborators
        # since there is no owner)
        self.post('/exps/',
                  {'exp': {'owner': 'jane', 'name': 'taken-name2'}},
                  self.jane)
        data, status_code = self.post(
            '/exps/',
            {'exp':
             {'name': 'taken-name2',
              'description': ('After motion effects '
                              'on smartphones'),
              'collaborator_ids': ['non-existing', self.ruphus.user_id]}})
        self.assertEqual(status_code, 401)
        self.assertEqual(data, self.error_401_dict)

        # Missing required field (name), unexisting collaborator, collaborator
        # user_id not set, owner in collaborators
        data, status_code = self.post(
            '/exps/',
            {'exp':
             {'owner': 'jane',
              'description': ('After motion effects '
                              'on smartphones'),
              'collaborator_ids': ['non-existing', self.ruphus.user_id]}})
        self.assertEqual(status_code, 401)
        self.assertEqual(data, self.error_401_dict)

        # Bad name synntax, unexisting collaborator, collaborator
        # user_id not set, owner in collaborators
        data, status_code = self.post(
            '/exps/',
            {'exp':
             {'owner': 'jane',
              'name': '-motion-after-effect',
              'description': ('After motion effects '
                              'on smartphones'),
              'collaborator_ids': ['non-existing', self.ruphus.user_id,
                                   'jane']}})
        self.assertEqual(status_code, 401)
        self.assertEqual(data, self.error_401_dict)

        # Name already taken, unexisting collaborator, collaborator
        # user_id not set, owner in collaborators
        self.post('/exps/',
                  {'exp': {'owner': 'jane', 'name': 'taken-name3'}},
                  self.jane)
        data, status_code = self.post(
            '/exps/',
            {'exp':
             {'owner': 'jane',
              'name': 'taken-name3',
              'description': ('After motion effects '
                              'on smartphones'),
              'collaborator_ids': ['non-existing', self.ruphus.user_id,
                                   'jane']}})
        self.assertEqual(status_code, 401)
        self.assertEqual(data, self.error_401_dict)

        # Unexisting collaborator, collaborator user_id not set,
        # owner in collaborators
        data, status_code = self.post(
            '/exps/',
            {'exp':
             {'owner': 'jane',
              'name': 'motion-after-effect',
              'description': ('After motion effects '
                              'on smartphones'),
              'collaborator_ids': ['non-existing', self.ruphus.user_id,
                                   'jane']}})
        self.assertEqual(status_code, 401)
        self.assertEqual(data, self.error_401_dict)

        # Collaborator user_id not set, owner in collaborators
        data, status_code = self.post(
            '/exps/',
            {'exp':
             {'owner': 'jane',
              'name': 'motion-after-effect',
              'description': ('After motion effects '
                              'on smartphones'),
              'collaborator_ids': [self.ruphus.user_id, 'jane']}})
        self.assertEqual(status_code, 401)
        self.assertEqual(data, self.error_401_dict)

        # Owner in collaborators
        data, status_code = self.post(
            '/exps/',
            {'exp':
             {'owner': 'jane',
              'name': 'motion-after-effect',
              'description': ('After motion effects '
                              'on smartphones'),
              'collaborator_ids': ['william', 'jane']}})
        self.assertEqual(status_code, 401)
        self.assertEqual(data, self.error_401_dict)

    @skip('not implemented yet')
    def test_root_post_malformed(self):
        data, status_code = self.post('/exps/',
                                      '{"Malformed JSON": "bla"',
                                      self.jane,
                                      dump_json_data=False)
        self.assertEqual(status_code, 400)
        self.assertEqual(data, self.error_400_malformed_dict)

    # No priority tests for other errors added to malformed JSON since it makes
    # no sense given the errors

    @skip('not implemented yet')
    def test_root_post_owner_mismatch(self):
        data, status_code = self.post(
            '/exps/',
            {'exp':
             {'owner_id': 'jane',
              'name': 'motion-after-effect',
              'description': ('After motion effects '
                              'on smartphones'),
              'collaborator_ids': ['beth', 'william']}},
            self.bill)
        self.assertEqual(status_code, 403)
        self.assertEqual(data, self.error_403_owner_mismatch)

    @skip('not implemented yet')
    def test_root_post_owner_mismatch_error_priorities(self):
        # Owner user_id not set, missing required field (name), unexisting
        # collaborator, collaborator user_id not set, owner in collaborators
        data, status_code = self.post(
            '/exps/',
            {'exp':
             {'owner_id': self.ruphus.user_id,
              'description': ('After motion effects '
                              'on smartphones'),
              'collaborator_ids': ['non-existing', self.ruphus.user_id]}},
            self.bill)
        self.assertEqual(status_code, 403)
        self.assertEqual(data, self.error_403_owner_mismatch)

        # Owner user_id not set, bad name syntax, unexisting collaborator,
        # collaborator user_id not set, owner in collaborators
        data, status_code = self.post(
            '/exps/',
            {'exp':
             {'owner_id': self.ruphus.user_id,
              'name': '-motion-after-effect',
              'description': ('After motion effects '
                              'on smartphones'),
              'collaborator_ids': ['non-existing', self.ruphus.user_id]}},
            self.bill)
        self.assertEqual(status_code, 403)
        self.assertEqual(data, self.error_403_owner_mismatch)

        # Owner user_id not set, name already taken, unexisting collaborator,
        # collaborator user_id not set, owner in collaborators
        self.post('/exps/',
                  {'exp': {'owner': 'jane', 'name': 'taken-name'}},
                  self.jane)
        data, status_code = self.post(
            '/exps/',
            {'exp':
             {'owner_id': self.ruphus.user_id,
              'name': 'taken-name',
              'description': ('After motion effects '
                              'on smartphones'),
              'collaborator_ids': ['non-existing', self.ruphus.user_id]}},
            self.bill)
        self.assertEqual(status_code, 403)
        self.assertEqual(data, self.error_403_owner_mismatch)

        # Missing required field (name), unexisting collaborator, collaborator
        # user_id not set, owner in collaborators
        data, status_code = self.post(
            '/exps/',
            {'exp':
             {'owner': 'jane',
              'description': ('After motion effects '
                              'on smartphones'),
              'collaborator_ids': ['non-existing', self.ruphus.user_id,
                                   'jane']}},
            self.bill)
        self.assertEqual(status_code, 403)
        self.assertEqual(data, self.error_403_owner_mismatch)

        # Bad name synntax, unexisting collaborator, collaborator
        # user_id not set, owner in collaborators
        data, status_code = self.post(
            '/exps/',
            {'exp':
             {'owner': 'jane',
              'name': '-motion-after-effect',
              'description': ('After motion effects '
                              'on smartphones'),
              'collaborator_ids': ['non-existing', self.ruphus.user_id,
                                   'jane']}},
            self.bill)
        self.assertEqual(status_code, 403)
        self.assertEqual(data, self.error_403_owner_mismatch)

        # Name already taken, unexisting collaborator, collaborator
        # user_id not set, owner in collaborators
        self.post('/exps/',
                  {'exp': {'owner': 'jane', 'name': 'taken-name2'}},
                  self.jane)
        data, status_code = self.post(
            '/exps/',
            {'exp':
             {'owner': 'jane',
              'name': 'taken-name2',
              'description': ('After motion effects '
                              'on smartphones'),
              'collaborator_ids': ['non-existing', self.ruphus.user_id,
                                   'jane']}},
            self.bill)
        self.assertEqual(status_code, 403)
        self.assertEqual(data, self.error_403_owner_mismatch)

        # Unexisting collaborator, collaborator user_id not set,
        # owner in collaborators
        data, status_code = self.post(
            '/exps/',
            {'exp':
             {'owner': 'jane',
              'name': 'motion-after-effect',
              'description': ('After motion effects '
                              'on smartphones'),
              'collaborator_ids': ['non-existing', self.ruphus.user_id,
                                   'jane']}},
            self.bill)
        self.assertEqual(status_code, 403)
        self.assertEqual(data, self.error_403_owner_mismatch)

        # Collaborator user_id not set, owner in collaborators
        data, status_code = self.post(
            '/exps/',
            {'exp':
             {'owner': 'jane',
              'name': 'motion-after-effect',
              'description': ('After motion effects '
                              'on smartphones'),
              'collaborator_ids': [self.ruphus.user_id, 'jane']}},
            self.bill)
        self.assertEqual(status_code, 403)
        self.assertEqual(data, self.error_403_owner_mismatch)

        # Owner in collaborators
        data, status_code = self.post(
            '/exps/',
            {'exp':
             {'owner': 'jane',
              'name': 'motion-after-effect',
              'description': ('After motion effects '
                              'on smartphones'),
              'collaborator_ids': ['william', 'jane']}},
            self.bill)
        self.assertEqual(status_code, 403)
        self.assertEqual(data, self.error_403_owner_mismatch)

    @skip('not implemented yet')
    def test_root_post_owner_user_id_not_set(self):
        pass

    @skip('not implemented yet')
    def test_root_post_owner_user_id_not_set_error_priorities(self):
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

    @skip('not implemented yet')
    def test_root_post_unexisting_collaborator(self):
        pass

    @skip('not implemented yet')
    def test_root_post_unexisting_collaborator_error_priorities(self):
        pass

    @skip('not implemented yet')
    def test_root_post_collaborator_user_id_not_set(self):
        pass

    @skip('not implemented yet')
    def test_root_post_collaborator_user_id_not_set_error_priorities(self):
        pass

    @skip('not implemented yet')
    def test_root_post_owner_in_collaborators(self):
        pass

    @skip('not implemented yet')
    def test_root_post_owner_in_collaborators_error_priorities(self):
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
