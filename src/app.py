#!/usr/bin/env python3
# coding: utf-8
# SPDX-License-Identifier: Apache-2.0


# Copyright 2019 AntiCompositeNumber

# Licensed under the Apache License, Version 2.0 (the "License");
# you may not use this file except in compliance with the License.
# You may obtain a copy of the License at

#   http://www.apache.org/licenses/LICENSE-2.0

# Unless required by applicable law or agreed to in writing, software
# distributed under the License is distributed on an "AS IS" BASIS,
# WITHOUT WARRANTIES OR CONDITIONS OF ANY KIND, either express or implied.
# See the License for the specific language governing permissions and
# limitations under the License.

import logging
import os
import json
import subprocess
import flask

# Configure logging
logging.basicConfig(filename='linkspam.log', level=logging.DEBUG)

# Set up Flask app
app = flask.Flask(__name__)

# Load config from json in the same directory as the app
__dir__ = os.path.dirname(__file__)
with open(os.path.join(__dir__, 'config.json')) as f:
    app.config.update(json.load(f))

# Get the short hash for the current git commit
rev = subprocess.run(['git', 'rev-parse', '--short', 'HEAD'],
                     universal_newlines=True, stdout=subprocess.PIPE,
                     stderr=subprocess.PIPE)
app.config['version'] = rev.stdout


@app.route('/')
def linksearch():
    with open(os.path.join(app.config['linkspam_data_dir'],
                           'linkspam_config.json')) as f:
        data = json.load(f)

    return flask.render_template('linkspam.html', data=data)


# @app.route('/<target>/job')
# def linksearch_job(target):
#    percent = flask.request.args.get('percent', '')
#    return flask.render_template('linkspam_submit.html',
#                                 percent=percent)


@app.route('/<target>')
def linksearch_result(target):
    try:
        with open(os.path.join(app.config['linkspam_data_dir'],
                               target + '.json')) as f:
            data = json.load(f)
    except FileNotFoundError:
        return flask.render_template(
            'linkspam_noresult.html', target=target), 404
    else:
        return flask.render_template('linkspam_result.html', data=data)
