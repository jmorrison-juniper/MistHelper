Client
SSH client & key policies

class paramiko.client.SSHClient
A high-level representation of a session with an SSH server. This class wraps Transport, Channel, and SFTPClient to take care of most aspects of authenticating and opening channels. A typical use case is:

client = SSHClient()
client.load_system_host_keys()
client.connect('ssh.example.com')
stdin, stdout, stderr = client.exec_command('ls -l')
You may pass in explicit overrides for authentication and server host key checking. The default mechanism is to try to use local key files or an SSH agent (if one is running).

Instances of this class may be used as context managers.

New in version 1.6.

__init__()
Create a new SSHClient.

load_system_host_keys(filename=None)
Load host keys from a system (read-only) file. Host keys read with this method will not be saved back by save_host_keys.

This method can be called multiple times. Each new set of host keys will be merged with the existing set (new replacing old if there are conflicts).

If filename is left as None, an attempt will be made to read keys from the user’s local “known hosts” file, as used by OpenSSH, and no exception will be raised if the file can’t be read. This is probably only useful on posix.

Parameters
filename (str) – the filename to read, or None

Raises
IOError – if a filename was provided and the file could not be read

load_host_keys(filename)
Load host keys from a local host-key file. Host keys read with this method will be checked after keys loaded via load_system_host_keys, but will be saved back by save_host_keys (so they can be modified). The missing host key policy AutoAddPolicy adds keys to this set and saves them, when connecting to a previously-unknown server.

This method can be called multiple times. Each new set of host keys will be merged with the existing set (new replacing old if there are conflicts). When automatically saving, the last hostname is used.

Parameters
filename (str) – the filename to read

Raises
IOError – if the filename could not be read

save_host_keys(filename)
Save the host keys back to a file. Only the host keys loaded with load_host_keys (plus any added directly) will be saved – not any host keys loaded with load_system_host_keys.

Parameters
filename (str) – the filename to save to

Raises
IOError – if the file could not be written

get_host_keys()
Get the local HostKeys object. This can be used to examine the local host keys or change them.

Returns
the local host keys as a HostKeys object.

set_log_channel(name)
Set the channel for logging. The default is "paramiko.transport" but it can be set to anything you want.

Parameters
name (str) – new channel name for logging

set_missing_host_key_policy(policy)
Set policy to use when connecting to servers without a known host key.

Specifically:

A policy is a “policy class” (or instance thereof), namely some subclass of MissingHostKeyPolicy such as RejectPolicy (the default), AutoAddPolicy, WarningPolicy, or a user-created subclass.

A host key is known when it appears in the client object’s cached host keys structures (those manipulated by load_system_host_keys and/or load_host_keys).

Parameters
policy (MissingHostKeyPolicy) – the policy to use when receiving a host key from a previously-unknown server

connect(hostname, port=22, username=None, password=None, pkey=None, key_filename=None, timeout=None, allow_agent=True, look_for_keys=True, compress=False, sock=None, gss_auth=False, gss_kex=False, gss_deleg_creds=True, gss_host=None, banner_timeout=None, auth_timeout=None, channel_timeout=None, gss_trust_dns=True, passphrase=None, disabled_algorithms=None, transport_factory=None, auth_strategy=None)
Connect to an SSH server and authenticate to it. The server’s host key is checked against the system host keys (see load_system_host_keys) and any local host keys (load_host_keys). If the server’s hostname is not found in either set of host keys, the missing host key policy is used (see set_missing_host_key_policy). The default policy is to reject the key and raise an SSHException.

Authentication is attempted in the following order of priority:

The pkey or key_filename passed in (if any)

key_filename may contain OpenSSH public certificate paths as well as regular private-key paths; when files ending in -cert.pub are found, they are assumed to match a private key, and both components will be loaded. (The private key itself does not need to be listed in key_filename for this to occur - just the certificate.)

Any key we can find through an SSH agent

Any “id_rsa”, “id_dsa” or “id_ecdsa” key discoverable in ~/.ssh/

When OpenSSH-style public certificates exist that match an existing such private key (so e.g. one has id_rsa and id_rsa-cert.pub) the certificate will be loaded alongside the private key and used for authentication.

Plain username/password auth, if a password was given

If a private key requires a password to unlock it, and a password is passed in, that password will be used to attempt to unlock the key.

Parameters
hostname (str) – the server to connect to

port (int) – the server port to connect to

username (str) – the username to authenticate as (defaults to the current local username)

password (str) – Used for password authentication; is also used for private key decryption if passphrase is not given.

passphrase (str) – Used for decrypting private keys.

pkey (PKey) – an optional private key to use for authentication

key_filename (str) – the filename, or list of filenames, of optional private key(s) and/or certs to try for authentication

timeout (float) – an optional timeout (in seconds) for the TCP connect

allow_agent (bool) – set to False to disable connecting to the SSH agent

look_for_keys (bool) – set to False to disable searching for discoverable private key files in ~/.ssh/

compress (bool) – set to True to turn on compression

sock (socket) – an open socket or socket-like object (such as a Channel) to use for communication to the target host

gss_auth (bool) – True if you want to use GSS-API authentication

gss_kex (bool) – Perform GSS-API Key Exchange and user authentication

gss_deleg_creds (bool) – Delegate GSS-API client credentials or not

gss_host (str) – The targets name in the kerberos database. default: hostname

gss_trust_dns (bool) – Indicates whether or not the DNS is trusted to securely canonicalize the name of the host being connected to (default True).

banner_timeout (float) – an optional timeout (in seconds) to wait for the SSH banner to be presented.

auth_timeout (float) – an optional timeout (in seconds) to wait for an authentication response.

channel_timeout (float) – an optional timeout (in seconds) to wait for a channel open response.

disabled_algorithms (dict) – an optional dict passed directly to Transport and its keyword argument of the same name.

transport_factory – an optional callable which is handed a subset of the constructor arguments (primarily those related to the socket, GSS functionality, and algorithm selection) and generates a Transport instance to be used by this client. Defaults to Transport.__init__.

auth_strategy –

an optional instance of AuthStrategy, triggering use of this newer authentication mechanism instead of SSHClient’s legacy auth method.

Warning
This parameter is incompatible with all other authentication-related parameters (such as, but not limited to, password, key_filename and allow_agent) and will trigger an exception if given alongside them.

Returns
AuthResult if auth_strategy is non-None; otherwise, returns None.

Raises
BadHostKeyException – if the server’s host key could not be verified.

AuthenticationException – if authentication failed.

UnableToAuthenticate – if authentication failed (when auth_strategy is non-None; and note that this is a subclass of AuthenticationException).

socket.error – if a socket error (other than connection-refused or host-unreachable) occurred while connecting.

NoValidConnectionsError – if all valid connection targets for the requested hostname (eg IPv4 and IPv6) yielded connection-refused or host-unreachable socket errors.

SSHException – if there was any other error connecting or establishing an SSH session.

Changed in version 1.15: Added the banner_timeout, gss_auth, gss_kex, gss_deleg_creds and gss_host arguments.

Changed in version 2.3: Added the gss_trust_dns argument.

Changed in version 2.4: Added the passphrase argument.

Changed in version 2.6: Added the disabled_algorithms argument.

Changed in version 2.12: Added the transport_factory argument.

Changed in version 3.2: Added the auth_strategy argument.

close()
Close this SSHClient and its underlying Transport.

This should be called anytime you are done using the client object.

Warning
Paramiko registers garbage collection hooks that will try to automatically close connections for you, but this is not presently reliable. Failure to explicitly close your client after use may lead to end-of-process hangs!

exec_command(command, bufsize=- 1, timeout=None, get_pty=False, environment=None)
Execute a command on the SSH server. A new Channel is opened and the requested command is executed. The command’s input and output streams are returned as Python file-like objects representing stdin, stdout, and stderr.

Parameters
command (str) – the command to execute

bufsize (int) – interpreted the same way as by the built-in file() function in Python

timeout (int) – set command’s channel timeout. See Channel.settimeout

get_pty (bool) – Request a pseudo-terminal from the server (default False). See Channel.get_pty

environment (dict) –

a dict of shell environment variables, to be merged into the default environment that the remote command executes within.

Warning
Servers may silently reject some environment variables; see the warning in Channel.set_environment_variable for details.

Returns
the stdin, stdout, and stderr of the executing command, as a 3-tuple

Raises
SSHException – if the server fails to execute the command

Changed in version 1.10: Added the get_pty kwarg.

invoke_shell(term='vt100', width=80, height=24, width_pixels=0, height_pixels=0, environment=None)
Start an interactive shell session on the SSH server. A new Channel is opened and connected to a pseudo-terminal using the requested terminal type and size.

Parameters
term (str) – the terminal type to emulate (for example, "vt100")

width (int) – the width (in characters) of the terminal window

height (int) – the height (in characters) of the terminal window

width_pixels (int) – the width (in pixels) of the terminal window

height_pixels (int) – the height (in pixels) of the terminal window

environment (dict) – the command’s environment

Returns
a new Channel connected to the remote shell

Raises
SSHException – if the server fails to invoke a shell

open_sftp()
Open an SFTP session on the SSH server.

Returns
a new SFTPClient session object

get_transport()
Return the underlying Transport object for this SSH connection. This can be used to perform lower-level tasks, like opening specific kinds of channels.

Returns
the Transport for this connection

class paramiko.client.MissingHostKeyPolicy
Interface for defining the policy that SSHClient should use when the SSH server’s hostname is not in either the system host keys or the application’s keys. Pre-made classes implement policies for automatically adding the key to the application’s HostKeys object (AutoAddPolicy), and for automatically rejecting the key (RejectPolicy).

This function may be used to ask the user to verify the key, for example.

missing_host_key(client, hostname, key)
Called when an SSHClient receives a server key for a server that isn’t in either the system or local HostKeys object. To accept the key, simply return. To reject, raised an exception (which will be passed to the calling application).

__weakref__
list of weak references to the object (if defined)

class paramiko.client.AutoAddPolicy
Policy for automatically adding the hostname and new host key to the local HostKeys object, and saving it. This is used by SSHClient.

missing_host_key(client, hostname, key)
Called when an SSHClient receives a server key for a server that isn’t in either the system or local HostKeys object. To accept the key, simply return. To reject, raised an exception (which will be passed to the calling application).

