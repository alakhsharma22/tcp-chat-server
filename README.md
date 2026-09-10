# TCP Chat Server

A simple TCP chat server in Python using non-blocking sockets and I/O multiplexing with `selectors`.

## Architecture

The server uses a single event loop to handle multiple clients without creating a thread per connection.

It supports:

* Multiple concurrent clients
* Non-blocking socket I/O
* `selectors.DefaultSelector`
* Message broadcasting
* Buffered writes
* Basic chat history
* Client disconnect handling

## Project Structure

```text
tcp-chat-server/
├── first_server.py
├── first_client.py
├── server.py
└── README.md
```

`server.py` contains the current selector-based implementation.

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

Type `exit` to disconnect.
