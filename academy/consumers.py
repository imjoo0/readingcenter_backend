# academy/consumers.py
from channels.generic.websocket import WebsocketConsumer
from channels.layers import get_channel_layer
from asgiref.sync import async_to_sync
import json

class NotificationConsumer(WebsocketConsumer):
    def connect(self):
        self.group_name = "notifications"
        async_to_sync(self.channel_layer.group_add)(
            self.group_name,
            self.channel_name
        )
        self.accept()

    def disconnect(self, close_code):
        async_to_sync(self.channel_layer.group_discard)(
            self.group_name,
            self.channel_name
        )

    def receive(self, text_data):
        pass

    def send_notification(self, message):
        self.send(text_data=json.dumps(message))
