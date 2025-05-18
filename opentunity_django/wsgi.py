"""
WSGI config for opentunity_django project.

It exposes the WSGI callable as a module-level variable named ``application``.

For more information on this file, see
https://docs.djangoproject.com/en/4.0/howto/deployment/wsgi/
"""

import sys
path = '/home/opentunity/opentunity_django'
if path not in sys.path:
    sys.path.append(path)

import os
os.environ['DJANGO_SETTINGS_MODULE'] = 'opentunity_django.settings'

from django.core.wsgi import get_wsgi_application
application = get_wsgi_application()
