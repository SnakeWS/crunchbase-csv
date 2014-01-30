#!/usr/bin/env python

import crunchbase
from collections import defaultdict
import argparse
import csv
import simplejson
import codecs
import pandas
import numpy as np
import sys
import Levenshtein
import logging
import re

logging.basicConfig()
log = logging.getLogger(__name__)
log.setLevel(logging.INFO)

from HTMLParser import HTMLParser

class MLStripper(HTMLParser):
    def __init__(self):
        self.reset()
        self.fed = []
    def handle_data(self, d):
        self.fed.append(d)
    def get_data(self):
        return ''.join(self.fed)

def strip_tags(html):
    s = MLStripper()
    s.feed(html)
    return s.get_data()

def cleanup(s):
    return re.sub(u' (inc|corp)\S*$','', s.lower().replace(',','').replace('.',''))

def crunchbase_csv(api_key, query, cache={}):
    cb = crunchbase.CrunchBase(api_key, cache=cache, check_update=False)
    log.info('Grabbing list of companies')
    companies = cb.listCompanies()

    log.info('Gathered list of %d companies' % len(companies))
    names = np.asarray([cleanup(x['name']) for x in companies])
    names_dict = defaultdict(lambda: [])
    for i,n in enumerate(names): names_dict[n[0]].append((i,n))
    company_info = []

    for q in query:
        names_d = names_dict[q[0]]
        dists = [Levenshtein.distance(q, x) for (i,x) in names_d]
        sort_ix = np.argsort(dists)
        closest = sort_ix[0]
        (orig_ix, name_closest) = names_d[closest]
        orig_name = companies[orig_ix]['name']
        orig_perma = companies[orig_ix]['permalink']
        log.info('Closest match to %s is %s, dist: %d' % (q, orig_name, dists[closest]))
        if dists[closest] <= 1:
            log.info('Querying %s (%s)' % (orig_name, orig_perma))
            info = cb.getCompanyData(orig_perma)
            company_info.append(info)

    with codecs.open('cache', mode='w') as cw:
        simplejson.dump(cb.getCache(), cw)

    ci = pandas.DataFrame(company_info)
    ci_red = ci.filter([
        'name', 'acquisition', 'category_code', 'deadpooled_year', 'description',
        'email_address', 'homepage_url', 'ipo', 'number_of_employees',
        'overview', 'total_money_raised'
    ])
    ci_red['ipo'] = ['$%s' % x['valuation_amount'] if x is not None else None for x in ci_red['ipo']]
    ci_red['acquisition'] = [x['source_description'] if x is not None else None for x in ci_red['acquisition']]
    ci_red['overview'] = [strip_tags(x).replace('\n',' ') if x is not None else None for x in ci_red['overview']]
    ci_red.to_csv(sys.stdout, sep=",", index=False, encoding='utf-8', quoting=csv.QUOTE_ALL)


def main():
    parser = argparse.ArgumentParser(description="Convert crunchbase to CSV")
    parser.add_argument("--api_key", help="CrunchBase API Key", required=True)
    args = parser.parse_args()
    query = np.asarray([cleanup(x.strip())
                        for x in codecs.getreader("utf-8")(sys.stdin)])

    with codecs.open('cache', 'r', encoding='utf-8') as cf:
        cache = simplejson.load(cf)

    crunchbase_csv(api_key=args.api_key, query=query, cache=cache)

if __name__ == "__main__":
    main()
