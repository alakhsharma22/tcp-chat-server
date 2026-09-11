# TCP Chat Server

A simple TCP chat server in Python built with non-blocking sockets and I/O multiplexing using `selectors`.

The project is being developed incrementally, with each version introducing cleaner networking and application architecture.

## Architecture

The server uses a single event loop to handle multiple connected clients without creating a thread per connection.

The current implementation separates **server orchestration** from **per-client connection handling**.

### `server.py`

Handles chat server orchestration and application-level behavior, including:

* Client management
* Message broadcasting
* Chat history
* Accepting new connections
* Client disconnect handling
* Selector event dispatch
* Server startup and shutdown

### `connections.py`

Handles per-client connection state and low-level socket I/O, including:

* `ClientState`
* Read operations
* Buffered write operations
* Selector read/write interest changes
* Connection cleanup

This keeps socket-level concerns separate from chat application logic.

## Features

* Multiple concurrent clients
* Non-blocking socket I/O
* `selectors.DefaultSelector`
* Single-threaded server event loop
* Message broadcasting
* Buffered writes
* Basic chat history
* Client disconnect handling
* Separate connection and server responsibilities

## Project Structure

```text
tcp-chat-server/
├── first_server.py
├── first_client.py
├── server.py
├── connections.py
└── README.md
```

### Current implementation

`server.py` contains the selector-based server orchestration.

`connections.py` contains client connection state and socket I/O operations.

`first_client.py` remains compatible with the current server implementation.

`first_server.py` preserves the earlier server implementation from before the selector-based refactor.

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

## Development Progress

```text
V1
Basic TCP chat server

V2.0
Selector-based non-blocking server

V2.1
Separated connection I/O from server orchestration
```

Future versions can build on this structure by introducing a framed application protocol, usernames, and explicit message types without mixing those concerns into the socket I/O layer.
