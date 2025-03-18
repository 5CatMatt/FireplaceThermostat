import paho.mqtt.client as mqtt
import random
import time

# MQTT Broker details
broker_address = "192.168.50.7"  # Replace with your broker's IP if not running locally
broker_port = 1883
topic = "test/topic"
temperature_topic = "Office Temperature"
humidity_topic = "Office Humidity"
battery_topic = "Office Battery"

# Callback when the client receives a CONNACK response from the server.
def on_connect(client, userdata, flags, rc):
    print(f"Connected with result code {rc}")
    # Subscribe to the topic
    client.subscribe(topic)
    client.subscribe(temperature_topic)
    client.subscribe(humidity_topic)
    client.subscribe(battery_topic)

# Callback when a PUBLISH message is received from the server.
def on_message(client, userdata, msg):
    # print(f"Received message: {msg.payload.decode()} on topic {msg.topic}")
    if msg.topic == temperature_topic:
        print(f"Received Temperature: {msg.payload.decode()} °F")
    elif msg.topic == humidity_topic:
        print(f"Received Humidity: {msg.payload.decode()} %")
    elif msg.topic == battery_topic:
        print(f"Received Battery: {msg.payload.decode()} Volts")

# Create an MQTT client instance
client = mqtt.Client()

# Assign the callbacks
client.on_connect = on_connect
client.on_message = on_message

# Connect to the broker
client.connect(broker_address, broker_port, 60)

# Start the loop to process network traffic and dispatch callbacks
client.loop_start()

try:
    while True:
        # # Generate a random number
        # random_number = random.randint(1, 100)
        
        # # Publish the random number to the topic
        # client.publish(topic, random_number)
        # print(f"Published: {random_number} to topic {topic}")
        
        # Wait for a second before publishing the next number
        time.sleep(1)

except KeyboardInterrupt:
    print("Script interrupted by user")

finally:
    # Stop the loop and disconnect
    client.loop_stop()
    client.disconnect()
    print("Disconnected from MQTT broker")