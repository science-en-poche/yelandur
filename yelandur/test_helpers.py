import unittest

from yelandur import helpers


class HashTestCase(unittest.TestCase):

    def test_md5hex(self):
        self.assertEqual(helpers.md5hex('test'),
                         '098f6bcd4621d373cade4e832627b4f6')

