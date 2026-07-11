import json

from app.mqtt.client import client


def publish_command(
    device_id: str,
    command: str,
    value,
):

    topic = f"silasez/device/{device_id}/command"

    client.publish(
        topic,
        json.dumps(
            {
                "command": command,
                "value": value,
            }
        ),
    )