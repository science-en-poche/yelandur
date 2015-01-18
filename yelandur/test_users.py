# -*- coding: utf-8 -*-

from .models import User, Exp
from .helpers import hexregex, APITestCase


# TODO: add CORS test


class UsersTestCase(APITestCase):

    maxDiff = None

    def setUp(self):
        super(UsersTestCase, self).setUp()

        # Four test users to work with
        self.jane = User.get_or_create_by_email('jane@example.com')
        self.jane.set_user_id('jane')
        self.ruphus = User.get_or_create_by_email('ru.p_h-us@example.com')
        self.toad = User.get_or_create_by_email('toad@example.com')
        self.toad.set_user_id('toad')
        self.toad_exp1 = Exp.create('exp1', self.toad)
        self.sophie = User.get_or_create_by_email('sophie@example.com')
        self.sophie.set_user_id('sophie')
        self.sophie_exp1 = Exp.create('exp1', self.sophie)
        self.sophie_exp2 = Exp.create('exp2', self.sophie)

        # ## Their corresponding dicts

        # Jane
        self.jane_dict_public = {'id': 'jane',
                                 'user_id_is_set': True,
                                 'gravatar_id': ('9e26471d35a78862'
                                                 'c17e467d87cddedf'),
                                 'exp_ids': [],
                                 'n_profiles': 0,
                                 'n_devices': 0,
                                 'n_results': 0,
                                 'n_exps': 0}
        self.jane_dict_private = self.jane_dict_public.copy()
        # Prevent the copy from keeping the same list
        self.jane_dict_private['exp_ids'] = []
        self.jane_dict_private['persona_email'] = 'jane@example.com'

        # Ruphus
        # First make sure there is no 'a' in the random user_id,
        # because we use id__contains=a in tests further down to get
        # toad and jane only.
        self.ruphus.user_id = self.ruphus.user_id.replace('a', 'b')
        self.ruphus.save()
        self.ruphus_dict_public = {'id': self.ruphus.user_id,
                                   'user_id_is_set': False,
                                   'gravatar_id': ('83db46ebd7f5f892'
                                                   'ca0d34146ad91cd3'),
                                   'exp_ids': [],
                                   'n_profiles': 0,
                                   'n_devices': 0,
                                   'n_results': 0,
                                   'n_exps': 0}
        self.ruphus_dict_private = self.ruphus_dict_public.copy()
        # Prevent the copy from keeping the same list
        self.ruphus_dict_private['exp_ids'] = []
        self.ruphus_dict_private['persona_email'] = 'ru.p_h-us@example.com'
        self.ruphus_dict_private_with_user_id = self.ruphus_dict_private.copy()
        # Prevent the copy from keeping the same list
        self.ruphus_dict_private_with_user_id['exp_ids'] = []
        self.ruphus_dict_private_with_user_id['id'] = 'ruphus'
        self.ruphus_dict_private_with_user_id['user_id_is_set'] = True

        # Toad
        self.toad_dict_public = {'id': 'toad',
                                 'user_id_is_set': True,
                                 'gravatar_id': ('d30e600432a4e06f'
                                                 'fb07da894302a207'),
                                 'exp_ids': [self.toad_exp1.exp_id],
                                 'n_profiles': 0,
                                 'n_devices': 0,
                                 'n_results': 0,
                                 'n_exps': 1}
        self.toad_dict_private = self.toad_dict_public.copy()
        # Prevent the copy from keeping the same list
        self.toad_dict_private['exp_ids'] = [self.toad_exp1.exp_id]
        self.toad_dict_private['persona_email'] = 'toad@example.com'

        # Sophie
        self.sophie_dict_public = {'id': 'sophie',
                                   'user_id_is_set': True,
                                   'gravatar_id': ('d321a55f6c5a8de3'
                                                   '67be6c741581e8ae'),
                                   'exp_ids': [self.sophie_exp1.exp_id,
                                               self.sophie_exp2.exp_id],
                                   'n_profiles': 0,
                                   'n_devices': 0,
                                   'n_results': 0,
                                   'n_exps': 2}
        self.sophie_dict_private = self.sophie_dict_public.copy()
        # Prevent the copy from keeping the same list
        self.sophie_dict_private['exp_ids'] = [self.sophie_exp1.exp_id,
                                               self.sophie_exp2.exp_id]
        self.sophie_dict_private['persona_email'] = 'sophie@example.com'

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

        # 403 resource can't be changed
        self.error_403_user_id_set_dict = {
            'error': {'status_code': 403,
                      'type': 'UserIdSet',
                      'message': 'user_id has already been set'}}

        # 409 user_id reserved
        self.error_409_user_id_reserved_dict = {
            'error': {'status_code': 409,
                      'type': 'UserIdReserved',
                      'message': 'The claimed user_id is reserved'}}

    def test_root_get(self):
        # A user with his user_id set
        data, status_code = self.get('/users', self.jane)
        self.assertEqual(status_code, 200)
        self.assertEqual(data, {'users': [self.jane_dict_public,
                                          self.ruphus_dict_public,
                                          self.sophie_dict_public,
                                          self.toad_dict_public]})

        # A user with his user_id not set
        data, status_code = self.get('/users', self.ruphus)
        self.assertEqual(status_code, 200)
        self.assertEqual(data, {'users': [self.jane_dict_public,
                                          self.ruphus_dict_public,
                                          self.sophie_dict_public,
                                          self.toad_dict_public]})

        # Without logging in
        data, status_code = self.get('/users')
        self.assertEqual(status_code, 200)
        self.assertEqual(data, {'users': [self.jane_dict_public,
                                          self.ruphus_dict_public,
                                          self.sophie_dict_public,
                                          self.toad_dict_public]})

    def test_root_get_by_id(self):
        # A single user by id, logging in
        data, status_code = self.get('/users?ids[]={}'.format('jane'),
                                     self.jane)
        self.assertEqual(status_code, 200)
        self.assertEqual(data, {'users': [self.jane_dict_public]})

        # A single user by id, not logging in
        data, status_code = self.get('/users?ids[]={}'.format('jane'))
        self.assertEqual(status_code, 200)
        self.assertEqual(data, {'users': [self.jane_dict_public]})

        # Two users by id, logging in
        data, status_code = self.get('/users?ids[]={}&ids[]={}'.format(
            'jane', self.ruphus_dict_public['id']), self.jane)
        self.assertEqual(status_code, 200)
        self.assertEqual(data, {'users': [self.jane_dict_public,
                                          self.ruphus_dict_public]})

        # Two users by id, not logging in
        data, status_code = self.get('/users?ids[]={}&ids[]={}'.format(
            'jane', self.ruphus_dict_public['id']))
        self.assertEqual(status_code, 200)
        self.assertEqual(data, {'users': [self.jane_dict_public,
                                          self.ruphus_dict_public]})

        # A non-existing user
        data, status_code = self.get('/users?ids[]={}'.format('non-exising'))
        self.assertEqual(status_code, 200)
        self.assertEqual(data, {'users': []})

    def test_root_get_public_operators_public(self):
        data, status_code = self.get('/users?id__contains=t')
        self.assertEqual(status_code, 200)
        self.assertEqual(data, {'users': [self.toad_dict_public]})

        data, status_code = self.get('/users?n_exps__gt=1')
        self.assertEqual(status_code, 200)
        self.assertEqual(data, {'users': [self.sophie_dict_public]})

        data, status_code = self.get('/users?n_exps__lte=1&id__startswith=to')
        self.assertEqual(status_code, 200)
        self.assertEqual(data, {'users': [self.toad_dict_public]})

        data, status_code = self.get('/users?n_exps__gt=1&id__startswith=to')
        self.assertEqual(status_code, 200)
        self.assertEqual(data, {'users': []})

        data, status_code = self.get(
            '/users?ids[]=toad&ids[]=sophie&n_exps__lt=2')
        self.assertEqual(status_code, 200)
        self.assertEqual(data, {'users': [self.toad_dict_public]})

        data, status_code = self.get(
            '/users?n_exps__lt=3&n_exps__gte=1')
        self.assertEqual(status_code, 200)
        self.assertEqual(data, {'users': [self.sophie_dict_public,
                                          self.toad_dict_public]})

        data, status_code = self.get('/users?exp_ids__contains={}'.format(
            self.sophie_exp2.exp_id[4:8]))
        self.assertEqual(status_code, 200)
        self.assertEqual(data, {'users': [self.sophie_dict_public]})

        data, status_code = self.get('/users?n_results__gt=1')
        self.assertEqual(status_code, 200)
        self.assertEqual(data, {'users': []})

        # Doubled query is ignored
        data, status_code = self.get(
            '/users?n_exps=1&n_exps=2')
        self.assertEqual(status_code, 200)
        self.assertEqual(data, {'users': [self.toad_dict_public]})

        data, status_code = self.get(
            '/users?n_exps=2&n_exps=1')
        self.assertEqual(status_code, 200)
        self.assertEqual(data, {'users': [self.sophie_dict_public]})

    def test_root_get_public_operators_private_ignored(self):
        data, status_code = self.get('/users?persona_email__contains=jane')
        self.assertEqual(status_code, 200)
        self.assertEqual(data, {'users': [self.jane_dict_public,
                                          self.ruphus_dict_public,
                                          self.sophie_dict_public,
                                          self.toad_dict_public]})

        data, status_code = self.get(
            '/users?n_exps__gt=1&persona_email__startswith=toad')
        self.assertEqual(status_code, 200)
        self.assertEqual(data, {'users': [self.sophie_dict_public]})

        data, status_code = self.get(
            '/users?ids[]=toad&ids[]=sophie&n_exps__lt=2'
            '&persona_email=jane')
        self.assertEqual(status_code, 200)
        self.assertEqual(data, {'users': [self.toad_dict_public]})

        data, status_code = self.get('/users?exp_ids__contains={}'
                                     '&persona_email=jane'.format(
                                         self.sophie_exp2.exp_id[4:8]))
        self.assertEqual(status_code, 200)
        self.assertEqual(data, {'users': [self.sophie_dict_public]})

    def test_root_get_public_operators_unexisting_ignored(self):
        data, status_code = self.get('/users?nonfield__contains=jane')
        self.assertEqual(status_code, 200)
        self.assertEqual(data, {'users': [self.jane_dict_public,
                                          self.ruphus_dict_public,
                                          self.sophie_dict_public,
                                          self.toad_dict_public]})

        data, status_code = self.get(
            '/users?n_exps__gt=1&nonfield__startswith=toad')
        self.assertEqual(status_code, 200)
        self.assertEqual(data, {'users': [self.sophie_dict_public]})

        data, status_code = self.get(
            '/users?ids[]=toad&ids[]=sophie&n_exps__lt=2'
            '&nonfield=jane')
        self.assertEqual(status_code, 200)
        self.assertEqual(data, {'users': [self.toad_dict_public]})

        data, status_code = self.get('/users?exp_ids__contains={}'
                                     '&nonfield=jane'.format(
                                         self.sophie_exp2.exp_id[4:8]))
        self.assertEqual(status_code, 200)
        self.assertEqual(data, {'users': [self.sophie_dict_public]})

    def test_root_get_public_order(self):
        # ## Normal working order parameter

        data, status_code = self.get('/users?order=-id')
        self.assertEqual(status_code, 200)
        self.assertEqual(data, {'users': [self.toad_dict_public,
                                          self.sophie_dict_public,
                                          self.ruphus_dict_public,
                                          self.jane_dict_public]})
        data, status_code = self.get('/users?order=-n_exps')
        self.assertEqual(status_code, 200)
        self.assertEqual(data, {'users': [self.sophie_dict_public,
                                          self.toad_dict_public,
                                          self.ruphus_dict_public,
                                          self.jane_dict_public]})

        # ## Multiple order parameters

        data, status_code = self.get('/users?order=-n_exps&order=-id')
        self.assertEqual(status_code, 200)
        self.assertEqual(data, {'users': [self.sophie_dict_public,
                                          self.toad_dict_public,
                                          self.ruphus_dict_public,
                                          self.jane_dict_public]})
        data, status_code = self.get('/users?order=+id&order=-n_exps')
        self.assertEqual(status_code, 200)
        self.assertEqual(data, {'users': [self.jane_dict_public,
                                          self.ruphus_dict_public,
                                          self.sophie_dict_public,
                                          self.toad_dict_public]})

        # ## Combining order and other query

        data, status_code = self.get('/users?order=-n_exps&n_exps__lte=1')
        self.assertEqual(status_code, 200)
        self.assertEqual(data, {'users': [self.toad_dict_public,
                                          self.ruphus_dict_public,
                                          self.jane_dict_public]})
        data, status_code = self.get('/users?order=+n_exps&order=-id'
                                     '&n_exps__lte=1')
        self.assertEqual(status_code, 200)
        self.assertEqual(data, {'users': [self.ruphus_dict_public,
                                          self.jane_dict_public,
                                          self.toad_dict_public]})
        data, status_code = self.get('/users?order=-n_exps&id__contains=a')
        self.assertEqual(status_code, 200)
        self.assertEqual(data, {'users': [self.toad_dict_public,
                                          self.jane_dict_public]})

    def test_root_get_public_order_private_ignored(self):
        # ## Ignored private order parameter

        data, status_code = self.get('/users?order=-persona_email')
        self.assertEqual(status_code, 200)
        self.assertEqual(data, {'users': [self.jane_dict_public,
                                          self.ruphus_dict_public,
                                          self.sophie_dict_public,
                                          self.toad_dict_public]})

        # ## Multiple order parameters, ignored private parameter

        data, status_code = self.get('/users?order=-n_exps'
                                     '&order=+persona_email')
        self.assertEqual(status_code, 200)
        self.assertEqual(data, {'users': [self.sophie_dict_public,
                                          self.toad_dict_public,
                                          self.ruphus_dict_public,
                                          self.jane_dict_public]})
        data, status_code = self.get('/users?order=+persona_email'
                                     '&order=-n_exps')
        self.assertEqual(status_code, 200)
        self.assertEqual(data, {'users': [self.sophie_dict_public,
                                          self.toad_dict_public,
                                          self.ruphus_dict_public,
                                          self.jane_dict_public]})

        # ## Combining order and other query, ignored private parameter

        data, status_code = self.get('/users?order=-persona_email'
                                     '&n_exps__lte=1')
        self.assertEqual(status_code, 200)
        self.assertEqual(data, {'users': [self.jane_dict_public,
                                          self.ruphus_dict_public,
                                          self.toad_dict_public]})
        data, status_code = self.get('/users?order=-persona_email'
                                     '&order=+n_exps&n_exps__lte=1')
        self.assertEqual(status_code, 200)
        self.assertEqual(data, {'users': [self.jane_dict_public,
                                          self.ruphus_dict_public,
                                          self.toad_dict_public]})
        data, status_code = self.get('/users?order=-persona_email'
                                     '&id__contains=a')
        self.assertEqual(status_code, 200)
        self.assertEqual(data, {'users': [self.jane_dict_public,
                                          self.toad_dict_public]})

    def test_root_get_public_limit(self):
        # ## Limit alone

        data, status_code = self.get('/users?limit=2')
        self.assertEqual(status_code, 200)
        self.assertEqual(data, {'users': [self.jane_dict_public,
                                          self.ruphus_dict_public]})
        data, status_code = self.get('/users?limit=5')
        self.assertEqual(status_code, 200)
        self.assertEqual(data, {'users': [self.jane_dict_public,
                                          self.ruphus_dict_public,
                                          self.sophie_dict_public,
                                          self.toad_dict_public]})

        # ## Limit with order

        data, status_code = self.get('/users?limit=2&order=-n_exps')
        self.assertEqual(status_code, 200)
        self.assertEqual(data, {'users': [self.sophie_dict_public,
                                          self.toad_dict_public]})
        data, status_code = self.get('/users?limit=5&order=-n_exps&order=-id')
        self.assertEqual(status_code, 200)
        self.assertEqual(data, {'users': [self.sophie_dict_public,
                                          self.toad_dict_public,
                                          self.ruphus_dict_public,
                                          self.jane_dict_public]})

        # ## Limit with order and other parameter

        data, status_code = self.get('/users?limit=1&order=-n_exps'
                                     '&id__contains=a')
        self.assertEqual(status_code, 200)
        self.assertEqual(data, {'users': [self.toad_dict_public]})
        data, status_code = self.get('/users?limit=5&order=-n_exps'
                                     '&n_exps__lte=1&order=-id')
        self.assertEqual(status_code, 200)
        self.assertEqual(data, {'users': [self.toad_dict_public,
                                          self.ruphus_dict_public,
                                          self.jane_dict_public]})

    def test_root_get_public_malformed_query_valid_field(self):
        # Unknown operator
        data, status_code = self.get('/users?id__notoperator=a')
        self.assertEqual(status_code, 400)
        self.assertEqual(data, self.error_400_query_unknown_operator_dict)
        # `count` is particular in that it does exist in mongoengine,
        # but is rejected here
        data, status_code = self.get('/users?exp_ids__count=2')
        self.assertEqual(status_code, 400)
        self.assertEqual(data, self.error_400_query_unknown_operator_dict)

        # Query too deep
        data, status_code = self.get('/users?exp_ids__count__lt=2')
        self.assertEqual(status_code, 400)
        self.assertEqual(data, self.error_400_query_too_deep_dict)

        # Querying on other than {list of} string/number/date
        data, status_code = self.get('/users?user_id_is_set=True')
        self.assertEqual(status_code, 400)
        self.assertEqual(data, self.error_400_query_non_queriable_dict)

        # Regexp on a field that's not a string or a list of strings
        data, status_code = self.get('/users?n_exps__startswith=1')
        self.assertEqual(status_code, 400)
        self.assertEqual(data, self.error_400_query_bad_typing_dict)
        data, status_code = self.get('/users?n_exps__contains=1')
        self.assertEqual(status_code, 400)
        self.assertEqual(data, self.error_400_query_bad_typing_dict)
        data, status_code = self.get('/users?n_exps__exact=1')
        self.assertEqual(status_code, 400)
        self.assertEqual(data, self.error_400_query_bad_typing_dict)

        # Unparsable number
        data, status_code = self.get('/users?n_exps__gte=a')
        self.assertEqual(status_code, 400)
        self.assertEqual(data, self.error_400_query_parsing_dict)
        data, status_code = self.get('/users?n_exps__gte=1.0')
        self.assertEqual(status_code, 400)
        self.assertEqual(data, self.error_400_query_parsing_dict)

    def test_root_get_public_limit_non_number(self):
        data, status_code = self.get('/users?limit=a')
        self.assertEqual(status_code, 400)
        self.assertEqual(data, self.error_400_query_parsing_dict)
        data, status_code = self.get('/users?limit=10.0')
        self.assertEqual(status_code, 400)
        self.assertEqual(data, self.error_400_query_parsing_dict)

    def test_root_get_public_order_not_orderable(self):
        # With a boolean
        data, status_code = self.get('/users?order=user_id_is_set')
        self.assertEqual(status_code, 400)
        self.assertEqual(data, self.error_400_query_non_orderable_dict)

        # With a list
        data, status_code = self.get('/users?order=exp_ids')
        self.assertEqual(status_code, 400)
        self.assertEqual(data, self.error_400_query_non_orderable_dict)

    def test_root_get_private(self):
        # As Jane
        data, status_code = self.get('/users?access=private',
                                     self.jane)
        self.assertEqual(status_code, 200)
        self.assertEqual(data, {'users': [self.jane_dict_private]})

        # As Ruphus
        data, status_code = self.get('/users?access=private',
                                     self.ruphus)
        self.assertEqual(status_code, 200)
        self.assertEqual(data, {'users': [self.ruphus_dict_private]})

        # Without authentication
        data, status_code = self.get('/users?access=private')
        self.assertEqual(status_code, 401)
        self.assertEqual(data, self.error_401_dict)

    def test_root_get_by_id_private(self):
        # A single user by id, logging in
        data, status_code = self.get(
            '/users?ids[]={}&access=private'.format('jane'), self.jane)
        self.assertEqual(status_code, 200)
        self.assertEqual(data, {'users': [self.jane_dict_private]})

        # A single user by id, not logging in
        data, status_code = self.get(
            '/users?ids[]={}&access=private'.format('jane'))
        self.assertEqual(status_code, 401)
        self.assertEqual(data, self.error_401_dict)

        # A single user by id, logging in as someone else
        data, status_code = self.get(
            '/users?ids[]={}&access=private'.format('jane'), self.ruphus)
        self.assertEqual(status_code, 200)
        self.assertEqual(data, {'users': []})

        # Two users by id, one without access, logging in
        data, status_code = self.get(
            '/users?ids[]={}&ids[]={}&access=private'.format(
                'jane', self.ruphus_dict_public['id']), self.jane)
        self.assertEqual(status_code, 200)
        self.assertEqual(data, {'users': [self.jane_dict_private]})

        # Two users by id, not logging in
        data, status_code = self.get(
            '/users?ids[]={}&ids[]={}&access=private'.format(
                'jane', self.ruphus_dict_public['id']))
        self.assertEqual(status_code, 401)
        self.assertEqual(data, self.error_401_dict)

    def test_root_get_private_operators_public(self):
        data, status_code = self.get('/users?id__contains=t',
                                     self.jane)
        self.assertEqual(status_code, 200)
        self.assertEqual(data, {'users': [self.toad_dict_public]})

        data, status_code = self.get('/users?id__contains=t&access=private',
                                     self.jane)
        self.assertEqual(status_code, 200)
        self.assertEqual(data, {'users': []})

        data, status_code = self.get('/users?n_exps__gt=1', self.sophie)
        self.assertEqual(status_code, 200)
        self.assertEqual(data, {'users': [self.sophie_dict_public]})

        data, status_code = self.get('/users?n_exps__gt=1&access=private',
                                     self.sophie)
        self.assertEqual(status_code, 200)
        self.assertEqual(data, {'users': [self.sophie_dict_private]})

        data, status_code = self.get('/users?n_exps__lte=1&id__startswith=to',
                                     self.toad)
        self.assertEqual(status_code, 200)
        self.assertEqual(data, {'users': [self.toad_dict_public]})

        data, status_code = self.get('/users?n_exps__lte=1&id__startswith=to'
                                     '&access=private', self.toad)
        self.assertEqual(status_code, 200)
        self.assertEqual(data, {'users': [self.toad_dict_private]})

        data, status_code = self.get(
            '/users?ids[]=toad&ids[]=sophie&n_exps__lt=2&access=private',
            self.toad)
        self.assertEqual(status_code, 200)
        self.assertEqual(data, {'users': [self.toad_dict_private]})

        data, status_code = self.get(
            '/users?ids[]=toad&ids[]=sophie&n_exps__lt=2&access=private',
            self.sophie)
        self.assertEqual(status_code, 200)
        self.assertEqual(data, {'users': []})

        data, status_code = self.get(
            '/users?n_exps__lt=3&n_exps__gte=1&access=private', self.sophie)
        self.assertEqual(status_code, 200)
        self.assertEqual(data, {'users': [self.sophie_dict_private]})

        data, status_code = self.get(
            '/users?exp_ids__contains={}&access=private'.format(
                self.sophie_exp2.exp_id[4:8]), self.sophie)
        self.assertEqual(status_code, 200)
        self.assertEqual(data, {'users': [self.sophie_dict_private]})

        data, status_code = self.get(
            '/users?exp_ids__contains={}&access=private'.format(
                self.sophie_exp2.exp_id[4:8]), self.toad)
        self.assertEqual(status_code, 200)
        self.assertEqual(data, {'users': []})

        data, status_code = self.get('/users?n_results__gt=1&access=private',
                                     self.sophie)
        self.assertEqual(status_code, 200)
        self.assertEqual(data, {'users': []})

        # Doubled query is ignored
        data, status_code = self.get(
            '/users?n_exps=1&n_exps=2&access=private', self.toad)
        self.assertEqual(status_code, 200)
        self.assertEqual(data, {'users': [self.toad_dict_private]})

        data, status_code = self.get(
            '/users?n_exps=2&n_exps=1&access=private', self.toad)
        self.assertEqual(status_code, 200)
        self.assertEqual(data, {'users': []})

    def test_root_get_private_operators_private(self):
        data, status_code = self.get('/users?persona_email__contains=jane',
                                     self.ruphus)
        self.assertEqual(status_code, 200)
        self.assertEqual(data, {'users': [self.jane_dict_public,
                                          self.ruphus_dict_public,
                                          self.sophie_dict_public,
                                          self.toad_dict_public]})

        data, status_code = self.get(
            '/users?persona_email__contains=jane&access=private', self.ruphus)
        self.assertEqual(status_code, 200)
        self.assertEqual(data, {'users': []})

        data, status_code = self.get(
            '/users?persona_email__contains=jane&access=private', self.jane)
        self.assertEqual(status_code, 200)
        self.assertEqual(data, {'users': [self.jane_dict_private]})

        data, status_code = self.get(
            '/users?n_exps__gt=1&persona_email__startswith=toad'
            '&access=private', self.toad)
        self.assertEqual(status_code, 200)
        self.assertEqual(data, {'users': []})

        data, status_code = self.get(
            '/users?n_exps__gt=1&persona_email__startswith=toad'
            '&access=private', self.sophie)
        self.assertEqual(status_code, 200)
        self.assertEqual(data, {'users': []})

        data, status_code = self.get(
            '/users?ids[]=toad&ids[]=sophie&n_exps__lt=2'
            '&persona_email=jane', self.jane)
        self.assertEqual(status_code, 200)
        self.assertEqual(data, {'users': [self.toad_dict_public]})

        data, status_code = self.get(
            '/users?ids[]=toad&ids[]=sophie&n_exps__lt=2'
            '&persona_email=jane&access=private', self.jane)
        self.assertEqual(status_code, 200)
        self.assertEqual(data, {'users': []})

        data, status_code = self.get(
            '/users?exp_ids__contains={}'
            '&persona_email=jane&access=private'.format(
                self.sophie_exp2.exp_id[4:8]), self.sophie)
        self.assertEqual(status_code, 200)
        self.assertEqual(data, {'users': []})

    def test_root_get_private_operators_unexisting_ignored(self):
        data, status_code = self.get('/users?nonfield__contains=jane'
                                     '&access=private', self.sophie)
        self.assertEqual(status_code, 200)
        self.assertEqual(data, {'users': [self.sophie_dict_private]})

        data, status_code = self.get(
            '/users?n_exps__gt=1&nonfield__startswith=toad&access=private',
            self.sophie)
        self.assertEqual(status_code, 200)
        self.assertEqual(data, {'users': [self.sophie_dict_private]})

        data, status_code = self.get(
            '/users?n_exps__gt=1&nonfield__startswith=toad&access=private',
            self.jane)
        self.assertEqual(status_code, 200)
        self.assertEqual(data, {'users': []})

        data, status_code = self.get(
            '/users?ids[]=toad&ids[]=sophie&n_exps__lt=2'
            '&nonfield=jane&access=private', self.sophie)
        self.assertEqual(status_code, 200)
        self.assertEqual(data, {'users': []})

        data, status_code = self.get(
            '/users?ids[]=toad&ids[]=sophie&n_exps__lt=2'
            '&nonfield=jane&access=private', self.toad)
        self.assertEqual(status_code, 200)
        self.assertEqual(data, {'users': [self.toad_dict_private]})

        data, status_code = self.get(
            '/users?exp_ids__contains={}&nonfield=jane'
            '&access=private'.format(self.sophie_exp2.exp_id[4:8]),
            self.sophie)
        self.assertEqual(status_code, 200)
        self.assertEqual(data, {'users': [self.sophie_dict_private]})

    def test_root_get_private_order(self):
        # None of this is very interesting since private access here
        # is always reduced to the authenticated user (at least for now)

        # ## Normal working order parameter

        data, status_code = self.get('/users?order=-id&access=private',
                                     self.jane)
        self.assertEqual(status_code, 200)
        self.assertEqual(data, {'users': [self.jane_dict_private]})

        # ## Multiple order parameters

        data, status_code = self.get(
            '/users?order=-n_exps&order=-id&access=private', self.sophie)
        self.assertEqual(status_code, 200)
        self.assertEqual(data, {'users': [self.sophie_dict_private]})

        # ## Combining order and other query

        data, status_code = self.get(
            '/users?order=-n_exps&n_exps__lte=1&access=private', self.jane)
        self.assertEqual(status_code, 200)
        self.assertEqual(data, {'users': [self.jane_dict_private]})
        data, status_code = self.get(
            '/users?order=+n_exps&order=-id&n_exps__lte=1'
            '&access=private', self.sophie)
        self.assertEqual(status_code, 200)
        self.assertEqual(data, {'users': []})
        data, status_code = self.get(
            '/users?order=-n_exps&id__contains=a&access=private', self.toad)
        self.assertEqual(status_code, 200)
        self.assertEqual(data, {'users': [self.toad_dict_private]})
        data, status_code = self.get(
            '/users?order=-n_exps&id__contains=a&access=private', self.sophie)
        self.assertEqual(status_code, 200)
        self.assertEqual(data, {'users': []})

    def test_root_get_private_order_private(self):
        # None of this is very interesting since private access here
        # is always reduced to the authenticated user (at least for now)

        # ## Private order parameter

        data, status_code = self.get(
            '/users?order=-persona_email&access=private', self.jane)
        self.assertEqual(status_code, 200)
        self.assertEqual(data, {'users': [self.jane_dict_private]})

        # ## Multiple order parameters, with private parameter

        data, status_code = self.get(
            '/users?order=-n_exps&order=-persona_email&access=private',
            self.toad)
        self.assertEqual(status_code, 200)
        self.assertEqual(data, {'users': [self.toad_dict_private]})
        data, status_code = self.get(
            '/users?order=-persona_email&order=-n_exps&access=private',
            self.sophie)
        self.assertEqual(status_code, 200)
        self.assertEqual(data, {'users': [self.sophie_dict_private]})

        # ## Combining order and other query, with private parameter

        data, status_code = self.get(
            '/users?order=-persona_email&n_exps__lte=1&access=private',
            self.jane)
        self.assertEqual(status_code, 200)
        self.assertEqual(data, {'users': [self.jane_dict_private]})

    def test_root_get_private_limit(self):
        # ## Limit alone

        data, status_code = self.get('/users?limit=2&access=private',
                                     self.jane)
        self.assertEqual(status_code, 200)
        self.assertEqual(data, {'users': [self.jane_dict_private]})
        data, status_code = self.get('/users?limit=5&access=private',
                                     self.sophie)
        self.assertEqual(status_code, 200)
        self.assertEqual(data, {'users': [self.sophie_dict_private]})

        # ## Limit with order

        data, status_code = self.get(
            '/users?limit=2&order=-n_exps&access=private', self.toad)
        self.assertEqual(status_code, 200)
        self.assertEqual(data, {'users': [self.toad_dict_private]})
        data, status_code = self.get(
            '/users?limit=5&order=-n_exps&order=-id&access=private',
            self.ruphus)
        self.assertEqual(status_code, 200)
        self.assertEqual(data, {'users': [self.ruphus_dict_private]})

        # ## Limit with order and other parameter

        data, status_code = self.get(
            '/users?limit=1&order=-n_exps&id__contains=a&access=private',
            self.jane)
        self.assertEqual(status_code, 200)
        self.assertEqual(data, {'users': [self.jane_dict_private]})
        data, status_code = self.get(
            '/users?limit=1&order=-n_exps&id__contains=a&access=private',
            self.toad)
        self.assertEqual(status_code, 200)
        self.assertEqual(data, {'users': [self.toad_dict_private]})
        data, status_code = self.get(
            '/users?limit=5&order=-n_exps&n_exps__lte=1&order=-id'
            '&access=private', self.jane)
        self.assertEqual(status_code, 200)
        self.assertEqual(data, {'users': [self.jane_dict_private]})

    def test_root_get_private_malformed_query_valid_field(self):
        # Unknown operator
        data, status_code = self.get(
            '/users?persona_email__notoperator=a&access=private', self.jane)
        self.assertEqual(status_code, 400)
        self.assertEqual(data, self.error_400_query_unknown_operator_dict)
        # `count` is particular in that it does exist in mongoengine,
        # but is rejected here
        data, status_code = self.get('/users?exp_ids__count=2&access=private',
                                     self.jane)
        self.assertEqual(status_code, 400)
        self.assertEqual(data, self.error_400_query_unknown_operator_dict)

        # Query too deep
        data, status_code = self.get(
            '/users?persona_email__count__lt=2&access=private', self.jane)
        self.assertEqual(status_code, 400)
        self.assertEqual(data, self.error_400_query_too_deep_dict)

        # Querying on other than {list of} string/number/date
        data, status_code = self.get(
            '/users?user_id_is_set=True&access=private', self.jane)
        self.assertEqual(status_code, 400)
        self.assertEqual(data, self.error_400_query_non_queriable_dict)

        # Regexp on a field that's not a string or a list of strings
        data, status_code = self.get(
            '/users?n_exps__startswith=1&access=private', self.jane)
        self.assertEqual(status_code, 400)
        self.assertEqual(data, self.error_400_query_bad_typing_dict)
        data, status_code = self.get(
            '/users?n_exps__contains=1&access=private', self.jane)
        self.assertEqual(status_code, 400)
        self.assertEqual(data, self.error_400_query_bad_typing_dict)
        data, status_code = self.get(
            '/users?n_exps__exact=1&access=private', self.jane)
        self.assertEqual(status_code, 400)
        self.assertEqual(data, self.error_400_query_bad_typing_dict)

        # Unparsable number
        data, status_code = self.get('/users?n_exps__gte=a&access=private',
                                     self.jane)
        self.assertEqual(status_code, 400)
        self.assertEqual(data, self.error_400_query_parsing_dict)
        data, status_code = self.get('/users?n_exps__gte=1.0&access=private',
                                     self.jane)
        self.assertEqual(status_code, 400)
        self.assertEqual(data, self.error_400_query_parsing_dict)

    def test_root_get_private_limit_non_number(self):
        data, status_code = self.get('/users?limit=a&access=private',
                                     self.jane)
        self.assertEqual(status_code, 400)
        self.assertEqual(data, self.error_400_query_parsing_dict)
        data, status_code = self.get('/users?limit=10.0&access=private',
                                     self.jane)
        self.assertEqual(status_code, 400)
        self.assertEqual(data, self.error_400_query_parsing_dict)

    def test_root_get_private_order_not_orderable(self):
        # With a boolean
        data, status_code = self.get(
            '/users?order=user_id_is_set&access=private', self.jane)
        self.assertEqual(status_code, 400)
        self.assertEqual(data, self.error_400_query_non_orderable_dict)

        # With a list
        data, status_code = self.get('/users?order=exp_ids&access=private',
                                     self.jane)
        self.assertEqual(status_code, 400)
        self.assertEqual(data, self.error_400_query_non_orderable_dict)

    def test_me_get(self):
        # A user with his user_id set
        data, status_code = self.get('/users/me', self.jane)
        self.assertEqual(status_code, 200)
        self.assertEqual(data, {'user': self.jane_dict_private})

        # A user with his user_id not set
        data, status_code = self.get('/users/me', self.ruphus)
        self.assertEqual(status_code, 200)
        self.assertEqual(data, {'user': self.ruphus_dict_private})
        self.assertEqual(data['user']['id'][:10], 'ru.p_h-us-')
        self.assertRegexpMatches(data['user']['id'][10:], hexregex)

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

        # ## Now without authentication

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

        # ## Now without authentication

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

    def test_user_put_successful(self):
        # Set the user_id for user with user_id not set
        data, status_code = self.put('/users/{}'.format(self.ruphus.user_id),
                                     {'user': {'id': 'ruphus'}},
                                     self.ruphus)
        self.assertEqual(status_code, 200)
        self.assertEqual(data, {'user': self.ruphus_dict_private_with_user_id})
        self.ruphus.reload()
        self.assertEqual(self.ruphus.user_id, 'ruphus')
        self.assertTrue(self.ruphus.user_id_is_set)

    def test_user_put_should_ignore_additional_data(self):
        data, status_code = self.put('/users/{}'.format(self.ruphus.user_id),
                                     {'user':
                                      {'id': 'ruphus', 'other': 'bla'},
                                      'other_root': 'blabla'},
                                     self.ruphus)
        self.assertEqual(status_code, 200)
        self.assertEqual(data, {'user': self.ruphus_dict_private_with_user_id})

    def test_user_put_user_not_found(self):
        data, status_code = self.put('/users/missing',
                                     {'user': {'id': 'ruphus'}},
                                     self.ruphus)
        self.assertEqual(status_code, 404)
        self.assertEqual(data, self.error_404_does_not_exist_dict)

    def test_user_put_user_not_found_error_priorities(self):
        # With no authentication and malformed data
        data, status_code = self.put('/users/missing',
                                     '{"malformed JSON"',
                                     dump_json_data=False)
        self.assertEqual(status_code, 404)
        self.assertEqual(data, self.error_404_does_not_exist_dict)

        # With no authentication and no 'user' root object
        data, status_code = self.put('/users/missing',
                                     {'not-user': 'bla'})
        self.assertEqual(status_code, 404)
        self.assertEqual(data, self.error_404_does_not_exist_dict)

        # With no authentication and missing required field
        data, status_code = self.put('/users/missing',
                                     {'user': {'no_user_id': 'ruphus'}})
        self.assertEqual(status_code, 404)
        self.assertEqual(data, self.error_404_does_not_exist_dict)

        # No authentication and user_id already set makes no sense

        # With no authentication and wrong user_id format
        data, status_code = self.put('/users/missing',
                                     {'user': {'id': '-ruphus'}})
        self.assertEqual(status_code, 404)
        self.assertEqual(data, self.error_404_does_not_exist_dict)

        # With no authentication and user_id already taken
        data, status_code = self.put('/users/missing',
                                     {'user': {'id': 'jane'}})
        self.assertEqual(status_code, 404)
        self.assertEqual(data, self.error_404_does_not_exist_dict)

        # With authentication but malformed data
        data, status_code = self.put('/users/missing',
                                     '{"malformed JSON"',
                                     self.jane,
                                     dump_json_data=False)
        self.assertEqual(status_code, 404)
        self.assertEqual(data, self.error_404_does_not_exist_dict)

        # With authentication but no 'user' root object
        data, status_code = self.put('/users/missing',
                                     {'not-user': 'bla'},
                                     self.jane)
        self.assertEqual(status_code, 404)
        self.assertEqual(data, self.error_404_does_not_exist_dict)

        # Authenticated as another user and missing required field
        data, status_code = self.put('/users/missing',
                                     {'user': {'no_user_id': 'ruphus'}},
                                     self.jane)
        self.assertEqual(status_code, 404)
        self.assertEqual(data, self.error_404_does_not_exist_dict)

        # Authenticated as another user and user_id already set
        data, status_code = self.put('/users/missing',
                                     {'user': {'id': 'jane2'}},
                                     self.jane)
        self.assertEqual(status_code, 404)
        self.assertEqual(data, self.error_404_does_not_exist_dict)

        # Authenticated as another user and wrong user_id syntax
        data, status_code = self.put('/users/missing',
                                     {'user': {'id': '-ruphus'}},
                                     self.ruphus)
        self.assertEqual(status_code, 404)
        self.assertEqual(data, self.error_404_does_not_exist_dict)

        # Authenticated as another user and an already taken user_id
        data, status_code = self.put('/users/missing',
                                     {'user': {'id': 'jane'}},
                                     self.ruphus)
        self.assertEqual(status_code, 404)
        self.assertEqual(data, self.error_404_does_not_exist_dict)

        # All other combinations make no sense or involve incompatible errors

    def test_user_put_no_authentication(self):
        data, status_code = self.put('/users/{}'.format(self.ruphus.user_id),
                                     {'user': {'id': 'ruphus'}})
        self.assertEqual(status_code, 401)
        self.assertEqual(data, self.error_401_dict)

    def test_user_put_no_authentication_error_priorities(self):
        # Bad JSON
        data, status_code = self.put('/users/{}'.format(self.ruphus.user_id),
                                     '{"malformed JSON"',
                                     dump_json_data=False)
        self.assertEqual(status_code, 401)
        self.assertEqual(data, self.error_401_dict)

        # Good JSON but no root 'user' object
        data, status_code = self.put('/users/{}'.format(self.ruphus.user_id),
                                     {'not-user': 'bla'})
        self.assertEqual(status_code, 401)
        self.assertEqual(data, self.error_401_dict)

        # With missing required field
        data, status_code = self.put('/users/{}'.format(self.ruphus.user_id),
                                     {'user': {'no_user_id': 'ruphus'}})
        self.assertEqual(status_code, 401)
        self.assertEqual(data, self.error_401_dict)

        # Authenticated as another user makes no sense since we required the
        # 'no authentication' error

        # With a user_id already set
        data, status_code = self.put('/users/jane',
                                     {'user': {'id': 'jane2'}})
        self.assertEqual(status_code, 401)
        self.assertEqual(data, self.error_401_dict)

        # With a wrong user_id syntax
        data, status_code = self.put('/users/{}'.format(self.ruphus.user_id),
                                     {'user': {'id': '-ruphus'}})
        self.assertEqual(status_code, 401)
        self.assertEqual(data, self.error_401_dict)

        # With an already taken user_id
        data, status_code = self.put('/users/{}'.format(self.ruphus.user_id),
                                     {'user': {'id': 'jane'}})
        self.assertEqual(status_code, 401)
        self.assertEqual(data, self.error_401_dict)

        # All other combinations make no sense or involve incompatible errors

    def test_user_put_malformed_data(self):
        # Bad JSON
        data, status_code = self.put('/users/{}'.format(self.ruphus.user_id),
                                     '{"malformed JSON"',
                                     self.ruphus, dump_json_data=False)
        self.assertEqual(status_code, 400)
        self.assertEqual(data, self.error_400_malformed_dict)

        # Good JSON, but no root 'user' object
        data, status_code = self.put('/users/{}'.format(self.ruphus.user_id),
                                     {'not-user': 'bla'},
                                     self.ruphus)
        self.assertEqual(status_code, 400)
        self.assertEqual(data, self.error_400_malformed_dict)

    # All other errors make no sense if data is malformed,
    # so no test_user_put_malformed_data_error_priorities here

    def test_user_put_missing_required_field(self):
        data, status_code = self.put('/users/{}'.format(self.ruphus.user_id),
                                     {'user': {'no_user_id': 'ruphus'}},
                                     self.ruphus)
        self.assertEqual(status_code, 400)
        self.assertEqual(data, self.error_400_missing_requirement_dict)

    def test_user_put_missing_required_field_error_priorities(self):
        # Authenticated as another user and user_id set and wrong user_id
        # syntax
        data, status_code = self.put('/users/jane',
                                     {'user': {'no_user_id': '-jane2'}},
                                     self.ruphus)
        self.assertEqual(status_code, 400)
        self.assertEqual(data, self.error_400_missing_requirement_dict)

        # With user_id already set and wrong user_id syntax
        data, status_code = self.put('/users/jane',
                                     {'user': {'no_user_id': '-jane2'}},
                                     self.jane)
        self.assertEqual(status_code, 400)
        self.assertEqual(data, self.error_400_missing_requirement_dict)

        # Wrong user_id syntax
        data, status_code = self.put('/users/{}'.format(self.ruphus.user_id),
                                     {'user': {'no_user_id': '-ruphus'}},
                                     self.ruphus)
        self.assertEqual(status_code, 400)
        self.assertEqual(data, self.error_400_missing_requirement_dict)

        # user_id already taken
        data, status_code = self.put('/users/{}'.format(self.ruphus.user_id),
                                     {'user': {'no_user_id': 'jane'}},
                                     self.ruphus)
        self.assertEqual(status_code, 400)
        self.assertEqual(data, self.error_400_missing_requirement_dict)

    def test_user_put_authenticated_as_other_user(self):
        # Authenticated as another user
        data, status_code = self.put('/users/{}'.format(self.ruphus.user_id),
                                     {'user': {'id': 'ruphus'}},
                                     self.jane)
        self.assertEqual(status_code, 403)
        self.assertEqual(data, self.error_403_unauthorized_dict)

    def test_user_put_authenticated_as_other_user_error_priorities(self):
        # With user_id already set and wrong user_id syntax
        data, status_code = self.put('/users/jane',
                                     {'user': {'id': '-jane2'}},
                                     self.ruphus)
        self.assertEqual(status_code, 403)
        self.assertEqual(data, self.error_403_unauthorized_dict)

        # Wrong user_id syntax
        data, status_code = self.put('/users/{}'.format(self.ruphus.user_id),
                                     {'user': {'id': '-ruphus'}},
                                     self.jane)
        self.assertEqual(status_code, 403)
        self.assertEqual(data, self.error_403_unauthorized_dict)

        # user_id already taken
        data, status_code = self.put('/users/{}'.format(self.ruphus.user_id),
                                     {'user': {'id': 'jane'}},
                                     self.jane)
        self.assertEqual(status_code, 403)
        self.assertEqual(data, self.error_403_unauthorized_dict)

    def test_user_put_user_id_set(self):
        # With Jane
        data, status_code = self.put('/users/jane',
                                     {'user': {'id': 'jane2'}},
                                     self.jane)
        self.assertEqual(status_code, 403)
        self.assertEqual(data, self.error_403_user_id_set_dict)

        # With Ruphus
        self.put('/users/{}'.format(self.ruphus.user_id),
                 {'user': {'id': 'ruphus'}},
                 self.ruphus)
        self.ruphus.reload()
        data, status_code = self.put('/users/ruphus',
                                     {'user': {'id': 'ruphus2'}},
                                     self.ruphus)
        self.assertEqual(status_code, 403)
        self.assertEqual(data, self.error_403_user_id_set_dict)

    def test_user_put_user_id_set_error_priorities(self):
        # ## Wrong user_id syntax
        # With Jane
        data, status_code = self.put('/users/jane',
                                     {'user': {'id': '-jane2'}},
                                     self.jane)
        self.assertEqual(status_code, 403)
        self.assertEqual(data, self.error_403_user_id_set_dict)

        # With Ruphus
        self.put('/users/{}'.format(self.ruphus.user_id),
                 {'user': {'id': 'ruphus'}},
                 self.ruphus)
        self.ruphus.reload()
        data, status_code = self.put('/users/ruphus',
                                     {'user': {'id': '-ruphus2'}},
                                     self.ruphus)
        self.assertEqual(status_code, 403)
        self.assertEqual(data, self.error_403_user_id_set_dict)

        # ## user_id already taken
        # With Jane
        data, status_code = self.put('/users/jane',
                                     {'user':
                                      {'id': self.ruphus.user_id}},
                                     self.jane)
        self.assertEqual(status_code, 403)
        self.assertEqual(data, self.error_403_user_id_set_dict)

        # With Ruphus
        self.put('/users/{}'.format(self.ruphus.user_id),
                 {'user': {'id': 'ruphus'}},
                 self.ruphus)
        self.ruphus.reload()
        data, status_code = self.put('/users/ruphus',
                                     {'user': {'id': 'jane'}},
                                     self.ruphus)
        self.assertEqual(status_code, 403)
        self.assertEqual(data, self.error_403_user_id_set_dict)

    def test_user_put_wrong_user_id_syntax(self):
        data, status_code = self.put('/users/{}'.format(self.ruphus.user_id),
                                     {'user': {'id': '-ruphus'}},
                                     self.ruphus)
        self.assertEqual(status_code, 400)
        self.assertEqual(data, self.error_400_bad_syntax_dict)

    # No error-priority test here: only one left is user_id already taken,
    # which implies that the submitted user_id has the right syntax

    def test_user_put_user_id_reserved(self):
        data, status_code = self.put('/users/{}'.format(self.ruphus.user_id),
                                     {'user': {'id': 'new'}},
                                     self.ruphus)
        self.assertEqual(status_code, 409)
        self.assertEqual(data, self.error_409_user_id_reserved_dict)
        data, status_code = self.put('/users/{}'.format(self.ruphus.user_id),
                                     {'user': {'id': 'settings'}},
                                     self.ruphus)
        self.assertEqual(status_code, 409)
        self.assertEqual(data, self.error_409_user_id_reserved_dict)

    # No error-priority test with "user_id already taken" because a reserved
    # user_id will never be taken

    def test_user_put_user_id_already_taken(self):
        data, status_code = self.put('/users/{}'.format(self.ruphus.user_id),
                                     {'user': {'id': 'jane'}},
                                     self.ruphus)
        self.assertEqual(status_code, 409)
        self.assertEqual(data, self.error_409_field_conflict_dict)

    # No error-priority test here: this was the last error