class paramiko.client.RejectPolicy
Policy for automatically rejecting the unknown hostname & key. This is used by SSHClient.

missing_host_key(client, hostname, key)
Called when an SSHClient receives a server key for a server that isn’t in either the system or local HostKeys object. To accept the key, simply return. To reject, raised an exception (which will be passed to the calling application).

class paramiko.client.WarningPolicy
Policy for logging a Python-style warning for an unknown host key, but accepting it. This is used by SSHClient.

missing_host_key(client, hostname, key)
Called when an SSHClient receives a server key for a server that isn’t in either the system or local HostKeys object. To accept the key, simply return. To reject, raised an exception (which will be passed to the calling application).

AI-powered ad network for devs. Get your message in front of the right developers with EthicalAds.
Ads by EthicalAds
Paramiko
A Python implementation of SSHv2.



Navigation
Channel
Client
Message
Packetizer
Transport
Authentication modules
SSH agents
Host keys / known_hosts files
Key handling
GSS-API authentication
GSS-API key exchange
Configuration
ProxyCommand support
Server implementation
SFTP
Buffered pipes
Buffered files
Cross-platform pipe implementations
Exceptions
Main website
Quick search
Donate/support
Professionally-supported Paramiko is available with the Tidelift Subscription.

©2025 Jeff Forcier. | Powered by Sphinx 4.3.2 & Alabaster 0.7.13 | Page source
Read the Docs
 stable


 Channel
Abstraction for an SSH2 channel.

class paramiko.channel.Channel(chanid)
A secure tunnel across an SSH Transport. A Channel is meant to behave like a socket, and has an API that should be indistinguishable from the Python socket API.

Because SSH2 has a windowing kind of flow control, if you stop reading data from a Channel and its buffer fills up, the server will be unable to send you any more data until you read some of it. (This won’t affect other channels on the same transport – all channels on a single transport are flow-controlled independently.) Similarly, if the server isn’t reading data you send, calls to send may block, unless you set a timeout. This is exactly like a normal network socket, so it shouldn’t be too surprising.

Instances of this class may be used as context managers.

__init__(chanid)
Create a new channel. The channel is not associated with any particular session or Transport until the Transport attaches it. Normally you would only call this method from the constructor of a subclass of Channel.

Parameters
chanid (int) – the ID of this channel, as passed by an existing Transport.

__repr__()
Return a string representation of this object, for debugging.

active
Whether the connection is presently active

chanid
Channel ID

close()
Close the channel. All future read/write operations on the channel will fail. The remote end will receive no more data (after queued data is flushed). Channels are automatically closed when their Transport is closed or when they are garbage collected.

closed
Whether the connection has been closed

exec_command(command)
Execute a command on the server. If the server allows it, the channel will then be directly connected to the stdin, stdout, and stderr of the command being executed.

When the command finishes executing, the channel will be closed and can’t be reused. You must open a new channel if you wish to execute another command.

Parameters
command (str) – a shell command to execute.

Raises
SSHException – if the request was rejected or the channel was closed

exit_status_ready()
Return true if the remote process has exited and returned an exit status. You may use this to poll the process status if you don’t want to block in recv_exit_status. Note that the server may not return an exit status in some cases (like bad servers).

Returns
True if recv_exit_status will return immediately, else False.

New in version 1.7.3.

fileno()
Returns an OS-level file descriptor which can be used for polling, but but not for reading or writing. This is primarily to allow Python’s select module to work.

The first time fileno is called on a channel, a pipe is created to simulate real OS-level file descriptor (FD) behavior. Because of this, two OS-level FDs are created, which will use up FDs faster than normal. (You won’t notice this effect unless you have hundreds of channels open at the same time.)

Returns
an OS-level file descriptor (int)

Warning
This method causes channel reads to be slightly less efficient.

get_id()
Return the int ID # for this channel.

The channel ID is unique across a Transport and usually a small number. It’s also the number passed to ServerInterface.check_channel_request when determining whether to accept a channel request in server mode.

get_name()
Get the name of this channel that was previously set by set_name.

get_pty(term='vt100', width=80, height=24, width_pixels=0, height_pixels=0)
Request a pseudo-terminal from the server. This is usually used right after creating a client channel, to ask the server to provide some basic terminal semantics for a shell invoked with invoke_shell. It isn’t necessary (or desirable) to call this method if you’re going to execute a single command with exec_command.

Parameters
term (str) – the terminal type to emulate (for example, 'vt100')

width (int) – width (in characters) of the terminal screen

height (int) – height (in characters) of the terminal screen

width_pixels (int) – width (in pixels) of the terminal screen

height_pixels (int) – height (in pixels) of the terminal screen

Raises
SSHException – if the request was rejected or the channel was closed

get_transport()
Return the Transport associated with this channel.

getpeername()
Return the address of the remote side of this Channel, if possible.

This simply wraps Transport.getpeername, used to provide enough of a socket-like interface to allow asyncore to work. (asyncore likes to call 'getpeername'.)

gettimeout()
Returns the timeout in seconds (as a float) associated with socket operations, or None if no timeout is set. This reflects the last call to setblocking or settimeout.

invoke_shell()
Request an interactive shell session on this channel. If the server allows it, the channel will then be directly connected to the stdin, stdout, and stderr of the shell.

Normally you would call get_pty before this, in which case the shell will operate through the pty, and the channel will be connected to the stdin and stdout of the pty.

When the shell exits, the channel will be closed and can’t be reused. You must open a new channel if you wish to open another shell.

Raises
SSHException – if the request was rejected or the channel was closed

invoke_subsystem(subsystem)
Request a subsystem on the server (for example, sftp). If the server allows it, the channel will then be directly connected to the requested subsystem.

When the subsystem finishes, the channel will be closed and can’t be reused.

Parameters
subsystem (str) – name of the subsystem being requested.

Raises
SSHException – if the request was rejected or the channel was closed

makefile(*params)
Return a file-like object associated with this channel. The optional mode and bufsize arguments are interpreted the same way as by the built-in file() function in Python.

Returns
ChannelFile object which can be used for Python file I/O.

makefile_stderr(*params)
Return a file-like object associated with this channel’s stderr stream. Only channels using exec_command or invoke_shell without a pty will ever have data on the stderr stream.

The optional mode and bufsize arguments are interpreted the same way as by the built-in file() function in Python. For a client, it only makes sense to open this file for reading. For a server, it only makes sense to open this file for writing.

Returns
ChannelStderrFile object which can be used for Python file I/O.

New in version 1.1.

makefile_stdin(*params)
Return a file-like object associated with this channel’s stdin stream.

The optional mode and bufsize arguments are interpreted the same way as by the built-in file() function in Python. For a client, it only makes sense to open this file for writing. For a server, it only makes sense to open this file for reading.

Returns
ChannelStdinFile object which can be used for Python file I/O.

New in version 2.6.

recv(nbytes)
Receive data from the channel. The return value is a string representing the data received. The maximum amount of data to be received at once is specified by nbytes. If a string of length zero is returned, the channel stream has closed.

Parameters
nbytes (int) – maximum number of bytes to read.

Returns
received data, as a bytes.

Raises
socket.timeout – if no data is ready before the timeout set by settimeout.

recv_exit_status()
Return the exit status from the process on the server. This is mostly useful for retrieving the results of an exec_command. If the command hasn’t finished yet, this method will wait until it does, or until the channel is closed. If no exit status is provided by the server, -1 is returned.

Warning
In some situations, receiving remote output larger than the current Transport or session’s window_size (e.g. that set by the default_window_size kwarg for Transport.__init__) will cause recv_exit_status to hang indefinitely if it is called prior to a sufficiently large Channel.recv (or if there are no threads calling Channel.recv in the background).

In these cases, ensuring that recv_exit_status is called after Channel.recv (or, again, using threads) can avoid the hang.

Returns
the exit code (as an int) of the process on the server.

New in version 1.2.

recv_ready()
Returns true if data is buffered and ready to be read from this channel. A False result does not mean that the channel has closed; it means you may need to wait before more data arrives.

Returns
True if a recv call on this channel would immediately return at least one byte; False otherwise.

recv_stderr(nbytes)
Receive data from the channel’s stderr stream. Only channels using exec_command or invoke_shell without a pty will ever have data on the stderr stream. The return value is a string representing the data received. The maximum amount of data to be received at once is specified by nbytes. If a string of length zero is returned, the channel stream has closed.

Parameters
nbytes (int) – maximum number of bytes to read.

Returns
received data as a bytes

Raises
socket.timeout – if no data is ready before the timeout set by settimeout.

New in version 1.1.

recv_stderr_ready()
Returns true if data is buffered and ready to be read from this channel’s stderr stream. Only channels using exec_command or invoke_shell without a pty will ever have data on the stderr stream.

Returns
True if a recv_stderr call on this channel would immediately return at least one byte; False otherwise.

New in version 1.1.

remote_chanid
Remote channel ID

request_forward_agent(handler)
Request for a forward SSH Agent on this channel. This is only valid for an ssh-agent from OpenSSH !!!

Parameters
handler – a required callable handler to use for incoming SSH Agent connections

Returns
True if we are ok, else False (at that time we always return ok)

Raises
SSHException in case of channel problem.

request_x11(screen_number=0, auth_protocol=None, auth_cookie=None, single_connection=False, handler=None)
Request an x11 session on this channel. If the server allows it, further x11 requests can be made from the server to the client, when an x11 application is run in a shell session.

From RFC 4254:

It is RECOMMENDED that the 'x11 authentication cookie' that is
sent be a fake, random cookie, and that the cookie be checked and
replaced by the real cookie when a connection request is received.
If you omit the auth_cookie, a new secure random 128-bit value will be generated, used, and returned. You will need to use this value to verify incoming x11 requests and replace them with the actual local x11 cookie (which requires some knowledge of the x11 protocol).

If a handler is passed in, the handler is called from another thread whenever a new x11 connection arrives. The default handler queues up incoming x11 connections, which may be retrieved using Transport.accept. The handler’s calling signature is:

handler(channel: Channel, (address: str, port: int))
Parameters
screen_number (int) – the x11 screen number (0, 10, etc.)

auth_protocol (str) – the name of the X11 authentication method used; if none is given, "MIT-MAGIC-COOKIE-1" is used

