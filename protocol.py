import json
import struct
from dataclasses import dataclass, field
from enum import Enum
from typing import Any

header_size = 4
max_payload_size = 64 * 1024

class MessageType(str, Enum):
    SET_NAME = "set_name"
    CHAT = "chat"
    RENAME = "rename"

    SYSTEM = "system"
    ERROR = "error"

## Previous abstraction was string, now it is Message
@dataclass(frozen=True)
class Message:
    type : MessageType
    data : dict[str, Any]


class ProtocolError(Exception):
    pass

def encode_msg(message: Message) -> bytes:
    document = {
        "type" : message.type.value,
        "data" : message.data
    }

    payload = json.dumps(document, ensure_ascii=True, separators=(",", ":")).encode("utf-8")

    if len(payload) > max_payload_size:
        raise ProtocolError("Message is too large")

    header = struct.pack("!I", len(payload)) # I is unsigned int and ! for network byte order

    return header + payload

def extract_msgs(buff):
    msgs = []

    while True:
        if len(buff) < header_size:
            break

        payload_sz = struct.unpack("!I", buff[:header_size])[0]
        if payload_sz > max_payload_size:
            raise ProtocolError("Message is too large")

        frame_sz = header_size + payload_sz

        if len(buff) < frame_sz: ## header complete but incomplete payload
            break

        payload = bytes(buff[header_size:frame_sz])
        del buff[:frame_sz]

        msgs.append(decode_payload(payload))

    return msgs

def decode_payload(payload):
    try:
        document = json.loads(payload.decode("utf-8"))
        msg_type = MessageType(document["type"])
        data = document.get("data", {})

        return Message(msg_type, data)

    except (UnicodeDecodeError, json.JSONDecodeError, KeyError, ValueError) as ex:
        raise ProtocolError("Invalid msg") from ex