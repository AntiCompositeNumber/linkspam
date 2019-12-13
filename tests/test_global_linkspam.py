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

import pytest
# import requests
# import mwparserfromhell as mwph
import json
import pywikibot
import unittest.mock as mock
import inspect
import sys
import os

__dir__ = os.path.realpath(os.path.dirname(__file__)+"/..")
conf = os.path.join(__dir__, 'src/config.json')

try:
    open(conf, 'r')
except FileNotFoundError:
    with open(conf, 'w') as f:
        json.dump({}, f)

sys.path.append(__dir__)
import src.global_linkspam as global_linkspam  # noqa: E402


def test_get_sitematrix():
    matrix = global_linkspam.get_sitematrix
    assert inspect.isgeneratorfunction(matrix)
    l_matrix = list(matrix())
    assert 'https://en.wikipedia.org' in l_matrix
    assert len(l_matrix) > 700


def test_check_status_closed():
    checksite = {'closed': '',
                 'code': 'wikimania2005',
                 'dbname': 'wikimania2005wiki',
                 'lang': 'wikimania2005',
                 'sitename': 'Wikipedia',
                 'url': 'https://wikimania2005.wikimedia.org'}

    assert not global_linkspam.check_status(checksite)


def test_check_status_private():
    checksite = {'code': 'wikimaniateam',
                 'dbname': 'wikimaniateamwiki',
                 'lang': 'en',
                 'private': '',
                 'sitename': 'WikimaniaTeam',
                 'url': 'https://wikimaniateam.wikimedia.org'}

    assert not global_linkspam.check_status(checksite)


def test_check_status_fishbowl():
    checksite = {'code': 'nostalgia',
                 'dbname': 'nostalgiawiki',
                 'fishbowl': '',
                 'lang': 'nostalgia',
                 'sitename': 'Wikipedia',
                 'url': 'https://nostalgia.wikipedia.org'}

    assert not global_linkspam.check_status(checksite)


def test_check_status_open():
    checksite = {'url': 'https://en.wikipedia.org'}

    assert global_linkspam.check_status(checksite)


def test_list_pages():
    m = mock.MagicMock()
    m.return_value = ['Test']
    with mock.patch('pywikibot.pagegenerators.LinksearchPageGenerator', m):
        output = list(global_linkspam.list_pages('site', 'example.com'))

    assert len(output) == 4
    calls = [mock.call('example.com', site='site', protocol='http'),
             mock.call('example.com', site='site', protocol='https'),
             mock.call('*.example.com', site='site', protocol='http'),
             mock.call('*.example.com', site='site', protocol='https')]
    assert m.mock_calls == calls


def test_run_check_true():
    m = mock.MagicMock()
    n = mock.MagicMock()
    n.text = 'True'
    m.return_value = n
    with mock.patch('pywikibot.Page', m):
        assert global_linkspam.run_check('', False) is None


def test_run_check_false():
    m = mock.MagicMock()
    n = mock.MagicMock()
    n.text = 'False'
    m.return_value = n
    with mock.patch('pywikibot.Page', m):
        with pytest.raises(pywikibot.UserBlocked):
            global_linkspam.run_check('', False)


def test_run_check_nonsense():
    m = mock.MagicMock()
    n = mock.MagicMock()
    n.text = 'Bananas'
    m.return_value = n
    with mock.patch('pywikibot.Page', m):
        with pytest.raises(pywikibot.UserBlocked):
            global_linkspam.run_check('', False)


def test_run_check_blank():
    m = mock.MagicMock()
    n = mock.MagicMock()
    n.text = ''
    m.return_value = n
    with mock.patch('pywikibot.Page', m):
        with pytest.raises(pywikibot.UserBlocked):
            global_linkspam.run_check('', False)


def test_run_check_override():
    m = mock.MagicMock()
    n = mock.MagicMock()
    n.text = 'False'
    m.return_value = n
    with mock.patch('pywikibot.Page', m):
        global_linkspam.run_check('', True)
