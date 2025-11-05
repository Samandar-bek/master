import os
from django.core.wsgi import get_wsgi_application

os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'config.settings')

application = get_wsgi_application()
# This WSGI application serves as the entry point for WSGI-compatible web servers
# to serve your Django project. It sets up the necessary environment and loads