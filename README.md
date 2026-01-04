# Django VPN Demo

A demonstration Django project showcasing how to run Django with **split public/private architecture** using VPN-based access control. This demo uses [django-hosts](https://django-hosts.readthedocs.io/) to route different parts of your application to different subdomains, with the admin interface accessible only via a private network (Tailscale VPN).

## What This Demo Demonstrates

- **Public Interface**: A polling application accessible to anyone on the internet
- **Private Interface**: Django admin panel accessible only through a VPN (Tailscale)
- **Single Codebase**: Both interfaces run from the same Django application
- **Subdomain Routing**: Uses `django-hosts` to route requests based on subdomain
- **Production-Ready Setup**: Includes WhiteNoise for static files and Gunicorn for deployment

### Use Cases

This pattern is useful when you want to:
- Keep your admin panel completely off the public internet
- Provide secure access to internal tools without complex authentication
- Separate public-facing features from internal management interfaces
- Use VPN-based security instead of (or in addition to) password authentication

---

## Quick Start (Local Development)

### Prerequisites

- Python 3.13+
- [uv](https://github.com/astral-sh/uv) (recommended) or pip

### 1. Clone and Install

```bash
git clone https://github.com/makkus/django-vpn-demo.git
cd django-vpn-demo

# Install dependencies
uv sync
# Or with pip:
# pip install -r requirements.txt
```

### 2. Run Database Migrations

```bash
uv run python manage.py migrate
```

### 3. Create a Superuser (Optional)

```bash
uv run python manage.py createsuperuser
```

Or use the demo credentials:
- **Username:** `admin`
- **Password:** `password123`

### 4. Start the Development Server

```bash
uv run python manage.py runserver 0.0.0.0:8000
```

### 5. Access the Application

Since `django-hosts` routes by subdomain, you need to access the app using subdomains:

**Public Interface:**
- http://django-vpn.demos.local:8000/
- View and vote on polls

**Private Admin Interface:**
- http://admin.django-vpn.demos.local:8000/
- Manage polls and choices (login with admin credentials)

#### Setting Up Local DNS

Add these entries to your `/etc/hosts` file (or `C:\Windows\System32\drivers\etc\hosts` on Windows):

```
127.0.0.1  django-vpn.demos.local
127.0.0.1  admin.django-vpn.demos.local
```

---

## Production Deployment

This section covers deploying the demo to a production environment with Tailscale VPN protection for the admin interface.

### Prerequisites

- A server with a public IP address
- A domain name you control
- [Tailscale](https://tailscale.com/) account
- DNS provider with API access (e.g., Cloudflare)
- Reverse proxy (Caddy or Traefik recommended)

### Step 1: DNS Configuration

Create two DNS A records pointing to different IP addresses:

| Record | Points To | Purpose |
|--------|-----------|---------|
| `django-vpn.yourdomain.com` | Public IP address | Public polling interface |
| `admin.django-vpn.yourdomain.com` | Tailscale IP (e.g., 100.x.x.x) | Private admin interface |

**Example with Cloudflare:**
1. Log in to Cloudflare dashboard
2. Select your domain
3. Go to DNS → Records
4. Add two A records as shown above
5. Disable Cloudflare proxy (orange cloud) if using Let's Encrypt DNS challenge

### Step 2: Tailscale Setup

1. **Create Tailscale Account**: Sign up at [tailscale.com](https://tailscale.com/)

2. **Install Tailscale on Your Client** (laptop/desktop):
   ```bash
   # macOS
   brew install tailscale

   # Linux
   curl -fsSL https://tailscale.com/install.sh | sh

   # Windows: Download from tailscale.com
   ```

3. **Connect Your Client**:
   ```bash
   sudo tailscale up
   ```

4. **Install Tailscale on Your Server**:
   ```bash
   # On your production server
   curl -fsSL https://tailscale.com/install.sh | sh
   sudo tailscale up
   ```

5. **Note Your Server's Tailscale IP**:
   ```bash
   tailscale ip -4
   # Example output: 100.101.102.103
   ```

   Update your DNS record for `admin.django-vpn.yourdomain.com` to point to this IP.

### Step 3: Reverse Proxy Configuration

You need a reverse proxy to:
- Handle HTTPS certificates (Let's Encrypt)
- Route traffic to your Django application
- Support DNS challenge for Let's Encrypt (since admin subdomain isn't publicly accessible)

#### Option A: Caddy (Recommended)

**Caddyfile example:**

```caddy
# Public subdomain
django-vpn.yourdomain.com {
    reverse_proxy localhost:8000

    tls {
        dns cloudflare {env.CLOUDFLARE_API_TOKEN}
    }
}

# Private subdomain (VPN only)
admin.django-vpn.yourdomain.com {
    reverse_proxy localhost:8000

    tls {
        dns cloudflare {env.CLOUDFLARE_API_TOKEN}
    }
}
```

#### Option B: Traefik

**traefik.yml example:**

```yaml
entryPoints:
  web:
    address: ":80"
  websecure:
    address: ":443"

certificatesResolvers:
  letsencrypt:
    acme:
      email: your-email@example.com
      storage: acme.json
      dnsChallenge:
        provider: cloudflare
        resolvers:
          - "1.1.1.1:53"
```

**Dynamic configuration:**

```yaml
http:
  routers:
    public:
      rule: "Host(`django-vpn.yourdomain.com`)"
      service: django
      tls:
        certResolver: letsencrypt

    admin:
      rule: "Host(`admin.django-vpn.yourdomain.com`)"
      service: django
      tls:
        certResolver: letsencrypt

  services:
    django:
      loadBalancer:
        servers:
          - url: "http://localhost:8000"
```

### Step 4: Django Configuration

1. **Update `settings.py`** with your domains:

   ```python
   ALLOWED_HOSTS = [
       'django-vpn.yourdomain.com',
       'admin.django-vpn.yourdomain.com',
   ]

   CSRF_TRUSTED_ORIGINS = [
       'https://django-vpn.yourdomain.com',
       'https://admin.django-vpn.yourdomain.com',
   ]

   # IMPORTANT: Set DEBUG to False in production!
   DEBUG = False

   # Generate a secure secret key
   SECRET_KEY = 'your-secure-secret-key-here'
   ```

2. **Collect Static Files**:
   ```bash
   python manage.py collectstatic --noinput
   ```

3. **Run Migrations**:
   ```bash
   python manage.py migrate
   ```

4. **Create Superuser**:
   ```bash
   python manage.py createsuperuser
   ```

### Step 5: Run with Gunicorn

```bash
gunicorn django_vpn_demo.wsgi:application --bind 0.0.0.0:8000 --workers 4
```

Or use the deployment command from `nixpacks.toml`:
```bash
python manage.py collectstatic --noinput && \
python manage.py migrate && \
gunicorn django_vpn_demo.wsgi:application --bind 0.0.0.0:8000
```

### Step 6: Create a Systemd Service (Optional)

Create `/etc/systemd/system/django-vpn-demo.service`:

```ini
[Unit]
Description=Django VPN Demo
After=network.target

[Service]
Type=notify
User=www-data
WorkingDirectory=/path/to/django-vpn-demo
Environment="PATH=/path/to/django-vpn-demo/.venv/bin"
ExecStart=/path/to/django-vpn-demo/.venv/bin/gunicorn \
    django_vpn_demo.wsgi:application \
    --bind 0.0.0.0:8000 \
    --workers 4

[Install]
WantedBy=multi-user.target
```

Enable and start:
```bash
sudo systemctl enable django-vpn-demo
sudo systemctl start django-vpn-demo
```

---

## Architecture Overview

### How It Works

This demo uses **django-hosts** to route requests to different URL configurations based on the subdomain:

```
┌─────────────────────────────────────────────────────────┐
│                     Internet Traffic                     │
└─────────────────────────────────────────────────────────┘
                          │
                          ▼
         ┌────────────────────────────────┐
         │      Reverse Proxy (Caddy)     │
         │     (Let's Encrypt SSL/TLS)    │
         └────────────────────────────────┘
                          │
              ┌───────────┴───────────┐
              │                       │
              ▼                       ▼
    Public IP: x.x.x.x      Tailscale IP: 100.x.x.x
    (django-vpn.domain)     (admin.django-vpn.domain)
              │                       │
              └───────────┬───────────┘
                          │
                          ▼
              ┌───────────────────────┐
              │  Django Application   │
              │   (django-hosts)      │
              └───────────────────────┘
                          │
              ┌───────────┴───────────┐
              │                       │
              ▼                       ▼
    ┌──────────────┐        ┌──────────────┐
    │ Public URLs  │        │ Admin URLs   │
    │ (polls app)  │        │ (admin panel)│
    └──────────────┘        └──────────────┘
```

### Key Files

- **`django_vpn_demo/hosts.py`**: Defines subdomain-to-URL routing
- **`django_vpn_demo/urls.py`**: Public interface URLs (polls)
- **`django_vpn_demo/admin_urls.py`**: Private interface URLs (admin only)
- **`django_vpn_demo/settings.py`**: Django configuration with django-hosts middleware

### django-hosts Configuration

In `hosts.py`:

```python
from django_hosts import patterns, host

host_patterns = patterns('',
    host(r'admin', 'django_vpn_demo.admin_urls', name='admin'),
    host(r'(\w+)', settings.ROOT_URLCONF, name='public'),
)
```

- Requests to `admin.*` subdomain → `admin_urls.py` (admin interface)
- All other subdomains → `urls.py` (public polls application)

---

## Project Structure

```
django-vpn-demo/
├── django_vpn_demo/           # Main Django project
│   ├── settings.py            # Django settings
│   ├── hosts.py               # django-hosts subdomain routing
│   ├── urls.py                # Public URLs (polls)
│   ├── admin_urls.py          # Private URLs (admin)
│   ├── wsgi.py                # WSGI entry point
│   └── asgi.py                # ASGI entry point
├── polls/                     # Polls application
│   ├── models.py              # Question and Choice models
│   ├── views.py               # Voting and results views
│   ├── urls.py                # App URL patterns
│   ├── admin.py               # Admin registration
│   └── templates/polls/       # HTML templates
├── docs/                      # Documentation
│   └── presentation.md        # Presentation slides
├── manage.py                  # Django management script
├── pyproject.toml             # Python dependencies
├── justfile                   # Task automation
└── README.md                  # This file
```

---

## Development Commands

If you have [just](https://github.com/casey/just) installed:

```bash
just runserver          # Start development server
just migrate            # Run database migrations
just make-migrations    # Create new migrations
```

Otherwise, use Django's `manage.py`:

```bash
python manage.py runserver 0.0.0.0:8000
python manage.py migrate
python manage.py makemigrations
```

---

## Troubleshooting

### "Invalid HTTP_HOST header"

**Problem**: Django rejects requests with error about invalid HTTP_HOST.

**Solution**: Make sure your domain is in `ALLOWED_HOSTS` in `settings.py`:

```python
ALLOWED_HOSTS = [
    'your-public-domain.com',
    'admin.your-public-domain.com',
]
```

### Admin interface shows "CSRF verification failed"

**Problem**: Cross-site request forgery check fails.

**Solution**: Add both subdomains to `CSRF_TRUSTED_ORIGINS`:

```python
CSRF_TRUSTED_ORIGINS = [
    'https://your-domain.com',
    'https://admin.your-domain.com',
]
```

### Can't access admin subdomain locally

**Problem**: Browser can't resolve `admin.django-vpn.demos.local`.

**Solution**: Add entry to `/etc/hosts`:

```
127.0.0.1  admin.django-vpn.demos.local
```

### Static files not loading in production

**Problem**: CSS/images return 404 errors.

**Solution**: Run `collectstatic` before starting Gunicorn:

```bash
python manage.py collectstatic --noinput
```

WhiteNoise is configured to serve these files automatically.

### Let's Encrypt certificate fails for admin subdomain

**Problem**: Can't get SSL certificate for subdomain pointing to private IP.

**Solution**: Use DNS challenge instead of HTTP challenge. Configure your reverse proxy with DNS provider credentials (e.g., Cloudflare API token).

### Tailscale connection issues

**Problem**: Can't access admin interface through Tailscale IP.

**Solution**:
1. Verify Tailscale is running: `tailscale status`
2. Check server's Tailscale IP: `tailscale ip -4`
3. Ensure DNS record points to this IP
4. Try accessing by IP directly: `https://100.x.x.x:443`

---

## Security Considerations

### For Production Use

⚠️ **This is a demo project. Before using this pattern in production:**

1. **Change SECRET_KEY**: Generate a new secret key
   ```bash
   python -c 'from django.core.management.utils import get_random_secret_key; print(get_random_secret_key())'
   ```

2. **Set DEBUG = False**: Never run with DEBUG enabled in production

3. **Use Environment Variables**: Don't hardcode secrets in settings.py
   ```python
   import os
   SECRET_KEY = os.environ.get('DJANGO_SECRET_KEY')
   DEBUG = os.environ.get('DEBUG', 'False') == 'True'
   ```

4. **Database**: Switch from SQLite to PostgreSQL or MySQL for production

5. **Firewall Rules**: Ensure your server firewall blocks direct access to port 8000

6. **Rate Limiting**: Add rate limiting to prevent abuse

7. **Monitoring**: Set up logging and monitoring for suspicious access

---

## Additional Resources

- [django-hosts documentation](https://django-hosts.readthedocs.io/)
- [Tailscale documentation](https://tailscale.com/kb/)
- [Let's Encrypt DNS Challenge](https://letsencrypt.org/docs/challenge-types/#dns-01-challenge)
- [WhiteNoise documentation](http://whitenoise.evans.io/)
- [Gunicorn documentation](https://docs.gunicorn.org/)

---

## Demo Credentials

For testing purposes only:

- **Username:** `admin`
- **Password:** `password123`

**Change these before deploying to production!**

---

## License

This is a demonstration project. Use and modify as needed for your own projects.

---

## Contributing

This is a demo project, but if you find issues or have suggestions:

1. Fork the repository
2. Create a feature branch
3. Submit a pull request

For questions or discussions, open an issue on GitHub.
