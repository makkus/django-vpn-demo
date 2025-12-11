# Django VPN Demo

This repository contains a demo Django project to show how to use Django partially behind a VPN.

## Demo credentials

- **Username:** `admin`
- **Password:** `password123`


## Steps

### DNS
- create API token from your DNS provider (e.g. Cloudflare)
- set up DNS records for your domain:
  - `[PRIVATE_SUBDOMAIN].<your-domain>` -> private VPN IP address (e.g. Tailscale IP)
  - `[PUBLIC_SUBDOMAIN].<your-domain>` -> public IP address

### Reverse Proxy

- configure reverse proxy to use Let's Encrypt certificates, using the DNS challenge

### Tailscale
- create a Tailscale account
- install Tailscale on your machine
- add your machine to tailscale
- add the server hosting your app to your tailscale network (tailnet)

### Django
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
    
```python
from django.conf import settings
from django_hosts import patterns, host

host_patterns = patterns('',
    host(r'admin', admin.site.urls, name='admin'),
    host(r'(\w+)', settings.ROOT_URLCONF, name='public'),
)
```
