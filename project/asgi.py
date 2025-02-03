#  import os
#  from django.core.asgi import get_asgi_application
#  from channels.routing import ProtocolTypeRouter, URLRouter
#  from channels.auth import AuthMiddlewareStack
#  import prof.routing  # Replace `your_app` with the name of your app containing `routing.py`
#
#  os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'project.settings')
#
#  # Django's ASGI application for HTTP
#  django_asgi_app = get_asgi_application()
#
#  # ProtocolTypeRouter to handle HTTP and WebSocket connections
#  application = ProtocolTypeRouter({
#      "http": django_asgi_app,  # Handles HTTP requests
#      "websocket": AuthMiddlewareStack(
#          URLRouter(
#              prof.routing.websocket_urlpatterns  # WebSocket routing
#          )
#      ),
#  })


import os
from django.core.asgi import get_asgi_application
from channels.routing import ProtocolTypeRouter

os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'project.settings')

application = ProtocolTypeRouter({
    "http": get_asgi_application(),
    # No WebSocket configuration needed for long polling
})