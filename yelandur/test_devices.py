# -*- coding: utf-8 -*-

from unittest import skip

from .models import Device
from .helpers import APITestCase


# TODO: add CORS test


class ExpsTestCase(APITestCase):

    maxDiff = None

    def setUp(self):
        super(ExpsTestCase, self).setUp()

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
        # Ignore authentication
        pass

    @skip('not implementation yet')
    def test_root_post_successful_ignore_additional_data(self):
        # Ignore authentication
        pass

    @skip('not implementation yet')
    def test_root_post_malformed(self):
        # Bad JSON
        # Good JSON but no root 'device' object
        # Good JSON but no 'vk_pem'
        # Ignore authentication
        pass

    @skip('not implementation yet')
    def test_root_post_already_registered(self):
        # Ignore authentication
        pass

    @skip('not implementation yet')
    def test_device_get(self):
        # Successful GET
        # Ignore authentication
        pass

    @skip('not implementation yet')
    def test_device_get_not_found(self):
        # 404
        # Ignore authentication
        pass
