"""Strict UUID normalization for historical, otherwise byte-identical Mach-O reproduction."""
import hashlib
import struct


def uuid_range(data):
    if len(data) < 32 or struct.unpack_from("<I", data)[0] != 0xfeedfacf:
        raise ValueError("Expected little-endian 64-bit Mach-O")
    count, size = struct.unpack_from("<II", data, 16)
    cursor, found = 32, []
    for _ in range(count):
        command, length = struct.unpack_from("<II", data, cursor)
        if length < 8 or cursor + length > 32 + size or cursor + length > len(data):
            raise ValueError("Invalid load command")
        if command == 0x1b:
            if length != 24:
                raise ValueError("Invalid UUID command")
            found.append((cursor + 8, cursor + 24))
        cursor += length
    if cursor != 32 + size or len(found) != 1:
        raise ValueError("Expected exactly one UUID")
    return found[0]


def without_uuid_hash(data):
    start, end = uuid_range(data)
    return hashlib.sha256(data[:start] + bytes(16) + data[end:]).hexdigest()


def reproduce_uuid(data, expected):
    if len(data) != expected["bytes"] or without_uuid_hash(data) != expected["without_uuid_sha256"]:
        raise ValueError("Executable differs beyond its UUID; refuse historical identity")
    start, end = uuid_range(data)
    result = data[:start] + bytes.fromhex(expected["uuid_hex"]) + data[end:]
    if hashlib.sha256(result).hexdigest() != expected["sha256"]:
        raise ValueError("Restored executable does not match the complete historical hash")
    return result
