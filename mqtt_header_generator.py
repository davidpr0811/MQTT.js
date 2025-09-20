#!/usr/bin/env python3
"""
MQTT Header Generator

This module provides a Python function to generate MQTT packet headers
that are compatible with the MQTT.js library. The headers are generated
before JSON payload objects and contain the necessary MQTT control information.

Based on the MQTT 3.1.1 and MQTT 5.0 protocol specifications.
"""

import struct
from typing import Optional, Dict, Any, Union


class MQTTHeaderGenerator:
    """
    MQTT Header Generator class that provides functionality to generate
    MQTT packet headers similar to the mqtt-packet JavaScript library.
    """
    
    # MQTT Command Types (from constants.js)
    COMMAND_TYPES = {
        'reserved': 0,
        'connect': 1,
        'connack': 2,
        'publish': 3,
        'puback': 4,
        'pubrec': 5,
        'pubrel': 6,
        'pubcomp': 7,
        'subscribe': 8,
        'suback': 9,
        'unsubscribe': 10,
        'unsuback': 11,
        'pingreq': 12,
        'pingresp': 13,
        'disconnect': 14,
        'auth': 15
    }
    
    # Protocol constants
    CMD_SHIFT = 4
    DUP_MASK = 0x08
    QOS_SHIFT = 1
    RETAIN_MASK = 0x01
    
    def __init__(self):
        """Initialize the MQTT Header Generator."""
        pass
    
    def encode_remaining_length(self, length: int) -> bytes:
        """
        Encode the remaining length field as a Variable Byte Integer.
        
        Args:
            length: The remaining length of the packet
            
        Returns:
            bytes: The encoded variable byte integer
            
        Raises:
            ValueError: If length exceeds maximum allowed value (268,435,455)
        """
        if length > 268435455:  # 0xFF, 0xFF, 0xFF, 0x7F
            raise ValueError("Remaining length exceeds maximum allowed value")
        
        encoded = bytearray()
        while True:
            byte = length % 128
            length = length // 128
            if length > 0:
                byte = byte | 0x80
            encoded.append(byte)
            if length == 0:
                break
        
        return bytes(encoded)
    
    def generate_fixed_header(self, 
                            command: str, 
                            qos: int = 0, 
                            dup: bool = False, 
                            retain: bool = False,
                            remaining_length: int = 0) -> bytes:
        """
        Generate MQTT fixed header bytes.
        
        Args:
            command: MQTT command type ('publish', 'subscribe', etc.)
            qos: Quality of Service level (0, 1, or 2)
            dup: Duplicate flag
            retain: Retain flag
            remaining_length: Length of the remaining packet
            
        Returns:
            bytes: The complete fixed header
            
        Raises:
            ValueError: If command is invalid or parameters are out of range
        """
        if command not in self.COMMAND_TYPES:
            raise ValueError(f"Invalid command type: {command}")
        
        if qos not in [0, 1, 2]:
            raise ValueError(f"Invalid QoS level: {qos}")
        
        # Build the first byte of the fixed header
        first_byte = 0
        first_byte |= self.COMMAND_TYPES[command] << self.CMD_SHIFT
        
        if dup:
            first_byte |= self.DUP_MASK
            
        first_byte |= qos << self.QOS_SHIFT
        
        if retain:
            first_byte |= self.RETAIN_MASK
        
        # Combine first byte with remaining length
        header = bytes([first_byte])
        header += self.encode_remaining_length(remaining_length)
        
        return header
    
    def generate_publish_header(self, 
                              topic: str,
                              payload: Union[str, bytes, dict] = "",
                              qos: int = 0,
                              dup: bool = False,
                              retain: bool = False,
                              message_id: Optional[int] = None) -> bytes:
        """
        Generate a complete MQTT PUBLISH packet header for a given topic and payload.
        
        Args:
            topic: MQTT topic string
            payload: Payload data (string, bytes, or dict for JSON)
            qos: Quality of Service level (0, 1, or 2)
            dup: Duplicate flag
            retain: Retain flag
            message_id: Message ID for QoS > 0
            
        Returns:
            bytes: Complete PUBLISH packet header
            
        Raises:
            ValueError: If parameters are invalid
        """
        if not topic:
            raise ValueError("Topic cannot be empty")
        
        if qos > 0 and message_id is None:
            raise ValueError("Message ID required for QoS > 0")
        
        # Calculate remaining length
        remaining_length = 0
        
        # Topic length (2 bytes) + topic
        topic_bytes = topic.encode('utf-8')
        remaining_length += 2 + len(topic_bytes)
        
        # Message ID for QoS > 0 (2 bytes)
        if qos > 0:
            remaining_length += 2
        
        # Payload length
        if isinstance(payload, dict):
            import json
            payload_bytes = json.dumps(payload).encode('utf-8')
        elif isinstance(payload, str):
            payload_bytes = payload.encode('utf-8')
        elif isinstance(payload, bytes):
            payload_bytes = payload
        else:
            payload_bytes = str(payload).encode('utf-8')
        
        remaining_length += len(payload_bytes)
        
        # Generate fixed header
        fixed_header = self.generate_fixed_header('publish', qos, dup, retain, remaining_length)
        
        # Generate variable header
        variable_header = bytearray()
        
        # Topic length and topic
        variable_header.extend(struct.pack('>H', len(topic_bytes)))
        variable_header.extend(topic_bytes)
        
        # Message ID for QoS > 0
        if qos > 0 and message_id is not None:
            variable_header.extend(struct.pack('>H', message_id))
        
        return fixed_header + bytes(variable_header)
    
    def generate_header_for_json_payload(self,
                                       topic: str,
                                       json_payload: dict,
                                       qos: int = 0,
                                       retain: bool = False,
                                       message_id: Optional[int] = None) -> bytes:
        """
        Generate MQTT header specifically for JSON payloads.
        This is the main function requested by the user.
        
        Args:
            topic: MQTT topic string
            json_payload: JSON object as dictionary
            qos: Quality of Service level (0, 1, or 2)
            retain: Retain flag
            message_id: Message ID for QoS > 0
            
        Returns:
            bytes: MQTT header that comes before the JSON object
            
        Example:
            >>> generator = MQTTHeaderGenerator()
            >>> header = generator.generate_header_for_json_payload(
            ...     topic="sensor/data",
            ...     json_payload={"temperature": 25.5, "humidity": 60}
            ... )
            >>> print(header.hex())
        """
        return self.generate_publish_header(
            topic=topic,
            payload=json_payload,
            qos=qos,
            dup=False,
            retain=retain,
            message_id=message_id
        )