auth_cookie (str) – hexadecimal string containing the x11 auth cookie; if none is given, a secure random 128-bit value is generated

single_connection (bool) – if True, only a single x11 connection will be forwarded (by default, any number of x11 connections can arrive over this session)

handler – an optional callable handler to use for incoming X11 connections

Returns
the auth_cookie used

resize_pty(width=80, height=24, width_pixels=0, height_pixels=0)
Resize the pseudo-terminal. This can be used to change the width and height of the terminal emulation created in a previous get_pty call.

Parameters
width (int) – new width (in characters) of the terminal screen

height (int) – new height (in characters) of the terminal screen

width_pixels (int) – new width (in pixels) of the terminal screen

height_pixels (int) – new height (in pixels) of the terminal screen

Raises
SSHException – if the request was rejected or the channel was closed

send(s)
Send data to the channel. Returns the number of bytes sent, or 0 if the channel stream is closed. Applications are responsible for checking that all data has been sent: if only some of the data was transmitted, the application needs to attempt delivery of the remaining data.

Parameters
s (bytes) – data to send

Returns
number of bytes actually sent, as an int

Raises
socket.timeout – if no data could be sent before the timeout set by settimeout.

send_exit_status(status)
Send the exit status of an executed command to the client. (This really only makes sense in server mode.) Many clients expect to get some sort of status code back from an executed command after it completes.

Parameters
status (int) – the exit code of the process

New in version 1.2.

send_ready()
Returns true if data can be written to this channel without blocking. This means the channel is either closed (so any write attempt would return immediately) or there is at least one byte of space in the outbound buffer. If there is at least one byte of space in the outbound buffer, a send call will succeed immediately and return the number of bytes actually written.

Returns
True if a send call on this channel would immediately succeed or fail

send_stderr(s)
Send data to the channel on the “stderr” stream. This is normally only used by servers to send output from shell commands – clients won’t use this. Returns the number of bytes sent, or 0 if the channel stream is closed. Applications are responsible for checking that all data has been sent: if only some of the data was transmitted, the application needs to attempt delivery of the remaining data.

Parameters
s (bytes) – data to send.

Returns
number of bytes actually sent, as an int.

Raises
socket.timeout – if no data could be sent before the timeout set by settimeout.

New in version 1.1.

sendall(s)
Send data to the channel, without allowing partial results. Unlike send, this method continues to send data from the given string until either all data has been sent or an error occurs. Nothing is returned.

Parameters
s (bytes) – data to send.

Raises
socket.timeout – if sending stalled for longer than the timeout set by settimeout.

socket.error – if an error occurred before the entire string was sent.

Note
If the channel is closed while only part of the data has been sent, there is no way to determine how much data (if any) was sent. This is irritating, but identically follows Python’s API.

sendall_stderr(s)
Send data to the channel’s “stderr” stream, without allowing partial results. Unlike send_stderr, this method continues to send data from the given bytestring until all data has been sent or an error occurs. Nothing is returned.

Parameters
s (bytes) – data to send to the client as “stderr” output.

Raises
socket.timeout – if sending stalled for longer than the timeout set by settimeout.

socket.error – if an error occurred before the entire string was sent.

New in version 1.1.

set_combine_stderr(combine)
Set whether stderr should be combined into stdout on this channel. The default is False, but in some cases it may be convenient to have both streams combined.

If this is False, and exec_command is called (or invoke_shell with no pty), output to stderr will not show up through the recv and recv_ready calls. You will have to use recv_stderr and recv_stderr_ready to get stderr output.

If this is True, data will never show up via recv_stderr or recv_stderr_ready.

Parameters
combine (bool) – True if stderr output should be combined into stdout on this channel.

Returns
the previous setting (a bool).

New in version 1.1.

set_environment_variable(name, value)
Set the value of an environment variable.

Warning
The server may reject this request depending on its AcceptEnv setting; such rejections will fail silently (which is common client practice for this particular request type). Make sure you understand your server’s configuration before using!

Parameters
name (str) – name of the environment variable

value (str) – value of the environment variable

Raises
SSHException – if the request was rejected or the channel was closed

set_name(name)
Set a name for this channel. Currently it’s only used to set the name of the channel in logfile entries. The name can be fetched with the get_name method.

Parameters
name (str) – new channel name

setblocking(blocking)
Set blocking or non-blocking mode of the channel: if blocking is 0, the channel is set to non-blocking mode; otherwise it’s set to blocking mode. Initially all channels are in blocking mode.

In non-blocking mode, if a recv call doesn’t find any data, or if a send call can’t immediately dispose of the data, an error exception is raised. In blocking mode, the calls block until they can proceed. An EOF condition is considered “immediate data” for recv, so if the channel is closed in the read direction, it will never block.

chan.setblocking(0) is equivalent to chan.settimeout(0); chan.setblocking(1) is equivalent to chan.settimeout(None).

Parameters
blocking (int) – 0 to set non-blocking mode; non-0 to set blocking mode.

settimeout(timeout)
Set a timeout on blocking read/write operations. The timeout argument can be a nonnegative float expressing seconds, or None. If a float is given, subsequent channel read/write operations will raise a timeout exception if the timeout period value has elapsed before the operation has completed. Setting a timeout of None disables timeouts on socket operations.

chan.settimeout(0.0) is equivalent to chan.setblocking(0); chan.settimeout(None) is equivalent to chan.setblocking(1).

Parameters
timeout (float) – seconds to wait for a pending read/write operation before raising socket.timeout, or None for no timeout.

shutdown(how)
Shut down one or both halves of the connection. If how is 0, further receives are disallowed. If how is 1, further sends are disallowed. If how is 2, further sends and receives are disallowed. This closes the stream in one or both directions.

Parameters
how (int) –

0 (stop receiving), 1 (stop sending), or 2 (stop receiving and
sending).

shutdown_read()
Shutdown the receiving side of this socket, closing the stream in the incoming direction. After this call, future reads on this channel will fail instantly. This is a convenience method, equivalent to shutdown(0), for people who don’t make it a habit to memorize unix constants from the 1970s.

New in version 1.2.

shutdown_write()
Shutdown the sending side of this socket, closing the stream in the outgoing direction. After this call, future writes on this channel will fail instantly. This is a convenience method, equivalent to shutdown(1), for people who don’t make it a habit to memorize unix constants from the 1970s.

New in version 1.2.

transport
Transport managing this channel

update_environment(environment)
Updates this channel’s remote shell environment.

Note
This operation is additive - i.e. the current environment is not reset before the given environment variables are set.

Warning
Servers may silently reject some environment variables; see the warning in set_environment_variable for details.

Parameters
environment (dict) – a dictionary containing the name and respective values to set

Raises
SSHException – if any of the environment variables was rejected by the server or the channel was closed

class paramiko.channel.ChannelFile(channel, mode='r', bufsize=- 1)
A file-like wrapper around Channel. A ChannelFile is created by calling Channel.makefile.

Warning
To correctly emulate the file object created from a socket’s makefile method, a Channel and its ChannelFile should be able to be closed or garbage-collected independently. Currently, closing the ChannelFile does nothing but flush the buffer.

__init__(channel, mode='r', bufsize=- 1)
__repr__()
Returns a string representation of this object, for debugging.

class paramiko.channel.ChannelStderrFile(channel, mode='r', bufsize=- 1)
A file-like wrapper around Channel stderr.

See Channel.makefile_stderr for details.

class paramiko.channel.ChannelStdinFile(channel, mode='r', bufsize=- 1)
A file-like wrapper around Channel stdin.

See Channel.makefile_stdin for details.

close()
Close the file. Future read and write operations will fail.

paramiko.channel.open_only(func)
Decorator for Channel methods which performs an openness check.

Raises
SSHException – If the wrapped method is called on an unopened Channel.

Reach the right audience on a privacy-first ad network only for software devs: EthicalAds
Ads by EthicalAds
Paramiko
A Python implementation of SSHv2.



Navigation
Channel
Client
Message
Packetizer
Transport
Authentication modules
SSH agents
Host keys / known_hosts files
Key handling
GSS-API authentication
GSS-API key exchange
Configuration
ProxyCommand support
Server implementation
SFTP
Buffered pipes
Buffered files
Cross-platform pipe implementations
Exceptions
Main website
Quick search
Donate/support
Professionally-supported Paramiko is available with the Tidelift Subscription.

©2025 Jeff Forcier. | Powered by Sphinx 4.3.2 & Alabaster 0.7.13 | Page source
Read the Docs
 stable


 Message
Implementation of an SSH2 “message”.

class paramiko.message.Message(content=None)
An SSH2 message is a stream of bytes that encodes some combination of strings, integers, bools, and infinite-precision integers. This class builds or breaks down such a byte stream.

Normally you don’t need to deal with anything this low-level, but it’s exposed for people implementing custom extensions, or features that paramiko doesn’t support yet.

__init__(content=None)
Create a new SSH2 message.

Parameters
content (bytes) – the byte stream to use as the message content (passed in only when decomposing a message).

__repr__()
Returns a string representation of this object, for debugging.

__weakref__
list of weak references to the object (if defined)

add(*seq)
Add a sequence of items to the stream. The values are encoded based on their type: bytes, str, int, bool, or list.

Warning
Longs are encoded non-deterministically. Don’t use this method.

Parameters
seq – the sequence of items

add_adaptive_int(n)
Add an integer to the stream.

Parameters
n (int) – integer to add

add_boolean(b)
Add a boolean value to the stream.

Parameters
b (bool) – boolean value to add

add_byte(b)
Write a single byte to the stream, without any formatting.

Parameters
b (bytes) – byte to add

add_bytes(b)
Write bytes to the stream, without any formatting.

Parameters
b (bytes) – bytes to add

add_int(n)
Add an integer to the stream.

Parameters
n (int) – integer to add

add_int64(n)
Add a 64-bit int to the stream.

Parameters
n (int) – long int to add

add_list(l)
Add a list of strings to the stream. They are encoded identically to a single string of values separated by commas. (Yes, really, that’s how SSH2 does it.)

Parameters
l – list of strings to add

add_mpint(z)
Add a long int to the stream, encoded as an infinite-precision integer. This method only works on positive numbers.

Parameters
z (int) – long int to add

add_string(s)
Add a bytestring to the stream.

