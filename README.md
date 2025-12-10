# Django VPN Demo

This repository contains a demo Django project to show how to use Django partially behind a VPN.

## Demo credentials

- **Username:** `admin`
- **Password:** `password123`


## Steps

- add [django-hosts](https://django-hosts.readthedocs.io/en/latest/) to project dependencies:
  - `uv add django-hosts`
- configure `django-hosts`:
  - add `django_hosts` to `INSTALLED_APPS`
  - add `django_hosts.middleware.HostsRequestMiddleware` to `MIDDLEWARE` (beginning)
  - add `django_hosts.middleware.HostsResponseMiddleware` to `MIDDLEWARE` (end)
  - create `hosts.py` file (next to root `urls.py`)
  - set `ROOT_HOSTCONF` to 'django-vpn-demo.hosts'
  - set `DEFAULT_HOST` to 'public'
  - configure `hosts.py` to use `public` and `private` hosts:
    - ```python
from django.conf import settings
from django_hosts import patterns, host

host_patterns = patterns('',
    host(r'admin', admin.site.urls, name='admin'),
    host(r'(\w+)', settings.ROOT_URLCONF, name='public'),
)
```