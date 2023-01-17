import socket
import queue
import threading

class UDP_Proxy():

    remote_ip = None
    remote_port = None

    local_ip = None
    local_port = None

    socket_local4 = None
    socket_remote6 = None

    threads = None
    fifo = None

    rx_count = 0
    tx_count = 0

    run = None

    count_lock = threading.Lock()

    def __init__(self, r_ip, r_port, l_ip='127.0.0.1', l_port=None):
        self.remote_ip = r_ip
        self.remote_port = r_port
        self.local_ip = l_ip
        self.local_port = l_port if l_port is not None else r_port

        self.threads = []
        self.fifo = queue.Queue()

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
        while self.running.is_set():

            try:
                data, addr = rx.recvfrom(4096)
            except socket.timeout:
                continue

            if data:
                if name == 's2c':
                    if port is None:
                        port = self.fifo.get()
                    tx.sendto(data, (self.local_ip, port))

                    with self.count_lock:
                        self.rx_count += 1

                else:
                    if port is None:
                        port = addr[1]
                        self.fifo.put_nowait(port)
                    tx.sendto(data, (self.remote_ip, self.remote_port))

                    with self.count_lock:
                        self.tx_count += 1

