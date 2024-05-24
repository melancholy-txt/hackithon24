import paho.mqtt.client as mqtt
import ssl
import os
from dotenv import load_dotenv

load_dotenv()


broker_address = "mqtt.portabo.cz"
port = 8883
mqtt_user = os.getenv("mqtt_user")
mqtt_password = os.getenv("mqtt_password")


def on_connect(client, userdata, flags, rc):
    print(f"Connected with result code {rc}")
    client.subscribe("#")


def on_message(client, userdata, msg):
    print(f"Message received: Topic: {msg.topic}")


client = mqtt.Client()
client.username_pw_set(mqtt_user, mqtt_password)
client.on_connect = on_connect
client.on_message = on_message

ssl_ctx = ssl.create_default_context()
ssl_ctx.check_hostname = False
ssl_ctx.verify_mode = ssl.CERT_NONE
client.tls_set_context(ssl_ctx)
client.tls_insecure_set(True)


client.connect(broker_address, port, 60)

client.loop_forever()
