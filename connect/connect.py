import bluetooth

class BTserver:
    def __init__(self, port=1):
        self.server = bluetooth.BluetoothSocket(bluetooth.RFCOMM)
        self.server.bind(("", port))
        self.server.listen(1);
        self.client, self.addr= self.server.accept()

    def receive(self, size=1024):
        print "Empfange Daten von ", self.addr
        return self.client.recv(size), "hi"

    def close(self):
        self.client.close()
        self.server.close()

class BTclient:
    def __init__(self, addr, port=1):
        self.socket = bluetooth.BluetoothSocket(bluetooth.RFCOMM)
        self.socket.connect((addr, port))

    def send(self, data):
        self.socket.send(data)

    def close(self):
        self.socket.close()
