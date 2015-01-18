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
        self.nd_dict = {'id': '3991cd52745e05f96baff356d82ce3fc'
                              'a48ee0f640422477676da645142c6153',
                        'name': 'numerical-distance',
                        'description': 'The numerical distance '
                                       'experiment, on smartphones',
                        'owner_id': 'jane',
                        'collaborator_ids': ['sophia', 'bill'],
                        'n_collaborators': 2,
                        'n_results': 0,
                        'n_profiles': 0,
                        'n_devices': 0}
        self.gp_dict = {'id': '3812bfcf957e8534a683a37ffa3d09a9'
                              'db9a797317ac20edc87809711e0d47cb',
                        'name': 'gender-priming',
                        'description': 'Controversial gender priming effects',
                        'owner_id': 'beth',
                        'collaborator_ids': ['william', 'bill'],
                        'n_collaborators': 2,
                        'n_results': 0,
                        'n_profiles': 0,
                        'n_devices': 0}
        self.mae_dict = {'id': 'b646639945296429f169a4b93829351a'
                               '70c92f9cf52095b70a17aa6ab1e2432c',
                         'name': 'motion-after-effect',
                         'description': 'After motion effects on smartphones',
                         'owner_id': 'jane',
                         'collaborator_ids': ['beth', 'william'],
                         'n_collaborators': 2,
                         'n_results': 0,
                         'n_profiles': 0,
                         'n_devices': 0}
        self.dd_dict = {'id': '3d7ebc752d7d1c0bfd81c752c65baa14'
                              '8bf1237db152a0539f19a1c9807ed357',
                        'name': 'daydreaming',
                        'description': 'Study mind-wandering',
                        'owner_id': 'william',
                        'collaborator_ids': [],
                        'n_collaborators': 0,
                        'n_results': 0,
                        'n_profiles': 0,
                        'n_devices': 0}
        self.gi_dict = {'id': 'd901ba49e6e5592d836764790da2db56'
                              'd98ff5934428ad6d4d59dc46fccd883f',
                        'name': 'gistr',
                        'description': 'You see what I mean, right?',
                        'owner_id': 'sophia',
                        'collaborator_ids': ['william'],
                        'n_collaborators': 1,
                        'n_results': 0,
                        'n_profiles': 0,
                        'n_devices': 0}
        self.so_dict = {'id': '01b16e31d89ec06fddad1ebd5e02ef5e'
                              '5d3fd2b1574404fbf765d8ea1f4d927d',
                        'name': 'subordinates',
                        'description': 'Processing-cost of different '
                                       'subordinate structures',
                        'owner_id': 'jane',
                        'collaborator_ids': ['bill'],
                        'n_collaborators': 1,
                        'n_results': 0,
                        'n_profiles': 0,
                        'n_devices': 0}
        self.mae_completed_defaults_dict = self.mae_dict.copy()
        self.mae_completed_defaults_dict['description'] = ''
        self.mae_completed_defaults_dict['collaborator_ids'] = []
        self.mae_completed_defaults_dict['n_collaborators'] = 0

        # 400 unknown operator
        self.error_400_query_unknown_operator_dict = {
            'error': {'status_code': 400,
                      'type': 'UnknownOperator',
                      'message': 'Found an unknown query operator '
                                 'on a valid field'}}

        # 400 query too deep
        self.error_400_query_too_deep_dict = {
            'error': {'status_code': 400,
                      'type': 'QueryTooDeep',
                      'message': 'Query parameter is too deep'}}

        # 400 non queriable type
        self.error_400_query_non_queriable_dict = {
            'error': {'status_code': 400,
                      'type': 'NonQueriableType',
                      'message': 'Field cannot be queried'}}

        # 400 non orderable type
        self.error_400_query_non_orderable_dict = {
            'error': {'status_code': 400,
                      'type': 'NonOrderableType',
                      'message': 'Field cannot be ordered'}}

        # 400 bad typing
        self.error_400_query_bad_typing_dict = {
            'error': {'status_code': 400,
                      'type': 'BadQueryType',
                      'message': 'Field, operator, or query value '
                                 'not compatible together'}}

        # 400 parsing
        self.error_400_query_parsing_dict = {
            'error': {'status_code': 400,
                      'type': 'ParsingError',
                      'message': 'Could not parse query value'}}

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

    def create_many_exps(self):
        self.create_exps()
        Exp.create('daydreaming', self.william,
                   'Study mind-wandering')
        Exp.create('gistr', self.sophia,
                   'You see what I mean, right?',
                   [self.william])
        Exp.create('subordinates', self.jane,
                   'Processing-cost of different subordinate structures',
                   [self.bill])

    def test_root_get(self):
        # ## With no exps
        data, status_code = self.get('/exps')
        self.assertEqual(status_code, 200)
        self.assertEqual(data['exps'], [])

        # ## Now with some exps
        self.create_exps()

        # As nobody
        data, status_code = self.get('/exps')
        self.assertEqual(status_code, 200)
        self.assertEqual(data, {'exps': [self.gp_dict, self.nd_dict]})

        # As jane
        data, status_code = self.get('/exps', self.jane)
        self.assertEqual(status_code, 200)
        self.assertEqual(data, {'exps': [self.gp_dict, self.nd_dict]})

        # As jane with ignored 'private' parameter
        data, status_code = self.get('/exps?access=private', self.jane)
        self.assertEqual(status_code, 200)
        self.assertEqual(data, {'exps': [self.gp_dict, self.nd_dict]})

    def test_root_get_by_id(self):
        # ## With no exps
        data, status_code = self.get('/exps?ids[]={}'.format(
            self.nd_dict['id']))
        self.assertEqual(status_code, 200)
        self.assertEqual(data['exps'], [])

        # ## Now with some exps
        self.create_exps()

        # As nobody, one exp
        data, status_code = self.get('/exps?ids[]={}'.format(
            self.nd_dict['id']))
        self.assertEqual(status_code, 200)
        self.assertEqual(data, {'exps': [self.nd_dict]})

        # As nobody, two exps
        data, status_code = self.get('/exps?ids[]={}&ids[]={}'.format(
            self.nd_dict['id'], self.gp_dict['id']))
        self.assertEqual(status_code, 200)
        self.assertEqual(data, {'exps': [self.gp_dict, self.nd_dict]})

        # As jane, one exp
        data, status_code = self.get('/exps?ids[]={}'.format(
            self.nd_dict['id']), self.jane)
        self.assertEqual(status_code, 200)
        self.assertEqual(data, {'exps': [self.nd_dict]})

        # As jane, two exps
        data, status_code = self.get('/exps?ids[]={}&ids[]={}'.format(
            self.nd_dict['id'], self.gp_dict['id']), self.jane)
        self.assertEqual(status_code, 200)
        self.assertEqual(data, {'exps': [self.gp_dict, self.nd_dict]})

        # A non-existing exp
        data, status_code = self.get('/exps?ids[]={}'.format('non-existing'))
        self.assertEqual(status_code, 200)
        self.assertEqual(data, {'exps': []})

    def test_root_get_public_operators(self):
        self.create_many_exps()

        # ## String operators
        data, status_code = self.get('/exps?name__startswith=gender')
        self.assertEqual(status_code, 200)
        self.assertEqual(data, {'exps': [self.gp_dict]})

        data, status_code = self.get('/exps?name__contains=In')
        self.assertEqual(status_code, 200)
        self.assertEqual(data, {'exps': []})

        data, status_code = self.get('/exps?name__icontains=in')
        self.assertEqual(status_code, 200)
        self.assertEqual(data, {'exps': [self.gp_dict, self.so_dict,
                                         self.dd_dict]})

        # ## Number operators
        data, status_code = self.get('/exps?n_collaborators__gt=1')
        self.assertEqual(status_code, 200)
        self.assertEqual(data, {'exps': [self.gp_dict, self.nd_dict]})

        # Doubled query is ignored
        data, status_code = self.get(
            '/exps?n_collaborators=1&n_collaborators=2')
        self.assertEqual(status_code, 200)
        self.assertEqual(data, {'exps': [self.so_dict, self.gi_dict]})

        data, status_code = self.get(
            '/exps?n_collaborators=2&n_collaborators=1')
        self.assertEqual(status_code, 200)
        self.assertEqual(data, {'exps': [self.gp_dict, self.nd_dict]})

        # ## Combined queries
        data, status_code = self.get(
            '/exps?name__contains=r&description__contains=see')
        self.assertEqual(status_code, 200)
        self.assertEqual(data, {'exps': [self.gi_dict]})

        # Combining with ids
        data, status_code = self.get(
            '/exps?ids[]=d901ba49e6e5592d836764790da2db56'
            'd98ff5934428ad6d4d59dc46fccd883f'
            '&ids[]=01b16e31d89ec06fddad1ebd5e02ef5e'
            '5d3fd2b1574404fbf765d8ea1f4d927d'
            '&collaborator_ids__contains=ill')
        self.assertEqual(status_code, 200)
        self.assertEqual(data, {'exps': [self.so_dict, self.gi_dict]})

        data, status_code = self.get(
            '/exps?ids[]=d901ba49e6e5592d836764790da2db56'
            'd98ff5934428ad6d4d59dc46fccd883f'
            '&ids[]=01b16e31d89ec06fddad1ebd5e02ef5e'
            '5d3fd2b1574404fbf765d8ea1f4d927d'
            '&collaborator_ids__endswith=am')
        self.assertEqual(status_code, 200)
        self.assertEqual(data, {'exps': [self.gi_dict]})

    def test_root_get_public_operators_unexisting_ignored(self):
        self.create_many_exps()

        data, status_code = self.get('/exps?nonfield__contains=jane')
        self.assertEqual(status_code, 200)
        self.assertEqual(data, {'exps': [self.gp_dict, self.nd_dict,
                                         self.so_dict, self.gi_dict,
                                         self.dd_dict]})

        data, status_code = self.get(
            '/exps?n_collaborators__gt=1&nonfield__contains=jane')
        self.assertEqual(status_code, 200)
        self.assertEqual(data, {'exps': [self.gp_dict, self.nd_dict]})

        data, status_code = self.get(
            '/exps?ids[]=d901ba49e6e5592d836764790da2db56'
            'd98ff5934428ad6d4d59dc46fccd883f'
            '&ids[]=01b16e31d89ec06fddad1ebd5e02ef5e'
            '5d3fd2b1574404fbf765d8ea1f4d927d'
            '&nonfield=jane')
        self.assertEqual(status_code, 200)
        self.assertEqual(data, {'exps': [self.so_dict, self.gi_dict]})

        data, status_code = self.get(
            '/exps?ids[]=d901ba49e6e5592d836764790da2db56'
            'd98ff5934428ad6d4d59dc46fccd883f'
            '&ids[]=01b16e31d89ec06fddad1ebd5e02ef5e'
            '5d3fd2b1574404fbf765d8ea1f4d927d'
            '&name__startswith=gi&nonfield__gt=jane')
        self.assertEqual(status_code, 200)
        self.assertEqual(data, {'exps': [self.gi_dict]})

    def test_root_get_public_order(self):
        self.create_many_exps()

        # ## Normal working order parameter

        data, status_code = self.get('/exps?order=-description')
        self.assertEqual(status_code, 200)
        self.assertEqual(data, {'exps': [self.gi_dict, self.nd_dict,
                                         self.dd_dict, self.so_dict,
                                         self.gp_dict]})

        # ## Multiple order parameters

        data, status_code = self.get(
            '/exps?order=+n_collaborators&order=-owner_id')
        self.assertEqual(status_code, 200)
        self.assertEqual(data, {'exps': [self.dd_dict, self.gi_dict,
                                         self.so_dict, self.nd_dict,
                                         self.gp_dict]})

        # ## Combining order and other query

        data, status_code = self.get('/exps?order=id&n_collaborators=1')
        self.assertEqual(status_code, 200)
        self.assertEqual(data, {'exps': [self.so_dict, self.gi_dict]})
        data, status_code = self.get(
            '/exps?order=-n_collaborators&name__contains=ing')
        self.assertEqual(status_code, 200)
        self.assertEqual(data, {'exps': [self.gp_dict, self.dd_dict]})

    def test_root_get_public_limit(self):
        self.create_many_exps()

        # ## Limit alone
        data, status_code = self.get('/exps?limit=2')
        self.assertEqual(status_code, 200)
        self.assertEqual(data, {'exps': [self.gp_dict, self.nd_dict]})
        data, status_code = self.get('/exps?limit=6')
        self.assertEqual(status_code, 200)
        self.assertEqual(data, {'exps': [self.gp_dict, self.nd_dict,
                                         self.so_dict, self.gi_dict,
                                         self.dd_dict]})

        # ## Limit with order

        data, status_code = self.get('/exps?limit=2&order=-name')
        self.assertEqual(status_code, 200)
        self.assertEqual(data, {'exps': [self.so_dict, self.nd_dict]})
        data, status_code = self.get(
            '/exps?limit=6&order=n_collaborators&order=-owner_id')
        self.assertEqual(status_code, 200)
        self.assertEqual(data, {'exps': [self.dd_dict, self.gi_dict,
                                         self.so_dict, self.nd_dict,
                                         self.gp_dict]})

        # ## Limit with order and other parameter

        data, status_code = self.get(
            '/exps?limit=2&order=-name&n_collaborators=2')
        self.assertEqual(status_code, 200)
        self.assertEqual(data, {'exps': [self.nd_dict, self.gp_dict]})
        data, status_code = self.get('/exps?limit=2&order=n_collaborators'
                                     '&order=-owner_id&name__contains=s')
        self.assertEqual(status_code, 200)
        self.assertEqual(data, {'exps': [self.gi_dict, self.so_dict]})

    def test_root_get_public_malformed_query_valid_field(self):
        self.create_many_exps()

        # Unknown operator
        data, status_code = self.get('/exps?name__notoperator=2')
        self.assertEqual(status_code, 400)
        self.assertEqual(data, self.error_400_query_unknown_operator_dict)
        # `count` is particular in that it does exist in mongoengine,
        # but is rejected here
        data, status_code = self.get('/exps?collaborator_ids__count=2')
        self.assertEqual(status_code, 400)
        self.assertEqual(data, self.error_400_query_unknown_operator_dict)

        # Query too deep
        data, status_code = self.get('/exps?collaborator_ids__count__lte=2')
        self.assertEqual(status_code, 400)
        self.assertEqual(data, self.error_400_query_too_deep_dict)

        # UnQueriableType can't be triggered, all fields are queriable

        # Regexp on a field that's not a string or a list of strings
        data, status_code = self.get('/exps?n_collaborators__contains=2')
        self.assertEqual(status_code, 400)
        self.assertEqual(data, self.error_400_query_bad_typing_dict)
        data, status_code = self.get('/exps?n_results__startswith=2')
        self.assertEqual(status_code, 400)
        self.assertEqual(data, self.error_400_query_bad_typing_dict)
        data, status_code = self.get('/exps?n_profiles__exact=2')
        self.assertEqual(status_code, 400)
        self.assertEqual(data, self.error_400_query_bad_typing_dict)

        # Unparsable number
        data, status_code = self.get('/exps?n_profiles__gte=a')
        self.assertEqual(status_code, 400)
        self.assertEqual(data, self.error_400_query_parsing_dict)
        data, status_code = self.get('/exps?n_profiles__gte=2.0')
        self.assertEqual(status_code, 400)
        self.assertEqual(data, self.error_400_query_parsing_dict)

    def test_root_get_public_limit_non_number(self):
        self.create_many_exps()

        data, status_code = self.get('/exps?limit=a')
        self.assertEqual(status_code, 400)
        self.assertEqual(data, self.error_400_query_parsing_dict)

        data, status_code = self.get('/exps?limit=1.0')
        self.assertEqual(status_code, 400)
        self.assertEqual(data, self.error_400_query_parsing_dict)

    def test_root_get_public_order_not_orderable(self):
        self.create_many_exps()

        data, status_code = self.get('/exps?order=collaborator_ids')
        self.assertEqual(status_code, 400)
        self.assertEqual(data, self.error_400_query_non_orderable_dict)

    def _test_post_successful(self, pexp_dict, rexp_dict, user):
        # User has no exps
        data, status_code = self.get('/users/{}'.format(
            rexp_dict['owner_id']))
        self.assertEqual(status_code, 200)
        self.assertEqual(data['user']['exp_ids'], [])

        # Add the exp
        data, status_code = self.post('/exps', pexp_dict, user)
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
            '/exps',
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
        data, status_code = self.post('/exps',
                                      '{"Malformed JSON": "bla"',
                                      dump_json_data=False)
        self.assertEqual(status_code, 401)
        self.assertEqual(data, self.error_401_dict)

        # Good JSON but no 'exp' root object
        data, status_code = self.post('/exps',
                                      {'not-exp': 'bla'})
        self.assertEqual(status_code, 401)
        self.assertEqual(data, self.error_401_dict)

        # Owner mismatch makes no sense without authentication

        # Owner user_id not set, missing required field (name), unexisting
        # collaborator, collaborator user_id not set, owner in collaborators
        data, status_code = self.post(
            '/exps',
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
            '/exps',
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
            '/exps',
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
            '/exps',
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
            '/exps',
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
            '/exps',
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
            '/exps',
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
            '/exps',
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
            '/exps',
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
            '/exps',
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
            '/exps',
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
            '/exps',
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
            '/exps',
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
            '/exps',
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
        data, status_code = self.post('/exps',
                                      '{"Malformed JSON": "bla"',
                                      self.jane,
                                      dump_json_data=False)
        self.assertEqual(status_code, 400)
        self.assertEqual(data, self.error_400_malformed_dict)

        # Good JSON but no 'exp' root object
        data, status_code = self.post('/exps',
                                      {'not-exp': 'bla'},
                                      self.jane)
        self.assertEqual(status_code, 400)
        self.assertEqual(data, self.error_400_malformed_dict)

    # No priority tests for other errors added to malformed JSON since it makes
    # no sense given the errors

    def test_root_post_owner_mismatch(self):
        data, status_code = self.post(
            '/exps',
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
            '/exps',
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
            '/exps',
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
            '/exps',
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
            '/exps',
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
            '/exps',
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
            '/exps',
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
            '/exps',
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
            '/exps',
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
            '/exps',
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
            '/exps',
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
            '/exps',
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
            '/exps',
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
            '/exps',
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
            '/exps',
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
            '/exps',
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
            '/exps',
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
            '/exps',
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
            '/exps',
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
            '/exps',
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
            '/exps',
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
            '/exps',
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
            '/exps',
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
            '/exps',
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
            '/exps',
            {'exp':
             {'name': 'motion-after-effect',
              'description': ('After motion effects '
                              'on smartphones'),
              'collaborator_ids': ['beth', 'william']}},
            self.jane)
        self.assertEqual(status_code, 400)
        self.assertEqual(data, self.error_400_missing_requirement_dict)

    def test_root_post_missing_required_field_error_priorities(self):
        # ## Missing name

        # Unexisting collaborator, collaborator user_id not set,
        # owner in collaborators
        data, status_code = self.post(
            '/exps',
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
            '/exps',
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
            '/exps',
            {'exp':
             {'owner_id': 'jane',
              'description': ('After motion effects '
                              'on smartphones'),
              'collaborator_ids': ['william', 'jane']}},
            self.jane)
        self.assertEqual(status_code, 400)
        self.assertEqual(data, self.error_400_missing_requirement_dict)

        # ## Missing owner

        # Unexisting collaborator, collaborator user_id not set, owner in
        # collaborators, bad name syntax
        data, status_code = self.post(
            '/exps',
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
            '/exps',
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
            '/exps',
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
            '/exps',
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
            '/exps',
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
            '/exps',
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
            '/exps',
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
            '/exps',
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
            '/exps',
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
            '/exps',
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
            '/exps',
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
            '/exps',
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
            '/exps',
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
            '/exps',
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
            '/exps',
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
            '/exps',
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
            '/exps',
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
            '/exps',
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
            '/exps',
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
            '/exps',
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
            '/exps',
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
            '/exps',
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
            '/exps',
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
            '/exps',
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
            '/exps',
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
        # ## Non-existing experiment
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

        # ## Now with existing experiments
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
