#!/usr/bin/python

import smtplib
import ConfigParser
import requests
from bs4 import BeautifulSoup


ROOT_URL = 'http://www.rcgroups.com/forums/'


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

        return [ROOT_URL + t.attrs['href'] for t in matching_tags]

    @property
    def new_matches(self):
        with open('matches.txt', 'a+') as f:
            past_matches = f.read()

        return [m for m in self.matches if m not in past_matches]

    def email_matching_posts(self):
        new_matches = self.new_matches
        if not new_matches:
            print 'no new matches'
            return
        username = fromaddr = self.config.get('email', 'username')
        toaddr = self.config.get('email', 'toaddr')
        password = self.config.get('email', 'password')
        msg_body = """
Here are the posts matching your keywords ({}):

{}
        """.format(self.config.get('rcgrouper', 'keywords'), '\n\n'.join(new_matches))
        msg = 'Subject: %s\n\n%s' % ('Posts you may be interested in', msg_body)
        server = smtplib.SMTP('smtp.gmail.com:587')
        server.ehlo()
        server.starttls()
        server.login(username, password)
        server.sendmail(fromaddr, toaddr, msg)
        server.quit()
        with open('matches.txt', 'a') as f:
            for m in self.new_matches:
                f.write(m + '\n')


if __name__ == '__main__':
    r = requests.get('http://www.rcgroups.com/aircraft-electric-multirotor-fs-w-733/')
    config = ConfigParser.RawConfigParser()
    config.read('.grouper')
    page = Page(r.text, config=config)
    page.email_matching_posts()
