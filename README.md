# TCP Chat Server

A simple TCP chat server in Python built with non-blocking sockets and I/O multiplexing using `selectors`.

## Architecture

The server uses a single event loop to handle multiple connected clients without creating a thread per connection.

The current implementation separates the system into three main concerns:

```text
Application Logic
      ↓
Application Protocol
      ↓
Socket / Transport I/O
      ↓
TCP
```

This keeps chat behavior, message representation, and low-level networking concerns independent from one another.

### `server.py`

Handles server orchestration and application-level chat behavior, including:

* Client management
* Message broadcasting
* Chat history
* Accepting new connections
* Client disconnect handling
* Selector event dispatch
* Application message handling
* Server startup and shutdown

The server works with structured `Message` objects rather than interpreting raw TCP data directly.

### `connections.py`

Handles per-client connection state and low-level socket I/O, including:

* `ClientState`
* Raw socket reads
* Buffered writes
* Receive buffering
* Selector read/write interest changes
* Connection cleanup

`connections.py` deals only with transport-level concerns.

It does not interpret chat messages, JSON payloads, or application message types.

### `protocol.py`

Defines the application protocol used between the client and server.

It is responsible for:

* `Message`
* `MessageType`
* Message serialization
* Message deserialization
* Length-prefixed framing
* Frame extraction from buffered TCP data
* Protocol validation
* Protocol errors

Messages are represented as structured objects instead of plain strings.

For example:

```python
Message(
    MessageType.CHAT,
    {
        "text": "hello"
    }
)
```

Before being sent over TCP, a message is serialized into JSON and framed using a 4-byte length prefix:

```text
┌─────────────────────┬──────────────────────────────┐
│ 4-byte payload size │ JSON payload                 │
└─────────────────────┴──────────────────────────────┘
```

This prevents the application from assuming that one call to `recv()` corresponds to exactly one message.

TCP provides an ordered byte stream, so a single read may contain:

* Part of one message
* Exactly one message
* Multiple complete messages
* Multiple messages followed by part of another message

Incoming bytes are therefore stored in a receive buffer until complete frames can be extracted.

### `first_client.py`

Provides the terminal-based chat client.

The client now uses the same application protocol as the server.

Outgoing user input is converted into a typed `Message`, encoded into a framed byte sequence, and sent over TCP.

Incoming TCP data is buffered and passed through the protocol layer so that complete messages can be extracted before they are displayed.

The client currently uses a background receive thread so incoming messages can be displayed while the main thread waits for terminal input.

---

## Message Flow

### Client to Server

```text
User input
    ↓
Message
    ↓
encode_msg()
    ↓
4-byte length + JSON payload
    ↓
TCP
    ↓
read_from_client()
    ↓
recv_buffer
    ↓
extract_msgs()
    ↓
Message
    ↓
server application logic
```

### Server to Client

```text
Server application logic
    ↓
Message
    ↓
encode_msg()
    ↓
send_buffer
    ↓
TCP
    ↓
client receive buffer
    ↓
extract_msgs()
    ↓
Message
    ↓
terminal output
```

---

## Message Types

The protocol uses explicit message types instead of determining behavior from arbitrary message strings.

Examples include:

```text
CHAT
SYSTEM
ERROR
SET_NAME
RENAME
```

This allows application behavior to be expressed explicitly.

For example, a future rename operation can be represented as:

```python
Message(
    MessageType.RENAME,
    {
        "name": "Alice"
    }
)
```

instead of requiring the server to inspect a normal chat string such as:

```text
Rename Alice
```

This prevents application commands from being confused with ordinary user messages and provides a cleaner foundation for future features.

`SET_NAME` is used when a client first connects to assign a display name to that client's connection state.

For example:

```python
Message(
    MessageType.SET_NAME,
    {
        "name": "Alice"
    }
)
```
`RENAME` is reserved for future support for changing a user's name after connecting.

---

## Features

* Multiple concurrent clients
* Non-blocking server socket I/O
* `selectors.DefaultSelector`
* Single-threaded server event loop
* Message broadcasting
* Buffered socket writes
* Buffered socket reads
* Length-prefixed TCP message framing
* Structured application messages
* Explicit message types
* JSON message serialization
* Handling of partial TCP frames
* Handling of multiple messages in a single TCP read
* Basic chat history
* System messages
* Client disconnect handling
* Separate transport, protocol, and application responsibilities
* User-defined display names
* Per-client username state
* Username-aware chat messages and disconnect notifications

---

## Project Structure

```text
tcp-chat-server/
├── first_server.py
├── first_client.py
├── server.py
├── connections.py
├── protocol.py
└── README.md
```

### Current implementation

`server.py` contains selector-based server orchestration and chat application behavior.

`connections.py` contains per-client connection state and low-level socket I/O.

`protocol.py` defines the framed application protocol and converts between structured messages and bytes.

`first_client.py` is the terminal client and communicates with the server using the framed protocol.

`first_server.py` preserves the earlier server implementation from before the selector-based refactor.

---

## Run

Start the server:

```bash
python server.py
```

Then start one or more clients:

```bash
python first_client.py
```

The server runs on:

```text
localhost:9999
```

Type `exit` in a client to disconnect.

---

## Development Progress

```text
V1
Basic TCP chat server

V2.0
Selector-based non-blocking server

V2.1
Separated connection I/O from server orchestration

V2.2
Introduced framed application protocol
- Length-prefixed messages
- JSON serialization
- Explicit message types
- Per-connection receive buffering
- Framed communication in both directions
```

## Current Architecture

```text
                 server.py
          Application / Chat Logic
                    │
                    │ Message
                    ▼
                protocol.py
       Framing / Serialization / Types
                    │
                    │ bytes
                    ▼
              connections.py
        Socket / Buffer / Selector I/O
                    │
                    ▼
                    TCP
```

Each layer has a distinct responsibility:

```text
server.py
"What should this message do?"

protocol.py
"What does this message mean on the wire?"

connections.py
"How do these bytes move through the socket?"
```
