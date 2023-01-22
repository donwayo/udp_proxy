# UDP Proxy by Wayo
Simple UDP proxy meant to enable IPv4 UDP applications to interface with IPv6 applications. It will listen on localhost for an IPv4 connection, and then forward it to the configured IPv6 address and port. 

I use it to connect to my Valheim server hosted on IPv6. 

# Requirements
pyqt5 -- for the UI

# Usage
Run ui.py, enter the remote server's IPv6 information in the UI and press start. The UI will show you the local address you should point your game to (Listening on:).

Alternatively, you can run proxy.py from the command line. 
```
usage: udpproxy [-h] [--local-port LOCAL_PORT] [--local-address LOCAL_ADDRESS] ipv6 port

UDP Proxy by wayo.

positional arguments:
  ipv6                  Remote IPv6 server to forward the connection to.
  port                  Port on the remote IPv6 server.

options:
  -h, --help            show this help message and exit
  --local-port LOCAL_PORT
                        Local port to listen on. Defaults to the same port as remote IPv6 server.
  --local-address LOCAL_ADDRESS
                        Local IPv4 address to listen on. Defaults to 127.0.0.1.
```

# Troubleshooting
Check the UI's sent/recv counters. If you see that recv stays at 0, then you're not able to receive anything from the server due to having the wrong address or your network settings. Make sure your server sends the UDP packets from the same source address as you have configured in the UI. Otherwise the return packets may never get to you and the recv counter will stay at 0. 

# Contributing
I'd like to make contributing to this project as easy and transparent as possible, whether it's:

- Reporting a bug
- Discussing the current state of the code
- Submitting a fix
- Proposing new features

Please use GitHub issues and send changes through pull requests.

# License
By contributing, you agree that your contributions will be licensed under its MIT License.