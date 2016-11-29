#!/usr/bin/python

import logging
import logging.handlers
import textwrap
from datetime import datetime, timedelta
import os
import smtplib
import ConfigParser
from bs4 import BeautifulSoup
import requests

SITES = {
    'multirotor': 'http://www.rcgroups.com/aircraft-electric-multirotor-fs-w-733/',
    'fpv': 'https://www.rcgroups.com/fpv-equipment-fs-w-710/',
    'lipo': 'https://www.rcgroups.com/aircraft-electric-batteries-and-chargers-fs-w-284/',
}

ROOT_URL = 'http://www.rcgroups.com/forums/'
PROJECT_DIR = os.path.dirname(__file__)
MATCH_FILE = os.path.join(PROJECT_DIR, 'matches.txt')
CONFIG_FILE = os.path.join(PROJECT_DIR, '.grouper')
LOG_FILE = os.path.join(PROJECT_DIR, 'grouper.log')
DATE_FORMAT = '%Y-%m-%d'

handler = logging.handlers.RotatingFileHandler(LOG_FILE, maxBytes=10000, backupCount=3)
logging.basicConfig(filename=LOG_FILE, format='%(asctime)s: %(message)s', level=logging.INFO)
grouper_logger = logging.getLogger()
grouper_logger.addHandler(handler)


class Page(object):

    def __init__(self, raw_html, config):
        self.raw_html = raw_html
        self.config = config
        self.keywords = self.config.get('rcgrouper', 'keywords').split(',')
        self.matches = self.get_kw_matches()

    def get_kw_matches(self):
        '''Return a list of Tag objects that match keywords in config'''
        soup = BeautifulSoup(self.raw_html, 'html.parser')
        a_tags = soup.find_all('a')
        matching_tags = []
        for a in a_tags:
            if any(kw.lower().strip() in a.text.lower() for kw in self.keywords):
                matching_tags.append(a)
        return matching_tags


    def get_new_matches(self):
        '''List of matches that have not been sent to user yet'''
        with open(MATCH_FILE, 'a+') as f:
            past_matches = f.read()
        return [m for m in self.matches if m.attrs['href'] not in past_matches]

    def email_matching_posts(self):
        new_matches = self.get_new_matches()
        if not new_matches:
            print 'no new matches'
            return
        username = fromaddr = self.config.get('email', 'username')
        toaddr = self.config.get('email', 'toaddr')
        password = self.config.get('email', 'password')
        keywords = self.config.get('rcgrouper', 'keywords')
        match_details = [m.text + '\n' + ROOT_URL + m.attrs['href'] for m in new_matches]
        msg_body = textwrap.dedent("""\
        Here are the posts matching your keywords ({}):

        {}
        """).format(keywords, '\n\n'.join(match_details).encode('utf-8'))
        msg = 'Subject: %s\n\n%s' % ('Posts you may be interested in', msg_body)
        server = smtplib.SMTP('smtp.gmail.com:587')
        server.ehlo()
        server.starttls()
        server.login(username, password)
        server.sendmail(fromaddr, toaddr, msg)
        server.quit()
        date_sent = datetime.now().strftime('%Y-%m-%d %H:%M')
        with open(MATCH_FILE, 'a') as f:
            f.write('Checked on ' + date_sent + '\n')
            grouper_logger.info('Email sent at %s', date_sent)
            for m in self.get_new_matches():
                f.write(ROOT_URL + m.attrs['href'] + '\n')

def set_expiration_date(config):
    '''Set a new expiration date in config file 1 week in future'''
    new_exp = datetime.now() + timedelta(weeks=1)
    exp_string = new_exp.strftime(DATE_FORMAT)
    config.set('rcgrouper', 'match_expiration', exp_string)
    with open(CONFIG_FILE, 'wb') as configfile:
        config.write(configfile)
    grouper_logger.info('New expiration date set to %s', exp_string)

def cleanup_matches(config):
    '''Clean up old matches and set new expiration date if necessary

    If the current date is >= the expiration date in the config file,
    empty matches.txt file and update config with new expiration date
    one week in the future.
    '''
    exp = config.get('rcgrouper', 'match_expiration')
    if not exp:
        set_expiration_date(config)
        grouper_logger.info('Expiration set for the first time')
        return
    exp_dt = datetime.strptime(exp, DATE_FORMAT)
    if datetime.now() >= exp_dt:
        open(MATCH_FILE, 'w').close()
        grouper_logger.info('Match file cleared')
        set_expiration_date(config)


if __name__ == '__main__':

    cfg = ConfigParser.RawConfigParser()
    cfg.read(CONFIG_FILE)
    for_sale_only = True if cfg.get('rcgrouper', 'for_sale_only') == 'true' else False
    suffix = '?prefixid=For_Sale_def_' if for_sale_only else ''
    sites_to_check = cfg.get('rcgrouper', 'sites_to_check').split(',')
    _html = ''

    for site in sites_to_check:
        _html += requests.get(SITES[site] + suffix).text

    page = Page(_html, config=cfg)
    page.email_matching_posts()
    cleanup_matches(cfg)
