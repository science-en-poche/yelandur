# -*- coding: utf-8 -*-

#from pprint import pprint
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
        self.p2 = Profile.create(self.p2_vk.to_pem(), self.exp_gp,
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

        # Three results we'll be creating through posts
        self.rp11_dict_private = {'profile_id': self.p1.profile_id,
                                  'exp_id': self.exp_nd.exp_id,
                                  'data': {'trials': 'worked'}}
        self.rp12_dict_private = {'profile_id': self.p1.profile_id,
                                  'exp_id': self.exp_nd.exp_id,
                                  'data': {'trials': 'failed'}}
        self.rp21_dict_private = {'profile_id': self.p2.profile_id,
                                  'exp_id': self.exp_gp.exp_id,
                                  'data': {'trials': 'skipped'}}

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
             'data': {}})

    def complete_result_dict(self, profile, result, result_dict):
        result_id = Result.build_result_id(profile, result.created_at,
                                           result_dict['data'])
        result_dict['result_id'] = result_id
        result_dict['created_at'] = result.created_at.strftime(iso8601)

    def test_root_no_trailing_slash_should_redirect(self):
        resp, status_code = self.get('/results', self.jane, False)
        # Redirects to '/results/'
        self.assertEqual(status_code, 301)
        self.assertRegexpMatches(resp.headers['Location'],
                                 r'{}$'.format(self.apize('/results/')))

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

    def test_result_get_no_auth(self):
        # Does not exist
        data, status_code = self.get('/results/non-existing')
        self.assertEqual(status_code, 404)
        self.assertEqual(data, self.error_404_does_not_exist_dict)

        # Create some results
        self.create_results()

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

    def test_result_get_with_auth(self):
        # Does not exist
        data, status_code = self.get('/results/non-existing', self.jane)
        self.assertEqual(status_code, 404)
        self.assertEqual(data, self.error_404_does_not_exist_dict)

        # Create some results
        self.create_results()

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
        # A first result
        data, status_code = self.spost('/results/',
                                       {'result':
                                        {'profile_id': self.p1.profile_id,
                                         'data': {'trials': 'worked'}}},
                                       self.p1_sk)
        # Need to get some information before testing
        r11 = Result.objects.get(profile_id=self.p1.profile_id)
        self.complete_result_dict(self.p1, r11, self.rp11_dict_private)
        self.assertEqual(status_code, 201)
        self.assertEqual(data, {'result': self.rp11_dict_private})

        # A second result
        data, status_code = self.spost('/results/',
                                       {'result':
                                        {'profile_id': self.p2.profile_id,
                                         'data': {'trials': 'skipped'}}},
                                       self.p2_sk)
        # Need to get some information before testing
        r21 = Result.objects.get(profile_id=self.p2.profile_id)
        self.complete_result_dict(self.p2, r21, self.rp21_dict_private)
        self.assertEqual(status_code, 201)
        self.assertEqual(data, {'result': self.rp21_dict_private})

    @skip('not implemented yet')
    def test_root_post_successful_in_bulk(self):
        # A first batch
        data, status_code = self.spost(
            '/results/',
            {'results':
             [{'profile_id': self.p1.profile_id,
               'data': {'trials': 'worked'}},
              {'profile_id': self.p1.profile_id,
               'data': {'trials': 'failed'}}]},
            self.p1_sk)
        # Need to get some information before testing
        results = Result.objects(profile_id=self.p1.profile_id)
        if results[0].data.trials == 'worked':
            r11, r12 = results
        else:
            r12, r11 = results
        self.complete_result_dict(self.p1, r11, self.rp11_dict_private)
        self.complete_result_dict(self.p1, r12, self.rp12_dict_private)
        self.assertEqual(status_code, 201)
        # FIXME: adapt once ordering works
        self.assertEqual(data.keys(), ['results'])
        self.assertIn(self.rp11_dict_private, data['results'])
        self.assertIn(self.rp12_dict_private, data['results'])
        self.assertEqual(len(data), 2)

        # A second batch, but with only one result
        data, status_code = self.spost(
            '/results/',
            {'results':
             [{'profile_id': self.p2.profile_id,
               'data': {'trials': 'worked'}}]},
            self.p2_sk)
        # Need to get some information before testing
        r21 = Result.objects.get(profile_id=self.p2.profile_id)
        self.complete_result_dict(self.p2, r21,
                                  self.rp21_dict_private)
        self.assertEqual(status_code, 201)
        self.assertEqual(data, {'results': [self.rp21_dict_private]})

    @skip('not implemented yet')
    def test_root_post_successful_ignore_additional_data(self):
        data, status_code = self.spost(
            '/results/',
            {'result':
             {'profile_id': self.p1.profile_id,
              'data': {'trials': 'worked'},
              'something-else': 'else'},
             'more-else': 'else'},
            self.p1_sk)
        # Need to get some information before testing
        r11 = Result.objects.get(profile_id=self.p1.profile_id)
        self.complete_result_dict(self.p1, r11, self.rp11_dict_private)
        self.assertEqual(status_code, 201)
        self.assertEqual(data, {'result': self.rp11_dict_private})

    @skip('not implemented yet')
    def test_root_post_successful_ignore_in_bulk_additional_data(self):
        data, status_code = self.spost(
            '/results/',
            {'results':
             [{'profile_id': self.p1.profile_id,
               'data': {'trials': 'worked'},
               'ignored': 'ignored'},
              {'profile_id': self.p1.profile_id,
               'data': {'trials': 'failed'},
               'ignored': 'ignored'}],
             'more-ignored': 'ignored'},
            self.p1_sk)
        # Need to get some information before testing
        results = Result.objects(profile_id=self.p1.profile_id)
        if results[0].data.trials == 'worked':
            r11, r12 = results
        else:
            r12, r11 = results
        self.complete_result_dict(self.p1, r11, self.rp11_dict_private)
        self.complete_result_dict(self.p1, r12, self.rp12_dict_private)
        self.assertEqual(status_code, 201)
        # FIXME: adapt once ordering works
        self.assertEqual(data.keys(), ['results'])
        self.assertIn(self.rp11_dict_private, data['results'])
        self.assertIn(self.rp12_dict_private, data['results'])
        self.assertEqual(len(data), 2)

    @skip('not implemented yet')
    def test_root_post_400_malformed_json_presig(self):
        data, status_code = self.post('/results/',
                                      '{"malformed JSON": "bla"',
                                      dump_json_data=False)
        self.assertEqual(status_code, 400)
        self.assertEqual(data, self.error_400_malformed_dict)

    # No error priority test with malformed json presig since it excludes all
    # lower-priority errors

    @skip('not implemented yet')
    def test_root_post_400_malformed_signature(self):
        # (no `payload`)
        data, status_code = self.post('/results/',
                                      {'signatures':
                                       [{'protected': 'bla',
                                         'signature': 'bla'}]})
        self.assertEqual(status_code, 400)
        self.assertEqual(data, self.error_400_malformed_dict)

        # (`payload` is not a base64url string)
        data, status_code = self.post('/results/',
                                      {'payload': {},
                                       'signatures':
                                       [{'protected': 'bla',
                                         'signature': 'bla'}]})
        self.assertEqual(status_code, 400)
        self.assertEqual(data, self.error_400_malformed_dict)
        data, status_code = self.post('/results/',
                                      {'payload': 'abcde',  # Incorrect padding
                                       'signatures':
                                       [{'protected': 'bla',
                                         'signature': 'bla'}]})
        self.assertEqual(status_code, 400)
        self.assertEqual(data, self.error_400_malformed_dict)

        # (no `signatures`)
        data, status_code = self.post('/results/',
                                      {'payload': 'bla'})
        self.assertEqual(status_code, 400)
        self.assertEqual(data, self.error_400_malformed_dict)

        # (`signatures` is not a list)
        data, status_code = self.post('/results/',
                                      {'payload': 'bla',
                                       'signatures': 30})
        self.assertEqual(status_code, 400)
        self.assertEqual(data, self.error_400_malformed_dict)
        data, status_code = self.post('/results/',
                                      {'payload': 'bla',
                                       'signatures': {}})
        self.assertEqual(status_code, 400)
        self.assertEqual(data, self.error_400_malformed_dict)
        data, status_code = self.post('/results/',
                                      {'payload': 'bla',
                                       'signatures': 'bli'})
        self.assertEqual(status_code, 400)
        self.assertEqual(data, self.error_400_malformed_dict)

        # (no `protected` in a signature)
        data, status_code = self.post('/results/',
                                      {'payload': 'bla',
                                       'signatures':
                                       [{'signature': 'bla'}]})
        self.assertEqual(status_code, 400)
        self.assertEqual(data, self.error_400_malformed_dict)

        # (`protected is not a base64url string)
        data, status_code = self.post('/results/',
                                      {'payload': 'bla',
                                       'signatures':
                                       [{'protected': {},
                                         'signature': 'bla'}]})
        self.assertEqual(status_code, 400)
        self.assertEqual(data, self.error_400_malformed_dict)
        data, status_code = self.post('/results/',
                                      {'payload': 'bla',
                                       'signatures':
                                       [{'protected': 30,
                                         'signature': 'bla'}]})
        self.assertEqual(status_code, 400)
        self.assertEqual(data, self.error_400_malformed_dict)
        data, status_code = self.post('/results/',
                                      {'payload': 'bla',
                                       'signatures':
                                       [{'protected': 'abcde',
                                         'signature': 'bla'}]})
        self.assertEqual(status_code, 400)
        self.assertEqual(data, self.error_400_malformed_dict)

        # (no `signature` in a signature)
        data, status_code = self.post('/results/',
                                      {'payload': 'bla',
                                       'signatures':
                                       [{'protected': 'bla'}]})
        self.assertEqual(status_code, 400)
        self.assertEqual(data, self.error_400_malformed_dict)

        # (`signature` is not base64url a string)
        data, status_code = self.post('/results/',
                                      {'payload': 'bla',
                                       'signatures':
                                       [{'protected': 'bla',
                                         'signature': {}}]})
        self.assertEqual(status_code, 400)
        self.assertEqual(data, self.error_400_malformed_dict)
        data, status_code = self.post('/results/',
                                      {'payload': 'bla',
                                       'signatures':
                                       [{'protected': 'bla',
                                         'signature': 30}]})
        self.assertEqual(status_code, 400)
        self.assertEqual(data, self.error_400_malformed_dict)
        data, status_code = self.post('/results/',
                                      {'payload': 'bla',
                                       'signatures':
                                       [{'protected': 'bla',
                                         'signature': 'abcde'}]})
        self.assertEqual(status_code, 400)
        self.assertEqual(data, self.error_400_malformed_dict)

    # No error priority test with malformed signature since it excludes all
    # lower-priority errors

    @skip('not implemented yet')
    def test_root_post_400_missing_signature(self):
        # A first result
        data, status_code = self.post(
            '/results/',
            {'result':
             {'profile_id': self.p1.profile_id,
              'data': {'trials': 'worked'}}})
        self.assertEqual(status_code, 400)
        self.assertEqual(data, self.error_400_malformed_dict)

        # And a batch
        data, status_code = self.post(
            '/results/',
            {'results':
             [{'profile_id': self.p1.profile_id,
               'data': {'trials': 'worked'}},
              {'profile_id': self.p1.profile_id,
               'data': {'trials': 'failed'}}]})
        self.assertEqual(status_code, 400)
        self.assertEqual(data, self.error_400_malformed_dict)

    @skip('not implemented yet')
    def test_root_post_400_missing_signature_error_priorities(self):
        ## As a single result

        # Missing signature, missing field (profile_id), (profile does not
        # exist makes no sense with missing profile_id), malformed data
        data, status_code = self.post(
            '/results/',
            {'result': {'data': 'non-dict'}})
        self.assertEqual(status_code, 400)
        self.assertEqual(data, self.error_400_malformed_dict)

        # Missing signature, missing field (data), profile does not
        # exist, (malformed data makes no sense with missing data)
        data, status_code = self.post(
            '/results/',
            {'result': {'profile_id': 'non-existing'}})
        self.assertEqual(status_code, 400)
        self.assertEqual(data, self.error_400_malformed_dict)

        ## As a batch

        # Missing signature, missing field (profile_id), (profile does not
        # exist makes no sense with missing profile_id), malformed data
        data, status_code = self.post(
            '/results/',
            {'results':
             [{'data': 'non-dict'},
              {'profile_id': self.p1.profile_id,
               'data': {'trials': 'failed'}}]})
        self.assertEqual(status_code, 400)
        self.assertEqual(data, self.error_400_malformed_dict)

        # Missing signature, missing field (data), profile does not
        # exist, (malformed data makes no sense with missing data)
        data, status_code = self.post(
            '/results/',
            {'results':
             [{'profile_id': 'non-existing'},
              {'profile_id': self.p1.profile_id,
               'data': {'trials': 'failed'}}]})
        self.assertEqual(status_code, 400)
        self.assertEqual(data, self.error_400_malformed_dict)

    @skip('not implemented yet')
    def test_root_post_400_too_many_signatures(self):
        # A first result
        data, status_code = self.spost(
            '/results/',
            {'result':
             {'profile_id': self.p1.profile_id,
              'data': {'trials': 'worked'}}},
            [self.p1_sk, self.p2_sk])
        self.assertEqual(status_code, 400)
        self.assertEqual(data, self.error_400_too_many_signatures_dict)

        # And a batch
        data, status_code = self.spost(
            '/results/',
            {'results':
             [{'profile_id': self.p1.profile_id,
               'data': {'trials': 'worked'}},
              {'profile_id': self.p1.profile_id,
               'data': {'trials': 'failed'}}]},
            [self.p1_sk, self.p2_sk])
        self.assertEqual(status_code, 400)
        self.assertEqual(data, self.error_400_too_many_signatures_dict)

    @skip('not implemented yet')
    def test_root_post_400_too_many_signatures_error_priorities(self):
        # FIXME: can't do this test yet since python-jws checks for JSON
        # conformity before signing.

        # Too many signatures, malformed JSON postsig
        #data, status_code = self.spost(
            #'/results/', '{"malformed JSON": "bla"',
            #[self.p3_sk, self.p4_sk], dump_json_data=False)
        #self.assertEqual(status_code, 400)
        #self.assertEqual(data, self.error_400_malformed_dict)

        ## As a single result

        # Too many signatures, missing field (profile_id), (profile does not
        # exist makes no sense with missing profile_id), malformed data
        data, status_code = self.spost(
            '/results/',
            {'result': {'data': 'non-dict'}},
            [self.p3_sk, self.p4_sk])
        self.assertEqual(status_code, 400)
        self.assertEqual(data, self.error_400_malformed_dict)

        # Too many signatures, missing field (data), profile does not
        # exist, invalid signature, (malformed data makes no sense with
        # missing data)
        data, status_code = self.spost(
            '/results/',
            {'result': {'profile_id': 'non-existing'}},
            [self.p3_sk, self.p4_sk])
        self.assertEqual(status_code, 400)
        self.assertEqual(data, self.error_400_malformed_dict)

        ## As a batch

        # Too many signatures, missing field (profile_id), (profile does not
        # exist makes no sense with missing profile_id), malformed data
        data, status_code = self.spost(
            '/results/',
            {'results':
             [{'data': 'non-dict'},
              {'profile_id': self.p1.profile_id,
               'data': {'trials': 'failed'}}]},
            [self.p3_sk, self.p4_sk])
        self.assertEqual(status_code, 400)
        self.assertEqual(data, self.error_400_malformed_dict)

        # Too many signatures, missing field (data), profile does not
        # exist, invalid signature, (malformed data makes no sense with
        # missing data)
        data, status_code = self.post(
            '/results/',
            {'results':
             [{'profile_id': 'non-existing'},
              {'profile_id': self.p1.profile_id,
               'data': {'trials': 'failed'}}]},
            [self.p3_sk, self.p4_sk])
        self.assertEqual(status_code, 400)
        self.assertEqual(data, self.error_400_malformed_dict)

    # FIXME: can't do this test yet since python-jws checks for JSON
    # conformity before signing.

    #def test_profile_put_400_malformed_json_postsig(self):
        #data, status_code = self.spost(
            #'/results/', '{"malformed JSON": "bla"',
            #self.p1_sk, dump_json_data=False)
        #self.assertEqual(status_code, 400)
        #self.assertEqual(data, self.error_400_malformed_dict)

    # No error priority test with malformed json postsig since it excludes all
    # lower-priority errors

    @skip('not implemented yet')
    def test_root_post_400_missing_field(self):
        ## As a single result

        # Missing profile_id
        data, status_code = self.spost('/results/',
                                       {'result':
                                        {'data': {'trials': 'worked'}}},
                                       self.p1_sk)
        self.assertEqual(status_code, 400)
        self.assertEqual(data, self.error_400_missing_requirement_dict)

        # Missing data
        data, status_code = self.spost('/results/',
                                       {'result':
                                        {'profile_id': self.p1.profile_id}},
                                       self.p1_sk)
        self.assertEqual(status_code, 400)
        self.assertEqual(data, self.error_400_missing_requirement_dict)

        ## And a batch

        # Missing profile_id
        data, status_code = self.spost(
            '/results/',
            {'results':
             [{'data': {'trials': 'worked'}},
              {'profile_id': self.p1.profile_id,
               'data': {'trials': 'failed'}}]},
            self.p1_sk)
        self.assertEqual(status_code, 400)
        self.assertEqual(data, self.error_400_missing_requirement_dict)

        # Missing data
        data, status_code = self.spost(
            '/results/',
            {'results':
             [{'profile_id': self.p1.profile_id},
              {'profile_id': self.p1.profile_id,
               'data': {'trials': 'failed'}}]},
            self.p1_sk)
        self.assertEqual(status_code, 400)
        self.assertEqual(data, self.error_400_missing_requirement_dict)

        # Mixed data and profile_id
        data, status_code = self.spost(
            '/results/',
            {'results':
             [{'data': {'trials': 'worked'}},
              {'profile_id': self.p1.profile_id}]},
            self.p1_sk)
        self.assertEqual(status_code, 400)
        self.assertEqual(data, self.error_400_missing_requirement_dict)

        # Missing list under 'results'
        data, status_code = self.spost(
            '/results/',
            {'results': 'non-list'},
            self.p1_sk)
        self.assertEqual(status_code, 400)
        self.assertEqual(data, self.error_400_missing_requirement_dict)

    @skip('not implemented yet')
    def test_root_post_400_missing_field_error_priorities(self):
        # including a bulk post

        ## As a single result

        # Missing profile_id, (profile does not exist makes no sense), (invalid
        # signature makes no sense), malformed data
        data, status_code = self.spost('/results/',
                                       {'result':
                                        {'data': 'non-dict'}},
                                       self.p1_sk)
        self.assertEqual(status_code, 400)
        self.assertEqual(data, self.error_400_missing_requirement_dict)

        # Missing data, profile does not exist, (invalid signature makes no
        # sense), (malformed data makes no sense)
        data, status_code = self.spost('/results/',
                                       {'result':
                                        {'profile_id': 'non-existing'}},
                                       self.p1_sk)
        self.assertEqual(status_code, 400)
        self.assertEqual(data, self.error_400_missing_requirement_dict)

        ## And a batch

        # Missing profile_id, malformed data, mixed with profile does not exist
        # and invalid signature
        data, status_code = self.spost(
            '/results/',
            {'results':
             [{'data': 'non-dict'},
              {'profile_id': 'non-existing',
               'data': {'trials': 'failed'}}]},
            self.p2_sk)
        self.assertEqual(status_code, 400)
        self.assertEqual(data, self.error_400_missing_requirement_dict)

        # Missing data, profile does not exist, mixed with invalid signature
        # and malformed data
        data, status_code = self.spost(
            '/results/',
            {'results':
             [{'profile_id': 'non-existing'},
              {'profile_id': self.p1.profile_id,
               'data': 'non-dict'}]},
            self.p2_sk)
        self.assertEqual(status_code, 400)
        self.assertEqual(data, self.error_400_missing_requirement_dict)

    @skip('not implemented yet')
    def test_root_post_400_profile_does_not_exist(self):
        # As a single result
        data, status_code = self.spost('/results/',
                                       {'result':
                                        {'profile_id': 'non-existing',
                                         'data': {'trials': 'worked'}}},
                                       self.p1_sk)
        self.assertEqual(status_code, 400)
        self.assertEqual(data, self.error_400_profile_does_not_exist_dict)

        # And a batch
        data, status_code = self.spost(
            '/results/',
            {'results':
             [{'profile_id': 'non-existing',
               'data': {'trials': 'worked'}},
              {'profile_id': self.p1.profile_id,
               'data': {'trials': 'failed'}}]},
            self.p1_sk)
        self.assertEqual(status_code, 400)
        self.assertEqual(data, self.error_400_profile_does_not_exist_dict)

    @skip('not implemented yet')
    def test_root_post_400_profile_does_not_exist_error_priorities(self):
        ## As a single result

        # Profile does not exist, malformed data
        data, status_code = self.spost('/results/',
                                       {'result':
                                        {'profile_id': 'non-existing',
                                         'data': 'non-dict'}},
                                       self.p1_sk)
        self.assertEqual(status_code, 400)
        self.assertEqual(data, self.error_400_profile_does_not_exist_dict)

        ## And a batch

        # Profile does not exist, invalid signature, malformed data
        data, status_code = self.spost(
            '/results/',
            {'results':
             [{'profile_id': 'non-existing',
               'data': 'non-dict'},
              {'profile_id': self.p1.profile_id,
               'data': {'trials': 'failed'}}]},
            self.p2_sk)
        self.assertEqual(status_code, 400)
        self.assertEqual(data, self.error_400_profile_does_not_exist_dict)

    @skip('not implemented yet')
    def test_root_post_403_invalid_signature(self):
        # As a single result
        data, status_code = self.spost('/results/',
                                       {'result':
                                        {'profile_id': self.p1.profile_id,
                                         'data': {'trials': 'worked'}}},
                                       self.p2_sk)
        self.assertEqual(status_code, 403)
        self.assertEqual(data, self.error_403_invalid_signature_dict)

        # And a batch
        data, status_code = self.spost(
            '/results/',
            {'results':
             [{'profile_id': self.p1.profile_id,
               'data': {'trials': 'worked'}},
              {'profile_id': self.p1.profile_id,
               'data': {'trials': 'failed'}}]},
            self.p2_sk)
        self.assertEqual(status_code, 403)
        self.assertEqual(data, self.error_403_invalid_signature_dict)

    @skip('not implemented yet')
    def test_root_post_403_invalid_signature_error_priorities(self):
        # As a single result, with malformed data
        data, status_code = self.spost('/results/',
                                       {'result':
                                        {'profile_id': self.p1.profile_id,
                                         'data': 'non-dict'}},
                                       self.p2_sk)
        self.assertEqual(status_code, 403)
        self.assertEqual(data, self.error_403_invalid_signature_dict)

        # And a batch, with malformed data
        data, status_code = self.spost(
            '/results/',
            {'results':
             [{'profile_id': self.p1.profile_id,
               'data': 'non-dict'},
              {'profile_id': self.p1.profile_id,
               'data': {'trials': 'failed'}}]},
            self.p2_sk)
        self.assertEqual(status_code, 403)
        self.assertEqual(data, self.error_403_invalid_signature_dict)

    @skip('not implemented yet')
    def test_root_post_400_malformed_data(self):
        # As a single result
        data, status_code = self.spost('/results/',
                                       {'result':
                                        {'profile_id': self.p1.profile_id,
                                         'data': 'non-dict'}},
                                       self.p1_sk)
        self.assertEqual(status_code, 400)
        self.assertEqual(data, self.error_400_malformed_dict)

        # And a batch
        data, status_code = self.spost(
            '/results/',
            {'results':
             [{'profile_id': self.p1.profile_id,
               'data': 'non-dict'},
              {'profile_id': self.p1.profile_id,
               'data': {'trials': 'failed'}}]},
            self.p1_sk)
        self.assertEqual(status_code, 400)
        self.assertEqual(data, self.error_400_malformed_dict)

    # No error-priority test since having malformed data is the
    # last possible error
