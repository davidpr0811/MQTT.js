#!/usr/bin/env python3
"""
Test file for MQTT Header Generator

This file contains tests to validate the MQTT header generation functionality
and compare it with the expected output from the mqtt-packet JavaScript library.
"""

import unittest
import json
from mqtt_header_generator import MQTTHeaderGenerator, generate_mqtt_header


class TestMQTTHeaderGenerator(unittest.TestCase):
    """Test cases for MQTT Header Generator."""
    
    def setUp(self):
        """Set up test fixtures."""
        self.generator = MQTTHeaderGenerator()
    
    def test_encode_remaining_length(self):
        """Test variable byte integer encoding."""
        # Test cases from MQTT specification
        test_cases = [
            (0, b'\x00'),
            (127, b'\x7f'),
            (128, b'\x80\x01'),
            (16383, b'\xff\x7f'),
            (16384, b'\x80\x80\x01'),
            (2097151, b'\xff\xff\x7f'),
            (2097152, b'\x80\x80\x80\x01'),
            (268435455, b'\xff\xff\xff\x7f'),
        ]
        
        for length, expected in test_cases:
            with self.subTest(length=length):
                result = self.generator.encode_remaining_length(length)
                self.assertEqual(result, expected)
    
    def test_encode_remaining_length_overflow(self):
        """Test that oversized lengths raise ValueError."""
        with self.assertRaises(ValueError):
            self.generator.encode_remaining_length(268435456)  # Max + 1
    
    def test_generate_fixed_header_publish(self):
        """Test fixed header generation for PUBLISH packets."""
        # PUBLISH, QoS 0, no DUP, no RETAIN
        header = self.generator.generate_fixed_header('publish', qos=0, dup=False, retain=False, remaining_length=10)
        expected_first_byte = 3 << 4  # PUBLISH command = 3
        self.assertEqual(header[0], expected_first_byte)
        self.assertEqual(header[1], 10)  # remaining length
    
    def test_generate_fixed_header_publish_with_flags(self):
        """Test fixed header with various flags set."""
        # PUBLISH, QoS 1, DUP=True, RETAIN=True
        header = self.generator.generate_fixed_header('publish', qos=1, dup=True, retain=True, remaining_length=5)
        expected_first_byte = (3 << 4) | 0x08 | (1 << 1) | 0x01  # Command | DUP | QoS | RETAIN
        self.assertEqual(header[0], expected_first_byte)
        self.assertEqual(header[1], 5)  # remaining length
    
    def test_invalid_command_type(self):
        """Test that invalid command types raise ValueError."""
        with self.assertRaises(ValueError):
            self.generator.generate_fixed_header('invalid_command')
    
    def test_invalid_qos(self):
        """Test that invalid QoS levels raise ValueError."""
        with self.assertRaises(ValueError):
            self.generator.generate_fixed_header('publish', qos=3)
    
    def test_generate_publish_header_qos0(self):
        """Test PUBLISH header generation for QoS 0."""
        topic = "test/topic"
        payload = "hello world"
        
        header = self.generator.generate_publish_header(
            topic=topic,
            payload=payload,
            qos=0
        )
        
        # Check that header starts with correct command byte
        self.assertEqual(header[0] & 0xF0, 3 << 4)  # PUBLISH command
        
        # Should contain topic length, topic, and be followed by payload
        topic_bytes = topic.encode('utf-8')
        expected_length = 2 + len(topic_bytes) + len(payload.encode('utf-8'))
        
        # Verify the variable header contains the topic
        topic_length_offset = len(self.generator.encode_remaining_length(expected_length)) + 1
        topic_length = int.from_bytes(header[topic_length_offset:topic_length_offset+2], 'big')
        self.assertEqual(topic_length, len(topic_bytes))
        
        topic_start = topic_length_offset + 2
        topic_in_header = header[topic_start:topic_start+len(topic_bytes)]
        self.assertEqual(topic_in_header, topic_bytes)
    
    def test_generate_publish_header_qos1_with_message_id(self):
        """Test PUBLISH header generation for QoS 1 with message ID."""
        topic = "sensor/data"
        payload = {"temperature": 25.5}
        message_id = 42
        
        header = self.generator.generate_publish_header(
            topic=topic,
            payload=payload,
            qos=1,
            message_id=message_id
        )
        
        # Check QoS bits in first byte
        self.assertEqual((header[0] >> 1) & 0x03, 1)  # QoS = 1
        
        # Should include message ID in variable header
        payload_bytes = json.dumps(payload).encode('utf-8')
        topic_bytes = topic.encode('utf-8')
        expected_length = 2 + len(topic_bytes) + 2 + len(payload_bytes)  # +2 for message ID
        
        self.assertTrue(len(header) >= 1 + len(self.generator.encode_remaining_length(expected_length)) + 2 + len(topic_bytes) + 2)
    
    def test_generate_publish_header_qos_without_message_id(self):
        """Test that QoS > 0 without message ID raises ValueError."""
        with self.assertRaises(ValueError):
            self.generator.generate_publish_header(
                topic="test",
                payload="test",
                qos=1
            )
    
    def test_empty_topic_raises_error(self):
        """Test that empty topic raises ValueError."""
        with self.assertRaises(ValueError):
            self.generator.generate_publish_header(topic="", payload="test")
    
    def test_generate_header_for_json_payload(self):
        """Test the main function for JSON payloads."""
        topic = "sensor/room1"
        json_payload = {
            "temperature": 25.5,
            "humidity": 60,
            "timestamp": "2024-01-15T10:30:00Z"
        }
        
        header = self.generator.generate_header_for_json_payload(
            topic=topic,
            json_payload=json_payload,
            qos=0
        )
        
        # Should be a valid MQTT header
        self.assertIsInstance(header, bytes)
        self.assertTrue(len(header) > 0)
        
        # First byte should indicate PUBLISH command
        self.assertEqual(header[0] & 0xF0, 3 << 4)
    
    def test_convenience_function(self):
        """Test the convenience function generate_mqtt_header."""
        topic = "test/data"
        json_payload = {"value": 123}
        
        header = generate_mqtt_header(topic, json_payload)
        
        self.assertIsInstance(header, bytes)
        self.assertTrue(len(header) > 0)
        self.assertEqual(header[0] & 0xF0, 3 << 4)  # PUBLISH command
    
    def test_different_payload_types(self):
        """Test header generation with different payload types."""
        topic = "test/topic"
        
        # Test with string payload
        header_str = self.generator.generate_publish_header(topic, "hello", qos=0)
        self.assertIsInstance(header_str, bytes)
        
        # Test with bytes payload
        header_bytes = self.generator.generate_publish_header(topic, b"hello", qos=0)
        self.assertIsInstance(header_bytes, bytes)
        
        # Test with dict payload
        header_dict = self.generator.generate_publish_header(topic, {"key": "value"}, qos=0)
        self.assertIsInstance(header_dict, bytes)
        
        # All should produce valid headers
        for header in [header_str, header_bytes, header_dict]:
            self.assertEqual(header[0] & 0xF0, 3 << 4)  # PUBLISH command
    
    def test_retain_flag(self):
        """Test that retain flag is properly set in header."""
        topic = "test/topic"
        payload = "test"
        
        # Without retain
        header_no_retain = self.generator.generate_publish_header(topic, payload, retain=False)
        self.assertEqual(header_no_retain[0] & 0x01, 0)  # RETAIN bit should be 0
        
        # With retain
        header_retain = self.generator.generate_publish_header(topic, payload, retain=True)
        self.assertEqual(header_retain[0] & 0x01, 1)  # RETAIN bit should be 1


def test_integration_with_javascript_output():
    """
    Integration test to verify our output matches what would be expected
    from the JavaScript mqtt-packet library.
    """
    print("\n=== Integration Test ===")
    
    # Test case 1: Simple QoS 0 publish
    topic = "test/topic"
    payload = {"message": "hello"}
    
    header = generate_mqtt_header(topic, payload, qos=0)
    print(f"QoS 0 Header: {header.hex()}")
    
    # Test case 2: QoS 1 with message ID
    header_qos1 = generate_mqtt_header(topic, payload, qos=1, message_id=1234)
    print(f"QoS 1 Header: {header_qos1.hex()}")
    
    # Test case 3: With retain flag
    header_retain = generate_mqtt_header(topic, payload, qos=0, retain=True)
    print(f"Retain Header: {header_retain.hex()}")
    
    # Show complete message structure
    json_bytes = json.dumps(payload).encode('utf-8')
    complete_msg = header + json_bytes
    print(f"Complete message: {complete_msg.hex()}")
    print(f"JSON part starts at byte: {len(header)}")


if __name__ == "__main__":
    # Run the unit tests
    unittest.main(verbosity=2, exit=False)
    
    # Run integration test
    test_integration_with_javascript_output()