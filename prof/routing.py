from django.urls import path
from .consumers import LongPollingConsumer

http_urlpatterns = [
    path("longpolling/", LongPollingConsumer.as_asgi()),
]