Parameters
s (byte) – bytestring to add

asbytes()
Return the byte stream content of this Message, as a bytes.

get_adaptive_int()
Fetch an int from the stream.

Returns
a 32-bit unsigned int.

get_binary()
Alias for get_string (obtains a bytestring).

get_boolean()
Fetch a boolean from the stream.

get_byte()
Return the next byte of the message, without decomposing it. This is equivalent to get_bytes(1).

Returns
the next (bytes) byte of the message, or b'\' if there aren’t any bytes remaining.

get_bytes(n)
Return the next n bytes of the message, without decomposing into an int, decoded string, etc. Just the raw bytes are returned. Returns a string of n zero bytes if there weren’t n bytes remaining in the message.

get_int()
Fetch an int from the stream.

get_int64()
Fetch a 64-bit int from the stream.

Returns
a 64-bit unsigned integer (int).

get_list()
Fetch a list of strings from the stream.

These are trivially encoded as comma-separated values in a string.

get_mpint()
Fetch a long int (mpint) from the stream.

Returns
an arbitrary-length integer (int).

get_remainder()
Return the bytes of this message that haven’t already been parsed and returned.

get_so_far()
Returns the bytes of this message that have been parsed and returned. The string passed into a message’s constructor can be regenerated by concatenating get_so_far and get_remainder.

get_string()
Fetch a “string” from the stream. This will actually be a bytes object, and may contain unprintable characters. (It’s not unheard of for a string to contain another byte-stream message.)

get_text()
Fetch a Unicode string from the stream.

This currently operates by attempting to encode the next “string” as utf-8.

rewind()
Rewind the message to the beginning as if no items had been parsed out of it yet.

Reach the right audience on a privacy-first ad network only for software devs: EthicalAds
Ads by EthicalAds
Paramiko
A Python implementation of SSHv2.



Navigation
Channel
Client
Message
Packetizer
Transport
Authentication modules
SSH agents
Host keys / known_hosts files
Key handling
GSS-API authentication
GSS-API key exchange
Configuration
ProxyCommand support
Server implementation
SFTP
Buffered pipes
Buffered files
Cross-platform pipe implementations
Exceptions
Main website
Quick search
Donate/support
Professionally-supported Paramiko is available with the Tidelift Subscription.

©2025 Jeff Forcier. | Powered by Sphinx 4.3.2 & Alabaster 0.7.13 | Page source
Read the Docs
 stable

 Packetizer
Packet handling

exception paramiko.packet.NeedRekeyException
Exception indicating a rekey is needed.

__weakref__
list of weak references to the object (if defined)

class paramiko.packet.Packetizer(socket)
Implementation of the base SSH packet protocol.

__init__(socket)¶
__weakref__
list of weak references to the object (if defined)

complete_handshake()
Tells Packetizer that the handshake has completed.

handshake_timed_out()
Checks if the handshake has timed out.

If start_handshake wasn’t called before the call to this function, the return value will always be False. If the handshake completed before a timeout was reached, the return value will be False

Returns
handshake time out status, as a bool

need_rekey()
Returns True if a new set of keys needs to be negotiated. This will be triggered during a packet read or write, so it should be checked after every read or write, or at least after every few.

read_all(n, check_rekey=False)
Read as close to N bytes as possible, blocking as long as necessary.

Parameters
n (int) – number of bytes to read

Returns
the data read, as a str

Raises
EOFError – if the socket was closed before all the bytes could be read

read_message()
Only one thread should ever be in this function (no other locking is done).

Raises
SSHException – if the packet is mangled

Raises
NeedRekeyException – if the transport should rekey

readline(timeout)
Read a line from the socket. We assume no data is pending after the line, so it’s okay to attempt large reads.

send_message(data)
Write a block of data using the current cipher, as an SSH block.

set_inbound_cipher(block_engine, block_size, mac_engine, mac_size, mac_key, etm=False, aead=False, iv_in=None)
Switch inbound data cipher. :param etm: Set encrypt-then-mac from OpenSSH

set_keepalive(interval, callback)
Turn on/off the callback keepalive. If interval seconds pass with no data read from or written to the socket, the callback will be executed and the timer will be reset.

set_log(log)
Set the Python log object to use for logging.

set_outbound_cipher(block_engine, block_size, mac_engine, mac_size, mac_key, sdctr=False, etm=False, aead=False, iv_out=None)
Switch outbound data cipher. :param etm: Set encrypt-then-mac from OpenSSH

start_handshake(timeout)
Tells Packetizer that the handshake process started. Starts a book keeping timer that can signal a timeout in the handshake process.

Parameters
timeout (float) – amount of seconds to wait before timing out

AI-powered ad network for devs. Get your message in front of the right developers with EthicalAds.
Ads by EthicalAds
Paramiko
A Python implementation of SSHv2.



Navigation
Channel
Client
Message
Packetizer
Transport
Authentication modules
SSH agents
Host keys / known_hosts files
Key handling
GSS-API authentication
GSS-API key exchange
Configuration
ProxyCommand support
Server implementation
SFTP
Buffered pipes
Buffered files
Cross-platform pipe implementations
Exceptions
Main website
Quick search
Donate/support
Professionally-supported Paramiko is available with the Tidelift Subscription.

©2025 Jeff Forcier. | Powered by Sphinx 4.3.2 & Alabaster 0.7.13 | Page source
Read the Docs
 stable

 Transport
Core protocol implementation

class paramiko.transport.Transport(sock, default_window_size=2097152, default_max_packet_size=32768, gss_kex=False, gss_deleg_creds=True, disabled_algorithms=None, server_sig_algs=True, strict_kex=True, packetizer_class=None)
An SSH Transport attaches to a stream (usually a socket), negotiates an encrypted session, authenticates, and then creates stream tunnels, called channels, across the session. Multiple channels can be multiplexed across a single session (and often are, in the case of port forwardings).

Instances of this class may be used as context managers.

__init__(sock, default_window_size=2097152, default_max_packet_size=32768, gss_kex=False, gss_deleg_creds=True, disabled_algorithms=None, server_sig_algs=True, strict_kex=True, packetizer_class=None)
Create a new SSH session over an existing socket, or socket-like object. This only creates the Transport object; it doesn’t begin the SSH session yet. Use connect or start_client to begin a client session, or start_server to begin a server session.

If the object is not actually a socket, it must have the following methods:

send(bytes): Writes from 1 to len(bytes) bytes, and returns an int representing the number of bytes written. Returns 0 or raises EOFError if the stream has been closed.

recv(int): Reads from 1 to int bytes and returns them as a string. Returns 0 or raises EOFError if the stream has been closed.

close(): Closes the socket.

settimeout(n): Sets a (float) timeout on I/O operations.

For ease of use, you may also pass in an address (as a tuple) or a host string as the sock argument. (A host string is a hostname with an optional port (separated by ":") which will be converted into a tuple of (hostname, port).) A socket will be connected to this address and used for communication. Exceptions from the socket call may be thrown in this case.

Note
Modifying the the window and packet sizes might have adverse effects on your channels created from this transport. The default values are the same as in the OpenSSH code base and have been battle tested.

Parameters
sock (socket) – a socket or socket-like object to create the session over.

default_window_size (int) – sets the default window size on the transport. (defaults to 2097152)

default_max_packet_size (int) – sets the default max packet size on the transport. (defaults to 32768)

gss_kex (bool) – Whether to enable GSSAPI key exchange when GSSAPI is in play. Default: False.

gss_deleg_creds (bool) – Whether to enable GSSAPI credential delegation when GSSAPI is in play. Default: True.

disabled_algorithms (dict) –

If given, must be a dictionary mapping algorithm type to an iterable of algorithm identifiers, which will be disabled for the lifetime of the transport.

Keys should match the last word in the class’ builtin algorithm tuple attributes, such as "ciphers" to disable names within _preferred_ciphers; or "kex" to disable something defined inside _preferred_kex. Values should exactly match members of the matching attribute.

For example, if you need to disable diffie-hellman-group16-sha512 key exchange (perhaps because your code talks to a server which implements it differently from Paramiko), specify disabled_algorithms={"kex": ["diffie-hellman-group16-sha512"]}.

server_sig_algs (bool) – Whether to send an extra message to compatible clients, in server mode, with a list of supported pubkey algorithms. Default: True.

strict_kex (bool) – Whether to advertise (and implement, if client also advertises support for) a “strict kex” mode for safer handshaking. Default: True.

packetizer_class – Which class to use for instantiating the internal packet handler. Default: None (i.e.: use Packetizer as normal).

Changed in version 1.15: Added the default_window_size and default_max_packet_size arguments.

Changed in version 1.15: Added the gss_kex and gss_deleg_creds kwargs.

Changed in version 2.6: Added the disabled_algorithms kwarg.

Changed in version 2.9: Added the server_sig_algs kwarg.

Changed in version 3.4: Added the strict_kex kwarg.

Changed in version 3.4: Added the packetizer_class kwarg.

__repr__()
Returns a string representation of this object, for debugging.

atfork()
Terminate this Transport without closing the session. On posix systems, if a Transport is open during process forking, both parent and child will share the underlying socket, but only one process can use the connection (without corrupting the session). Use this method to clean up a Transport object without disrupting the other process.

New in version 1.5.3.

get_security_options()
Return a SecurityOptions object which can be used to tweak the encryption algorithms this transport will permit (for encryption, digest/hash operations, public keys, and key exchanges) and the order of preference for them.

set_gss_host(gss_host, trust_dns=True, gssapi_requested=True)
Normalize/canonicalize self.gss_host depending on various factors.

Parameters
gss_host (str) – The explicitly requested GSS-oriented hostname to connect to (i.e. what the host’s name is in the Kerberos database.) Defaults to self.hostname (which will be the ‘real’ target hostname and/or host portion of given socket object.)

trust_dns (bool) – Indicates whether or not DNS is trusted; if true, DNS will be used to canonicalize the GSS hostname (which again will either be gss_host or the transport’s default hostname.) (Defaults to True due to backwards compatibility.)

gssapi_requested (bool) – Whether GSSAPI key exchange or authentication was even requested. If not, this is a no-op and nothing happens (and self.gss_host is not set.) (Defaults to True due to backwards compatibility.)

Returns
None.

