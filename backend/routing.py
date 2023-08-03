from channels.routing import ProtocolTypeRouter, URLRouter
from django.urls import path,re_path
from student import consumers as student_consumers
from academy import consumers as academy_consumers

websocket_urlpatterns = [
    path("ws/student_path/", student_consumers.AttendanceConsumer.as_asgi()),
    path("ws/academy_path/", academy_consumers.NotificationConsumer.as_asgi()),
]

application = ProtocolTypeRouter({
    "websocket": URLRouter(websocket_urlpatterns),
})
