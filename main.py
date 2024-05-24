import os
import ssl
import paho.mqtt.client as mqtt
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker
from sqlalchemy.ext.declarative import declarative_base
from dotenv import load_dotenv
from sqlalchemy import Column, Integer, TIMESTAMP, String
from datetime import datetime

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

DATABASE_URL = f"""mysql+pymysql://{maria_user}:{
    maria_password}@{db_host}:{db_port}/h24"""

engine = create_engine(DATABASE_URL)
SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)

Base.metadata.create_all(bind=engine)


def on_connect(client, userdata, flags, rc):
    print(f"Connected with result code {rc}")
    client.subscribe("#")


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
client.loop_forever()
