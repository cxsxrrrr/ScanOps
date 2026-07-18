"""Shared helpers for admin views (geolocation, IP resolution, etc.)."""
import socket
from urllib.parse import urlparse

import requests
from django.core.cache import cache


def get_server_public_ip():
    """Return the server's public IP, cached for 24h."""
    server_public_ip = cache.get('server_public_ip')
    if not server_public_ip:
        try:
            server_public_ip = requests.get('https://api.ipify.org', timeout=2).text
            cache.set('server_public_ip', server_public_ip, 86400)
        except Exception:
            server_public_ip = "8.8.8.8"
    return server_public_ip


def get_geo_info(ip, fallback_ip=None):
    """Resolve an IP to lat/lng/country/city using ip-api, with 7-day cache."""
    fallback_ip = fallback_ip or get_server_public_ip()
    if ip in ('127.0.0.1', 'localhost', '0.0.0.0', '::1'):
        ip = fallback_ip

    cache_key = f'geo_{ip.replace(":", "_")}'
    cached = cache.get(cache_key)
    if cached:
        return cached

    try:
        res = requests.get(
            f'http://ip-api.com/json/{ip}?fields=status,country,city,lat,lon',
            timeout=1.5,
        ).json()
        if res.get('status') == 'success':
            geo = {
                'lat': res['lat'],
                'lng': res['lon'],
                'country': res['country'],
                'city': res['city'],
            }
            cache.set(cache_key, geo, 86400 * 7)
            return geo
    except Exception:
        pass

    return {'lat': 0, 'lng': 0, 'country': 'Desconocido', 'city': 'Desconocido'}


def get_target_ip(url):
    """Resolve a URL's hostname to an IPv4 address."""
    try:
        hostname = urlparse(url).hostname
        return socket.gethostbyname(hostname)
    except Exception:
        return "1.1.1.1"
