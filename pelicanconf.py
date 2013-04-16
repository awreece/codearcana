#!/usr/bin/env python
# -*- coding: utf-8 -*- #

AUTHOR = u'Alex Reece'
SITENAME = u'Code Arcana'
SITEURL = 'http://codearcana.com'

TIMEZONE = 'America/Los_Angeles'

THEME = './theme'

DEFAULT_LANG = u'en'

TAG_CLOUD_MAX_ITEMS = 10

# Blogroll
LINKS =  (
   ('PPP Blog', 'http://ppp.cylab.cmu.edu/wordpress/'),
   ('Coding Horror', 'http://www.codinghorror.com/blog/'),
   ('Embedded in Academia', 'http://blog.regehr.org/'),
   ('High Scalability', 'http://highscalability.com/'),
   ('Coder Weekly', 'http://coderweekly.com/'),
   ('phrack', 'http://www.phrack.org/'),
   ("skier_'s blog", 'http://jbremer.org/'),
)

# Social widget
SOCIAL = (
    ('twitter', 'https://twitter.com/awreece'),
    ('github', 'https://github.com/awreece'),
    ('google+', 'https://plus.google.com/106589059588263736517/posts'),
)

MENUITEMS = (
    ('Blog', SITEURL),
    ('Archives', SITEURL + "/archives.html"),
)

# GITHUB_URL = 'https://github.com/awreece'
TWITTER_USERNAME = 'awreece'

FILES_TO_COPY = (
  ('../extras/CNAME', 'CNAME'),
  ('../extras/README.md', 'README.md'),
)

YEAR_ARCHIVE_SAVE_AS =  'posts/{date:%Y}/index.html'
MONTH_ARCHIVE_SAVE_AS = 'posts/{date:%Y}/{date:%m}/index.html'
ARTICLE_URL =           'posts/{date:%Y}/{date:%m}/{slug}.html'
ARTICLE_SAVE_AS =       'posts/{date:%Y}/{date:%m}/{slug}.html'
ARTICLE_LANG_URL =      'posts/{date:%Y}/{date:%m}/{slug}-{lang}.html'
ARTICLE_LANG_SAVE_AS =  'posts/{date:%Y}/{date:%m}/{slug}-{lang}.html'

DEFAULT_PAGINATION = 10
