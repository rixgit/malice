# !/usr/bin/env python
# -*- coding: utf-8 -*-

__author__ = 'Josh Maine'
__copyright__ = '''Copyright (C) 2013-2014 Josh "blacktop" Maine
                   This file is part of Malice - https://github.com/blacktop/malice
                   See the file 'docs/LICENSE' for copying permission.'''

# Copyright (C) 2010-2014 Cuckoo Foundation.
# This file is part of Cuckoo Sandbox - http://www.cuckoosandbox.org
# See the file 'docs/LICENSE' for copying permission.

import os
import sys
import copy
import json
import urllib
import urllib2
import requests
import logging
import logging.handlers

import modules.av
import modules.intel
import modules.file
import modules.sandbox

from lib.common.colors import red, green, yellow, cyan
from lib.common.config import Config
from lib.common.constants import MALICE_ROOT, MALICE_VERSION
from lib.common.exceptions import MaliceStartupError
# from lib.common.exceptions import MaliceOperationalError
# from lib.common.utils import create_folders
# from lib.core.database import Database, TASK_RUNNING
from lib.core.plugins import import_plugin, import_package, list_plugins

log = logging.getLogger()


def check_python_version():
    """Checks if Python version is supported by Malice.
    @raise MaliceStartupError: if version is not supported.
    """
    if sys.version_info[:2] != (2, 7):
        raise MaliceStartupError("You are running an incompatible version "
                                 "of Python, please use 2.7")


# def check_working_directory():
#     """Checks if working directories are ready.
#     @raise MaliceStartupError: if directories are not properly configured.
#     """
#     if not os.path.exists(MALICE_ROOT):
#         raise MaliceStartupError("You specified a non-existing root "
#                                  "directory: {0}".format(MALICE_ROOT))
#
#     cwd = os.path.join(os.getcwd(), "malice.py")
#     if not os.path.exists(cwd):
#         raise MaliceStartupError("You are not running Malice from it's "
#                                  "root directory")


def check_configs():
    """Checks if config files exist.
    @raise MaliceStartupError: if config files do not exist.
    """
    configs = [os.path.join(MALICE_ROOT, "conf", "malice.conf"),
               os.path.join(MALICE_ROOT, "conf", "av.conf"),
               os.path.join(MALICE_ROOT, "conf", "intel.conf"),
               os.path.join(MALICE_ROOT, "conf", "file.conf")]

    for config in configs:
        if not os.path.exists(config):
            raise MaliceStartupError("Config file does not exist at "
                                     "path: {0}".format(config))

    return True


# def create_structure():
# """Creates Malice directories."""
#     folders = [
#         "log",
#         "storage",
#         os.path.join("storage", "analyses"),
#         os.path.join("storage", "binaries")
#     ]
#
#     try:
#         create_folders(root=MALICE_ROOT, folders=folders)
#     except MaliceOperationalError as e:
#         raise MaliceStartupError(e)

def check_version():
    """Checks version of Malice."""
    cfg = Config()

    if not cfg.malice.version_check:
        return

    print(" Checking for updates...")

    url = "https://api.github.com/repos/blacktop/malice/releases"
    try:
        response = requests.get(url=url)
    except requests.RequestException as e:
        print(red(" Failed! ") + "Unable to establish connection.\n")
        return
        # return dict(error=e)

    if response.status_code == requests.codes.ok:
        try:
            response_data = response.json()
        except:
            print(red(" Failed! ") + "Invalid response.\n")
            return
        latest_version = response_data[0][u'name']
        if latest_version != MALICE_VERSION:
            msg = "Malice version {0} is available " \
                  "now.\n".format(latest_version)
            print(red(" Outdated! ") + msg)
        else:
            print(green(" Good! ") + "You have the latest version "
                                     "available.\n")


# class DatabaseHandler(logging.Handler):
#     """Logging to database handler."""
#
#     def emit(self, record):
#         if hasattr(record, "task_id"):
#             db = Database()
#             db.add_error(record.msg, int(record.task_id))


class ConsoleHandler(logging.StreamHandler):
    """Logging to console handler."""

    def emit(self, record):
        colored = copy.copy(record)

        if record.levelname == "WARNING":
            colored.msg = yellow(record.msg)
        elif record.levelname == "ERROR" or record.levelname == "CRITICAL":
            colored.msg = red(record.msg)
        else:
            if "analysis procedure completed" in record.msg:
                colored.msg = cyan(record.msg)
            else:
                colored.msg = record.msg

        logging.StreamHandler.emit(self, colored)


def init_logging():
    """Initializes logging."""
    formatter = logging.Formatter("%(asctime)s [%(name)s] %(levelname)s: %(message)s")

    fh = logging.handlers.WatchedFileHandler(os.path.join(MALICE_ROOT, "logs", "malice.log"))
    fh.setFormatter(formatter)
    log.addHandler(fh)

    ch = ConsoleHandler()
    ch.setFormatter(formatter)
    log.addHandler(ch)

    # dh = DatabaseHandler()
    # dh.setLevel(logging.ERROR)
    # log.addHandler(dh)

    log.setLevel(logging.INFO)


# def init_tasks():
#     """Check tasks and reschedule uncompleted ones."""
#     # db = Database()
#     cfg = Config()
#
#     if cfg.malice.reschedule:
#         log.debug("Checking for locked tasks...")
#
#         tasks = db.list_tasks(status=TASK_RUNNING)
#
#         for task in tasks:
#             db.reschedule(task.id)
#             log.info("Rescheduled task with ID {0} and "
#                      "target {1}".format(task.id, task.target))


def init_modules():
    """Initializes plugins."""
    log.debug("Importing modules...")

    # Import all antivirus modules.
    import_package(modules.av)
    # Import all intel modules.
    import_package(modules.intel)
    # Import all file analysis modules.
    import_package(modules.file)
    # Import all file sandbox modules.
    import_package(modules.sandbox)

    for category, entries in list_plugins().items():
        log.debug("Imported \"%s\" modules:", category)

        for entry in entries:
            if entry == entries[-1]:
                log.debug("\t `-- %s", entry.__name__)
            else:
                log.debug("\t |-- %s", entry.__name__)
