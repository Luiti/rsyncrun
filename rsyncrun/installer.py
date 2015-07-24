# -*-coding:utf-8-*-

__all__ = ["Installer"]

import os
import pkg_resources


class Installer(object):
    """
    Give a incremental code changelog, and install relative changed Python package.
    """

    def __init__(self, execute_dir, package_dir_list):
        self.execute_dir = execute_dir
        self.package_dir_list = package_dir_list

    def run(self, incremental_code_changelog):
        """
        `incremental_code_changelog` is lines sync filenames.
        """
        print
        print "[incremental_code_changelog]", incremental_code_changelog
        print

        for pkg in self.package_dir_list:
            pkg_short = pkg.split("/")[-1]  # if has dir
            dirs = self.select_matched_package_dirs(pkg, incremental_code_changelog)

            if len(dirs) > 0:
                print "[install packaqe]", pkg_short, "is changed ..."
                for dir1 in dirs:
                    os.system("cd %s; python setup.py install" % dir1)
            else:
                print "[install packaqe]", pkg_short, "is not changed."

    def select_matched_package_dirs(self, pkg, incremental_code_changelog):
        """ find pkg dir through `incremental_code_changelog`. """
        matched_lines = [line.strip() for line in incremental_code_changelog.split("\n") if pkg in line]
        result = list()

        for dir1 in matched_lines:
            package_dir = os.path.join(self.execute_dir, dir1)
            while package_dir != self.execute_dir:
                if self.is_valid_package(package_dir):
                    result.append(package_dir)
                package_dir = os.path.dirname(package_dir)
        return result

    def is_pkg_installed(self, pkg):
        yes = False
        try:
            pkg_resources.require(pkg)
            yes = True
        except ImportError:
            pass
        return yes

    def is_valid_package(self, package_dir):
        python_setup = os.path.join(package_dir, "setup.py")
        return os.path.exists(python_setup)
