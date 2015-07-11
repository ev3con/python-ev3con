import sys, time, argparse, socket, netifaces

if __name__ == "__main__":
    parser = argparse.ArgumentParser( sys.argv[0] )
    parser.add_argument( "-iface", dest="iface", type=str, default="wlan0" )
    args = parser.parse_args( sys.argv[1:] )

    sock = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
    sock.setsockopt(socket.SOL_SOCKET, socket.SO_BROADCAST, 1)
    sock.bind(("0.0.0.0",5005))
    sock.settimeout(0.25)

    broadcast = netifaces.ifaddresses(iface)[netifaces.AF_INET][0]["broadcast"]
    platoon = []

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

            mesg = mesg.split(":")

            if not mesg[0] == "ACK":
                mesg = "ACK"
                sock.sendto(mesg, (addr[0],5005))
                print "Gesendet [" + str((time.time() - lasttime) * 1000) + "ms] an " + addr[0] + ": '" + mesg + "'"
                lasttime = time.time()

            elif mesg[0] == "WHOS" and leader == None:
                if addr[0] in platoon:
                    platoon.remove(addr[0])
                    platoon.append(addr[0])

            elif mesg[0] == "BARRIER":
                mesg = "STOP:" + ":".join( platoon[platoon.index(addr[0]):] )
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
