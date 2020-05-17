#!/usr/bin/env python
# -*- coding: utf-8 -*- #

try:
  import sys
  sys.path.append('.')
  #
  # Download https://github.com/getpelican/pelican-plugins to some directory
  # and set PLUGIN_PATHS = ['path/to/that/dir'] in pelicanconf_local.py
  #
  from pelicanconf_local import *
except:
  pass

PLUGINS = ['tag_cloud']

AUTHOR = u'Alex Reece'
SITENAME = u'Code Arcana'
SITEURL = 'http://codearcana.com'

TIMEZONE = 'America/Los_Angeles'

THEME = './theme'

DEFAULT_LANG = u'en'

TAG_CLOUD_MAX_ITEMS = 10

# Social widget
SOCIAL = (
    ('twitter', 'https://twitter.com/awreece'),
    ('github', 'https://github.com/awreece'),
    ('linkedin', 'http://www.linkedin.com/in/awreece'),
)

MENUITEMS = (
    ('About', SITEURL + '/pages/about.html'),
    ('Blog', SITEURL),
)

# GITHUB_URL = 'https://github.com/awreece'
TWITTER_USERNAME = 'awreece'

STATIC_PATHS = [
    'images',
    '../extras/CNAME',
    '../extras/README.md',
]

EXTRA_PATH_METADATA = {
    '../extras/CNAME': {'path': 'CNAME'},
    '../extras/README.md': {'path': 'README.md'}
}

YEAR_ARCHIVE_SAVE_AS =  'posts/{date:%Y}/index.html'
MONTH_ARCHIVE_SAVE_AS = 'posts/{date:%Y}/{date:%m}/index.html'
DAY_ARCHIVE_SAVE_AS =   'posts/{date:%Y}/{date:%m}/{date:%d}/index.html'
ARTICLE_URL =           'posts/{date:%Y}/{date:%m}/{date:%d}/{slug}.html'
ARTICLE_SAVE_AS =       'posts/{date:%Y}/{date:%m}/{date:%d}/{slug}.html'
ARTICLE_LANG_URL =      'posts/{date:%Y}/{date:%m}/{date:%d}/{slug}-{lang}.html'
ARTICLE_LANG_SAVE_AS =  'posts/{date:%Y}/{date:%m}/{date:%d}/{slug}-{lang}.html'

DEFAULT_PAGINATION = 10

RELATIVE_URLS=True
