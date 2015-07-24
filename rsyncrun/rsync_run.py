# -*-coding:utf-8-*-

__all__ = ["RsyncRun"]

import os
import getpass
import argparse
import json
import pkg_resources
import datetime
from cached_property import cached_property

from .json_conf_template import JsonConfTemplate
from .compatible import Compatible
from .shell import Shell

# TODO mock remote server


class RsyncRun(object):

    ordered_steps_list = [
        "setup_conf",
        "validate",
        "sync_source_code",
        "prepare_virtualenv",
        "install_package_lazily",
        "run_some_before_scripts",
        "launch_program",
        "clean",
    ]

    def __init__(self, sys_argv=[]):
        self.argv = sys_argv
        self.pid = os.getpid()
        self.directory = self.args.directory
        self.user = self.args.user

        self.guess_conf_file = os.path.join(self.directory, JsonConfTemplate.name_prefix + "_" + self.user + ".json")
        self.conf_file = self.args.conf or self.guess_conf_file
        self.is_auto_guessed = self.guess_conf_file == self.conf_file

        Compatible.compatible_with_old_API(self)

    def run(self):
        # TODO colorize shell output
        for idx, step in enumerate(self.ordered_steps_list):
            print "[Step#%s]:" % (idx + 1), step.replace("_", " ")
            getattr(self, step)()

    @cached_property
    def shell(self):
        return Shell(self.remote_user_host, self.execute_dir)

    @cached_property
    def old_api_json_filename(self):
        return self.guess_conf_file.replace(JsonConfTemplate.name_prefix, JsonConfTemplate.name_prefix_old)

    @cached_property
    def parser(self):
        parser = argparse.ArgumentParser(description="rsyncrun --- Rsync your code to server and run.")
        parser.add_argument(
            '--directory', default=os.getcwd(),
            help=u"Use this directory to find guessed config json file automately.", required=False, )
        parser.add_argument(
            '--user', default=getpass.getuser(),
            help=u"Use username to find guessed config json file automately.", required=False, )
        parser.add_argument(
            '--conf', default=getpass.getuser(),
            help=u"Force to specify a conf file.", required=False, )
        return parser

    @cached_property
    def args(self):
        return self.parser.parse_args(self.argv[1:])

    @cached_property
    def conf(self):
        return json.loads(file(self.conf_file).read())

    @cached_property
    def rsync_cmd(self):
        # TODO check rsync exists
        base = "rsync -av "  # rsync 不要 -z 选项
        exclude_rules = self.conf["sync_projects"].get("exclude_rules", list())
        for rule1 in exclude_rules:
            base += (" --exclude %s " % rule1)
        return base

    @cached_property
    def execute_dir(self):
        return self.conf["remote_server"]["execute_dir"]

    @cached_property
    def rsync_output_file(self):
        today_str = datetime.datetime.now().strftime("%Y%m%d")
        return "/tmp/%s_%s_%s" % (JsonConfTemplate.name_prefix, today_str, self.pid)

    @cached_property
    def rsync_output_file_remote(self):
        return "%s_2" % self.rsync_output_file

    def setup_conf(self):
        if not os.path.exists(self.conf_file):
            print """[warn] can't find %s ! Please create one, e.g. %s""" % (
                self.conf_file, JsonConfTemplate.example)
            exit(1)

    def validate(self):
        assert isinstance(self.conf, dict)
        assert "sync_projects" in self.conf, "See valid example in conf %s" % JsonConfTemplate.example
        assert "remote_server" in self.conf, "See valid example in conf %s" % JsonConfTemplate.example
        conf_file_msg = "Auto detected" if self.guess_conf_file is self.conf_file else "Specified"
        print "** %s config file is %s" % (conf_file_msg, self.conf_file)

    @cached_property
    def remote_user_host(self):
        return "%s@%s" % (self.conf["remote_server"]["user"], self.conf["remote_server"]["host"],)

    def sync_source_code(self):
        for sync_opts_type in ["local_to_remote", "remote_to_remote"]:
            sync_opt2 = self.conf["sync_projects"][sync_opts_type]
            for project1 in sync_opt2:

                if sync_opts_type == "remote_to_remote":
                    from_addr, to_addr = sync_opt2[project1]
                else:
                    from_addr = sync_opt2[project1][0]
                    to_addr = "%s:%s" % (self.remote_user_host, sync_opt2[project1][1])
                source_code_sync_command2 = """%s %s  %s | tee -a %s """ % \
                    (self.rsync_cmd,
                     from_addr,
                     to_addr,
                     self.rsync_output_file)

                if sync_opts_type == "remote_to_remote":
                    self.shell.remote(source_code_sync_command2)
                else:
                    self.shell.local(source_code_sync_command2)

        # get remote changed content
        self.shell.local("""scp %s:%s %s; cat %s >> %s; rm -f %s; """ % (
            self.remote_user_host,
            self.rsync_output_file,
            self.rsync_output_file_remote,
            self.rsync_output_file_remote,
            self.rsync_output_file,
            self.rsync_output_file_remote))
        self.source_code_sync_result = file(self.rsync_output_file).read()

        self.shell.local("echo rsync_output_file; cat %s" % self.rsync_output_file)
        self.shell.local("rm -f %s" % self.rsync_output_file)

    def prepare_virtualenv(self):
        self.shell.remote("""
        if [ ! -f ENV/bin/activate ]; then
            pip install virtualenv
            virtualenv ENV
        fi;
        """)

    @cached_property
    def dep_packages_with_install_cmd(self):
        # assign some variables
        dep_packages_with_install_cmd = self.conf.get("dep_packages_with_install_cmd", dict())

        def install_package_cmd(package_name):
            return """cd %s; cd %s; python setup.py install
                """ % (self.execute_dir, package_name,)

        for pkg1 in self.conf["sync_projects"]["projects_lazy_install_by_python"]:
            dep_packages_with_install_cmd[pkg1] = {
                "match": "\n%s/" % pkg1,  # sync files is line by line.
                "cmd": install_package_cmd(pkg1), }
        return dep_packages_with_install_cmd

    def install_package_lazily(self):
        for pkg1, install_cmd1 in self.dep_packages_with_install_cmd.iteritems():
            # compact with interrupt of sync code, and `rsync` will not detect changed code, and will not install updated packages.
            pkg1 = pkg1.split("/")[-1]  # if has dir
            need_install1 = False
            try:
                pkg_resources.require(pkg1)
            except:
                need_install1 = True
            if install_cmd1["match"] in self.source_code_sync_result:
                need_install1 = True

            if need_install1:
                print "[install packaqe]", pkg1, "is changed ..."
                self.shell.remote(install_cmd1["cmd"])
            else:
                print "[install packaqe]", pkg1, "is not changed."

    def run_some_before_scripts(self):
        for script1 in self.conf.get("scripts_before_run", list()):
            self.shell.remote(script1)

    def launch_program(self):
        task_opts = self.conf["launch"].get("params_list", list())
        if not isinstance(task_opts, list):
            task_opts = [task_opts]
        params_index = self.conf["launch"].get("params_index", 0)
        task_opts = task_opts[params_index]
        self.shell.remote(self.conf["launch"]["template"] % tuple(task_opts))

    def clean(self):
        """ when exit, clean """
        clean_file_under_root_tmp = """find /tmp/ -maxdepth 1 -type f -mmin +30 | grep %s | xargs rm -f ;"""
        self.shell.remote(clean_file_under_root_tmp % JsonConfTemplate.name_prefix)
