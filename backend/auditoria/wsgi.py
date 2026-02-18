"""
WSGI config for Auditoría Web.
"""
import os
from django.core.wsgi import get_wsgi_application

os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'auditoria.settings')
application = get_wsgi_application()
