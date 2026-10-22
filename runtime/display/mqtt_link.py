#!/usr/bin/env python3
"""Bounded MQTT 3.1.1 QoS0 link for the local display adapter (stdlib only)."""
import socket
import struct
import time


def field(value):
    raw = value.encode() if isinstance(value, str) else value
    return struct.pack('!H', len(raw)) + raw


def packet(kind, payload=b''):
    size = len(payload)
    remaining = bytearray()
    while True:
        digit = size % 128
        size //= 128
        remaining.append(digit | (128 if size else 0))
        if not size:
            return bytes([kind]) + remaining + payload


class Link:
    def __init__(self, host, port, name, username=None, password=None):
        self.sock = socket.create_connection((host, int(port)), timeout=5)
        self.sock.settimeout(5)
        flags = 2
        body = field(name)
        if username is not None:
            flags |= 128
            body += field(username)
            if password is not None:
                flags |= 64
                body += field(password)
        self.sock.sendall(packet(0x10, field('MQTT') + bytes([4, flags]) + struct.pack('!H', 60) + body))
        self.buffer = bytearray()
        self.last_ping = time.monotonic()
        # CONNACK may be split across TCP packets.
        while len(self.buffer) < 4:
            chunk = self.sock.recv(4-len(self.buffer))
            if not chunk:
                raise ConnectionError('MQTT connection closed')
            self.buffer.extend(chunk)
        if self.buffer != b'\x20\x02\x00\x00':
            raise ConnectionError('MQTT connection rejected')
        self.buffer.clear()

    def subscribe(self, topics):
        self.sock.sendall(packet(0x82, b'\x00\x01' + b''.join(field(t) + b'\x00' for t in topics)))

    def publish(self, topic, payload):
        if isinstance(payload, str):
            payload = payload.encode()
        self.sock.sendall(packet(0x30, field(topic) + payload))

    def ping(self):
        if time.monotonic() - self.last_ping >= 20:
            self.sock.sendall(packet(0xc0))
            self.last_ping = time.monotonic()

    def receive(self):
        chunk = self.sock.recv(65536)
        if not chunk:
            raise ConnectionError('MQTT disconnected')
        self.buffer.extend(chunk)
        messages = []
        while len(self.buffer) >= 2:
            size, factor, pos = 0, 1, 1
            while True:
                if pos >= len(self.buffer):
                    return messages
                digit = self.buffer[pos]
                size += (digit & 127) * factor
                pos += 1
                if size > 1048576 or pos > 5:
                    raise ValueError('MQTT packet limit')
                if not digit & 128:
                    break
                factor *= 128
            if len(self.buffer) < pos + size:
                return messages
            kind = self.buffer[0]
            body = bytes(self.buffer[pos:pos+size])
            del self.buffer[:pos+size]
            if kind >> 4 == 3:
                if len(body) < 2 or kind & 6:
                    raise ValueError('Expected MQTT QoS0 publish')
                length = struct.unpack('!H', body[:2])[0]
                if len(body) < length+2:
                    raise ValueError('Truncated MQTT topic')
                messages.append((body[2:2+length].decode(), body[2+length:]))
        return messages
