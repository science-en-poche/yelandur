# -*- coding: utf-8 -*-

from unittest import skip

import ecdsa

from .models import User, Exp, Device, Profile, Result
from .helpers import APITestCase, sha256hex, iso8601


# TODO: add CORS test


class ResultsTestCase(APITestCase):

    def setUp(self):
        super(ResultsTestCase, self).setUp()

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

        ## Four profiles to work with

        # One with a device
        self.p1_sk = ecdsa.SigningKey.generate(curve=ecdsa.curves.NIST256p)
        self.p1_vk = self.p1_sk.verifying_key
        self.p1 = Profile.create(self.p1_vk.to_pem(), self.exp_nd,
                                 {'occupation': 'student'}, self.d1)
        self.p1_dict_public = {'profile_id': sha256hex(self.p1_vk.to_pem()),
                               'vk_pem': self.p1_vk.to_pem()}
        self.p1_dict_private = self.p1_dict_public.copy()
        self.p1_dict_private.update({'exp_id': self.exp_nd.exp_id,
                                     'device_id': self.d1.device_id,
                                     'data': {'occupation': 'student'},
                                     'n_results': 0})

        # A second without device
        self.p2_sk = ecdsa.SigningKey.generate(curve=ecdsa.curves.NIST256p)
        self.p2_vk = self.p2_sk.verifying_key
        self.p2 = Profile.create(self.p2_vk.to_pem(), self.exp_gd,
                                 {'occupation': 'social worker'})
        self.p2_dict_public = {'profile_id': sha256hex(self.p2_vk.to_pem()),
                               'vk_pem': self.p2_vk.to_pem()}
        self.p2_dict_private = self.p2_dict_public.copy()
        self.p2_dict_private.update({'exp_id': self.exp_gp.exp_id,
                                     'data': {'occupation': 'social worker'},
                                     'n_results': 0})

        # A third and fourth for bad signing
        self.p3_sk = ecdsa.SigningKey.generate(curve=ecdsa.curves.NIST256p)
        self.p4_sk = ecdsa.SigningKey.generate(curve=ecdsa.curves.NIST256p)

    def create_results(self):
        self.r11 = Result.create(self.p1, {'trials': [1, 2, 3]})
        self.r11_dict_public = {'result_id': self.r11.result_id}
        self.r11_dict_private = self.r11_dict_public.copy()
        self.r11_dict_private.update(
            {'profile_id': self.p1.profile_id,
             'exp_id': self.exp_nd.exp_id,
             'created_at': self.r11.created_at.strftime(iso8601),
             'data': {'trials': [1, 2, 3]}})

        self.r12 = Result.create(self.p1, {'trials': [4, 5, 6]})
        self.r12_dict_public = {'result_id': self.r12.result_id}
        self.r12_dict_private = self.r12_dict_public.copy()
        self.r12_dict_private.update(
            {'profile_id': self.p1.profile_id,
             'exp_id': self.exp_nd.exp_id,
             'created_at': self.r12.created_at.strftime(iso8601),
             'data': {'trials': [4, 5, 6]}})

        self.r21 = Result.create(self.p2, {'trials': [7, 8, 9]})
        self.r21_dict_public = {'result_id': self.r21.result_id}
        self.r21_dict_private = self.r21_dict_public.copy()
        self.r21_dict_private.update(
            {'profile_id': self.p2.profile_id,
             'exp_id': self.exp_gp.exp_id,
             'created_at': self.r21.created_at.strftime(iso8601),
             'data': {'trials': [7, 8, 9]}})

        self.r22 = Result.create(self.p2, {})
        self.r22_dict_public = {'result_id': self.r22.result_id}
        self.r22_dict_private = self.r22_dict_public.copy()
        self.r22_dict_private.update(
            {'profile_id': self.p2.profile_id,
             'exp_id': self.exp_gp.exp_id,
             'created_at': self.r22.created_at.strftime(iso8601),
             'data': {'trials': {}}})

    @skip('not implemented yet')
    def test_root_no_trailing_slash_should_redirect(self):
        resp, status_code = self.get('/results', self.jane, False)
        # Redirects to '/results/'
        self.assertEqual(status_code, 301)
        self.assertRegexpMatches(resp.headers['Location'],
                                 r'{}$'.format(self.apize('/results/')))

    @skip('not implemented yet')
    def test_root_get_no_auth(self):
        # Empty array
        data, status_code = self.get('/results/')
        self.assertEqual(status_code, 200)
        self.assertEqual(data, {'results': []})

        # Create some results
        self.create_results()

        # Without access=private
        data, status_code = self.get('/results/')
        self.assertEqual(status_code, 200)
        # FIXME: adapt once ordering works
        self.assertEqual(data.keys(), ['results'])
        self.assertIn(self.r11_dict_public, data['results'])
        self.assertIn(self.r12_dict_public, data['results'])
        self.assertIn(self.r21_dict_public, data['results'])
        self.assertIn(self.r22_dict_public, data['results'])
        self.assertEqual(len(data['results']), 4)

        # With access=private
        data, status_code = self.get('/results/?access=private')
        self.assertEqual(status_code, 401)
        self.assertEqual(data, self.error_401_dict)

    @skip('not implemented yet')
    def test_root_get_with_auth(self):
        # Empty list, then, as outsider/owner/collab
        # Without access=private, as outsider/owner/collab
        # With access=private, as outsider/owner/collab
        # For an empty result, or not, as outsider/owner/collab

        # Empty array
        data, status_code = self.get('/results/', self.jane)
        self.assertEqual(status_code, 200)
        self.assertEqual(data, {'results': []})

        # Create some results
        self.create_results()

        ## Without access=private
        data, status_code = self.get('/results/', self.jane)
        self.assertEqual(status_code, 200)
        # FIXME: adapt once ordering works
        self.assertEqual(data.keys(), ['results'])
        self.assertIn(self.r11_dict_public, data['results'])
        self.assertIn(self.r12_dict_public, data['results'])
        self.assertIn(self.r21_dict_public, data['results'])
        self.assertIn(self.r22_dict_public, data['results'])
        self.assertEqual(len(data['results']), 4)

        ## With access=private

        # As owner
        data, status_code = self.get('/results/?access=private', self.jane)
        self.assertEqual(status_code, 200)
        # FIXME: adapt once ordering works
        self.assertEqual(data.keys(), ['results'])
        self.assertIn(self.r11_dict_private, data['results'])
        self.assertIn(self.r12_dict_private, data['results'])
        self.assertEqual(len(data['results']), 2)

        # As collaborator
        data, status_code = self.get('/results/?access=private', self.bill)
        self.assertEqual(status_code, 200)
        # FIXME: adapt once ordering works
        self.assertEqual(data.keys(), ['results'])
        self.assertIn(self.r11_dict_private, data['results'])
        self.assertIn(self.r12_dict_private, data['results'])
        self.assertEqual(len(data['results']), 2)

        # As owner again
        data, status_code = self.get('/results/?access=private', self.sophia)
        self.assertEqual(status_code, 200)
        # FIXME: adapt once ordering works
        self.assertEqual(data.keys(), ['results'])
        self.assertIn(self.r21_dict_private, data['results'])
        self.assertIn(self.r22_dict_private, data['results'])
        self.assertEqual(len(data['results']), 2)

    @skip('not implemented yet')
    def test_result_get_no_auth(self):
        # Does not exist
        data, status_code = self.get('/results/non-existing')
        self.assertEqual(status_code, 404)
        self.assertEqual(data, self.error_404_does_not_exist_dict)

        # Without access=private
        data, status_code = self.get('/results/{}'.format(self.r11.result_id))
        self.assertEqual(status_code, 200)
        self.assertEqual(data, {'result': self.r11_dict_public})
        # (with empty data)
        data, status_code = self.get('/results/{}'.format(self.r22.result_id))
        self.assertEqual(status_code, 200)
        self.assertEqual(data, {'result': self.r22_dict_public})

        # With access=private
        data, status_code = self.get('/results/{}?access=private'.format(
            self.r11.result_id))
        self.assertEqual(status_code, 401)
        self.assertEqual(data, self.error_401_dict)

    @skip('not implemented yet')
    def test_result_get_with_auth(self):
        # Does not exist
        # Without access=private, as outsider/owner/collab
        # With access=private, as outsider/owner/collab
        # Empty result, or not, as outsider/owner/collab

        # Does not exist
        data, status_code = self.get('/results/non-existing', self.jane)
        self.assertEqual(status_code, 404)
        self.assertEqual(data, self.error_404_does_not_exist_dict)

        ## Without access=private

        # As owner
        data, status_code = self.get('/results/{}'.format(self.r11.result_id),
                                     self.jane)
        self.assertEqual(status_code, 200)
        self.assertEqual(data, {'result': self.r11_dict_public})

        # As collaborator
        data, status_code = self.get('/results/{}'.format(self.r11.result_id),
                                     self.bill)
        self.assertEqual(status_code, 200)
        self.assertEqual(data, {'result': self.r11_dict_public})

        # As someone else
        data, status_code = self.get('/results/{}'.format(self.r11.result_id),
                                     self.sophia)
        self.assertEqual(status_code, 200)
        self.assertEqual(data, {'result': self.r11_dict_public})

        # As owner with empty data
        data, status_code = self.get('/results/{}'.format(self.r22.result_id),
                                     self.sophia)
        self.assertEqual(status_code, 200)
        self.assertEqual(data, {'result': self.r22_dict_public})

        ## With access=private

        # As owner
        data, status_code = self.get('/results/{}?access=private'.format(
            self.r11.result_id), self.jane)
        self.assertEqual(status_code, 200)
        self.assertEqual(data, {'result': self.r11_dict_private})

        # As collaborator
        data, status_code = self.get('/results/{}?access=private'.format(
            self.r11.result_id), self.bill)
        self.assertEqual(status_code, 200)
        self.assertEqual(data, {'result': self.r11_dict_private})

        # As someone else
        data, status_code = self.get('/results/{}?access=private'.format(
            self.r11.result_id), self.sophia)
        self.assertEqual(status_code, 403)
        self.assertEqual(data, self.error_403_unauthorized_dict)

        # As owner with empty data
        data, status_code = self.get('/results/{}?access=private'.format(
            self.r22.result_id), self.sophia)
        self.assertEqual(status_code, 200)
        self.assertEqual(data, {'result': self.r22_dict_private})

    @skip('not implemented yet')
    def test_root_post_successful(self):
        pass

    @skip('not implemented yet')
    def test_root_post_successful_in_bulk(self):
        pass

    @skip('not implemented yet')
    def test_root_post_successful_ignore_additional_data(self):
        pass

    @skip('not implemented yet')
    def test_root_post_successful_ignore_in_bulk_additional_data(self):
        pass

    @skip('not implemented yet')
    def test_root_post_400_malformed_json_presig(self):
        pass

    # No error priority test with malformed json presig since it excludes all
    # lower-priority errors

    @skip('not implemented yet')
    def test_root_post_400_malformed_signature(self):
        pass

    # No error priority test with malformed signature since it excludes all
    # lower-priority errors

    @skip('not implemented yet')
    def test_root_post_400_missing_signature(self):
        pass

    @skip('not implemented yet')
    def test_root_post_400_missing_signature_error_priorities(self):
        pass

    @skip('not implemented yet')
    def test_root_post_400_too_many_signatures(self):
        pass

    @skip('not implemented yet')
    def test_root_post_400_too_many_signatures_error_priorities(self):
        pass

    # FIXME: can't do this test yet since python-jws checks for JSON
    # conformity before signing.

    @skip('not implemented yet')
    def test_profile_put_400_malformed_json_postsig(self):
        pass

    # No error priority test with malformed json postsig since it excludes all
    # lower-priority errors

    @skip('not implemented yet')
    def test_root_post_400_missing_field(self):
        # including a bulk post
        pass

    @skip('not implemented yet')
    def test_root_post_400_missing_field_error_priorities(self):
        # including a bulk post
        pass

    @skip('not implemented yet')
    def test_root_post_400_profile_does_not_exist(self):
        # including a bulk post
        pass

    @skip('not implemented yet')
    def test_root_post_400_profile_does_not_exist_error_priorities(self):
        # including a bulk post
        pass

    @skip('not implemented yet')
    def test_root_post_403_invalid_signature(self):
        # including a bulk post with different profile_ids
        pass

    @skip('not implemented yet')
    def test_root_post_403_invalid_signature_error_priorities(self):
        # including a bulk post with different profile_ids
        pass

    @skip('not implemented yet')
    def test_root_post_400_malformed_data(self):
        # including a bulk post
        pass

    # No error-priority test since having malformed data is the
    # last possible error