start_client(event=None, timeout=None)
Negotiate a new SSH2 session as a client. This is the first step after creating a new Transport. A separate thread is created for protocol negotiation.

If an event is passed in, this method returns immediately. When negotiation is done (successful or not), the given Event will be triggered. On failure, is_active will return False.

(Since 1.4) If event is None, this method will not return until negotiation is done. On success, the method returns normally. Otherwise an SSHException is raised.

After a successful negotiation, you will usually want to authenticate, calling auth_password or auth_publickey.

Note
connect is a simpler method for connecting as a client.

Note
After calling this method (or start_server or connect), you should no longer directly read from or write to the original socket object.

Parameters
event (threading.Event) – an event to trigger when negotiation is complete (optional)

timeout (float) – a timeout, in seconds, for SSH2 session negotiation (optional)

Raises
SSHException – if negotiation fails (and no event was passed in)

start_server(event=None, server=None)
Negotiate a new SSH2 session as a server. This is the first step after creating a new Transport and setting up your server host key(s). A separate thread is created for protocol negotiation.

If an event is passed in, this method returns immediately. When negotiation is done (successful or not), the given Event will be triggered. On failure, is_active will return False.

(Since 1.4) If event is None, this method will not return until negotiation is done. On success, the method returns normally. Otherwise an SSHException is raised.

After a successful negotiation, the client will need to authenticate. Override the methods get_allowed_auths, check_auth_none, check_auth_password, and check_auth_publickey in the given server object to control the authentication process.

After a successful authentication, the client should request to open a channel. Override check_channel_request in the given server object to allow channels to be opened.

Note
After calling this method (or start_client or connect), you should no longer directly read from or write to the original socket object.

Parameters
event (threading.Event) – an event to trigger when negotiation is complete.

server (ServerInterface) – an object used to perform authentication and create channels

Raises
SSHException – if negotiation fails (and no event was passed in)

add_server_key(key)
Add a host key to the list of keys used for server mode. When behaving as a server, the host key is used to sign certain packets during the SSH2 negotiation, so that the client can trust that we are who we say we are. Because this is used for signing, the key must contain private key info, not just the public half. Only one key of each type (RSA or DSS) is kept.

Parameters
key (PKey) – the host key to add, usually an RSAKey or DSSKey.

get_server_key()
Return the active host key, in server mode. After negotiating with the client, this method will return the negotiated host key. If only one type of host key was set with add_server_key, that’s the only key that will ever be returned. But in cases where you have set more than one type of host key (for example, an RSA key and a DSS key), the key type will be negotiated by the client, and this method will return the key of the type agreed on. If the host key has not been negotiated yet, None is returned. In client mode, the behavior is undefined.

Returns
host key (PKey) of the type negotiated by the client, or None.

static load_server_moduli(filename=None)
(optional) Load a file of prime moduli for use in doing group-exchange key negotiation in server mode. It’s a rather obscure option and can be safely ignored.

In server mode, the remote client may request “group-exchange” key negotiation, which asks the server to send a random prime number that fits certain criteria. These primes are pretty difficult to compute, so they can’t be generated on demand. But many systems contain a file of suitable primes (usually named something like /etc/ssh/moduli). If you call load_server_moduli and it returns True, then this file of primes has been loaded and we will support “group-exchange” in server mode. Otherwise server mode will just claim that it doesn’t support that method of key negotiation.

Parameters
filename (str) – optional path to the moduli file, if you happen to know that it’s not in a standard location.

Returns
True if a moduli file was successfully loaded; False otherwise.

Note
This has no effect when used in client mode.

close()
Close this session, and any open channels that are tied to it.

get_remote_server_key()
Return the host key of the server (in client mode).

Note
Previously this call returned a tuple of (key type, key string). You can get the same effect by calling PKey.get_name for the key type, and str(key) for the key string.

Raises
SSHException – if no session is currently active.

Returns
public key (PKey) of the remote server

is_active()
Return true if this session is active (open).

Returns
True if the session is still active (open); False if the session is closed

open_session(window_size=None, max_packet_size=None, timeout=None)
Request a new channel to the server, of type "session". This is just an alias for calling open_channel with an argument of "session".

Note
Modifying the the window and packet sizes might have adverse effects on the session created. The default values are the same as in the OpenSSH code base and have been battle tested.

Parameters
window_size (int) – optional window size for this session.

max_packet_size (int) – optional max packet size for this session.

Returns
a new Channel

Raises
SSHException – if the request is rejected or the session ends prematurely

Changed in version 1.13.4/1.14.3/1.15.3: Added the timeout argument.

Changed in version 1.15: Added the window_size and max_packet_size arguments.

open_x11_channel(src_addr=None)
Request a new channel to the client, of type "x11". This is just an alias for open_channel('x11', src_addr=src_addr).

Parameters
src_addr (tuple) – the source address ((str, int)) of the x11 server (port is the x11 port, ie. 6010)

Returns
a new Channel

Raises
SSHException – if the request is rejected or the session ends prematurely

open_forward_agent_channel()
Request a new channel to the client, of type "auth-agent@openssh.com".

This is just an alias for open_channel('auth-agent@openssh.com').

Returns
a new Channel

Raises
SSHException – if the request is rejected or the session ends prematurely

open_forwarded_tcpip_channel(src_addr, dest_addr)
Request a new channel back to the client, of type forwarded-tcpip.

This is used after a client has requested port forwarding, for sending incoming connections back to the client.

Parameters
src_addr – originator’s address

dest_addr – local (server) connected address

open_channel(kind, dest_addr=None, src_addr=None, window_size=None, max_packet_size=None, timeout=None)
Request a new channel to the server. Channels are socket-like objects used for the actual transfer of data across the session. You may only request a channel after negotiating encryption (using connect or start_client) and authenticating.

Note
Modifying the the window and packet sizes might have adverse effects on the channel created. The default values are the same as in the OpenSSH code base and have been battle tested.

Parameters
kind (str) – the kind of channel requested (usually "session", "forwarded-tcpip", "direct-tcpip", or "x11")

dest_addr (tuple) – the destination address (address + port tuple) of this port forwarding, if kind is "forwarded-tcpip" or "direct-tcpip" (ignored for other channel types)

src_addr – the source address of this port forwarding, if kind is "forwarded-tcpip", "direct-tcpip", or "x11"

window_size (int) – optional window size for this session.

max_packet_size (int) – optional max packet size for this session.

timeout (float) – optional timeout opening a channel, default 3600s (1h)

Returns
a new Channel on success

Raises
SSHException – if the request is rejected, the session ends prematurely or there is a timeout opening a channel

Changed in version 1.15: Added the window_size and max_packet_size arguments.

request_port_forward(address, port, handler=None)
Ask the server to forward TCP connections from a listening port on the server, across this SSH session.

If a handler is given, that handler is called from a different thread whenever a forwarded connection arrives. The handler parameters are:

handler(
    channel,
    (origin_addr, origin_port),
    (server_addr, server_port),
)
where server_addr and server_port are the address and port that the server was listening on.

If no handler is set, the default behavior is to send new incoming forwarded connections into the accept queue, to be picked up via accept.

Parameters
address (str) – the address to bind when forwarding

port (int) – the port to forward, or 0 to ask the server to allocate any port

handler (callable) – optional handler for incoming forwarded connections, of the form func(Channel, (str, int), (str, int)).

Returns
the port number (int) allocated by the server

Raises
SSHException – if the server refused the TCP forward request

cancel_port_forward(address, port)
Ask the server to cancel a previous port-forwarding request. No more connections to the given address & port will be forwarded across this ssh connection.

Parameters
address (str) – the address to stop forwarding

port (int) – the port to stop forwarding

open_sftp_client()
Create an SFTP client channel from an open transport. On success, an SFTP session will be opened with the remote host, and a new SFTPClient object will be returned.

Returns
a new SFTPClient referring to an sftp session (channel) across this transport

send_ignore(byte_count=None)
Send a junk packet across the encrypted link. This is sometimes used to add “noise” to a connection to confuse would-be attackers. It can also be used as a keep-alive for long lived connections traversing firewalls.

Parameters
byte_count (int) – the number of random bytes to send in the payload of the ignored packet – defaults to a random number from 10 to 41.

renegotiate_keys()
Force this session to switch to new keys. Normally this is done automatically after the session hits a certain number of packets or bytes sent or received, but this method gives you the option of forcing new keys whenever you want. Negotiating new keys causes a pause in traffic both ways as the two sides swap keys and do computations. This method returns when the session has switched to new keys.

Raises
SSHException – if the key renegotiation failed (which causes the session to end)

set_keepalive(interval)
Turn on/off keepalive packets (default is off). If this is set, after interval seconds without sending any data over the connection, a “keepalive” packet will be sent (and ignored by the remote host). This can be useful to keep connections alive over a NAT, for example.

Parameters
interval (int) – seconds to wait before sending a keepalive packet (or 0 to disable keepalives).

global_request(kind, data=None, wait=True)
Make a global request to the remote host. These are normally extensions to the SSH2 protocol.

Parameters
kind (str) – name of the request.

data (tuple) – an optional tuple containing additional data to attach to the request.

wait (bool) – True if this method should not return until a response is received; False otherwise.

Returns
a Message containing possible additional data if the request was successful (or an empty Message if wait was False); None if the request was denied.

accept(timeout=None)
Return the next channel opened by the client over this transport, in server mode. If no channel is opened before the given timeout, None is returned.

Parameters
timeout (int) – seconds to wait for a channel, or None to wait forever

Returns
a new Channel opened by the client

connect(hostkey=None, username='', password=None, pkey=None, gss_host=None, gss_auth=False, gss_kex=False, gss_deleg_creds=True, gss_trust_dns=True)
Negotiate an SSH2 session, and optionally verify the server’s host key and authenticate using a password or private key. This is a shortcut for start_client, get_remote_server_key, and Transport.auth_password or Transport.auth_publickey. Use those methods if you want more control.

You can use this method immediately after creating a Transport to negotiate encryption with a server. If it fails, an exception will be thrown. On success, the method will return cleanly, and an encrypted session exists. You may immediately call open_channel or open_session to get a Channel object, which is used for data transfer.

Note
If you fail to supply a password or private key, this method may succeed, but a subsequent open_channel or open_session call may fail because you haven’t authenticated yet.

