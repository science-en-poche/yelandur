# -*- coding: utf-8 -*-

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
        self.nd_dict = {'id': ('3991cd52745e05f96baff356d82ce3fc'
                               'a48ee0f640422477676da645142c6153'),
                        'name': 'numerical-distance',
                        'description': ('The numerical distance '
                                        'experiment, on smartphones'),
                        'owner_id': 'jane',
                        'collaborator_ids': ['sophia', 'bill'],
                        'n_results': 0,
                        'n_profiles': 0,
                        'n_devices': 0}
        self.gp_dict = {'id': ('3812bfcf957e8534a683a37ffa3d09a9'
                               'db9a797317ac20edc87809711e0d47cb'),
                        'name': 'gender-priming',
                        'description': 'Controversial gender priming effects',
                        'owner_id': 'beth',
                        'collaborator_ids': ['william', 'bill'],
                        'n_results': 0,
                        'n_profiles': 0,
                        'n_devices': 0}
        self.mae_dict = {'id': ('b646639945296429f169a4b93829351a'
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
        self.error_403_owner_mismatch_dict = {
            'error': {'status_code': 403,
                      'type': 'OwnerMismatch',
                      'message': ('Authenticated user does not match '
                                  'provided owner user_id')}}

        # 400 collaborator not found
        self.error_400_collaborator_not_found_dict = {
            'error': {'status_code': 400,
                      'type': 'CollaboratorNotFound',
                      'message': ('One of the claimed collaborators '
                                  'was not found')}}

        # 403 owner user_id not set dict
        self.error_403_owner_user_id_not_set_dict = {
            'error': {'status_code': 403,
                      'type': 'OwnerUserIdNotSet',
                      'message': "Owner's user_id is not set"}}

        # 400 collaborator user_id not set dict
        self.error_400_collaborator_user_id_not_set_dict = {
            'error': {'status_code': 400,
                      'type': 'CollaboratorUserIdNotSet',
                      'message': ("A collaborator's "
                                  'user_id is not set')}}

        # 400 owner in collaborators
        self.error_400_owner_in_collaborators = {
            'error': {'status_code': 400,
                      'type': 'OwnerInCollaborators',
                      'message': ('The owner is also one '
                                  'of the collaborators')}}

    def create_exps(self):
        Exp.create('numerical-distance', self.jane,
                   'The numerical distance experiment, on smartphones',
                   [self.sophia, self.bill])
        Exp.create('gender-priming', self.beth,
                   'Controversial gender priming effects',
                   [self.william, self.bill])

    def test_root_no_trailing_slash_should_redirect(self):
        resp, status_code = self.get('/exps', self.jane, False)
        # Redirects to '/exps/'
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
        self.assertEqual(data.keys(), ['exps'])
        self.assertIn(self.nd_dict, data['exps'])
        self.assertIn(self.gp_dict, data['exps'])
        self.assertEqual(len(data['exps']), 2)

        # As jane
        data, status_code = self.get('/exps/', self.jane)
        self.assertEqual(status_code, 200)
        # FIXME: adapt once ordering works
        self.assertEqual(data.keys(), ['exps'])
        self.assertIn(self.nd_dict, data['exps'])
        self.assertIn(self.gp_dict, data['exps'])
        self.assertEqual(len(data['exps']), 2)

        # As jane with ignored 'private' parameter
        data, status_code = self.get('/exps/?access=private', self.jane)
        self.assertEqual(status_code, 200)
        # FIXME: adapt once ordering works
        self.assertEqual(data.keys(), ['exps'])
        self.assertIn(self.nd_dict, data['exps'])
        self.assertIn(self.gp_dict, data['exps'])
        self.assertEqual(len(data['exps']), 2)

    def _test_post_successful(self, pexp_dict, rexp_dict, user):
        # User has no exps
        data, status_code = self.get('/users/{}'.format(
            rexp_dict['owner_id']))
        self.assertEqual(status_code, 200)
        self.assertEqual(data['user']['exp_ids'], [])

        # Add the exp
        data, status_code = self.post('/exps/', pexp_dict, user)
        self.assertEqual(status_code, 201)
        self.assertEqual(data, {'exp': rexp_dict})

        # The exp exists
        data, status_code = self.get('/exps/{}'.format(
            rexp_dict['id']))
        self.assertEqual(status_code, 200)
        self.assertEqual(data, {'exp': rexp_dict})

        # The exp is counted in the user's exps
        data, status_code = self.get('/users/{}'.format(
            rexp_dict['owner_id']))
        self.assertEqual(status_code, 200)
        self.assertEqual(data['user']['exp_ids'], [rexp_dict['id']])

        # And it's in the collaborators' exps
        for cid in pexp_dict.get('collaborator_ids', []):
            data, status_code = self.get('/users/{}'.format(cid))
            self.assertEqual(status_code, 200)
            self.assertEqual(data['user']['exp_ids'], [rexp_dict['id']])

    def test_root_post_successful(self):
        self._test_post_successful(
            {'exp':
             {'owner_id': 'jane',
              'name': 'motion-after-effect',
              'description': ('After motion effects '
                              'on smartphones'),
              'collaborator_ids': ['beth', 'william']}},
            self.mae_dict, self.jane)

    def test_root_post_successful_ignore_additional_data(self):
        self._test_post_successful(
            {'exp':
             {'owner_id': 'jane',
              'name': 'motion-after-effect',
              'description': ('After motion effects '
                              'on smartphones'),
              'collaborator_ids': ['beth', 'william'],
              'something-else': 1234},
             'more-stuff': 'not included'},
            self.mae_dict, self.jane)

    def test_root_post_successful_complete_optional_missing_data(self):
        self._test_post_successful(
            {'exp':
             {'owner_id': 'jane',
              'name': 'motion-after-effect'}},
            self.mae_completed_defaults_dict, self.jane)

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

    def test_root_post_no_authentication_error_priorities(self):
        # Malformed JSON
        data, status_code = self.post('/exps/',
                                      '{"Malformed JSON": "bla"',
                                      dump_json_data=False)
        self.assertEqual(status_code, 401)
        self.assertEqual(data, self.error_401_dict)

        # Good JSON but no 'exp' root object
        data, status_code = self.post('/exps/',
                                      {'not-exp': 'bla'})
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

        # Owner user_id not set, unexisting collaborator, collaborator
        # user_id not set, owner in collaborators, bad name syntax
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

        # Owner user_id not set, unexisting collaborator, collaborator
        # user_id not set, owner in collaborators, name already taken
        Exp.create('numerical-distance', self.jane,
                   'The numerical distance experiment, on smartphones',
                   [self.sophia, self.bill])
        data, status_code = self.post(
            '/exps/',
            {'exp':
             {'owner_id': self.ruphus.user_id,
              'name': 'numerical-distance',
              'description': ('After motion effects '
                              'on smartphones'),
              'collaborator_ids': ['non-existing', self.ruphus.user_id]}})
        self.assertEqual(status_code, 401)
        self.assertEqual(data, self.error_401_dict)

        # Missing required field (owner), unexisting collaborator,
        # collaborator user_id not set (no owner in collaborators
        # since there is no owner), bad name syntax
        data, status_code = self.post(
            '/exps/',
            {'exp':
             {'name': '-motion-after-effect',
              'description': ('After motion effects '
                              'on smartphones'),
              'collaborator_ids': ['non-existing', self.ruphus.user_id]}})
        self.assertEqual(status_code, 401)
        self.assertEqual(data, self.error_401_dict)

        # Missing required field (owner), unexisting collaborator,
        # collaborator user_id not set (no owner in collaborators
        # since there is no owner), name already taken
        data, status_code = self.post(
            '/exps/',
            {'exp':
             {'name': 'numerical-distance',
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
             {'owner_id': 'jane',
              'description': ('After motion effects '
                              'on smartphones'),
              'collaborator_ids': ['non-existing', self.ruphus.user_id]}})
        self.assertEqual(status_code, 401)
        self.assertEqual(data, self.error_401_dict)

        # Unexisting collaborator, collaborator user_id not set, owner in
        # collaborators, bad name syntax
        data, status_code = self.post(
            '/exps/',
            {'exp':
             {'owner_id': 'jane',
              'name': '-motion-after-effect',
              'description': ('After motion effects '
                              'on smartphones'),
              'collaborator_ids': ['non-existing', self.ruphus.user_id,
                                   'jane']}})
        self.assertEqual(status_code, 401)
        self.assertEqual(data, self.error_401_dict)

        # Unexisting collaborator, collaborator user_id not set, owner in
        # collaborators, name already taken
        data, status_code = self.post(
            '/exps/',
            {'exp':
             {'owner_id': 'jane',
              'name': 'numerical-distance',
              'description': ('After motion effects '
                              'on smartphones'),
              'collaborator_ids': ['non-existing', self.ruphus.user_id,
                                   'jane']}})
        self.assertEqual(status_code, 401)
        self.assertEqual(data, self.error_401_dict)

        # Collaborator user_id not set, owner in collaborators,
        # bad name syntax
        data, status_code = self.post(
            '/exps/',
            {'exp':
             {'owner_id': 'jane',
              'name': '-motion-after-effect',
              'description': ('After motion effects '
                              'on smartphones'),
              'collaborator_ids': [self.ruphus.user_id, 'jane']}})
        self.assertEqual(status_code, 401)
        self.assertEqual(data, self.error_401_dict)

        # Collaborator user_id not set, owner in collaborators,
        # name already taken
        data, status_code = self.post(
            '/exps/',
            {'exp':
             {'owner_id': 'jane',
              'name': 'numerical-distance',
              'description': ('After motion effects '
                              'on smartphones'),
              'collaborator_ids': [self.ruphus.user_id, 'jane']}})
        self.assertEqual(status_code, 401)
        self.assertEqual(data, self.error_401_dict)

        # Owner in collaborators, bad name syntax
        data, status_code = self.post(
            '/exps/',
            {'exp':
             {'owner_id': 'jane',
              'name': '-motion-after-effect',
              'description': ('After motion effects '
                              'on smartphones'),
              'collaborator_ids': ['william', 'jane']}})
        self.assertEqual(status_code, 401)
        self.assertEqual(data, self.error_401_dict)

        # Owner in collaborators, name already taken
        data, status_code = self.post(
            '/exps/',
            {'exp':
             {'owner_id': 'jane',
              'name': 'numerical-distance',
              'description': ('After motion effects '
                              'on smartphones'),
              'collaborator_ids': ['william', 'jane']}})
        self.assertEqual(status_code, 401)
        self.assertEqual(data, self.error_401_dict)

        # Bad name syntax
        data, status_code = self.post(
            '/exps/',
            {'exp':
             {'owner_id': 'jane',
              'name': '-motion-after-effect',
              'description': ('After motion effects '
                              'on smartphones'),
              'collaborator_ids': ['beth', 'william']}})
        self.assertEqual(status_code, 401)
        self.assertEqual(data, self.error_401_dict)

        # Name already taken
        data, status_code = self.post(
            '/exps/',
            {'exp':
             {'owner_id': 'jane',
              'name': 'numerical-distance',
              'description': ('After motion effects '
                              'on smartphones'),
              'collaborator_ids': ['beth', 'william']}})
        self.assertEqual(status_code, 401)
        self.assertEqual(data, self.error_401_dict)

    def test_root_post_malformed(self):
        # Bad JSON
        data, status_code = self.post('/exps/',
                                      '{"Malformed JSON": "bla"',
                                      self.jane,
                                      dump_json_data=False)
        self.assertEqual(status_code, 400)
        self.assertEqual(data, self.error_400_malformed_dict)

        # Good JSON but no 'exp' root object
        data, status_code = self.post('/exps/',
                                      {'not-exp': 'bla'},
                                      self.jane)
        self.assertEqual(status_code, 400)
        self.assertEqual(data, self.error_400_malformed_dict)

    # No priority tests for other errors added to malformed JSON since it makes
    # no sense given the errors

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
        self.assertEqual(data, self.error_403_owner_mismatch_dict)

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
        self.assertEqual(data, self.error_403_owner_mismatch_dict)

        # Owner user_id not set, unexisting collaborator, collaborator
        # user_id not set, owner in collaborators, bad name syntax
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
        self.assertEqual(data, self.error_403_owner_mismatch_dict)

        # Owner user_id not set, unexisting collaborator, collaborator
        # user_id not set, owner in collaborators, name already taken
        Exp.create('numerical-distance', self.jane,
                   'The numerical distance experiment, on smartphones',
                   [self.sophia, self.bill])
        data, status_code = self.post(
            '/exps/',
            {'exp':
             {'owner_id': self.ruphus.user_id,
              'name': 'numerical-distance',
              'description': ('After motion effects '
                              'on smartphones'),
              'collaborator_ids': ['non-existing', self.ruphus.user_id]}},
            self.bill)
        self.assertEqual(status_code, 403)
        self.assertEqual(data, self.error_403_owner_mismatch_dict)

        # Missing required field (name), unexisting collaborator, collaborator
        # user_id not set, owner in collaborators
        data, status_code = self.post(
            '/exps/',
            {'exp':
             {'owner_id': 'jane',
              'description': ('After motion effects '
                              'on smartphones'),
              'collaborator_ids': ['non-existing', self.ruphus.user_id,
                                   'jane']}},
            self.bill)
        self.assertEqual(status_code, 403)
        self.assertEqual(data, self.error_403_owner_mismatch_dict)

        # Unexisting collaborator, collaborator user_id not set,
        # owner in collaborators, bad name syntax
        data, status_code = self.post(
            '/exps/',
            {'exp':
             {'owner_id': 'jane',
              'name': '-motion-after-effect',
              'description': ('After motion effects '
                              'on smartphones'),
              'collaborator_ids': ['non-existing', self.ruphus.user_id,
                                   'jane']}},
            self.bill)
        self.assertEqual(status_code, 403)
        self.assertEqual(data, self.error_403_owner_mismatch_dict)

        # Unexisting collaborator, collaborator user_id not set,
        # owner in collaborators, name already taken
        data, status_code = self.post(
            '/exps/',
            {'exp':
             {'owner_id': 'jane',
              'name': 'numerical-distance',
              'description': ('After motion effects '
                              'on smartphones'),
              'collaborator_ids': ['non-existing', self.ruphus.user_id,
                                   'jane']}},
            self.bill)
        self.assertEqual(status_code, 403)
        self.assertEqual(data, self.error_403_owner_mismatch_dict)

        # Collaborator user_id not set, owner in collaborators,
        # bad name syntax
        data, status_code = self.post(
            '/exps/',
            {'exp':
             {'owner_id': 'jane',
              'name': '-motion-after-effect',
              'description': ('After motion effects '
                              'on smartphones'),
              'collaborator_ids': [self.ruphus.user_id, 'jane']}},
            self.bill)
        self.assertEqual(status_code, 403)
        self.assertEqual(data, self.error_403_owner_mismatch_dict)

        # Collaborator user_id not set, owner in collaborators,
        # name already taken
        data, status_code = self.post(
            '/exps/',
            {'exp':
             {'owner_id': 'jane',
              'name': 'numerical-distance',
              'description': ('After motion effects '
                              'on smartphones'),
              'collaborator_ids': [self.ruphus.user_id, 'jane']}},
            self.bill)
        self.assertEqual(status_code, 403)
        self.assertEqual(data, self.error_403_owner_mismatch_dict)

        # Owner in collaborators, bad name syntax
        data, status_code = self.post(
            '/exps/',
            {'exp':
             {'owner_id': 'jane',
              'name': '-motion-after-effect',
              'description': ('After motion effects '
                              'on smartphones'),
              'collaborator_ids': ['william', 'jane']}},
            self.bill)
        self.assertEqual(status_code, 403)
        self.assertEqual(data, self.error_403_owner_mismatch_dict)

        # Owner in collaborators, name already taken
        data, status_code = self.post(
            '/exps/',
            {'exp':
             {'owner_id': 'jane',
              'name': 'numerical-distance',
              'description': ('After motion effects '
                              'on smartphones'),
              'collaborator_ids': ['william', 'jane']}},
            self.bill)
        self.assertEqual(status_code, 403)
        self.assertEqual(data, self.error_403_owner_mismatch_dict)

        # Bad name syntax
        data, status_code = self.post(
            '/exps/',
            {'exp':
             {'owner_id': 'jane',
              'name': '-motion-after-effect',
              'description': ('After motion effects '
                              'on smartphones'),
              'collaborator_ids': ['beth', 'william']}},
            self.bill)
        self.assertEqual(status_code, 403)
        self.assertEqual(data, self.error_403_owner_mismatch_dict)

        # Name already taken
        data, status_code = self.post(
            '/exps/',
            {'exp':
             {'owner_id': 'jane',
              'name': 'numerical-distance',
              'description': ('After motion effects '
                              'on smartphones'),
              'collaborator_ids': ['beth', 'william']}},
            self.bill)
        self.assertEqual(status_code, 403)
        self.assertEqual(data, self.error_403_owner_mismatch_dict)

    def test_root_post_owner_user_id_not_set(self):
        data, status_code = self.post(
            '/exps/',
            {'exp':
             {'owner_id': self.ruphus.user_id,
              'name': 'motion-after-effect',
              'description': ('After motion effects '
                              'on smartphones'),
              'collaborator_ids': ['beth', 'william']}},
            self.ruphus)
        self.assertEqual(status_code, 403)
        self.assertEqual(data, self.error_403_owner_user_id_not_set_dict)

    def test_root_post_owner_user_id_not_set_error_priorities(self):
        # Missing required field (name), unexisting collaborator, collaborator
        # user_id not set, owner in collaborators
        data, status_code = self.post(
            '/exps/',
            {'exp':
             {'owner_id': self.ruphus.user_id,
              'description': ('After motion effects '
                              'on smartphones'),
              'collaborator_ids': ['non-existing', self.ruphus.user_id]}},
            self.ruphus)
        self.assertEqual(status_code, 403)
        self.assertEqual(data, self.error_403_owner_user_id_not_set_dict)

        # Unexisting collaborator, collaborator user_id not set, owner in
        # collaborators, bad name syntax
        data, status_code = self.post(
            '/exps/',
            {'exp':
             {'owner_id': self.ruphus.user_id,
              'name': '-motion-after-effect',
              'description': ('After motion effects '
                              'on smartphones'),
              'collaborator_ids': ['non-existing', self.ruphus.user_id]}},
            self.ruphus)
        self.assertEqual(status_code, 403)
        self.assertEqual(data, self.error_403_owner_user_id_not_set_dict)

        # Unexisting collaborator, collaborator user_id not set, owner in
        # collaborators, name already taken
        Exp.create('numerical-distance', self.jane,
                   'The numerical distance experiment, on smartphones',
                   [self.sophia, self.bill])
        data, status_code = self.post(
            '/exps/',
            {'exp':
             {'owner_id': self.ruphus.user_id,
              'name': 'numerical-distance',
              'description': ('After motion effects '
                              'on smartphones'),
              'collaborator_ids': ['non-existing', self.ruphus.user_id]}},
            self.ruphus)
        self.assertEqual(status_code, 403)
        self.assertEqual(data, self.error_403_owner_user_id_not_set_dict)

        # Collaborator user_id not set, owner in collaborators,
        # bad name syntax
        data, status_code = self.post(
            '/exps/',
            {'exp':
             {'owner_id': self.ruphus.user_id,
              'name': '-motion-after-effect',
              'description': ('After motion effects '
                              'on smartphones'),
              'collaborator_ids': ['william', self.ruphus.user_id]}},
            self.ruphus)
        self.assertEqual(status_code, 403)
        self.assertEqual(data, self.error_403_owner_user_id_not_set_dict)

        # Collaborator user_id not set, owner in collaborators,
        # name already taken
        data, status_code = self.post(
            '/exps/',
            {'exp':
             {'owner_id': self.ruphus.user_id,
              'name': 'numerical-distance',
              'description': ('After motion effects '
                              'on smartphones'),
              'collaborator_ids': ['william', self.ruphus.user_id]}},
            self.ruphus)
        self.assertEqual(status_code, 403)
        self.assertEqual(data, self.error_403_owner_user_id_not_set_dict)

        # Owner in collaborators, bad name syntax (this is the same as
        # the above case)
        data, status_code = self.post(
            '/exps/',
            {'exp':
             {'owner_id': self.ruphus.user_id,
              'name': '-motion-after-effect',
              'description': ('After motion effects '
                              'on smartphones'),
              'collaborator_ids': ['william', self.ruphus.user_id]}},
            self.ruphus)
        self.assertEqual(status_code, 403)
        self.assertEqual(data, self.error_403_owner_user_id_not_set_dict)

        # Owner in collaborators, name already taken
        data, status_code = self.post(
            '/exps/',
            {'exp':
             {'owner_id': self.ruphus.user_id,
              'name': 'numerical-distance',
              'description': ('After motion effects '
                              'on smartphones'),
              'collaborator_ids': ['william', self.ruphus.user_id]}},
            self.ruphus)
        self.assertEqual(status_code, 403)
        self.assertEqual(data, self.error_403_owner_user_id_not_set_dict)

        # Bad name syntax
        data, status_code = self.post(
            '/exps/',
            {'exp':
             {'owner_id': self.ruphus.user_id,
              'name': '-motion-after-effect',
              'description': ('After motion effects '
                              'on smartphones'),
              'collaborator_ids': ['beth', 'william']}},
            self.ruphus)
        self.assertEqual(status_code, 403)
        self.assertEqual(data, self.error_403_owner_user_id_not_set_dict)

        # Name already taken
        data, status_code = self.post(
            '/exps/',
            {'exp':
             {'owner_id': self.ruphus.user_id,
              'name': 'numerical-distance',
              'description': ('After motion effects '
                              'on smartphones'),
              'collaborator_ids': ['beth', 'william']}},
            self.ruphus)
        self.assertEqual(status_code, 403)
        self.assertEqual(data, self.error_403_owner_user_id_not_set_dict)

    def test_root_post_missing_required_field(self):
        # Missing name
        data, status_code = self.post(
            '/exps/',
            {'exp':
             {'owner_id': 'jane',
              'description': ('After motion effects '
                              'on smartphones'),
              'collaborator_ids': ['beth', 'william']}},
            self.jane)
        self.assertEqual(status_code, 400)
        self.assertEqual(data, self.error_400_missing_requirement_dict)

        # Missing owner
        data, status_code = self.post(
            '/exps/',
            {'exp':
             {'name': 'motion-after-effect',
              'description': ('After motion effects '
                              'on smartphones'),
              'collaborator_ids': ['beth', 'william']}},
            self.jane)
        self.assertEqual(status_code, 400)
        self.assertEqual(data, self.error_400_missing_requirement_dict)

    def test_root_post_missing_required_field_error_priorities(self):
        ## Missing name

        # Unexisting collaborator, collaborator user_id not set,
        # owner in collaborators
        data, status_code = self.post(
            '/exps/',
            {'exp':
             {'owner_id': 'jane',
              'description': ('After motion effects '
                              'on smartphones'),
              'collaborator_ids': ['non-existing', self.ruphus.user_id,
                                   'jane']}},
            self.jane)
        self.assertEqual(status_code, 400)
        self.assertEqual(data, self.error_400_missing_requirement_dict)

        # Collaborator user_id not set, owner in collaborators
        data, status_code = self.post(
            '/exps/',
            {'exp':
             {'owner_id': 'jane',
              'description': ('After motion effects '
                              'on smartphones'),
              'collaborator_ids': [self.ruphus.user_id, 'jane']}},
            self.jane)
        self.assertEqual(status_code, 400)
        self.assertEqual(data, self.error_400_missing_requirement_dict)

        # Owner in collaborators
        data, status_code = self.post(
            '/exps/',
            {'exp':
             {'owner_id': 'jane',
              'description': ('After motion effects '
                              'on smartphones'),
              'collaborator_ids': ['william', 'jane']}},
            self.jane)
        self.assertEqual(status_code, 400)
        self.assertEqual(data, self.error_400_missing_requirement_dict)

        ## Missing owner

        # Unexisting collaborator, collaborator user_id not set, owner in
        # collaborators, bad name syntax
        data, status_code = self.post(
            '/exps/',
            {'exp':
             {'name': '-motion-after-effect',
              'description': ('After motion effects '
                              'on smartphones'),
              'collaborator_ids': ['non-existing', self.ruphus.user_id,
                                   'jane']}},
            self.jane)
        self.assertEqual(status_code, 400)
        self.assertEqual(data, self.error_400_missing_requirement_dict)

        # Unexisting collaborator, collaborator user_id not set, owner in
        # collaborators, name already taken
        Exp.create('numerical-distance', self.jane,
                   'The numerical distance experiment, on smartphones',
                   [self.sophia, self.bill])
        data, status_code = self.post(
            '/exps/',
            {'exp':
             {'name': 'numerical-distance',
              'description': ('After motion effects '
                              'on smartphones'),
              'collaborator_ids': ['non-existing', self.ruphus.user_id,
                                   'jane']}},
            self.jane)
        self.assertEqual(status_code, 400)
        self.assertEqual(data, self.error_400_missing_requirement_dict)

        # Collaborator user_id not set, owner in collaborators,
        # bad name syntax
        data, status_code = self.post(
            '/exps/',
            {'exp':
             {'name': '-motion-after-effect',
              'description': ('After motion effects '
                              'on smartphones'),
              'collaborator_ids': [self.ruphus.user_id, 'jane']}},
            self.jane)
        self.assertEqual(status_code, 400)
        self.assertEqual(data, self.error_400_missing_requirement_dict)

        # Collaborator user_id not set, owner in collaborators,
        # name already taken
        data, status_code = self.post(
            '/exps/',
            {'exp':
             {'name': 'numerical-distance',
              'description': ('After motion effects '
                              'on smartphones'),
              'collaborator_ids': [self.ruphus.user_id, 'jane']}},
            self.jane)
        self.assertEqual(status_code, 400)
        self.assertEqual(data, self.error_400_missing_requirement_dict)

        # Owner in collaborators, bad name syntax
        data, status_code = self.post(
            '/exps/',
            {'exp':
             {'name': '-motion-after-effect',
              'description': ('After motion effects '
                              'on smartphones'),
              'collaborator_ids': ['william', 'jane']}},
            self.jane)
        self.assertEqual(status_code, 400)
        self.assertEqual(data, self.error_400_missing_requirement_dict)

        # Owner in collaborators, name already taken
        data, status_code = self.post(
            '/exps/',
            {'exp':
             {'name': 'numerical-distance',
              'description': ('After motion effects '
                              'on smartphones'),
              'collaborator_ids': ['william', 'jane']}},
            self.jane)
        self.assertEqual(status_code, 400)
        self.assertEqual(data, self.error_400_missing_requirement_dict)

        # Bad name syntax
        data, status_code = self.post(
            '/exps/',
            {'exp':
             {'name': '-motion-after-effect',
              'description': ('After motion effects '
                              'on smartphones'),
              'collaborator_ids': ['beth', 'william']}},
            self.jane)
        self.assertEqual(status_code, 400)
        self.assertEqual(data, self.error_400_missing_requirement_dict)

        # Name already taken
        data, status_code = self.post(
            '/exps/',
            {'exp':
             {'name': 'numerical-distance',
              'description': ('After motion effects '
                              'on smartphones'),
              'collaborator_ids': ['beth', 'william']}},
            self.jane)
        self.assertEqual(status_code, 400)
        self.assertEqual(data, self.error_400_missing_requirement_dict)

    def test_root_post_unexisting_collaborator(self):
        data, status_code = self.post(
            '/exps/',
            {'exp':
             {'owner_id': 'jane',
              'name': 'motion-after-effect',
              'description': ('After motion effects '
                              'on smartphones'),
              'collaborator_ids': ['non-existing', 'william']}},
            self.jane)
        self.assertEqual(status_code, 400)
        self.assertEqual(data, self.error_400_collaborator_not_found_dict)

    def test_root_post_unexisting_collaborator_error_priorities(self):
        # Collaborator user_id not set, owner in collaborators,
        # bad name syntax
        data, status_code = self.post(
            '/exps/',
            {'exp':
             {'owner_id': 'jane',
              'name': '-motion-after-effect',
              'description': ('After motion effects '
                              'on smartphones'),
              'collaborator_ids': ['non-existing', self.ruphus.user_id,
                                   'jane']}},
            self.jane)
        self.assertEqual(status_code, 400)
        self.assertEqual(data, self.error_400_collaborator_not_found_dict)

        # Collaborator user_id not set, owner in collaborators,
        # name already taken
        Exp.create('numerical-distance', self.jane,
                   'The numerical distance experiment, on smartphones',
                   [self.sophia, self.bill])
        data, status_code = self.post(
            '/exps/',
            {'exp':
             {'owner_id': 'jane',
              'name': 'numerical-distance',
              'description': ('After motion effects '
                              'on smartphones'),
              'collaborator_ids': ['non-existing', self.ruphus.user_id,
                                   'jane']}},
            self.jane)
        self.assertEqual(status_code, 400)
        self.assertEqual(data, self.error_400_collaborator_not_found_dict)

        # Owner in collaborators, bad name syntax
        data, status_code = self.post(
            '/exps/',
            {'exp':
             {'owner_id': 'jane',
              'name': '-motion-after-effect',
              'description': ('After motion effects '
                              'on smartphones'),
              'collaborator_ids': ['non-existing', 'jane']}},
            self.jane)
        self.assertEqual(status_code, 400)
        self.assertEqual(data, self.error_400_collaborator_not_found_dict)

        # Owner in collaborators, name already taken
        data, status_code = self.post(
            '/exps/',
            {'exp':
             {'owner_id': 'jane',
              'name': 'numerical-distance',
              'description': ('After motion effects '
                              'on smartphones'),
              'collaborator_ids': ['non-existing', 'jane']}},
            self.jane)
        self.assertEqual(status_code, 400)
        self.assertEqual(data, self.error_400_collaborator_not_found_dict)

        # Bad name syntax
        data, status_code = self.post(
            '/exps/',
            {'exp':
             {'owner_id': 'jane',
              'name': '-motion-after-effect',
              'description': ('After motion effects '
                              'on smartphones'),
              'collaborator_ids': ['non-existing', 'william']}},
            self.jane)
        self.assertEqual(status_code, 400)
        self.assertEqual(data, self.error_400_collaborator_not_found_dict)

        # Name already taken
        data, status_code = self.post(
            '/exps/',
            {'exp':
             {'owner_id': 'jane',
              'name': 'numerical-distance',
              'description': ('After motion effects '
                              'on smartphones'),
              'collaborator_ids': ['non-existing', 'william']}},
            self.jane)
        self.assertEqual(status_code, 400)
        self.assertEqual(data, self.error_400_collaborator_not_found_dict)

    def test_root_post_collaborator_user_id_not_set(self):
        data, status_code = self.post(
            '/exps/',
            {'exp':
             {'owner_id': 'jane',
              'name': 'motion-after-effect',
              'description': ('After motion effects '
                              'on smartphones'),
              'collaborator_ids': ['william', self.ruphus.user_id]}},
            self.jane)
        self.assertEqual(status_code, 400)
        self.assertEqual(data,
                         self.error_400_collaborator_user_id_not_set_dict)

    def test_root_post_collaborator_user_id_not_set_error_priorities(self):
        # Owner in collaborators, bad name syntax
        data, status_code = self.post(
            '/exps/',
            {'exp':
             {'owner_id': 'jane',
              'name': '-motion-after-effect',
              'description': ('After motion effects '
                              'on smartphones'),
              'collaborator_ids': ['jane', self.ruphus.user_id]}},
            self.jane)
        self.assertEqual(status_code, 400)
        self.assertEqual(data,
                         self.error_400_collaborator_user_id_not_set_dict)

        # Owner in collaborators, name already taken
        Exp.create('numerical-distance', self.jane,
                   'The numerical distance experiment, on smartphones',
                   [self.sophia, self.bill])
        data, status_code = self.post(
            '/exps/',
            {'exp':
             {'owner_id': 'jane',
              'name': 'numerical-distance',
              'description': ('After motion effects '
                              'on smartphones'),
              'collaborator_ids': ['jane', self.ruphus.user_id]}},
            self.jane)
        self.assertEqual(status_code, 400)
        self.assertEqual(data,
                         self.error_400_collaborator_user_id_not_set_dict)

        # Bad name syntax
        data, status_code = self.post(
            '/exps/',
            {'exp':
             {'owner_id': 'jane',
              'name': '-motion-after-effect',
              'description': ('After motion effects '
                              'on smartphones'),
              'collaborator_ids': ['william', self.ruphus.user_id]}},
            self.jane)
        self.assertEqual(status_code, 400)
        self.assertEqual(data,
                         self.error_400_collaborator_user_id_not_set_dict)

        # Name already taken
        data, status_code = self.post(
            '/exps/',
            {'exp':
             {'owner_id': 'jane',
              'name': 'numerical-distance',
              'description': ('After motion effects '
                              'on smartphones'),
              'collaborator_ids': ['william', self.ruphus.user_id]}},
            self.jane)
        self.assertEqual(status_code, 400)
        self.assertEqual(data,
                         self.error_400_collaborator_user_id_not_set_dict)

    def test_root_post_owner_in_collaborators(self):
        data, status_code = self.post(
            '/exps/',
            {'exp':
             {'owner_id': 'jane',
              'name': 'motion-after-effect',
              'description': ('After motion effects '
                              'on smartphones'),
              'collaborator_ids': ['william', 'jane']}},
            self.jane)
        self.assertEqual(status_code, 400)
        self.assertEqual(data, self.error_400_owner_in_collaborators)

    def test_root_post_owner_in_collaborators_error_priorities(self):
        # Bad name syntax
        data, status_code = self.post(
            '/exps/',
            {'exp':
             {'owner_id': 'jane',
              'name': '-motion-after-effect',
              'description': ('After motion effects '
                              'on smartphones'),
              'collaborator_ids': ['william', 'jane']}},
            self.jane)
        self.assertEqual(status_code, 400)
        self.assertEqual(data, self.error_400_owner_in_collaborators)

        # Name already taken
        Exp.create('numerical-distance', self.jane,
                   'The numerical distance experiment, on smartphones',
                   [self.sophia, self.bill])
        data, status_code = self.post(
            '/exps/',
            {'exp':
             {'owner_id': 'jane',
              'name': 'numerical-distance',
              'description': ('After motion effects '
                              'on smartphones'),
              'collaborator_ids': ['william', 'jane']}},
            self.jane)
        self.assertEqual(status_code, 400)
        self.assertEqual(data, self.error_400_owner_in_collaborators)

    def test_root_post_bad_name_syntax(self):
        data, status_code = self.post(
            '/exps/',
            {'exp':
             {'owner_id': 'jane',
              'name': '-motion-after-effect',
              'description': ('After motion effects '
                              'on smartphones'),
              'collaborator_ids': ['beth', 'william']}},
            self.jane)
        self.assertEqual(status_code, 400)
        self.assertEqual(data, self.error_400_bad_syntax_dict)

    # No error priorities test since this is a leaf case

    def test_root_post_name_already_taken(self):
        Exp.create('numerical-distance', self.jane,
                   'The numerical distance experiment, on smartphones',
                   [self.sophia, self.bill])
        data, status_code = self.post(
            '/exps/',
            {'exp':
             {'owner_id': 'jane',
              'name': 'numerical-distance',
              'description': ('After motion effects '
                              'on smartphones'),
              'collaborator_ids': ['beth', 'william']}},
            self.jane)
        self.assertEqual(status_code, 409)
        self.assertEqual(data, self.error_409_field_conflict_dict)

    # No error priorities test since this is a leaf case

    def test_exp_get(self):
        ## Non-existing experiment
        # As nodbody
        data, status_code = self.get('/exps/{}'.format(self.nd_dict['id']))
        self.assertEqual(status_code, 404)
        self.assertEqual(data, self.error_404_does_not_exist_dict)

        # As jane
        data, status_code = self.get('/exps/{}'.format(self.nd_dict['id']),
                                     self.jane)
        self.assertEqual(status_code, 404)
        self.assertEqual(data, self.error_404_does_not_exist_dict)

        # As jane with ignored 'private' paramter
        data, status_code = self.get('/exps/{}?access=private'.format(
            self.nd_dict['id']), self.jane)
        self.assertEqual(status_code, 404)
        self.assertEqual(data, self.error_404_does_not_exist_dict)

        ## Now with existing experiments
        self.create_exps()

        # As nobody
        data, status_code = self.get('/exps/{}'.format(self.nd_dict['id']))
        self.assertEqual(status_code, 200)
        self.assertEqual(data, {'exp': self.nd_dict})

        data, status_code = self.get('/exps/{}'.format(self.gp_dict['id']))
        self.assertEqual(status_code, 200)
        self.assertEqual(data, {'exp': self.gp_dict})

        # As jane
        data, status_code = self.get('/exps/{}'.format(self.nd_dict['id']),
                                     self.jane)
        self.assertEqual(status_code, 200)
        self.assertEqual(data, {'exp': self.nd_dict})

        data, status_code = self.get('/exps/{}'.format(self.gp_dict['id']),
                                     self.jane)
        self.assertEqual(status_code, 200)
        self.assertEqual(data, {'exp': self.gp_dict})

        # As jane with ignored 'private' parameter
        data, status_code = self.get('/exps/{}?access=private'.format(
            self.nd_dict['id']), self.jane)
        self.assertEqual(status_code, 200)
        self.assertEqual(data, {'exp': self.nd_dict})

        data, status_code = self.get('/exps/{}?access=private'.format(
            self.gp_dict['id']), self.jane)
        self.assertEqual(status_code, 200)
        self.assertEqual(data, {'exp': self.gp_dict})
