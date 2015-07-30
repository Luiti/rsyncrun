# -*- coding: utf-8 -*-

import os
import sys
root_dir = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
sys.path.insert(0, root_dir)

import unittest
from rsyncrun import RsyncRun


class TestRsyncrun(unittest.TestCase):

    def test_compatible(self):
        self.assertEqual(RsyncRun, RsyncRun)  # dumb test


if __name__ == '__main__':
    unittest.main()
