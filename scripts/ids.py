"""Shared deterministic UUIDs so schematic symbols and PCB footprints link by path."""
import uuid
NS2 = uuid.UUID("a3c1e5f0-2b7d-4e0a-9c55-0d1f6e2b8a10")

def U(key):
    return str(uuid.uuid5(NS2, key))