Parameters
hostkey (PKey) – the host key expected from the server, or None if you don’t want to do host key verification.

username (str) – the username to authenticate as.

password (str) – a password to use for authentication, if you want to use password authentication; otherwise None.

pkey (PKey) – a private key to use for authentication, if you want to use private key authentication; otherwise None.

gss_host (str) – The target’s name in the kerberos database. Default: hostname

gss_auth (bool) – True if you want to use GSS-API authentication.

gss_kex (bool) – Perform GSS-API Key Exchange and user authentication.

gss_deleg_creds (bool) – Whether to delegate GSS-API client credentials.

gss_trust_dns – Indicates whether or not the DNS is trusted to securely canonicalize the name of the host being connected to (default True).

Raises
SSHException – if the SSH2 negotiation fails, the host key supplied by the server is incorrect, or authentication fails.

Changed in version 2.3: Added the gss_trust_dns argument.

get_exception()
Return any exception that happened during the last server request. This can be used to fetch more specific error information after using calls like start_client. The exception (if any) is cleared after this call.

Returns
an exception, or None if there is no stored exception.

New in version 1.1.

set_subsystem_handler(name, handler, *args, **kwargs)
Set the handler class for a subsystem in server mode. If a request for this subsystem is made on an open ssh channel later, this handler will be constructed and called – see SubsystemHandler for more detailed documentation.

Any extra parameters (including keyword arguments) are saved and passed to the SubsystemHandler constructor later.

Parameters
name (str) – name of the subsystem.

handler – subclass of SubsystemHandler that handles this subsystem.

is_authenticated()
Return true if this session is active and authenticated.

Returns
True if the session is still open and has been authenticated successfully; False if authentication failed and/or the session is closed.

get_username()
Return the username this connection is authenticated for. If the session is not authenticated (or authentication failed), this method returns None.

Returns
username that was authenticated (a str), or None.

get_banner()
Return the banner supplied by the server upon connect. If no banner is supplied, this method returns None.

Returns
server supplied banner (str), or None.

New in version 1.13.

auth_none(username)
Try to authenticate to the server using no authentication at all. This will almost always fail. It may be useful for determining the list of authentication types supported by the server, by catching the BadAuthenticationType exception raised.

Parameters
username (str) – the username to authenticate as

Returns
list of auth types permissible for the next stage of authentication (normally empty)

Raises
BadAuthenticationType – if “none” authentication isn’t allowed by the server for this user

Raises
SSHException – if the authentication failed due to a network error

New in version 1.5.

auth_password(username, password, event=None, fallback=True)
Authenticate to the server using a password. The username and password are sent over an encrypted link.

If an event is passed in, this method will return immediately, and the event will be triggered once authentication succeeds or fails. On success, is_authenticated will return True. On failure, you may use get_exception to get more detailed error information.

Since 1.1, if no event is passed, this method will block until the authentication succeeds or fails. On failure, an exception is raised. Otherwise, the method simply returns.

Since 1.5, if no event is passed and fallback is True (the default), if the server doesn’t support plain password authentication but does support so-called “keyboard-interactive” mode, an attempt will be made to authenticate using this interactive mode. If it fails, the normal exception will be thrown as if the attempt had never been made. This is useful for some recent Gentoo and Debian distributions, which turn off plain password authentication in a misguided belief that interactive authentication is “more secure”. (It’s not.)

If the server requires multi-step authentication (which is very rare), this method will return a list of auth types permissible for the next step. Otherwise, in the normal case, an empty list is returned.

Parameters
username (str) – the username to authenticate as

password (basestring) – the password to authenticate with

event (threading.Event) – an event to trigger when the authentication attempt is complete (whether it was successful or not)

fallback (bool) – True if an attempt at an automated “interactive” password auth should be made if the server doesn’t support normal password auth

Returns
list of auth types permissible for the next stage of authentication (normally empty)

Raises
BadAuthenticationType – if password authentication isn’t allowed by the server for this user (and no event was passed in)

Raises
AuthenticationException – if the authentication failed (and no event was passed in)

Raises
SSHException – if there was a network error

auth_publickey(username, key, event=None)
Authenticate to the server using a private key. The key is used to sign data from the server, so it must include the private part.

If an event is passed in, this method will return immediately, and the event will be triggered once authentication succeeds or fails. On success, is_authenticated will return True. On failure, you may use get_exception to get more detailed error information.

Since 1.1, if no event is passed, this method will block until the authentication succeeds or fails. On failure, an exception is raised. Otherwise, the method simply returns.

If the server requires multi-step authentication (which is very rare), this method will return a list of auth types permissible for the next step. Otherwise, in the normal case, an empty list is returned.

Parameters
username (str) – the username to authenticate as

key (PKey) – the private key to authenticate with

event (threading.Event) – an event to trigger when the authentication attempt is complete (whether it was successful or not)

Returns
list of auth types permissible for the next stage of authentication (normally empty)

Raises
BadAuthenticationType – if public-key authentication isn’t allowed by the server for this user (and no event was passed in)

Raises
AuthenticationException – if the authentication failed (and no event was passed in)

Raises
SSHException – if there was a network error

auth_interactive(username, handler, submethods='')
Authenticate to the server interactively. A handler is used to answer arbitrary questions from the server. On many servers, this is just a dumb wrapper around PAM.

This method will block until the authentication succeeds or fails, periodically calling the handler asynchronously to get answers to authentication questions. The handler may be called more than once if the server continues to ask questions.

The handler is expected to be a callable that will handle calls of the form: handler(title, instructions, prompt_list). The title is meant to be a dialog-window title, and the instructions are user instructions (both are strings). prompt_list will be a list of prompts, each prompt being a tuple of (str, bool). The string is the prompt and the boolean indicates whether the user text should be echoed.

A sample call would thus be: handler('title', 'instructions', [('Password:', False)]).

The handler should return a list or tuple of answers to the server’s questions.

If the server requires multi-step authentication (which is very rare), this method will return a list of auth types permissible for the next step. Otherwise, in the normal case, an empty list is returned.

Parameters
username (str) – the username to authenticate as

handler (callable) – a handler for responding to server questions

submethods (str) – a string list of desired submethods (optional)

Returns
list of auth types permissible for the next stage of authentication (normally empty).

Raises
BadAuthenticationType – if public-key authentication isn’t allowed by the server for this user

Raises
AuthenticationException – if the authentication failed

Raises
SSHException – if there was a network error

New in version 1.5.

auth_interactive_dumb(username, handler=None, submethods='')
Authenticate to the server interactively but dumber. Just print the prompt and / or instructions to stdout and send back the response. This is good for situations where partial auth is achieved by key and then the user has to enter a 2fac token.

auth_gssapi_with_mic(username, gss_host, gss_deleg_creds)
Authenticate to the Server using GSS-API / SSPI.

Parameters
username (str) – The username to authenticate as

gss_host (str) – The target host

gss_deleg_creds (bool) – Delegate credentials or not

Returns
list of auth types permissible for the next stage of authentication (normally empty)

Raises
BadAuthenticationType – if gssapi-with-mic isn’t allowed by the server (and no event was passed in)

Raises
AuthenticationException – if the authentication failed (and no event was passed in)

Raises
SSHException – if there was a network error

auth_gssapi_keyex(username)
Authenticate to the server with GSS-API/SSPI if GSS-API kex is in use.

Parameters
username (str) – The username to authenticate as.

Returns
a list of auth types permissible for the next stage of authentication (normally empty)

Raises
BadAuthenticationType – if GSS-API Key Exchange was not performed (and no event was passed in)

Raises
AuthenticationException – if the authentication failed (and no event was passed in)

Raises
SSHException – if there was a network error

set_log_channel(name)
Set the channel for this transport’s logging. The default is "paramiko.transport" but it can be set to anything you want. (See the logging module for more info.) SSH Channels will log to a sub-channel of the one specified.

Parameters
name (str) – new channel name for logging

New in version 1.1.

get_log_channel()
Return the channel name used for this transport’s logging.

Returns
channel name as a str

New in version 1.2.

set_hexdump(hexdump)
Turn on/off logging a hex dump of protocol traffic at DEBUG level in the logs. Normally you would want this off (which is the default), but if you are debugging something, it may be useful.

Parameters
hexdump (bool) – True to log protocol traffix (in hex) to the log; False otherwise.

get_hexdump()
Return True if the transport is currently logging hex dumps of protocol traffic.

Returns
True if hex dumps are being logged, else False.

New in version 1.4.

use_compression(compress=True)
Turn on/off compression. This will only have an affect before starting the transport (ie before calling connect, etc). By default, compression is off since it negatively affects interactive sessions.

Parameters
compress (bool) – True to ask the remote client/server to compress traffic; False to refuse compression

New in version 1.5.2.

getpeername()
Return the address of the remote side of this Transport, if possible.

This is effectively a wrapper around getpeername on the underlying socket. If the socket-like object has no getpeername method, then ("unknown", 0) is returned.

Returns
the address of the remote host, if known, as a (str, int) tuple.

run()
Method representing the thread’s activity.

You may override this method in a subclass. The standard run() method invokes the callable object passed to the object’s constructor as the target argument, if any, with sequential and keyword arguments taken from the args and kwargs arguments, respectively.

class paramiko.transport.SecurityOptions(transport)
Simple object containing the security preferences of an ssh transport. These are tuples of acceptable ciphers, digests, key types, and key exchange algorithms, listed in order of preference.

Changing the contents and/or order of these fields affects the underlying Transport (but only if you change them before starting the session). If you try to add an algorithm that paramiko doesn’t recognize, ValueError will be raised. If you try to assign something besides a tuple to one of the fields, TypeError will be raised.

__init__(transport)
__repr__()
Returns a string representation of this object, for debugging.

property ciphers
Symmetric encryption ciphers

property digests
Digest (one-way hash) algorithms

property key_types
Public-key algorithms

property kex
Key exchange algorithms

property compression
Compression algorithms

class paramiko.transport.ServiceRequestingTransport(*args, **kwargs)
Transport, but also handling service requests, like it oughtta!

New in version 3.2.

__init__(*args, **kwargs)
Create a new SSH session over an existing socket, or socket-like object. This only creates the Transport object; it doesn’t begin the SSH session yet. Use connect or start_client to begin a client session, or start_server to begin a server session.

