#!/usr/bin/python

import textwrap
from datetime import datetime
import os
import smtplib
import ConfigParser
from bs4 import BeautifulSoup
import requests

# TODO clear out matching links list periodically

ROOT_URL = 'http://www.rcgroups.com/forums/'
PROJECT_DIR = os.path.dirname(__file__)
MATCH_FILE = os.path.join(PROJECT_DIR, 'matches.txt')
CONFIG_FILE = os.path.join(PROJECT_DIR, '.grouper')


class Page(object):

    def __init__(self, raw_html, config):
        self.raw_html = raw_html
        self.config = config
        self.keywords = self.config.get('rcgrouper', 'keywords').split(',')
        self.matches = self.get_kw_matches()

    def get_kw_matches(self):
        soup = BeautifulSoup(self.raw_html, 'html.parser')
        a_tags = soup.find_all('a')
        matching_tags = []
        for a in a_tags:
            if any(kw.lower().strip() in a.text.lower() for kw in self.keywords):
                matching_tags.append(a)
        return matching_tags

    @property
    def new_matches(self):
        with open(MATCH_FILE, 'a+') as f:
            past_matches = f.read()
        return [m for m in self.matches if m.attrs['href'] not in past_matches]

    def email_matching_posts(self):
        new_matches = self.new_matches
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
        """).format(keywords, '\n\n'.join(match_details))
        msg = 'Subject: %s\n\n%s' % ('Posts you may be interested in', msg_body)
        server = smtplib.SMTP('smtp.gmail.com:587')
        server.ehlo()
        server.starttls()
        server.login(username, password)
        server.sendmail(fromaddr, toaddr, msg)
        server.quit()
        with open(MATCH_FILE, 'a') as f:
            f.write('Checked on ' + datetime.now().strftime('%Y-%m-%d %H:%M') + '\n')
            for m in self.new_matches:
                f.write(ROOT_URL + m.attrs['href'] + '\n')


if __name__ == '__main__':
    r = requests.get('http://www.rcgroups.com/aircraft-electric-multirotor-fs-w-733/')
    cfg = ConfigParser.RawConfigParser()
    cfg.read(CONFIG_FILE)
    page = Page(r.text, config=cfg)
    page.email_matching_posts()
