from django.conf import settings
from django_hosts import patterns, host

host_patterns = patterns('',
    host(r'admin', 'django_vpn_demo.admin_urls', name='admin'),
    host(r'(\w+)', settings.ROOT_URLCONF, name='public'),
)