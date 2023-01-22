import socket
import queue
import threading

class UDP_Proxy():

    rx_count = 0
    tx_count = 0

    running = None

    def __init__(self, r_ip, r_port, l_ip='127.0.0.1', l_port=None):
        self.remote_ip = r_ip
        self.remote_port = r_port
        self.local_ip = l_ip
        self.local_port = l_port if l_port is not None else r_port

        # Set up sockets
        self.socket_remote6 = socket.socket(socket.AF_INET6, socket.SOCK_DGRAM)
        self.socket_remote6.settimeout(1)
        self.socket_remote6.connect((self.remote_ip, self.remote_port))
        
        self.socket_local4 = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
        self.socket_local4.settimeout(1)

        try:
            self.socket_local4.bind((self.local_ip, self.local_port))
        except socket.error as e:
            if e.errno == errno.EADDRINUSE:
                self.socket_local4.bind((self.local_ip, 0))
            else:
                raise e

        # If the default port (0) is set, the system will give us a random port.
        self.local_port = self.socket_local4.getsockname()[1]

        # Set up threads
        self.count_lock = threading.Lock()

        self.threads = []
        self.fifo = queue.Queue()

        self.threads = [
            threading.Thread(daemon=True, target=self.forwarder, args=('s2c', self.socket_remote6, self.socket_local4)),
            threading.Thread(daemon=True, target=self.forwarder, args=('c2s', self.socket_local4, self.socket_remote6))
        ]

        self.running = threading.Event()
    
    @property
    def packets_in(self):
        with self.count_lock:
            return self.rx_count
    
    @property
    def packets_out(self):
        with self.count_lock:
            return self.tx_count


    def run(self):
        self.running.set()

        for t in self.threads:
            t.start()
        
        
    def stop(self):
        self.running.clear()
    
        for t in self.threads:
            t.join()
    

    def forwarder(self, name, rx, tx):
        port = None
        s2c = name == 's2c'

        while self.running.is_set():

            try:
                data, addr = rx.recvfrom(4096)

            except socket.timeout:
                continue
            except ConnectionResetError:
                # Need to fix
                continue

            if data:
                if s2c:
                    # Get the port from the other thread
                    if port is None or not self.fifo.empty():
                        # Block until we get a port to send data to.
                        port = self.fifo.get(block=True) 
                    tx.sendto(data, (self.local_ip, port))

                    with self.count_lock:
                        self.rx_count += 1

                else:
                    # Send the port of the client to the other thread on 
                    # first connect or when it changes (new connection).
                    if port is None or port != addr[1]:
                        port = addr[1]
                        self.fifo.put_nowait(port)
                    tx.sendto(data, (self.remote_ip, self.remote_port))

                    with self.count_lock:
                        self.tx_count += 1
            

if __name__ == "__main__":
    import argparse
    import time

    parser = argparse.ArgumentParser(
                    prog = 'udpproxy',
                    description = 'UDP Proxy by wayo.',)
    parser.add_argument('ipv6', help='Remote IPv6 server to forward the connection to.')
    parser.add_argument('port', help='Port on the remote IPv6 server.', type=int)
    parser.add_argument('--local-port', help='Local port to listen on. Defaults to the same port as remote IPv6 server.', default=-1, required=False, type=int)
    parser.add_argument('--local-address', help='Local IPv4 address to listen on. Defaults to 127.0.0.1.', default="127.0.0.1", required=False)

    args = parser.parse_args()

    r_ip6 = args.ipv6
    r_port = args.port
    l_ip = args.local_address
    l_port = None

    if args.local_port < 0 or args.local_port > 65535:
        l_port = args.port
    else:
        l_port = args.local_port

    proxy = UDP_Proxy(r_ip6, r_port, l_ip, l_port)

    proxy.run()
    print(f"Waiting on {l_ip}:{l_port} for connections... ")

    while True:
        time.sleep(0.3)
        print(f"Packets sent: {proxy.packets_out} / Packets recv: {proxy.packets_in}", end="\r")
