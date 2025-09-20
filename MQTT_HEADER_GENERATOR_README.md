# MQTT Header Generator for Python

This Python module provides functionality to generate MQTT packet headers that are compatible with the MQTT.js library. It generates the headers that appear before JSON objects in MQTT payloads, as specified in the MQTT protocol.

## Overview

MQTT (Message Queuing Telemetry Transport) is a lightweight messaging protocol for IoT devices. Each MQTT message consists of:

1. **Fixed Header** - Contains the message type, flags, and remaining length
2. **Variable Header** - Contains fields like topic name and message ID
3. **Payload** - The actual message content (e.g., JSON data)

This module generates the fixed and variable headers that precede JSON payloads.

## Features

- ✅ MQTT 3.1.1 and 5.0 protocol compatibility
- ✅ Support for all QoS levels (0, 1, 2)
- ✅ RETAIN and DUP flag support
- ✅ Variable-length integer encoding
- ✅ JSON payload handling
- ✅ Message ID support for QoS > 0
- ✅ Unicode topic support
- ✅ Comprehensive error handling

## Installation

Simply copy the `mqtt_header_generator.py` file to your project directory.

## Quick Start

```python
from mqtt_header_generator import generate_mqtt_header
import json

# Create a JSON payload
payload = {
    "temperature": 25.5,
    "humidity": 60,
    "timestamp": "2024-01-15T10:30:00Z"
}

# Generate the MQTT header
header = generate_mqtt_header(
    topic="sensor/room1",
    json_payload=payload,
    qos=1,
    message_id=42
)

# Create complete MQTT message
json_bytes = json.dumps(payload).encode('utf-8')
complete_message = header + json_bytes

print(f"Header: {header.hex()}")
print(f"Complete message: {complete_message.hex()}")
```

## API Reference

### `generate_mqtt_header(topic, json_payload, qos=0, retain=False, message_id=None)`

Main convenience function to generate MQTT headers for JSON payloads.

**Parameters:**
- `topic` (str): MQTT topic string
- `json_payload` (dict): JSON object as dictionary
- `qos` (int): Quality of Service level (0, 1, or 2)
- `retain` (bool): Retain flag
- `message_id` (int, optional): Message ID for QoS > 0

**Returns:**
- `bytes`: MQTT header bytes

### `MQTTHeaderGenerator` Class

Advanced usage with the main class:

```python
from mqtt_header_generator import MQTTHeaderGenerator

generator = MQTTHeaderGenerator()

# Generate fixed header only
header = generator.generate_fixed_header(
    command='publish',
    qos=1,
    dup=False,
    retain=True,
    remaining_length=50
)

# Generate complete publish header
header = generator.generate_publish_header(
    topic="sensor/data",
    payload={"value": 123},
    qos=1,
    message_id=1001
)
```

## Examples

### Basic Usage

```python
# QoS 0 (Fire and forget)
header = generate_mqtt_header("sensor/temp", {"value": 23.5})

# QoS 1 (At least once delivery)
header = generate_mqtt_header(
    topic="alerts/fire", 
    json_payload={"level": "critical"}, 
    qos=1, 
    message_id=1001
)

# QoS 2 with retain (Exactly once delivery, retained)
header = generate_mqtt_header(
    topic="config/device", 
    json_payload={"enabled": True}, 
    qos=2, 
    retain=True, 
    message_id=2002
)
```

### Working with Complete Messages

```python
import json
from mqtt_header_generator import generate_mqtt_header

# Prepare data
topic = "sensor/temperature"
data = {"value": 25.5, "unit": "celsius"}

# Generate header
header = generate_mqtt_header(topic, data, qos=0)

# Create complete MQTT packet
json_str = json.dumps(data, separators=(',', ':'))
json_bytes = json_str.encode('utf-8')
mqtt_packet = header + json_bytes

# The packet is ready to be sent over the network
print(f"Complete MQTT packet: {mqtt_packet.hex()}")
```

### Advanced Usage

```python
from mqtt_header_generator import MQTTHeaderGenerator

generator = MQTTHeaderGenerator()

# Handle different payload types
generator.generate_publish_header("topic1", "string payload")
generator.generate_publish_header("topic2", b"binary payload")
generator.generate_publish_header("topic3", {"json": "payload"})

# Variable length encoding
length_bytes = generator.encode_remaining_length(268435455)  # Max length

# Custom fixed headers
header = generator.generate_fixed_header(
    command='subscribe',
    qos=1,
    remaining_length=100
)
```

## MQTT Header Structure

The generated headers follow the MQTT protocol specification:

```
Byte 1: Fixed Header
├── Bits 7-4: Message Type (PUBLISH = 3)
├── Bit 3: DUP flag
├── Bits 2-1: QoS level
└── Bit 0: RETAIN flag

Bytes 2-5: Remaining Length (Variable Length Integer)

Variable Header:
├── Topic Length (2 bytes, big-endian)
├── Topic String (UTF-8)
└── Message ID (2 bytes, for QoS > 0)
```

## Testing

Run the included tests:

```bash
python3 test_mqtt_header_generator.py
```

Run the demonstration:

```bash
python3 demo_mqtt_headers.py
```

## Error Handling

The module includes comprehensive error handling:

```python
# Invalid QoS level
try:
    generate_mqtt_header("topic", {}, qos=3)
except ValueError as e:
    print(f"Error: {e}")  # Invalid QoS level: 3

# Missing message ID for QoS > 0
try:
    generate_mqtt_header("topic", {}, qos=1)
except ValueError as e:
    print(f"Error: {e}")  # Message ID required for QoS > 0

# Empty topic
try:
    generate_mqtt_header("", {})
except ValueError as e:
    print(f"Error: {e}")  # Topic cannot be empty
```

## Compatibility

This implementation is designed to be compatible with:

- MQTT.js library
- MQTT 3.1.1 protocol
- MQTT 5.0 protocol
- Standard MQTT brokers (Mosquitto, HiveMQ, etc.)

## Use Cases

1. **IoT Data Collection**: Generate headers for sensor data transmission
2. **MQTT Proxy/Gateway**: Process and forward MQTT messages
3. **Protocol Testing**: Create test MQTT packets
4. **Custom MQTT Clients**: Build specialized MQTT client applications
5. **Message Analysis**: Parse and understand MQTT packet structure

## Contributing

Feel free to submit issues and enhancement requests!

## License

This code is provided as-is for educational and practical use in the MQTT.js project context.