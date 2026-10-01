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
| `open()` | Connect, send one subscribe frame for each channel, and wait for `channel_subscribed` for each channel. The wait is 10 seconds. Raise on `subscribe_failed` or on the timeout. |
| `run(on_event)` | Read until the connection closes. Call `on_event` for each data event. Send a ping after 20 quiet seconds. Close after 2 silent intervals. |
| `close()` | Close the socket from any thread. `run` then returns. |

A channel stream runner calls `open` and `run` again after a break, up to 3 times.

## ShellClient

One connection to a shell address or a screen command address.

| Method | Behavior |
| - | - |
| `open(url, cols, rows)` | Check the address with the policy, connect, and send the size. |
| `read()` | Return the next output bytes, or `None` on a quiet interval. Raise `ConnectionClosed` at the end. |
| `send(text)` | Send one binary frame: a NUL byte, then the UTF-8 text. |
| `resize(cols, rows)` | Send the text frame `{"resize": {"width": cols, "height": rows}}`. |
| `close()` | Close the socket from any thread. |

`send` and `resize` can run on a web thread while `read` runs on the reader thread. The
client opens the socket with `enable_multithread=True`.

## Log rule

Each class logs the host label, the state, and the byte counts. No class logs the address
path, the token, a cookie, input text, or output bytes.
