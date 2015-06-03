import time
import bluetooth

port = 1
tgl = True
server = bluetooth.BluetoothSocket(bluetooth.RFCOMM)
server.bind(("", port))
server.listen(1)
server.setblocking(False)
peers = []

while True:
    try:
        bufsock, bufaddr = server.accept()
        peers.append(bufsock)
        print "Neue Verbindung erstellt (Anzahl: %f)" % len(peers)
    except:
        print "Nichts anliegend"
        pass

    start_time = time.time()

    if tgl:
        for p in peers:
            p.send("on")
    else:
        for p in peers:
            p.send("off")

    end_time = time.time()

    print "%f" % ( end_time - start_time )

    tgl = not tgl

    time.sleep(0.5)
