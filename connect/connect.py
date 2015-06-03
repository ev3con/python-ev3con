import bluetooth

class BTserver:
    def __init__(self, port=1):
        self.server = bluetooth.BluetoothSocket(bluetooth.RFCOMM)
        self.server.bind(("", port))
        self.server.listen(8)
        self.peers = []

    def accept_forever(self):
        while True:
            self.peers.append( self.server.accept() )

    def send2all(self, data):
        for p in self.peers:
            p.send(data)

    # Vorerst spricht nur der Server zum Client
    # def receive_all(self, size=1024):
    #     return self.client.recv(size)

    def close(self):
        self.server.close()
        for p in self.peers:
            p.close()

class BTclient:
    def __init__(self):
        self.socket = bluetooth.BluetoothSocket(bluetooth.RFCOMM)

    def connect2server(self, sname="btserver", port=1, timeout=5):
        btdev = bluetooth.discover_devices(duration=timeout, lookup_names=True)

        for dev in btdev:
            if dev[1] == sname:
                self.socket.connect((dev[0], port))
                return

    # Vorerst spricht nur der Server zum Client
    # def send(self, data):
    #     self.socket.send(data)

    def receive(self, size=1024):
        return self.socket.recv(size)

    def close(self):
        self.socket.close()
