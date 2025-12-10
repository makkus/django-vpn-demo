from django.conf import settings
from django_hosts import patterns, host

from polls import admin

host_patterns = patterns('',
    host(r'admin', admin.admin.site.urls, name='admin'),
    host(r'(\w+)', settings.ROOT_URLCONF, name='public'),
)