If the object is not actually a socket, it must have the following methods:

send(bytes): Writes from 1 to len(bytes) bytes, and returns an int representing the number of bytes written. Returns 0 or raises EOFError if the stream has been closed.

recv(int): Reads from 1 to int bytes and returns them as a string. Returns 0 or raises EOFError if the stream has been closed.

close(): Closes the socket.

settimeout(n): Sets a (float) timeout on I/O operations.

For ease of use, you may also pass in an address (as a tuple) or a host string as the sock argument. (A host string is a hostname with an optional port (separated by ":") which will be converted into a tuple of (hostname, port).) A socket will be connected to this address and used for communication. Exceptions from the socket call may be thrown in this case.

Note
Modifying the the window and packet sizes might have adverse effects on your channels created from this transport. The default values are the same as in the OpenSSH code base and have been battle tested.

Parameters
sock (socket) – a socket or socket-like object to create the session over.

default_window_size (int) – sets the default window size on the transport. (defaults to 2097152)

default_max_packet_size (int) – sets the default max packet size on the transport. (defaults to 32768)

gss_kex (bool) – Whether to enable GSSAPI key exchange when GSSAPI is in play. Default: False.

gss_deleg_creds (bool) – Whether to enable GSSAPI credential delegation when GSSAPI is in play. Default: True.

disabled_algorithms (dict) –

If given, must be a dictionary mapping algorithm type to an iterable of algorithm identifiers, which will be disabled for the lifetime of the transport.

Keys should match the last word in the class’ builtin algorithm tuple attributes, such as "ciphers" to disable names within _preferred_ciphers; or "kex" to disable something defined inside _preferred_kex. Values should exactly match members of the matching attribute.

For example, if you need to disable diffie-hellman-group16-sha512 key exchange (perhaps because your code talks to a server which implements it differently from Paramiko), specify disabled_algorithms={"kex": ["diffie-hellman-group16-sha512"]}.

server_sig_algs (bool) – Whether to send an extra message to compatible clients, in server mode, with a list of supported pubkey algorithms. Default: True.

strict_kex (bool) – Whether to advertise (and implement, if client also advertises support for) a “strict kex” mode for safer handshaking. Default: True.

packetizer_class – Which class to use for instantiating the internal packet handler. Default: None (i.e.: use Packetizer as normal).

Changed in version 1.15: Added the default_window_size and default_max_packet_size arguments.

Changed in version 1.15: Added the gss_kex and gss_deleg_creds kwargs.

Changed in version 2.6: Added the disabled_algorithms kwarg.

Changed in version 2.9: Added the server_sig_algs kwarg.

Changed in version 3.4: Added the strict_kex kwarg.

Changed in version 3.4: Added the packetizer_class kwarg.

auth_none(username)
Try to authenticate to the server using no authentication at all. This will almost always fail. It may be useful for determining the list of authentication types supported by the server, by catching the BadAuthenticationType exception raised.

Parameters
username (str) – the username to authenticate as

Returns
list of auth types permissible for the next stage of authentication (normally empty)

Raises
BadAuthenticationType – if “none” authentication isn’t allowed by the server for this user

Raises
SSHException – if the authentication failed due to a network error

New in version 1.5.

auth_password(username, password, fallback=True)
Authenticate to the server using a password. The username and password are sent over an encrypted link.

If an event is passed in, this method will return immediately, and the event will be triggered once authentication succeeds or fails. On success, is_authenticated will return True. On failure, you may use get_exception to get more detailed error information.

Since 1.1, if no event is passed, this method will block until the authentication succeeds or fails. On failure, an exception is raised. Otherwise, the method simply returns.

Since 1.5, if no event is passed and fallback is True (the default), if the server doesn’t support plain password authentication but does support so-called “keyboard-interactive” mode, an attempt will be made to authenticate using this interactive mode. If it fails, the normal exception will be thrown as if the attempt had never been made. This is useful for some recent Gentoo and Debian distributions, which turn off plain password authentication in a misguided belief that interactive authentication is “more secure”. (It’s not.)

If the server requires multi-step authentication (which is very rare), this method will return a list of auth types permissible for the next step. Otherwise, in the normal case, an empty list is returned.

Parameters
username (str) – the username to authenticate as

password (basestring) – the password to authenticate with

event (threading.Event) – an event to trigger when the authentication attempt is complete (whether it was successful or not)

fallback (bool) – True if an attempt at an automated “interactive” password auth should be made if the server doesn’t support normal password auth

Returns
list of auth types permissible for the next stage of authentication (normally empty)

Raises
BadAuthenticationType – if password authentication isn’t allowed by the server for this user (and no event was passed in)

Raises
AuthenticationException – if the authentication failed (and no event was passed in)

Raises
SSHException – if there was a network error

auth_publickey(username, key)
Authenticate to the server using a private key. The key is used to sign data from the server, so it must include the private part.

If an event is passed in, this method will return immediately, and the event will be triggered once authentication succeeds or fails. On success, is_authenticated will return True. On failure, you may use get_exception to get more detailed error information.

Since 1.1, if no event is passed, this method will block until the authentication succeeds or fails. On failure, an exception is raised. Otherwise, the method simply returns.

If the server requires multi-step authentication (which is very rare), this method will return a list of auth types permissible for the next step. Otherwise, in the normal case, an empty list is returned.

Parameters
username (str) – the username to authenticate as

key (PKey) – the private key to authenticate with

event (threading.Event) – an event to trigger when the authentication attempt is complete (whether it was successful or not)

Returns
list of auth types permissible for the next stage of authentication (normally empty)

Raises
BadAuthenticationType – if public-key authentication isn’t allowed by the server for this user (and no event was passed in)

Raises
AuthenticationException – if the authentication failed (and no event was passed in)

Raises
SSHException – if there was a network error

auth_interactive(username, handler, submethods='')
Authenticate to the server interactively. A handler is used to answer arbitrary questions from the server. On many servers, this is just a dumb wrapper around PAM.

This method will block until the authentication succeeds or fails, periodically calling the handler asynchronously to get answers to authentication questions. The handler may be called more than once if the server continues to ask questions.

The handler is expected to be a callable that will handle calls of the form: handler(title, instructions, prompt_list). The title is meant to be a dialog-window title, and the instructions are user instructions (both are strings). prompt_list will be a list of prompts, each prompt being a tuple of (str, bool). The string is the prompt and the boolean indicates whether the user text should be echoed.

A sample call would thus be: handler('title', 'instructions', [('Password:', False)]).

The handler should return a list or tuple of answers to the server’s questions.

If the server requires multi-step authentication (which is very rare), this method will return a list of auth types permissible for the next step. Otherwise, in the normal case, an empty list is returned.

Parameters
username (str) – the username to authenticate as

handler (callable) – a handler for responding to server questions

submethods (str) – a string list of desired submethods (optional)

Returns
list of auth types permissible for the next stage of authentication (normally empty).

Raises
BadAuthenticationType – if public-key authentication isn’t allowed by the server for this user

Raises
AuthenticationException – if the authentication failed

Raises
SSHException – if there was a network error

New in version 1.5.

auth_interactive_dumb(username, handler=None, submethods='')
Authenticate to the server interactively but dumber. Just print the prompt and / or instructions to stdout and send back the response. This is good for situations where partial auth is achieved by key and then the user has to enter a 2fac token.

auth_gssapi_with_mic(username, gss_host, gss_deleg_creds)
Authenticate to the Server using GSS-API / SSPI.

Parameters
username (str) – The username to authenticate as

gss_host (str) – The target host

gss_deleg_creds (bool) – Delegate credentials or not

Returns
list of auth types permissible for the next stage of authentication (normally empty)

Raises
BadAuthenticationType – if gssapi-with-mic isn’t allowed by the server (and no event was passed in)

Raises
AuthenticationException – if the authentication failed (and no event was passed in)

Raises
SSHException – if there was a network error

auth_gssapi_keyex(username)
Authenticate to the server with GSS-API/SSPI if GSS-API kex is in use.

Parameters
username (str) – The username to authenticate as.

Returns
a list of auth types permissible for the next stage of authentication (normally empty)

Raises
BadAuthenticationType – if GSS-API Key Exchange was not performed (and no event was passed in)

Raises
AuthenticationException – if the authentication failed (and no event was passed in)

Raises
SSHException – if there was a network error

AI-powered ad network for devs. Get your message in front of the right developers with EthicalAds.
Ads by EthicalAds
Paramiko
A Python implementation of SSHv2.



Navigation
Channel
Client
Message
Packetizer
Transport
Authentication modules
SSH agents
Host keys / known_hosts files
Key handling
GSS-API authentication
GSS-API key exchange
Configuration
ProxyCommand support
Server implementation
SFTP
Buffered pipes
Buffered files
Cross-platform pipe implementations
Exceptions
Main website
Quick search
Donate/support
Professionally-supported Paramiko is available with the Tidelift Subscription.

©2025 Jeff Forcier. | Powered by Sphinx 4.3.2 & Alabaster 0.7.13 | Page source
Read the Docs
 stable


 Buffered pipes
Attempt to generalize the “feeder” part of a Channel: an object which can be read from and closed, but is reading from a buffer fed by another thread. The read operations are blocking and can have a timeout set.

class paramiko.buffered_pipe.BufferedPipe
A buffer that obeys normal read (with timeout) & close semantics for a file or socket, but is fed data from another thread. This is used by Channel.

__init__()
__len__()¶
Return the number of bytes buffered.

Returns
number (int) of bytes buffered

__weakref__
list of weak references to the object (if defined)

close()
Close this pipe object. Future calls to read after the buffer has been emptied will return immediately with an empty string.

empty()
Clear out the buffer and return all data that was in it.

Returns
any data that was in the buffer prior to clearing it out, as a str

feed(data)
Feed new data into this pipe. This method is assumed to be called from a separate thread, so synchronization is done.

Parameters
data – the data to add, as a str or bytes

read(nbytes, timeout=None)
Read data from the pipe. The return value is a string representing the data received. The maximum amount of data to be received at once is specified by nbytes. If a string of length zero is returned, the pipe has been closed.

The optional timeout argument can be a nonnegative float expressing seconds, or None for no timeout. If a float is given, a PipeTimeout will be raised if the timeout period value has elapsed before any data arrives.

