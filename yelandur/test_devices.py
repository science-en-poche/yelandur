# -*- coding: utf-8 -*-

from unittest import skip

from .models import User, Device
from .helpers import APITestCase


# TODO: add CORS test


class DevicesTestCase(APITestCase):

    def setUp(self):
        super(DevicesTestCase, self).setUp()

        # A User to authenticate with
        self.jane = User.get_or_create_by_email('jane@example.com')
        self.jane.set_user_id('jane')

        # Resulting dicts for devices
        self.d1_dict = {
            'vk_pem': 'public key for d1',
            'device_id': ('4f2b67a9b422f553d50138002609e02d'
                          '72bcec52c678d6f038ce212add39d58f')}
        self.d2_dict = {
            'vk_pem': 'public key for d2',
            'device_id': ('1a4d957eedb96b1fd344506bfd5f75ca'
                          '5d21af973d9fcd9c791977747106c80b')}
        self.d3_dict = {
            'vk_pem': 'public key for d3',
            'device_id': ('b8fca263396546f94c435ecf92cbf8b0'
                          '629795cab02f12d4fac9407c3b59fc45')}

    def create_devices(self):
        self.d1 = Device.create('public key for d1')
        self.d2 = Device.create('public key for d2')

    @skip('not implementation yet')
    def test_root_get(self):
        # Emtpy GET with ignored authentication
        data, status_code = self.get('/devices/', self.jane)
        self.assertEqual(status_code, 200)
        self.assertEqual(data, {'devices': []})

        # Emtpy GET with ignored authentication
        data, status_code = self.get('/devices/')
        self.assertEqual(status_code, 200)
        self.assertEqual(data, {'devices': []})

        # Create devices
        self.create_devices()

        # GET with ignored authentication
        data, status_code = self.get('/device/', self.jane)
        self.assertEqual(status_code, 200)
        # FIXME: adapt once ordering works
        self.assertEqual(data.keys(), ['devices'])
        self.assertIn(self.d1_dict, data['devices'])
        self.assertIn(self.d2_dict, data['devices'])
        self.assertEqual(len(data['devices']), 2)

        # GET with ignored authentication
        data, status_code = self.get('/device/')
        self.assertEqual(status_code, 200)
        # FIXME: adapt once ordering works
        self.assertEqual(data.keys(), ['devices'])
        self.assertIn(self.d1_dict, data['devices'])
        self.assertIn(self.d2_dict, data['devices'])
        self.assertEqual(len(data['devices']), 2)

    @skip('not implementation yet')
    def test_root_post_successful(self):
        # Post with ignored authentication
        data, status_code = self.post('/devices/',
                                      {'device':
                                       {'vk_pem': 'public key for d1'}},
                                      self.jane)
        self.assertEqual(status_code, 201)
        self.assertEqual(data, {'device': self.d1_dict})

        # The device now exists
        data, status_code = self.get('/devices/{}'.format(
            self.d1_dict['device_id']))
        self.assertEqual(status_code, 200)
        self.assertEqual(data, {'device': self.d1_dict})

        # Post without authentication
        data, status_code = self.post('/devices/',
                                      {'device':
                                       {'vk_pem': 'public key for d2'}})
        self.assertEqual(status_code, 201)
        self.assertEqual(data, {'device': self.d2_dict})

        # The device now exists
        data, status_code = self.get('/devices/{}'.format(
            self.d2_dict['device_id']))
        self.assertEqual(status_code, 200)
        self.assertEqual(data, {'device': self.d2_dict})

    @skip('not implementation yet')
    def test_root_post_successful_ignore_additional_data(self):
        # Ignored additional data, with ignored authentication
        data, status_code = self.post('/devices/',
                                      {'device':
                                       {'vk_pem': 'public key for d1',
                                        'more': 'ignored'},
                                       'and again more': 'ignored data'},
                                      self.jane)
        self.assertEqual(status_code, 201)
        self.assertEqual(data, {'device': self.d1_dict})

        # The device now exists
        data, status_code = self.get('/devices/{}'.format(
            self.d1_dict['device_id']))
        self.assertEqual(status_code, 200)
        self.assertEqual(data, {'device': self.d1_dict})

        # Ignored addtional data without authentication
        data, status_code = self.post('/devices/',
                                      {'device':
                                       {'vk_pem': 'public key for d2',
                                        'more': 'ignored'},
                                       'and again more': 'ignored data'})
        self.assertEqual(status_code, 201)
        self.assertEqual(data, {'device': self.d2_dict})

        # The device now exists
        data, status_code = self.get('/devices/{}'.format(
            self.d2_dict['device_id']))
        self.assertEqual(status_code, 200)
        self.assertEqual(data, {'device': self.d2_dict})

    @skip('not implementation yet')
    def test_root_post_malformed(self):
        # Malformed JSON with ignored authentication
        data, status_code = self.post('/devices/', '{"malformed JSON":',
                                      self.jane, dump_json_data=False)
        self.assertEqual(status_code, 400)
        self.assertEqual(data, self.error_400_malformed_dict)

        # Malformed JSON without authentication
        data, status_code = self.post('/devices/', '{"malformed JSON":',
                                      dump_json_data=False)
        self.assertEqual(status_code, 400)
        self.assertEqual(data, self.error_400_malformed_dict)

        # Good JSON but no root 'device' object, with ignored authentication
        data, status_code = self.post('/devices/',
                                      {'no-device-root': 'anything'},
                                      self.jane)
        self.assertEqual(status_code, 400)
        self.assertEqual(data, self.error_400_malformed_dict)

        # Good JSON but no root 'device' object, without authentication
        data, status_code = self.post('/devices/',
                                      {'no-device-root': 'anything'})
        self.assertEqual(status_code, 400)
        self.assertEqual(data, self.error_400_malformed_dict)

        # Good JSON but no 'vk_pem' object, with ignored authentication
        data, status_code = self.post('/devices/',
                                      {'device': {'no-vk_pem': 'anything'}},
                                      self.jane)
        self.assertEqual(status_code, 400)
        self.assertEqual(data, self.error_400_malformed_dict)

        # Good JSON but no 'vk_pem' object, without authentication
        data, status_code = self.post('/devices/',
                                      {'device': {'no-vk_pem': 'anything'}})
        self.assertEqual(status_code, 400)
        self.assertEqual(data, self.error_400_malformed_dict)

    @skip('not implementation yet')
    def test_root_post_already_registered(self):
        # First create a device
        data, status_code = self.post('/devices/',
                                      {'device':
                                       {'vk_pem': 'public key for d1'}})
        self.assertEqual(status_code, 201)
        self.assertEqual(data, {'device': self.d1_dict})

        # Then try to POST it again (ignored authentication)
        data, status_code = self.post('/devices/',
                                      {'device':
                                       {'vk_pem': 'public key for d1'}},
                                      self.jane)
        self.assertEqual(status_code, 409)
        self.assertEqual(data, self.error_409_field_conflict_dict)

        # Then try to POST it again (with no authentication)
        data, status_code = self.post('/devices/',
                                      {'device':
                                       {'vk_pem': 'public key for d1'}})
        self.assertEqual(status_code, 409)
        self.assertEqual(data, self.error_409_field_conflict_dict)

    @skip('not implementation yet')
    def test_device_get(self):
        self.create_devices()

        # Now test getting the devices, with ignored authentication
        data, status_code = self.get('/devices/{}'.format(
            self.d1_dict['device_id']), self.jane)
        self.assertEqual(status_code, 200)
        self.assertEqual(data, {'device': self.d1_dict})
        data, status_code = self.get('/devices/{}'.format(
            self.d2_dict['device_id']), self.jane)
        self.assertEqual(status_code, 200)
        self.assertEqual(data, {'device': self.d2_dict})

        # And the same without authentication
        data, status_code = self.get('/devices/{}'.format(
            self.d1_dict['device_id']))
        self.assertEqual(status_code, 200)
        self.assertEqual(data, {'device': self.d1_dict})
        data, status_code = self.get('/devices/{}'.format(
            self.d2_dict['device_id']))
        self.assertEqual(status_code, 200)
        self.assertEqual(data, {'device': self.d2_dict})

    @skip('not implementation yet')
    def test_device_get_not_found(self):
        # Get unexisting device (ignored authentication)
        data, status_code = self.get('/devices/{}'.format(
            self.d1_dict['device_id']), self.jane)
        self.assertEqual(status_code, 404)
        self.assertEqual(data, self.error_404_does_not_exist_dict)
        data, status_code = self.get('/devices/{}'.format(
            self.d2_dict['device_id']), self.jane)
        self.assertEqual(status_code, 404)
        self.assertEqual(data, self.error_404_does_not_exist_dict)

        # Get unexisting device (no authentication)
        data, status_code = self.get('/devices/{}'.format(
            self.d1_dict['device_id']))
        self.assertEqual(status_code, 404)
        self.assertEqual(data, self.error_404_does_not_exist_dict)
        data, status_code = self.get('/devices/{}'.format(
            self.d2_dict['device_id']))
        self.assertEqual(status_code, 404)
        self.assertEqual(data, self.error_404_does_not_exist_dict)

        # Now create devices
        self.create_devices()

        # And check with a third device (ignored authentication)
        data, status_code = self.get('/devices/{}'.format(
            self.d3_dict['device_id']), self.jane)
        self.assertEqual(status_code, 404)
        self.assertEqual(data, self.error_404_does_not_exist_dict)

        # Check with no authentication
        data, status_code = self.get('/devices/{}'.format(
            self.d3_dict['device_id']))
        self.assertEqual(status_code, 404)
        self.assertEqual(data, self.error_404_does_not_exist_dict)
