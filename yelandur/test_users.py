# -*- coding: utf-8 -*-

from .models import User, Exp
from .helpers import hexregex, sha256hex, APITestCase


# TODO: add CORS test


class UsersTestCase(APITestCase):

    def setUp(self):
        super(UsersTestCase, self).setUp()

        # Two test users to work with
        self.jane = User.get_or_create_by_email('jane@example.com')
        self.jane.set_user_id('jane')
        self.ruphus = User.get_or_create_by_email('ruphus@example.com')

        # Their corresponding dicts
        self.jane_dict_public = {'user_id': 'jane',
                                 'user_id_is_set': True,
                                 'gravatar_id': ('9e26471d35a78862'
                                                 'c17e467d87cddedf'),
                                 'exp_ids': [],
                                 'n_profiles': 0,
                                 'n_devices': 0,
                                 'n_results': 0}
        self.jane_dict_private = self.jane_dict_public.copy()
        # Prevent the copy from keeping the same list
        self.jane_dict_private['exp_ids'] = []
        self.jane_dict_private['persona_email'] = 'jane@example.com'
        self.ruphus_dict_public = {'user_id': self.ruphus.user_id,
                                   'user_id_is_set': False,
                                   'gravatar_id': ('441d567f9db81987'
                                                   'ca712fed581d17d9'),
                                   'exp_ids': [],
                                   'n_profiles': 0,
                                   'n_devices': 0,
                                   'n_results': 0}
        self.ruphus_dict_private = self.ruphus_dict_public.copy()
        # Prevent the copy from keeping the same list
        self.ruphus_dict_private['exp_ids'] = []
        self.ruphus_dict_private['persona_email'] = 'ruphus@example.com'
        self.ruphus_dict_private_with_user_id = self.ruphus_dict_private.copy()
        # Prevent the copy from keeping the same list
        self.ruphus_dict_private_with_user_id['exp_ids'] = []
        self.ruphus_dict_private_with_user_id['user_id'] = 'ruphus'
        self.ruphus_dict_private_with_user_id['user_id_is_set'] = True

        # 403 resource can't be changed
        self.error_403_user_id_set_dict = {
            'error': {'status_code': 403,
                      'type': 'UserIdSet',
                      'message': 'user_id has already been set'}}

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
        # FIXME: adapt once ordering works
        self.assertEqual(data.keys(), ['users'])
        self.assertIn(self.jane_dict_public, data['users'])
        self.assertIn(self.ruphus_dict_public, data['users'])
        self.assertEqual(len(data['users']), 2)

        # A user with his user_id not set
        data, status_code = self.get('/users/', self.ruphus)
        self.assertEqual(status_code, 200)
        # FIXME: adapt once ordering works
        self.assertEqual(data.keys(), ['users'])
        self.assertIn(self.jane_dict_public, data['users'])
        self.assertIn(self.ruphus_dict_public, data['users'])
        self.assertEqual(len(data['users']), 2)

        # Without loging in
        data, status_code = self.get('/users/')
        self.assertEqual(status_code, 200)
        # FIXME: adapt once ordering works
        self.assertEqual(data.keys(), ['users'])
        self.assertIn(self.jane_dict_public, data['users'])
        self.assertIn(self.ruphus_dict_public, data['users'])
        self.assertEqual(len(data['users']), 2)

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
        exp_id = sha256hex('jane/test-exp')
        self.jane_dict_public['exp_ids'].append(exp_id)
        self.jane_dict_private['exp_ids'].append(exp_id)
        self.ruphus_dict_public['exp_ids'].append(exp_id)
        self.ruphus_dict_private['exp_ids'].append(exp_id)
        self.ruphus_dict_private_with_user_id['exp_ids'].append(exp_id)

        # Add a user to make sure the following answers aren't just
        # including all available users
        u = User.get_or_create_by_email('temp@example.com')
        u.set_user_id('temp')

        # Jane sees both herself and Ruphus
        data, status_code = self.get('/users/?access=private',
                                     self.jane)
        self.assertEqual(status_code, 200)
        # FIXME: adapt once ordering works
        self.assertEqual(data.keys(), ['users'])
        self.assertIn(self.jane_dict_private, data['users'])
        self.assertIn(self.ruphus_dict_private_with_user_id, data['users'])
        self.assertEqual(len(data['users']), 2)

        # Ruphus sees both himself and Jane
        data, status_code = self.get('/users/?access=private',
                                     self.ruphus)
        self.assertEqual(status_code, 200)
        # FIXME: adapt once ordering works
        self.assertEqual(data.keys(), ['users'])
        self.assertIn(self.jane_dict_private, data['users'])
        self.assertIn(self.ruphus_dict_private_with_user_id, data['users'])
        self.assertEqual(len(data['users']), 2)

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
        exp_id = sha256hex('jane/test-exp')
        self.jane_dict_public['exp_ids'].append(exp_id)
        self.jane_dict_private['exp_ids'].append(exp_id)
        self.ruphus_dict_public['exp_ids'].append(exp_id)
        self.ruphus_dict_private['exp_ids'].append(exp_id)
        self.ruphus_dict_private_with_user_id['exp_ids'].append(exp_id)

        data, status_code = self.get('/users/ruphus?access=private',
                                     self.jane)
        self.assertEqual(status_code, 200)
        self.assertEqual(data,
                         {'user': self.ruphus_dict_private_with_user_id})

        data, status_code = self.get('/users/jane?access=private',
                                     self.ruphus)
        self.assertEqual(status_code, 200)
        self.assertEqual(data, {'user': self.jane_dict_private})

    def test_user_put_successful(self):
        # Set the user_id for user with user_id not set
        data, status_code = self.put('/users/{}'.format(self.ruphus.user_id),
                                     {'user': {'user_id': 'ruphus'}},
                                     self.ruphus)
        self.assertEqual(status_code, 200)
        self.assertEqual(data, {'user': self.ruphus_dict_private_with_user_id})
        self.ruphus.reload()
        self.assertEqual(self.ruphus.user_id, 'ruphus')
        self.assertTrue(self.ruphus.user_id_is_set)

    def test_user_put_should_ignore_additional_data(self):
        data, status_code = self.put('/users/{}'.format(self.ruphus.user_id),
                                     {'user':
                                      {'user_id': 'ruphus', 'other': 'bla'},
                                      'other_root': 'blabla'},
                                     self.ruphus)
        self.assertEqual(status_code, 200)
        self.assertEqual(data, {'user': self.ruphus_dict_private_with_user_id})

    def test_user_put_user_not_found(self):
        data, status_code = self.put('/users/missing',
                                     {'user': {'user_id': 'ruphus'}},
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
                                     {'user': {'user_id': '-ruphus'}})
        self.assertEqual(status_code, 404)
        self.assertEqual(data, self.error_404_does_not_exist_dict)

        # With no authentication and user_id already taken
        data, status_code = self.put('/users/missing',
                                     {'user': {'user_id': 'jane'}})
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
                                     {'user': {'user_id': 'jane2'}},
                                     self.jane)
        self.assertEqual(status_code, 404)
        self.assertEqual(data, self.error_404_does_not_exist_dict)

        # Authenticated as another user and wrong user_id syntax
        data, status_code = self.put('/users/missing',
                                     {'user': {'user_id': '-ruphus'}},
                                     self.ruphus)
        self.assertEqual(status_code, 404)
        self.assertEqual(data, self.error_404_does_not_exist_dict)

        # Authenticated as another user and an already taken user_id
        data, status_code = self.put('/users/missing',
                                     {'user': {'user_id': 'jane'}},
                                     self.ruphus)
        self.assertEqual(status_code, 404)
        self.assertEqual(data, self.error_404_does_not_exist_dict)

        # All other combinations make no sense or involve incompatible errors

    def test_user_put_no_authentication(self):
        data, status_code = self.put('/users/{}'.format(self.ruphus.user_id),
                                     {'user': {'user_id': 'ruphus'}})
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
                                     {'user': {'user_id': 'jane2'}})
        self.assertEqual(status_code, 401)
        self.assertEqual(data, self.error_401_dict)

        # With a wrong user_id syntax
        data, status_code = self.put('/users/{}'.format(self.ruphus.user_id),
                                     {'user': {'user_id': '-ruphus'}})
        self.assertEqual(status_code, 401)
        self.assertEqual(data, self.error_401_dict)

        # With an already taken user_id
        data, status_code = self.put('/users/{}'.format(self.ruphus.user_id),
                                     {'user': {'user_id': 'jane'}})
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
                                     {'user': {'user_id': 'ruphus'}},
                                     self.jane)
        self.assertEqual(status_code, 403)
        self.assertEqual(data, self.error_403_unauthorized_dict)

    def test_user_put_authenticated_as_other_user_error_priorities(self):
        # With user_id already set and wrong user_id syntax
        data, status_code = self.put('/users/jane',
                                     {'user': {'user_id': '-jane2'}},
                                     self.ruphus)
        self.assertEqual(status_code, 403)
        self.assertEqual(data, self.error_403_unauthorized_dict)

        # Wrong user_id syntax
        data, status_code = self.put('/users/{}'.format(self.ruphus.user_id),
                                     {'user': {'user_id': '-ruphus'}},
                                     self.jane)
        self.assertEqual(status_code, 403)
        self.assertEqual(data, self.error_403_unauthorized_dict)

        # user_id already taken
        data, status_code = self.put('/users/{}'.format(self.ruphus.user_id),
                                     {'user': {'user_id': 'jane'}},
                                     self.jane)
        self.assertEqual(status_code, 403)
        self.assertEqual(data, self.error_403_unauthorized_dict)

    def test_user_put_user_id_set(self):
        # With Jane
        data, status_code = self.put('/users/jane',
                                     {'user': {'user_id': 'jane2'}},
                                     self.jane)
        self.assertEqual(status_code, 403)
        self.assertEqual(data, self.error_403_user_id_set_dict)

        # With Ruphus
        self.put('/users/{}'.format(self.ruphus.user_id),
                 {'user': {'user_id': 'ruphus'}},
                 self.ruphus)
        self.ruphus.reload()
        data, status_code = self.put('/users/ruphus',
                                     {'user': {'user_id': 'ruphus2'}},
                                     self.ruphus)
        self.assertEqual(status_code, 403)
        self.assertEqual(data, self.error_403_user_id_set_dict)

    def test_user_put_user_id_set_error_priorities(self):
        ## Wrong user_id syntax
        # With Jane
        data, status_code = self.put('/users/jane',
                                     {'user': {'user_id': '-jane2'}},
                                     self.jane)
        self.assertEqual(status_code, 403)
        self.assertEqual(data, self.error_403_user_id_set_dict)

        # With Ruphus
        self.put('/users/{}'.format(self.ruphus.user_id),
                 {'user': {'user_id': 'ruphus'}},
                 self.ruphus)
        self.ruphus.reload()
        data, status_code = self.put('/users/ruphus',
                                     {'user': {'user_id': '-ruphus2'}},
                                     self.ruphus)
        self.assertEqual(status_code, 403)
        self.assertEqual(data, self.error_403_user_id_set_dict)

        ## user_id already taken
        # With Jane
        data, status_code = self.put('/users/jane',
                                     {'user':
                                      {'user_id': self.ruphus.user_id}},
                                     self.jane)
        self.assertEqual(status_code, 403)
        self.assertEqual(data, self.error_403_user_id_set_dict)

        # With Ruphus
        self.put('/users/{}'.format(self.ruphus.user_id),
                 {'user': {'user_id': 'ruphus'}},
                 self.ruphus)
        self.ruphus.reload()
        data, status_code = self.put('/users/ruphus',
                                     {'user': {'user_id': 'jane'}},
                                     self.ruphus)
        self.assertEqual(status_code, 403)
        self.assertEqual(data, self.error_403_user_id_set_dict)

    def test_user_put_wrong_user_id_syntax(self):
        data, status_code = self.put('/users/{}'.format(self.ruphus.user_id),
                                     {'user': {'user_id': '-ruphus'}},
                                     self.ruphus)
        self.assertEqual(status_code, 400)
        self.assertEqual(data, self.error_400_bad_syntax_dict)

    # No error-priority test here: only one left is user_id already taken,
    # which implies that the submitted user_id has the right syntax

    def test_user_put_user_id_already_taken(self):
        data, status_code = self.put('/users/{}'.format(self.ruphus.user_id),
                                     {'user': {'user_id': 'jane'}},
                                     self.ruphus)
        self.assertEqual(status_code, 409)
        self.assertEqual(data, self.error_409_field_conflict_dict)

    # No error-priority test here: this was the last error
