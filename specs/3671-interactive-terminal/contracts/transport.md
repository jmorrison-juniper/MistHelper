# Contract: Transport Classes

The classes live in `src/websocket_streams/live/transport/`. Each class takes its socket
factory and its clock as constructor values, so the unit tests use fakes.

## MistStreamEndpoint

Build the connection values from the Mist API session.

| Method | Result |
| - | - |
| `stream_url()` | `wss://` + the cloud host with `api.` changed to `api-ws.` + `/api-ws/v1/stream` |
| `headers()` | `["Authorization: Token <token>"]` for token sign-in, or an empty list |
| `cookie()` | The cookie text for password sign-in, or `None`. A cookie with CR or LF is skipped. |
| `sslopt()` | The TLS options from `verify` and `cert` of the API session |
| `host_label(url)` | The host name of a URL. Logs use this value only. |

The tests build the endpoint with a `ws://` test address.

## ShellAddressPolicy

| Method | Result |
| - | - |
| `check(url)` | Return the URL when the scheme is `wss` and the host is in the Mist domain. If not, raise `StreamRequestError("bad_request", ...)`. |

The Mist domain is the last 2 labels of the cloud host. The tests use a policy that also
accepts `ws://127.0.0.1`.

## ConnectFailure

Turn a WebSocket open error into a plain reason for the operator. Issue #3671 added this
class, because a failed open showed "Read the portal log for the cause" or a raw operating
system message.

| Error from the open | Reason |
| - | - |
| `websocket.WebSocketBadStatusException` | The Mist cloud refused the WebSocket connection with HTTP status N. |
| `TimeoutError` or `websocket.WebSocketTimeoutException` | The Mist cloud did not answer the WebSocket connection in time. |
| `ssl.SSLError` | The TLS check of the Mist cloud connection failed. |
| `websocket.WebSocketAddressException` | The portal could not find the address of the Mist cloud. |
| `OSError`, `ConnectionError`, a proxy error, or a lost connection | The portal could not connect to the Mist cloud. |

`reason(error)` returns `None` for other errors. The caller then keeps its own handling.
The rule order matters, because a timeout and a TLS error are also an `OSError`.

The runners use the reason in these ways.

- The shell runner and the screen runner end the session as `Failed` with the reason.
  An address policy refusal keeps its own reason.
- The device command runner ends the session as `Failed` with the reason.
- The channel runner ends the session at once for HTTP status 400 through 499, but not
  for 408 or 429. It connects again after each other failure. When the retry budget ends,
  the final reason is the reason of the last failed open. A subscribe timeout or a drop
  after a subscribe clears that reason. The final reason is then
  `The WebSocket connection failed after retry attempts.`

The fake cloud in
`tests/unit/websocket_streams/live/transport/fake_mist_cloud/server.py` can fail one
handshake path in three ways: `HandshakeFault("refuse", status_code)`,
`HandshakeFault("stall")`, and `HandshakeFault("reset")`.

## ConnectionClosed and SubscribeError

| Class | Fields | Meaning |
| - | - | - |
| `ConnectionClosed` | `code`, `dropped` | The connection ended. `code` is the close code, 1005 for a close frame with no payload, or `None` when no close frame arrived. `dropped` is true when the far side or the network ended the connection. |
| `SubscribeError` | `channel`, `detail` | A channel subscription failed. `detail` is the refusal detail, or `timeout`. |

## FrameReader

`FrameReader` reads the frames of one socket for `StreamClient` and `ShellClient`.

| Method | Result |
| - | - |
| `read(timeout)` | Return one data frame as `FrameRead(opcode, payload)`. Return `None` after a quiet interval or a control frame. Send a ping after one quiet interval. Raise `ConnectionClosed` after 2 silent intervals or when the socket closes. |
| `close_socket(socket)` | Abort, close, and shut down one socket. |

## FrameDecoder

| Method | Result |
| - | - |
| `event(frame)` | Decode one stream frame into a dictionary. Remove NUL bytes from binary data. Text that is not JSON becomes `{"raw": text}`. |
| `data_payload(event)` | Return the inner data of a `data` event. Decode JSON text. |

## StreamClient

One Mist stream connection with one or more channels. A channel stream can watch more
than one site or device, so the client takes a list of channel paths.

| Method | Behavior |
| - | - |
| `open()` | Connect, send one subscribe frame for each channel, and wait for `channel_subscribed` for each channel. The wait is 10 seconds. Raise `SubscribeError` on `subscribe_failed` or on the timeout. |
| `next_event(timeout)` | Return the next decoded data event, or `None` when the wait ends. The device command runner uses this method. |
| `run(on_event)` | Read until the connection closes. Call `on_event` for each data event. Send a ping after 20 quiet seconds. Close after 2 silent intervals. |
| `close()` | Close the socket from any thread. `run` then returns. |

A channel stream runner calls `open` and `run` again after a break, up to 3 times.
An immediate drop after subscription consumes the current retry budget. The runner resets
that budget only after it receives one data event or stays subscribed for 5 stable seconds
(issue #3740).

## ShellClient

One connection to a shell address or a screen command address.

| Method | Behavior |
| - | - |
| `open(url, cols, rows)` | Check the address with the policy, connect, and send the size. |
| `read()` | Return the next output bytes, or `None` on a quiet interval. Remove exactly one leading NUL byte from each output frame, because the Mist cloud puts one before each frame. Raise `ConnectionClosed` at the end. |
| `send(text)` | Send one binary frame: a NUL byte, then the UTF-8 text. |
| `resize(cols, rows)` | Send the text frame `{"resize": {"width": cols, "height": rows}}`. |
| `close()` | Close the socket from any thread. |

`send` and `resize` can run on a web thread while `read` runs on the reader thread. The
client opens the socket with `enable_multithread=True`.
If either local write fails, the client closes the socket and raises `not_open`. The
terminal runner then records `WRITE_FAILED_REASON` instead of an operator stop (issue
#3741).

## Log rule

Each class logs the host label, the state, and the byte counts. No class logs the address
path, the token, a cookie, input text, or output bytes.
