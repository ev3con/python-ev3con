# platooning_server.py - Externer Server fuer Betrieb des Konvoys im Platooning-Modus
# 2015-07-13 - Hauptseminar IT - Lukas Egge, Justus Rischke, Tobias Waurick, Patrick Ziegler - TU Dresden

import sys, time, argparse, socket, netifaces

if __name__ == "__main__":
    parser = argparse.ArgumentParser( sys.argv[0] )
    parser.add_argument( "-iface", dest="iface", type=str, default="wlan0" )
    parser.add_argument( "-timeout", dest="timeout", type=float, default=0.25 )
    args = parser.parse_args( sys.argv[1:] )

    sock = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
    sock.setsockopt(socket.SOL_SOCKET, socket.SO_BROADCAST, 1)
    sock.bind(("0.0.0.0",5005))
    sock.settimeout(args.timeout)

    broadcast = netifaces.ifaddresses(iface)[netifaces.AF_INET][0]["broadcast"]
    ownaddr = broadcast = netifaces.ifaddresses(iface)[netifaces.AF_INET][0]["addr"]
    platoon = []
    try:
        sock.sendto("WHOS", (broadcast,5005))
        mesg, addr = sock.recvfrom(255)
        if addr[0] == ownaddr:
            mesg, addr = sock.recvfrom(255)
        if mesg.startswith("ACK"):
            print "Es existiert bereits ein Leader des Konvoys!"
            sys.exit(1)
    except socket.timeout:
        pass

    lasttime = time.time()

    try:
        while True:
            try:
                mesg, addr = sock.recvfrom(255)
            except socket.timeout:
                mesg = "None"
                addr = "None"

            print "Empfangen [" + str((time.time() - lasttime) * 1000) + "ms] von " + addr[0] + ": '" + mesg + "'"
            lasttime = time.time()

            if not addr[0] == ownaddr and not mesg == "None":
                mesg = mesg.split(":")

                elif mesg[0] == "WHOS" and leader == None:
                    sock.sendto("ACK", (addr[0],5005))
                    if addr[0] in platoon:
                        platoon.remove(addr[0])
                    platoon.append(addr[0])
                    print "Gesendet [" + str((time.time() - lasttime) * 1000) + "ms] an " + addr[0] + ": 'ACK'"
                    lasttime = time.time()

                elif mesg[0] == "BARRIER":
                    mesg = "STOP:" + ":".join( platoon[platoon.index(addr[0])+1:] )
                    sock.sendto(mesg, (broadcast,5005))
                    print "Gesendet [" + str((time.time() - lasttime) * 1000) + "ms] an " + broadcast + ": '" + mesg + "'"
                    lasttime = time.time()

                elif mesg[0] == "PATHCLEAR":
                    mesg = "START:" + ":".join( platoon[platoon.index(addr[0]):] )
                    sock.sendto(mesg, (broadcast,5005))
                    print "Gesendet [" + str((time.time() - lasttime) * 1000) + "ms] an " + broadcast + ": '" + mesg + "'"
                    lasttime = time.time()

    except (KeyboardInterrupt, SystemExit):
        sock.close()
        print "Programm wird beendet"
