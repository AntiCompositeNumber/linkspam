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

"""Generates reports for a link cleanup project"""

import time
from datetime import datetime
import urllib.parse
import json
import os
import argparse
import logging
import requests
import pywikibot
from pywikibot import pagegenerators

version = '1.3.0'

# Load config.json in the same directory as the code
config = {}
__dir__ = os.path.dirname(__file__)
with open(os.path.join(__dir__, 'config.json')) as f:
    config.update(json.load(f))


def get_sitematrix():
    """Request the sitematrix from the API, check if open, then yield URLs"""

    # Construct the request to the Extension:Sitematrix api
    payload = {"action": "sitematrix", "format": "json",
               "smlangprop": "site", "smsiteprop": "url"}
    headers = {'user-agent': 'HijackSpam ' + version + ' as AntiCompositeBot'
               + ' on Toolforge. User:AntiCompositeNumber, pywikibot/'
               + pywikibot.__version__}
    url = 'https://meta.wikimedia.org/w/api.php'

    # Send the request, except on HTTP errors, and try to decode the json
    r = requests.get(url, headers=headers, params=payload)
    r.raise_for_status()
    result = r.json()['sitematrix']

    # Parse the result into a generator of urls of public open wikis
    for key, lang in result.items():
        if key == 'count':
            continue
        elif key == 'specials':
            for site in lang:
                if check_status(site):
                    yield site['url']
        else:
            for site in lang['site']:
                if check_status(site):
                    yield site['url']


def check_status(checksite):
    """Return true only if wiki is public and open"""
    return ((checksite.get('closed') is None)
            and (checksite.get('private') is None)
            and (checksite.get('fishbowl') is None))


def list_pages(site, target):
    """Takes a site object and yields the pages linking to the target"""

    # Linksearch is specific, and treats http/https and TLD/subdomain
    # links differently, so we need to run through them all
    for num in range(0, 4):
        if num % 2 == 0:
            # Even numbers run https, odds run http
            protocol = 'http'
        else:
            protocol = 'https'

        if num > 1:
            # 0 and 1 run top-level domain, 2 and 3 run subdomains
            ctar = '*.' + target
        else:
            ctar = target

        # Iterate over the pages and yeild them
        for page in pagegenerators.LinksearchPageGenerator(
                ctar, site=site, protocol=protocol):
            yield page


def site_report(pages, site, preload_sums, report_site):
    """Generate the full linksearch report for a site"""

    # Try to get preloaded edit summaries from config.
    # First check for a summary in the wiki's language, then fall back to
    # English, then just return an empty string.
    summary = urllib.parse.quote(preload_sums.get(
        site.code, preload_sums.get('en', '')))

    # Prepare an empty list for reports
    reports = []

    # Iterate over the pages in the data
    for page in pages:
        # Get the full URL for the page
        url = page.full_url()
        # Turn that url into an edit link using URL parameters
        edit_link = url + '?action=edit&summary=' + summary + '&minor=1'

        # Construct a dict using the report data
        page_line = dict(page_title=page.title(),
                         page_link=url, edit_link=edit_link)

        # If the page is already in the reports, skip it.
        # Otherwise, add the page line to the end of the list
        if page_line not in reports:
            reports.append(page_line)

    # Count the reports for this wiki
    count = len(reports)

    # If there's something to report, return it and the count.
    # Otherwise, just return an empty dict.
    if count > 0:
        return {'reports': reports, 'count': count}
    else:
        return {}


def summary_table(counts):
    """Takes a dictionary of dbnames and counts and returns at table"""

    # Filter for only wikis with non-zero counts
    entries = {key: value for key, value in counts.items() if value != 0}
    # Sum the per-wiki counts and count the wikis
    total_pages = sum(entries.values())
    total_wikis = len(entries)

    # Return all that as a dict.
    return dict(entries=entries, total_pages=total_pages,
                total_wikis=total_wikis)


def run_check(site, runOverride):
    """Prevents the tool from running if the runpage is false"""
    # TODO issue #16
    runpage = pywikibot.Page(site, 'User:AntiCompositeBot/HijackSpam/Run')
    run = runpage.text.endswith('True')
    if run is False and runOverride is False:
        print('Runpage is false, quitting...')
        raise pywikibot.UserBlocked('Runpage is false')


def save_page(new_text, target):
    """Saves the report data and updates the config"""
    data_dir = config['linkspam_data_dir']
    with open(os.path.join(data_dir, target + '.json'), 'w') as f:
        json.dump(new_text, f, indent=4)

    with open(os.path.join(data_dir, 'linkspam_config.json'), 'r') as f:
        linkspam_config = json.load(f)

    linkspam_config[target]['last_update'] = new_text['start_time']

    # If the report is marked new, mark it not new.
    if linkspam_config[target]['status'] == 'new':
        if linkspam_config[target]['frequency'] == 'manual':
            linkspam_config[target]['status'] = 'finished'
        else:
            linkspam_config[target]['status'] = 'automatic'

    with open(os.path.join(data_dir, 'linkspam_config.json'), 'w') as f:
        json.dump(linkspam_config, f, indent=4)


def main():
    # define empty dicts
    counts = {}
    output = {}

    # Parse command line arguments for target domain
    parser = argparse.ArgumentParser(description='Generate global link usage')
    parser.add_argument(
        'target', help='Domain, such as "example.com", to search for')
    target = parser.parse_args().target

    # Set up on enwiki and check runpage
    enwiki = pywikibot.Site('en', 'wikipedia')
    run_check(enwiki, False)

    # Load linkspam_config.json
    with open(os.path.join(
            config['linkspam_data_dir'], 'linkspam_config.json'), 'r') as f:
        linkspam_config = json.load(f)

    # Check for configuration for target
    if linkspam_config.get(target) is None:
        logging.warning('No config found. Using the default configs.')
        linkspam_config[target] = linkspam_config['default']

    # Load preload summaries from config
    preload_sums = linkspam_config[target].get('summary')

    # Get the list of sites from get_sitematrix(), retrying once
    try:
        sitematrix = get_sitematrix()
    except requests.exceptions:
        time.sleep(5)
        sitematrix = get_sitematrix()

    # Add the start time and target to the output
    output['target'] = target
    output['start_time'] = datetime.utcnow().isoformat()

    # Run through the sitematrix. If pywikibot works on that site, generate
    # a report. Otherwise, add it to the skipped list.
    skipped = []
    site_reports = {}
    for url in sitematrix:
        try:
            cur_site = pywikibot.Site(url=url + '/wiki/MediaWiki:Delete/en')
            # Get the combined usage on this site
            pages = list_pages(cur_site, target)
            # Generate the report data from the usage list
            report = site_report(pages, cur_site, preload_sums, enwiki)
        except Exception:
            skipped.append(url)
            continue
        # Only add the reports with data to the output
        if report:
            print(url)
            site_reports[cur_site.dbName()] = report
            counts[cur_site.dbName()] = report['count']

    # Add all the generated reports and the skipped sites to the output
    output['site_reports'] = site_reports
    output['skipped'] = skipped

    # Generate the data for the summary table
    output['summary_table'] = summary_table(counts)

    # Save the report
    save_page(output, target)


if __name__ == '__main__':
    main()
