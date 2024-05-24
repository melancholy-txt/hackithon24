import paho.mqtt.client as mqtt
import ssl
import os
from dotenv import load_dotenv
from apscheduler.schedulers.background import BackgroundScheduler

load_dotenv()

messages = 0
troughput = 0

messages_per_minute = 0
troughput_per_minute = 0


def every_second():
    global messages, troughput, messages_per_minute, troughput_per_minute
    print(f"Zprav za sekundu: {messages}, Datovy tok: {troughput} B/s")
    messages_per_minute += messages
    troughput_per_minute += troughput
    messages = 0
    troughput = 0


def every_minute():
    global messages_per_minute, troughput_per_minute
    print()
    print(f"Zprav za minutu: {messages_per_minute}, Datovy tok: {
          int(troughput_per_minute / 1024)} kB,")
    print()
    messages_per_minute = 0
    troughput_per_minute = 0


scheduler = BackgroundScheduler()
scheduler.add_job(every_second, 'interval', seconds=1)
scheduler.add_job(every_minute, 'interval', minutes=1)
scheduler.start()


broker_address = "mqtt.portabo.cz"
port = 8883
mqtt_user = os.getenv("mqtt_user")
mqtt_password = os.getenv("mqtt_password")


def on_connect(client, userdata, flags, rc):
    print(f"Connected with result code {rc}")
    client.subscribe("#")


def on_message(client, userdata, msg):
    global messages, troughput
    messages += 1
    troughput += len(msg.payload)

    # print(f"Message received: Topic: {msg.topic}")


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
