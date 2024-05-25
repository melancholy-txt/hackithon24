import json
import asyncio
import websockets
import paho.mqtt.client as mqtt
import os
import ssl
from dotenv import load_dotenv
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker
from sqlalchemy.ext.declarative import declarative_base
from dotenv import load_dotenv
from sqlalchemy import Column, Integer, TIMESTAMP, String
from datetime import datetime


# Global list of connected WebSocket clients
websocket_clients = []

Base = declarative_base()
load_dotenv()


class Message(Base):
    __tablename__ = "messages"

    id = Column(Integer, primary_key=True, index=True, autoincrement=True)
    date = Column(TIMESTAMP, default=datetime.utcnow)
    size = Column(Integer)
    topic = Column(String(255))


# Database connection setup
maria_user = os.getenv("maria_user")
maria_password = os.getenv("maria_password")
db_host = os.getenv("db_host")
db_port = os.getenv("db_port")
database = os.getenv("database")

DATABASE_URL = f"""mysql+pymysql://{maria_user}:{
    maria_password}@{db_host}:{db_port}/{database}"""

engine = create_engine(DATABASE_URL)
SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)

Base.metadata.create_all(bind=engine)


def on_connect(client, userdata, flags, rc):
    print(f"Connected with result code {rc}")
    client.subscribe("/ttndata/#")


def on_message(client, userdata, msg):
    session = SessionLocal()
    try:
        # Create a new message instance
        message = Message(
            date=datetime.utcnow(),
            size=len(msg.payload),
            topic=msg.topic
        )
        session.add(message)
        session.commit()
        # print(f"Message added to DB: {message}")
    except Exception as e:
        session.rollback()
        print(f"Failed to add message to DB: {e}")
    finally:
        session.close()

    msg.payload = msg.payload.decode()
    coordinates = extract_gateway_coordinates(msg.payload)
    asyncio.run(send_to_websockets(str(coordinates)))


async def send_to_websockets(message):
    if websocket_clients:
        # Create tasks from coroutines before waiting on them
        tasks = [asyncio.create_task(client.send(message))
                 for client in websocket_clients]
        await asyncio.wait(tasks)

# WebSocket handling


def extract_gateway_coordinates(json_message):
    try:
        data = json.loads(json_message)

        # Extracting gateway IDs and their corresponding coordinates
        gateway_coordinates = {}
        for gateway in data.get('uplink_message', {}).get('rx_metadata', []):
            gateway_id = gateway.get('gateway_ids', {}).get('gateway_id')
            location = gateway.get('location', {})
            if gateway_id and location:
                gateway_coordinates[gateway_id] = {
                    "latitude": location['latitude'],
                    "longitude": location['longitude']
                }
            elif gateway_id == "lora-m013":
                gateway_coordinates[gateway_id] = {
                    "latitude": "50.67299221831517",
                    "longitude": "14.048330412098741",
                    "location": "spsul"
                }
            elif gateway_id:
                gateway_coordinates[gateway_id] = {}
            elif location:
                gateway_coordinates["unknown"] = {
                    "latitude": location['latitude'],
                    "longitude": location['longitude']
                }

        return gateway_coordinates
    except json.JSONDecodeError:
        print("Invalid JSON format")
        return {"error": "Invalid JSON format"}


async def websocket_handler(websocket, path):
    websocket_clients.append(websocket)
    try:
        async for message in websocket:
            pass  # WebSocket clients are not expected to send messages
    except websockets.ConnectionClosed:
        pass
    finally:
        websocket_clients.remove(websocket)


async def main():
    server = await websockets.serve(websocket_handler, '0.0.0.0', 8765)
    print("WebSocket server started at ws://0.0.0.0:8765")
    await server.wait_closed()

# Starting MQTT client


def start_mqtt_client():
    broker_address = "mqtt.portabo.cz"
    port = 8883
    mqtt_user = os.getenv("mqtt_user")
    mqtt_password = os.getenv("mqtt_password")
    print(mqtt_user, mqtt_password)

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
    client.loop_start()


if __name__ == "__main__":
    start_mqtt_client()
    asyncio.run(main())
