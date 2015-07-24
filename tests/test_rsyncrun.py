# -*- coding: utf-8 -*-

import os
import sys
root_dir = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
sys.path.insert(0, root_dir)

import mock
import unittest
from rsyncrun import RsyncRun


class TestRsyncrun(unittest.TestCase):

    @mock.patch("rsyncrun.compatible.find_old_api")
    def test_compatible(self, find_old_api):
        find_old_api.return_value = True

        rr = RsyncRun("rsyncrun --user mvj3".split(" "))
        self.assertEqual(rr.guess_conf_file.split("/")[-1], "rsyncrun_mvj3.json")
        self.assertEqual(rr.conf_file.split("/")[-1], "xdeploy_mvj3.json")

    def test_installer(self):
        from rsyncrun.installer import Installer

        def is_valid_package_in_fake(self, package_dir):
            return {
                "/tmp/foobar": True,
                "/tmp/foobar/barfoo.py": False,
            }[package_dir]
        Installer.is_valid_package = is_valid_package_in_fake

        installer = Installer("/tmp", ["foobar"])

        result1 = installer.select_matched_package_dirs("foobar", """
        foobar/barfoo.py
        helloworld
        """)
        self.assertEqual(result1, ["/tmp/foobar"])


if __name__ == '__main__':
    unittest.main()