def generate_mqtt_header(topic: str, 
                        json_payload: dict, 
                        qos: int = 0,
                        retain: bool = False,
                        message_id: Optional[int] = None) -> bytes:
    """
    Convenience function to generate MQTT headers for JSON payloads.
    
    This function generates the header that appears before JSON objects
    in MQTT payloads, as requested by the user.
    
    Args:
        topic: MQTT topic string
        json_payload: JSON object as dictionary
        qos: Quality of Service level (0, 1, or 2)
        retain: Retain flag
        message_id: Message ID for QoS > 0
        
    Returns:
        bytes: MQTT header bytes
        
    Example:
        >>> header = generate_mqtt_header(
        ...     topic="sensor/data",
        ...     json_payload={"temperature": 25.5, "humidity": 60}
        ... )
        >>> print(f"Header: {header.hex()}")
        >>> 
        >>> # To create a complete MQTT message:
        >>> import json
        >>> complete_message = header + json.dumps(json_payload).encode('utf-8')
    """
    generator = MQTTHeaderGenerator()
    return generator.generate_header_for_json_payload(
        topic=topic,
        json_payload=json_payload,
        qos=qos,
        retain=retain,
        message_id=message_id
    )


if __name__ == "__main__":
    # Example usage
    import json
    
    # Create a sample JSON payload
    sample_payload = {
        "temperature": 25.5,
        "humidity": 60,
        "timestamp": "2024-01-15T10:30:00Z"
    }
    
    # Generate the header
    header = generate_mqtt_header(
        topic="sensor/room1",
        json_payload=sample_payload,
        qos=1,
        message_id=42
    )
    
    print(f"Generated MQTT header: {header.hex()}")
    print(f"Header length: {len(header)} bytes")
    
    # Show how to construct complete message
    json_bytes = json.dumps(sample_payload).encode('utf-8')
    complete_message = header + json_bytes
    
    print(f"Complete MQTT message: {complete_message.hex()}")
    print(f"Complete message length: {len(complete_message)} bytes")
    
    # Demonstrate different QoS levels
    print("\nDifferent QoS examples:")
    for qos_level in [0, 1, 2]:
        msg_id = 123 if qos_level > 0 else None
        hdr = generate_mqtt_header(
            topic="test/topic",
            json_payload={"qos": qos_level},
            qos=qos_level,
            message_id=msg_id
        )
        print(f"QoS {qos_level}: {hdr.hex()}")