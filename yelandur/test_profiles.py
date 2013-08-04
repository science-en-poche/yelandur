# -*- coding: utf-8 -*-

from unittest import skip

import ecdsa

from .models import User, Exp, Device, Profile
from .helpers import APITestCase, sha256hex


class ProfilesTestCase(APITestCase):

    def setUp(self):
        super(ProfilesTestCase, self).setUp()

        # Some users to work with
        self.jane = User.get_or_create_by_email('jane@example.com')
        self.jane.set_user_id('jane')
        self.bill = User.get_or_create_by_email('bill@example.com')
        self.bill.set_user_id('bill')
        self.sophia = User.get_or_create_by_email('sophia@example.com')
        self.sophia.set_user_id('sophia')

        # Two experiments to work with
        self.exp_nd = Exp.create('numerical-distance', self.jane,
                                 'The numerical distance experiment, '
                                 'on smartphones', [self.bill])
        self.exp_gp = Exp.create('gender-priming', self.sophia,
                                 'Controversial gender priming effects')

        # Two devices to work with
        self.d1_sk = ecdsa.SigningKey.generate(curve=ecdsa.curves.NIST256p)
        self.d1 = Device.create(self.d1_sk.verifying_key.to_pem())
        self.d2_sk = ecdsa.SigningKey.generate(curve=ecdsa.curves.NIST256p)
        self.d2 = Device.create(self.d2_sk.verifying_key.to_pem())

        ## Two profiles to work with

        # One with a device
        self.p1_sk = ecdsa.SigningKey.generate(curve=ecdsa.curves.NIST256p)
        self.p1_vk = self.p1_sk.verifying_key
        self.p1_dict_public = {'profile_id': sha256hex(self.p1_vk.to_pem()),
                               'vk_pem': self.p1_vk.to_pem()}
        self.p1_dict_private = self.p1_dict_public.copy()
        self.p1_dict_private.extend({'exp_id': self.exp_nd['exp_id'],
                                     'device_id': self.d1['device_id'],
                                     'data': {'occupation': 'student'},
                                     'n_results': 0})

        # The other without device
        self.p2_sk = ecdsa.SigningKey.generate(curve=ecdsa.curves.NIST256p)
        self.p2_vk = self.p2_sk.verifying_key
        self.p2_dict_public = {'profile_id': sha256hex(self.p2_vk.to_pem()),
                               'vk_pem': self.p2_vk.to_pem()}
        self.p2_dict_private = self.p2_dict_public.copy()
        self.p2_dict_private.extend({'exp_id': self.exp_gp['exp_id'],
                                     'data': {'occupation': 'social worker'},
                                     'n_results': 0})

    def create_profiles(self):
        self.p1 = Profile.create(self.p1_vk.to_pem(),
                                 self.exp_nd, {'occupation': 'student'},
                                 self.d1)
        self.p2 = Profile.create(self.p2_vk.to_pem(),
                                 self.exp_gp, {'occupation': 'social worker'})

    @skip('not implemented yet')
    def test_profile_get_no_auth(self):
        self.create_profiles()

        # For p1
        data, status_code = self.get('/profiles/{}'.format(
            self.p1_dict_public['profile_id']))
        self.assertEqual(status_code, 200)
        self.assertEqual(data, {'profile': self.p1_dict_public})

        # For p2
        data, status_code = self.get('/profiles/{}'.format(
            self.p2_dict_public['profile_id']))
        self.assertEqual(status_code, 200)
        self.assertEqual(data, {'profile': self.p2_dict_public})

        ## Now asking for private access

        # For p1
        data, status_code = self.get('/profiles/{}?access=private'.format(
            self.p1_dict_public['profile_id']))
        self.assertEqual(status_code, 401)
        self.assertEqual(data, self.error_401_dict)

        # For p2
        data, status_code = self.get('/profiles/{}?access=private'.format(
            self.p2_dict_public['profile_id']))
        self.assertEqual(status_code, 401)
        self.assertEqual(data, self.error_401_dict)

    @skip('not implemented yet')
    def test_profile_get_with_auth(self):
        self.create_profiles()

        ## GET with auth to accessible profile (owner, collab)

        # As owner
        data, status_code = self.get('/profiles/{}'.format(
            self.p1_dict_public['profile_id']), self.jane)
        self.assertEqual(status_code, 200)
        self.assertEqual(data, {'profile': self.p1_dict_public})

        # As collaborator
        data, status_code = self.get('/profiles/{}'.format(
            self.p1_dict_public['profile_id']), self.bill)
        self.assertEqual(status_code, 200)
        self.assertEqual(data, {'profile': self.p1_dict_public})

        ## GET with auth to non-privately-accessible profile

        data, status_code = self.get('/profiles/{}'.format(
            self.p2_dict_public['profile_id']), self.jane)
        self.assertEqual(status_code, 200)
        self.assertEqual(data, {'profile': self.p2_dict_public})

        ## GET with auth with private access to accessible profile (owner,
        ## collab)

        # As owner
        data, status_code = self.get('/profiles/{}?access=private'.format(
            self.p1_dict_public['profile_id']), self.jane)
        self.assertEqual(status_code, 200)
        self.assertEqual(data, {'profile': self.p1_dict_private})

        # As collaborator
        data, status_code = self.get('/profiles/{}?access=private'.format(
            self.p1_dict_public['profile_id']), self.bill)
        self.assertEqual(status_code, 200)
        self.assertEqual(data, {'profile': self.p1_dict_private})

        ## GET with auth with private access to non-accessible profile

        data, status_code = self.get('/profiles/{}?access=private'.format(
            self.p2_dict_public['profile_id']), self.jane)
        self.assertEqual(status_code, 403)
        self.assertEqual(data, self.error_403_unauthorized_dict)

    @skip('not implemented yet')
    def test_profile_get_not_found(self):
        ### With auth

        ## GET with auth to privately-accessible profile

        # As owner
        data, status_code = self.get('/profiles/{}'.format(
            self.p1_dict_public['profile_id']), self.jane)
        self.assertEqual(status_code, 404)
        self.assertEqual(data, self.error_404_does_not_exist_dict)

        # As collaborator
        data, status_code = self.get('/profiles/{}'.format(
            self.p1_dict_public['profile_id']), self.bill)
        self.assertEqual(status_code, 404)
        self.assertEqual(data, self.error_404_does_not_exist_dict)

        ## GET with auth to non-privately-accessible profile

        data, status_code = self.get('/profiles/{}'.format(
            self.p2_dict_public['profile_id']), self.jane)
        self.assertEqual(status_code, 404)
        self.assertEqual(data, self.error_404_does_not_exist_dict)

        ## GET with auth with private access to accessible profile (owner,
        ## collab)

        # As owner
        data, status_code = self.get('/profiles/{}?access=private'.format(
            self.p1_dict_public['profile_id']), self.jane)
        self.assertEqual(status_code, 404)
        self.assertEqual(data, self.error_404_does_not_exist_dict)

        # As collaborator
        data, status_code = self.get('/profiles/{}?access=private'.format(
            self.p1_dict_public['profile_id']), self.bill)
        self.assertEqual(status_code, 404)
        self.assertEqual(data, self.error_404_does_not_exist_dict)

        ## GET with auth with private access to non-accessible profile

        data, status_code = self.get('/profiles/{}?access=private'.format(
            self.p2_dict_public['profile_id']), self.jane)
        self.assertEqual(status_code, 404)
        self.assertEqual(data, self.error_404_does_not_exist_dict)

        ### Without auth

        # For p1
        data, status_code = self.get('/profiles/{}'.format(
            self.p1_dict_public['profile_id']))
        self.assertEqual(status_code, 404)
        self.assertEqual(data, self.error_404_does_not_exist_dict)

        # For p2
        data, status_code = self.get('/profiles/{}'.format(
            self.p2_dict_public['profile_id']))
        self.assertEqual(status_code, 404)
        self.assertEqual(data, self.error_404_does_not_exist_dict)

        ## Now asking for private access

        # For p1
        data, status_code = self.get('/profiles/{}?access=private'.format(
            self.p1_dict_public['profile_id']))
        self.assertEqual(status_code, 404)
        self.assertEqual(data, self.error_404_does_not_exist_dict)

        # For p2
        data, status_code = self.get('/profiles/{}?access=private'.format(
            self.p2_dict_public['profile_id']))
        self.assertEqual(status_code, 404)
        self.assertEqual(data, self.error_404_does_not_exist_dict)

    @skip('not implemented yet')
    def test_profile_put_data_successful(self):
        self.create_profiles()

        # For p1
        data, status_code = self.sput('/profiles/{}'.format(
            self.p1_dict_public['profile_id']),
            {'profile':
             {'data':
              {'next_occupation': 'striker',
               'age': 25}}},
            self.p1_sk)
        self.p1_dict_private['data'].pop('occupation')
        self.p1_dict_private['data']['next_occupation'] = 'striker'
        self.p1_dict_private['data']['age'] = 25
        self.assertEqual(status_code, 200)
        self.assertEqual(data, {'profile': self.p1_dict_private})

        # For p2
        data, status_code = self.sput('/profiles/{}'.format(
            self.p2_dict_public['profile_id']),
            {'profile':
             {'data':
              {'next_occupation': 'playerin',
               'age': 30}}},
            self.p2_sk)
        self.p2_dict_private['data'].pop('occupation')
        self.p2_dict_private['data']['next_occupation'] = 'playerin'
        self.p2_dict_private['data']['age'] = 30
        self.assertEqual(status_code, 200)
        self.assertEqual(data, {'profile': self.p2_dict_private})

        ## And the same with ignore authentication

        # For p1
        data, status_code = self.sput('/profiles/{}'.format(
            self.p1_dict_public['profile_id']),
            {'profile':
             {'data':
              {'next_second_occupation': 'partier',
               'age': 26}}},
            self.p1_sk, self.sophia)
        self.p1_dict_private['data'].pop('next_occupation')
        self.p1_dict_private['data']['next_second_occupation'] = 'playerin'
        self.p1_dict_private['data']['age'] = 26
        self.assertEqual(status_code, 200)
        self.assertEqual(data, {'profile': self.p1_dict_private})

        # For p2
        data, status_code = self.sput('/profiles/{}'.format(
            self.p2_dict_public['profile_id']),
            {'profile':
             {'data':
              {'next_second_occupation': 'performer',
               'age': 31}}},
            self.p2_sk, self.sophia)
        self.p2_dict_private['data'].pop('next_occupation')
        self.p2_dict_private['data']['next_second_occupation'] = 'performer'
        self.p2_dict_private['data']['age'] = 31
        self.assertEqual(status_code, 200)
        self.assertEqual(data, {'profile': self.p2_dict_private})

    @skip('not implemented yet')
    def test_profile_put_data_ignore_additional_fields(self):
        self.create_profiles()

        # For p1
        data, status_code = self.sput('/profiles/{}'.format(
            self.p1_dict_public['profile_id']),
            {'profile':
             {'data':
              {'next_occupation': 'striker',
               'age': 25},
              'profile_id': 'bla-bla-bla-ignored',
              'n_results': 'bli-bli-bli-ignored',
              'device_id': 'ignored-because-only-one-signature-present'},
             'some-other-stuff': 'also-ignored'},
            self.p1_sk)
        self.p1_dict_private['data'].pop('occupation')
        self.p1_dict_private['data']['next_occupation'] = 'striker'
        self.p1_dict_private['data']['age'] = 25
        self.assertEqual(status_code, 200)
        self.assertEqual(data, {'profile': self.p1_dict_private})

        # For p2
        data, status_code = self.sput('/profiles/{}'.format(
            self.p2_dict_public['profile_id']),
            {'profile':
             {'data':
              {'next_occupation': 'playerin',
               'age': 30},
              'profile_id': 'bla-bla-bla-ignored',
              'n_results': 'bli-bli-bli-ignored',
              'device_id': 'ignored-because-only-one-signature-present'},
             'some-other-stuff': 'also-ignored'},
            self.p2_sk)
        self.p2_dict_private['data'].pop('occupation')
        self.p2_dict_private['data']['next_occupation'] = 'playerin'
        self.p2_dict_private['data']['age'] = 30
        self.assertEqual(status_code, 200)
        self.assertEqual(data, {'profile': self.p2_dict_private})

    @skip('not implemented yet')
    def test_profile_put_empty_data_empties(self):
        self.create_profiles()

        ## Pushing without any `data` field doesn't do anything

        # For p1
        data, status_code = self.sput('/profiles/{}'.format(
            self.p1_dict_public['profile_id']),
            {'profile': {}}, self.p1_sk)
        self.assertEqual(status_code, 200)
        self.assertEqual(data, {'profile': self.p1_dict_private})

        # For p2
        data, status_code = self.sput('/profiles/{}'.format(
            self.p2_dict_public['profile_id']),
            {'profile': {}}, self.p2_sk)
        self.assertEqual(status_code, 200)
        self.assertEqual(data, {'profile': self.p2_dict_private})

        # Note that above, not providing a `device_id` field for p2 does not
        # remove the device from the device (that tie is irreversible).

        ## But pushing with an empty `data` field empties the data

        # For p1
        data, status_code = self.sput('/profiles/{}'.format(
            self.p1_dict_public['profile_id']),
            {'profile': {'data': {}}}, self.p1_sk)
        self.p1_dict_private['data'] = {}
        self.assertEqual(status_code, 200)
        self.assertEqual(data, {'profile': self.p1_dict_private})

        # For p2
        data, status_code = self.sput('/profiles/{}'.format(
            self.p2_dict_public['profile_id']),
            {'profile': {'data': {}}}, self.p2_sk)
        self.p2_dict_private['data'] = {}
        self.assertEqual(status_code, 200)
        self.assertEqual(data, {'profile': self.p2_dict_private})

    @skip('not implemented yet')
    def test_profile_put_device_successful(self):
        self.create_profiles()

        # For only p2
        data, status_code = self.sput('/profiles/{}'.format(
            self.p2_dict_public['profile_id']),
            {'profile':
             {'device_id': self.d2_dict['device_id']}},
            [self.p2_sk, self.d2_sk])
        self.assertEqual(status_code, 200)
        self.p2_dict_private['device_id'] = self.d2_dict['device_id']
        self.assertEqual(data, {'profile': self.p2_dict_private})

    @skip('not implemented yet')
    def test_profile_put_device_and_data_successful(self):
        self.create_profiles()

        # For only p2
        data, status_code = self.sput('/profiles/{}'.format(
            self.p2_dict_public['profile_id']),
            {'profile':
             {'device_id': self.d2_dict['device_id'],
              'data':
              {'next_occupation': 'playerin',
               'age': 30}}},
            [self.p2_sk, self.d2_sk])
        self.assertEqual(status_code, 200)
        self.p2_dict_private['device_id'] = self.d2_dict['device_id']
        self.p2_dict_private['data'].pop('occupation')
        self.p2_dict_private['data']['next_occupation'] = 'playerin'
        self.p2_dict_private['age'] = 30
        self.assertEqual(data, {'profile': self.p2_dict_private})

    @skip('not implemented yet')
    def test_profile_put_device_and_empty_data_successful(self):
        self.create_profiles()

        # For only p2
        data, status_code = self.sput('/profiles/{}'.format(
            self.p2_dict_public['profile_id']),
            {'profile':
             {'device_id': self.d2_dict['device_id'],
              'data': {}}},
            [self.p2_sk, self.d2_sk])
        self.assertEqual(status_code, 200)
        self.p2_dict_private['device_id'] = self.d2_dict['device_id']
        self.p2_dict_private['data'] = {}
        self.assertEqual(data, {'profile': self.p2_dict_private})

    @skip('not implemented yet')
    def test_profile_put_device_and_data_ignore_additional_fields(self):
        self.create_profiles()

        # For only p2
        data, status_code = self.sput('/profiles/{}'.format(
            self.p2_dict_public['profile_id']),
            {'profile':
             {'device_id': self.d2_dict['device_id'],
              'data':
              {'next_occupation': 'playerin',
               'age': 30},
              'profile_id': 'bla-bla-bla-ignored',
              'n_results': 'bli-bli-bli-ignored'},
             'some-other-stuff': 'also-ignored'},
            [self.p2_sk, self.d2_sk])
        self.assertEqual(status_code, 200)
        self.p2_dict_private['device_id'] = self.d2_dict['device_id']
        self.p2_dict_private['device_id'] = self.d2_dict['device_id']
        self.p2_dict_private['data'].pop('occupation')
        self.p2_dict_private['data']['next_occupation'] = 'playerin'
        self.assertEqual(data, {'profile': self.p2_dict_private})

    @skip('not implemented yet')
    def test_profile_put_404_not_found(self):
        # For data or device or both
        pass

    @skip('not implemented yet')
    def test_profile_put_404_not_found_error_priorities(self):
        # For data or device or both
        pass

    @skip('not implemented yet')
    def test_profile_put_400_malformed_json_presig(self):
        # For data or device or both
        pass

    @skip('not implemented yet')
    def test_profile_put_400_malformed_json_presig_eerror_priorities(self):
        # For data or device or both
        pass

    @skip('not implemented yet')
    def test_profile_put_400_missing_signature(self):
        # For data or device or both
        pass

    @skip('not implemented yet')
    def test_profile_put_400_missing_signature_error_priorities(self):
        # For data or device or both
        pass

    @skip('not implemented yet')
    def test_profile_put_400_malformed_json_postsig(self):
        # For data or device or both
        pass

    @skip('not implemented yet')
    def test_profile_put_400_malformed_json_postsig_eerror_priorities(self):
        # For data or device or both
        pass

    @skip('not implemented yet')
    def test_profile_put_400_missing_field(self):
        # For data or device or both
        pass

    @skip('not implemented yet')
    def test_profile_put_400_missing_field_error_priorities(self):
        # For data or device or both
        pass

    @skip('not implemented yet')
    def test_profile_put_400_device_does_not_exist(self):
        # With or without added data
        pass

    @skip('not implemented yet')
    def test_profile_put_400_device_does_not_exist_error_priorities(self):
        # With or without added data
        pass

    @skip('not implemented yet')
    def test_profile_put_403_invalid_signature(self):
        # For data or device or both
        pass

    @skip('not implemented yet')
    def test_profile_put_403_invalid_signature_error_priorities(self):
        # For data or device or both
        pass

    @skip('not implemented yet')
    def test_profile_put_403_device_already_set(self):
        # For only p2
        pass

    @skip('not implemented yet')
    def test_profile_put_403_device_already_set_error_priorities(self):
        # For only p2
        pass

    @skip('not implemented yet')
    def test_root_no_trailing_slash_should_redirect(self):
        resp, status_code = self.get('/profiles', self.jane, False)
        # Redirects to '/profiles/'
        self.assertEqual(status_code, 301)
        self.assertRegexpMatches(resp.headers['Location'],
                                 r'{}$'.format(self.apize('/profiles/')))

    @skip('not implemented yet')
    def test_root_get_no_auth(self):
        # Empty array or not

        # GET without auth
        # GET without auth with private access
        pass

    @skip('not implemented yet')
    def test_root_get_with_auth(self):
        # Empty array or not

        # GET with auth with private access
        # GET with auth with private access
        pass

    @skip('not implemented yet')
    def test_root_post_data_successful(self):
        pass

    @skip('not implemented yet')
    def test_root_post_data_ignore_additional_data(self):
        # E.g. an additional `profile_id`
        pass

    @skip('not implemented yet')
    def test_root_post_data_complete_missing_fields(self):
        pass

    @skip('not implemented yet')
    def test_root_post_device_and_data_successful(self):
        pass

    @skip('not implemented yet')
    def test_root_post_device_and_data_ignore_additional_data(self):
        # E.g. an additional `profile_id`
        pass

    @skip('not implemented yet')
    def test_root_post_complete_missing_fields(self):
        pass

    @skip('not implemented yet')
    def test_root_post_400_malformed_json_presig(self):
        pass

    @skip('not implemented yet')
    def test_root_post_400_malformed_json_presig_error_priorities(self):
        pass

    @skip('not implemented yet')
    def test_root_post_400_missing_signature(self):
        pass

    @skip('not implemented yet')
    def test_root_post_400_missing_signature_error_priorities(self):
        pass

    @skip('not implemented yet')
    def test_root_post_400_malformed_json_postsig(self):
        pass

    @skip('not implemented yet')
    def test_root_post_400_malformed_json_postsig_error_priorities(self):
        pass

    @skip('not implemented yet')
    def test_root_post_400_missing_field(self):
        pass

    @skip('not implemented yet')
    def test_root_post_400_missing_field_error_priorities(self):
        pass

    @skip('not implemented yet')
    def test_root_post_403_invalid_signature(self):
        pass

    @skip('not implemented yet')
    def test_root_post_403_invalid_signature_error_priorities(self):
        pass

    @skip('not implemented yet')
    def test_root_post_409_key_already_registered(self):
        pass

    @skip('not implemented yet')
    def test_root_post_409_key_already_registered_error_priorities(self):
        pass

    @skip('not implemented yet')
    def test_root_post_400_experiment_not_found(self):
        pass

    @skip('not implemented yet')
    def test_root_post_400_experiment_not_found_error_priorities(self):
        pass
