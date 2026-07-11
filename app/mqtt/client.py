import json
import threading
import paho.mqtt.client as mqtt

from app.core.config import settings
from app.mqtt.handlers import handle_message

client = mqtt.Client()


def on_connect(client, userdata, flags, rc):

    print("MQTT Connected:", rc)

    client.subscribe("silasez/device/+/status")
    client.subscribe("silasez/device/+/sensor")


def on_message(client, userdata, msg):

    payload = json.loads(msg.payload.decode())

    handle_message(
        msg.topic,
        payload,
    )


client.on_connect = on_connect
client.on_message = on_message


def start():

    client.username_pw_set(
        settings.MQTT_USERNAME,
        settings.MQTT_PASSWORD,
    )

    client.connect(
        settings.MQTT_HOST,
        settings.MQTT_PORT,
    )

    threading.Thread(
        target=client.loop_forever,
        daemon=True,
    ).start()