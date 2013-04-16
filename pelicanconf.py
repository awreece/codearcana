#!/usr/bin/env python
# -*- coding: utf-8 -*- #

AUTHOR = u'Alex Reece'
SITENAME = u'Code Arcana'
SITEURL = 'http://codearcana.com'

TIMEZONE = 'America/Los_Angeles'

TYPOGRIFY = True

THEME = './theme'

DEFAULT_LANG = u'en'

TAG_CLOUD_MAX_ITEMS = 10

# Blogroll
LINKS =  (
   ('PPP Blog', 'http://ppp.cylab.cmu.edu/wordpress/'),
   ('Coding Horror', 'http://www.codinghorror.com/blog/'),
   ('Embedded in Academia', 'http://blog.regehr.org/'),
)

# Social widget
SOCIAL = (
    ('twitter', 'https://twitter.com/awreece'),
    ('github', 'https://github.com/awreece'),
    ('google+', 'https://plus.google.com/106589059588263736517/posts'),
)

MENUITEMS = (
    ('Blog', SITEURL),
    ('About Me', SITEURL),
)

# GITHUB_URL = 'https://github.com/awreece'
TWITTER_USERNAME = 'awreece'

FILES_TO_COPY = (
  ('../extras/CNAME', 'CNAME'),
  ('../extras/README.md', 'README.md'),
)

DEFAULT_PAGINATION = 10
