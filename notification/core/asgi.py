import os
import django
import socketio
from django.core.asgi import get_asgi_application
from notifications.sio import sio

os.environ.setdefault("DJANGO_SETTINGS_MODULE", "core.settings")
django.setup()

django_asgi_app = get_asgi_application()

# Combine Django + Socket.IO
application = socketio.ASGIApp(sio, django_asgi_app)

