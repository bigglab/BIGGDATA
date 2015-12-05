# -*- coding: utf-8 -*-
#
# This file is part of Flask-Collect.
# Copyright (C) 2012, 2013 Kirill Klenov.
# Copyright (C) 2014 CERN.
#
# Flask-Collect is free software; you can redistribute it and/or modify it
# under the terms of the Revised BSD License; see LICENSE file for
# more details.

"""Abstract File Storage."""

from __future__ import print_function

from os import path as op, walk


class BaseStorage(object):

    """Base class for storages."""

    def __init__(self, collect, verbose=False):
        """Initialize base storage."""
        self.verbose = verbose
        self.collect = collect

    def __iter__(self):
        """Seek static files and result full and relative paths.

        :return generator: Walk files
        """
        app_and_blueprints = self.collect.filter(
            [self.collect.app] + list(self.collect.blueprints.values()))

        destination_list = set()

        for bp in app_and_blueprints:
            if bp.has_static_folder and op.isdir(bp.static_folder):
                for root, _, files in walk(bp.static_folder):
                    for f in files:
                        spath = op.join(root, f)
                        tpath = op.relpath(spath, bp.static_folder.rstrip('/'))
                        relative = (bp.static_url_path and
                                    self.collect.static_url and
                                    bp.static_url_path.startswith(op.join(
                                        self.collect.static_url, '')))  # noqa
                        if relative:
                            tpath = op.join(
                                op.relpath(bp.static_url_path, self.collect.static_url), tpath)

                        if tpath in destination_list:
                            self.log("{0} already sourced".format(tpath))
                            continue

                        destination_list.add(tpath)
                        yield bp, spath, tpath

    def log(self, msg):
        """Log message."""
        if self.verbose:
            print(msg)
