# platooning_server.py - Externer Server fuer Betrieb des Konvoys im Platooning-Modus
# 2015-07-13 - Hauptseminar IT - Lukas Egge, Justus Rischke, Tobias Waurick, Patrick Ziegler - TU Dresden

import sys, time, argparse, socket, netifaces
from autonomes_fahren_platooning import tell, order

if __name__ == "__main__":
    parser = argparse.ArgumentParser( sys.argv[0] )
    parser.add_argument( "-iface", dest="iface", type=str, default="wlan0" )
    parser.add_argument( "-timeout", dest="timeout", type=float, default=0.25 )
    args = parser.parse_args( sys.argv[1:] )

    # Socket erstellen und an eigene IPs (inkl. Broadcast) binden
    sock = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
    sock.setsockopt(socket.SOL_SOCKET, socket.SO_BROADCAST, 1)
    sock.bind(("0.0.0.0",5005))
    sock.settimeout(args.timeout)

    # Adressvariablen erstellen und Leader finden, falls vorhanden
    broadcast = netifaces.ifaddresses(args.iface)[netifaces.AF_INET][0]["broadcast"]
    ownaddr = netifaces.ifaddresses(args.iface)[netifaces.AF_INET][0]["addr"]
    platoon = []
    if tell(sock, ownaddr, broadcast, "WHOS"):
        print "Es existiert bereits ein Leader des Platoons!"
        sys.exit(1)

    lasttime = time.time()

    try:
        while True:
            # Nachricht empfangen
            try:
                mesg, addr = sock.recvfrom(255)
            except socket.timeout:
                mesg = "None"
                addr = "None"

            print "Empfangen [" + str((time.time() - lasttime) * 1000) + "ms] von " + addr[0] + ": '" + mesg + "'"
            lasttime = time.time()

            # Nachricht auswerten
            if not addr[0] == ownaddr and not mesg == "None":
                mesg = mesg.split(":")

                if mesg[0] == "WHOS":
                    sock.sendto("ACK", (addr[0],5005))
                    if addr[0] in platoon:
                        platoon.remove(addr[0])
                    platoon.append(addr[0])

                elif mesg[0] == "BARRIER":
                    sock.sendto("ACK", (addr[0],5005))
                    order(sock, ownaddr, broadcast, platoon, "STOP:" + ":".join(platoon[platoon.index(addr[0])+1:]))

                elif mesg[0] == "PATHCLEAR":
                    sock.sendto("ACK", (addr[0],5005))
                    order(sock, ownaddr, broadcast, platoon, "START:" + ":".join(platoon[platoon.index(addr[0]):]))

                elif mesg[0] == "QUIT":
                    sys.exit(1)

    except (KeyboardInterrupt, SystemExit):
        sock.close()
        print "Programm wird beendet"