Parameters
nbytes (int) – maximum number of bytes to read

timeout (float) – maximum seconds to wait (or None, the default, to wait forever)

Returns
the read data, as a str or bytes

Raises
PipeTimeout – if a timeout was specified and no data was ready before that timeout

read_ready()
Returns true if data is buffered and ready to be read from this feeder. A False result does not mean that the feeder has closed; it means you may need to wait before more data arrives.

Returns
True if a read call would immediately return at least one byte; False otherwise.

set_event(event)
Set an event on this buffer. When data is ready to be read (or the buffer has been closed), the event will be set. When no data is ready, the event will be cleared.

Parameters
event (threading.Event) – the event to set/clear

exception paramiko.buffered_pipe.PipeTimeout
Indicates that a timeout was reached on a read from a BufferedPipe.

__weakref__
list of weak references to the object (if defined)

Reach the right audience on a privacy-first ad network only for software devs: EthicalAds
Ads by EthicalAds
Paramiko
A Python implementation of SSHv2.



Navigation
Channel
Client
Message
Packetizer
Transport
Authentication modules
SSH agents
Host keys / known_hosts files
Key handling
GSS-API authentication
GSS-API key exchange
Configuration
ProxyCommand support
Server implementation
SFTP
Buffered pipes
Buffered files
Cross-platform pipe implementations
Exceptions
Main website
Quick search
Donate/support
Professionally-supported Paramiko is available with the Tidelift Subscription.

©2025 Jeff Forcier. | Powered by Sphinx 4.3.2 & Alabaster 0.7.13 | Page source
Read the Docs
 stable

Buffered files
class paramiko.file.BufferedFile
Reusable base class to implement Python-style file buffering around a simpler stream.

__init__()
__iter__()
Returns an iterator that can be used to iterate over the lines in this file. This iterator happens to return the file itself, since a file is its own iterator.

Raises
ValueError – if the file is closed.

__next__()
Returns the next line from the input, or raises StopIteration when EOF is hit. Unlike python file objects, it’s okay to mix calls to next and readline.

Raises
StopIteration – when the end of the file is reached.

Returns
a line (str, or bytes if the file was opened in binary mode) read from the file.

close()
Close the file. Future read and write operations will fail.

flush()
Write out any data in the write buffer. This may do nothing if write buffering is not turned on.

read(size=None)
Read at most size bytes from the file (less if we hit the end of the file first). If the size argument is negative or omitted, read all the remaining data in the file.

Note
'b' mode flag is ignored (self.FLAG_BINARY in self._flags), because SSH treats all files as binary, since we have no idea what encoding the file is in, or even if the file is text data.

Parameters
size (int) – maximum number of bytes to read

Returns
data read from the file (as bytes), or an empty string if EOF was encountered immediately

readable()
Check if the file can be read from.

Returns
True if the file can be read from. If False, read will raise an exception.

readinto(buff)
Read up to len(buff) bytes into bytearray buff and return the number of bytes read.

Returns
The number of bytes read.

readline(size=None)
Read one entire line from the file. A trailing newline character is kept in the string (but may be absent when a file ends with an incomplete line). If the size argument is present and non-negative, it is a maximum byte count (including the trailing newline) and an incomplete line may be returned. An empty string is returned only when EOF is encountered immediately.

Note
Unlike stdio’s fgets, the returned string contains null characters ('\0') if they occurred in the input.

Parameters
size (int) – maximum length of returned string.

Returns
next line of the file, or an empty string if the end of the file has been reached.

If the file was opened in binary ('b') mode: bytes are returned Else: the encoding of the file is assumed to be UTF-8 and character strings (str) are returned

readlines(sizehint=None)
Read all remaining lines using readline and return them as a list. If the optional sizehint argument is present, instead of reading up to EOF, whole lines totalling approximately sizehint bytes (possibly after rounding up to an internal buffer size) are read.

Parameters
sizehint (int) – desired maximum number of bytes to read.

Returns
list of lines read from the file.

seek(offset, whence=0)
Set the file’s current position, like stdio’s fseek. Not all file objects support seeking.

Note
If a file is opened in append mode ('a' or 'a+'), any seek operations will be undone at the next write (as the file position will move back to the end of the file).

Parameters
offset (int) – position to move to within the file, relative to whence.

whence (int) – type of movement: 0 = absolute; 1 = relative to the current position; 2 = relative to the end of the file.

Raises
IOError – if the file doesn’t support random access.

seekable()
Check if the file supports random access.

Returns
True if the file supports random access. If False, seek will raise an exception.

tell()
Return the file’s current position. This may not be accurate or useful if the underlying file doesn’t support random access, or was opened in append mode.

Returns
file position (number of bytes).

writable()
Check if the file can be written to.

Returns
True if the file can be written to. If False, write will raise an exception.

write(data)
Write data to the file. If write buffering is on (bufsize was specified and non-zero), some or all of the data may not actually be written yet. (Use flush or close to force buffered data to be written out.)

Parameters
data – str/bytes data to write

writelines(sequence)
Write a sequence of strings to the file. The sequence can be any iterable object producing strings, typically a list of strings. (The name is intended to match readlines; writelines does not add line separators.)

Parameters
sequence – an iterable sequence of strings.

xreadlines()
Identical to iter(f). This is a deprecated file interface that predates Python iterator support.

Reach the right audience on a privacy-first ad network only for software devs: EthicalAds
Ads by EthicalAds
Paramiko
A Python implementation of SSHv2.



Navigation
Channel
Client
Message
Packetizer
Transport
Authentication modules
SSH agents
Host keys / known_hosts files
Key handling
GSS-API authentication
GSS-API key exchange
Configuration
ProxyCommand support
Server implementation
SFTP
Buffered pipes
Buffered files
Cross-platform pipe implementations
Exceptions
Main website
Quick search
Donate/support
Professionally-supported Paramiko is available with the Tidelift Subscription.

©2025 Jeff Forcier. | Powered by Sphinx 4.3.2 & Alabaster 0.7.13 | Page source
Read the Docs
 stable

 Exceptions
exception paramiko.ssh_exception.AuthenticationException
Exception raised when authentication failed for some reason. It may be possible to retry with different credentials. (Other classes specify more specific reasons.)

New in version 1.6.

exception paramiko.ssh_exception.BadAuthenticationType(explanation, types)
Exception raised when an authentication type (like password) is used, but the server isn’t allowing that type. (It may only allow public-key, for example.)

New in version 1.1.

__init__(explanation, types)
__str__()
Return str(self).

exception paramiko.ssh_exception.BadHostKeyException(hostname, got_key, expected_key)
The host key given by the SSH server did not match what we were expecting.

Parameters
hostname (str) – the hostname of the SSH server

got_key (PKey) – the host key presented by the server

expected_key (PKey) – the host key expected

New in version 1.6.

__init__(hostname, got_key, expected_key)
__str__()
Return str(self).

exception paramiko.ssh_exception.ChannelException(code, text)
Exception raised when an attempt to open a new Channel fails.

Parameters
code (int) – the error code returned by the server

New in version 1.6.

__init__(code, text)
__str__()
Return str(self).

exception paramiko.ssh_exception.ConfigParseError
A fatal error was encountered trying to parse SSH config data.

Typically this means a config file violated the ssh_config specification in a manner that requires exiting immediately, such as not matching key = value syntax or misusing certain Match keywords.

New in version 2.7.

exception paramiko.ssh_exception.CouldNotCanonicalize
Raised when hostname canonicalization fails & fallback is disabled.

New in version 2.7.

exception paramiko.ssh_exception.IncompatiblePeer
A disagreement arose regarding an algorithm required for key exchange.

New in version 2.9.

exception paramiko.ssh_exception.MessageOrderError
Out-of-order protocol messages were received, violating “strict kex” mode.

New in version 3.4.

exception paramiko.ssh_exception.NoValidConnectionsError(errors)
Multiple connection attempts were made and no families succeeded.

This exception class wraps multiple “real” underlying connection errors, all of which represent failed connection attempts. Because these errors are not guaranteed to all be of the same error type (i.e. different errno, socket.error subclass, message, etc) we expose a single unified error message and a None errno so that instances of this class match most normal handling of socket.error objects.

To see the wrapped exception objects, access the errors attribute. errors is a dict whose keys are address tuples (e.g. ('127.0.0.1', 22)) and whose values are the exception encountered trying to connect to that address.

It is implied/assumed that all the errors given to a single instance of this class are from connecting to the same hostname + port (and thus that the differences are in the resolution of the hostname - e.g. IPv4 vs v6).

New in version 1.16.

__init__(errors)
Parameters
errors (dict) – The errors dict to store, as described by class docstring.

__reduce__()
Helper for pickle.

__weakref__
list of weak references to the object (if defined)

exception paramiko.ssh_exception.PartialAuthentication(types)
An internal exception thrown in the case of partial authentication.

__init__(types)
__str__()
Return str(self).

exception paramiko.ssh_exception.PasswordRequiredException
Exception raised when a password is needed to unlock a private key file.

exception paramiko.ssh_exception.ProxyCommandFailure(command, error)
The “ProxyCommand” found in the .ssh/config file returned an error.

Parameters
command (str) – The command line that is generating this exception.

error (str) – The error captured from the proxy command output.

__init__(command, error)
__str__()
Return str(self).

exception paramiko.ssh_exception.SSHException
Exception raised by failures in SSH2 protocol negotiation or logic errors.

__weakref__
list of weak references to the object (if defined)

exception paramiko.ssh_exception.UnableToAuthenticate
Reach the right audience on a privacy-first ad network only for software devs: EthicalAds
Ads by EthicalAds
Paramiko
A Python implementation of SSHv2.



Navigation
Channel
Client
Message
Packetizer
Transport
Authentication modules
SSH agents
Host keys / known_hosts files
Key handling
GSS-API authentication
GSS-API key exchange
Configuration
ProxyCommand support
Server implementation
SFTP
Buffered pipes
Buffered files
Cross-platform pipe implementations
Exceptions
Main website
Quick search
Donate/support
Professionally-supported Paramiko is available with the Tidelift Subscription.

©2025 Jeff Forcier. | Powered by Sphinx 4.3.2 & Alabaster 0.7.13 | Page source
Read the Docs
 stable


 