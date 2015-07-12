# autonomes_fahren_hopbyhop.py - Linienverfolgung des Konvoys mit Kommunikation benachbarter Fahrzeuge
# 2015-07-13, Hauptseminar IT, Lukas Egge, Justus Rischke, Tobias Waurick, Patrick Ziegler - TU Dresden

import sys, time, argparse, socket, netifaces
from multiprocessing import Process
from ev3.ev3dev import Tone
from autonomes_fahren import *

def propagate(sock, dest_addr="127.0.0.1", dest_mesg="spameggsausageandspam", tries=3):
    from_mesg = ""
    from_addr = [""]

    for i in range(0,tries):
        sock.sendto(dest_mesg, (dest_addr,5005))
        try:
            from_mesg, from_addr = sock.recvfrom(255)
        except socket.timeout:
            pass
        if from_mesg.startswith("ACK"):
            return from_addr[0]

    for i in range(0,tries):
        sock.sendto("LOST:" + dest_addr, (dest_addr,5005))
        try:
            from_mesg, from_addr = sock.recvfrom(255)
        except socket.timeout:
            pass
        if from_mesg.startswith("ACK"):
            return send(sock, dest_addr, dest_mesg, 3)

    return None

if __name__ == "__main__":
    parser = argparse.ArgumentParser( sys.argv[0] )
    parser.add_argument( "-Vref", dest="Vref", type=float, default=350 )
    parser.add_argument( "-colmax", dest="colmax", type=float, default=63.0 )           # Reflexionswert auf Hintergrund
    parser.add_argument( "-colmin", dest="colmin", type=float, default=7.0 )            # Reflexionswert auf Linie
    parser.add_argument( "-distref", dest="distref", type=float, default=20.0 )         # Abstand in cm
    parser.add_argument( "-waitmax", dest="waitmax", type=float, default=0.5 )          # Maximale Zuckelzeit in Sekunden
    parser.add_argument( "-cycledelay", dest="cycledelay", type=float, default=0.0 )    # Verlaengerung der Zyklusdauer in Sekunden
    parser.add_argument( "-lKp", dest="lKp", type=float, default=3.5 )
    parser.add_argument( "-lKi", dest="lKi", type=float, default=0.0 )
    parser.add_argument( "-lKd", dest="lKd", type=float, default=2.0 )
    parser.add_argument( "-dKp", dest="dKp", type=float, default=30.0 )
    parser.add_argument( "-dKi", dest="dKi", type=float, default=0.0 )
    parser.add_argument( "-dKd", dest="dKd", type=float, default=0.0 )
    parser.add_argument( "-iface", dest="iface", type=str, default="wlan0" )
    parser.add_argument( "-timeout", dest="timeout", type=float, default=0.25 )         # Standardtimeout des sockets
    parser.add_argument( "-start_idle", dest="start_idle", action="store_true", default=False )
    args = parser.parse_args( sys.argv[1:] )

    # Sammlung der Argumente fuer die Funktion follow_line
    follow_line_args = (args.Vref, args.colmax, args.colmin, args.distref, args.waitmax, args.cycledelay, args.lKp, args.lKi, args.lKd, args.dKp, args.dKi, args.dKd)

    # Socket erstellen und an eigene IPs (inkl. Broadcast) binden
    sock = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
    sock.setsockopt(socket.SOL_SOCKET, socket.SO_BROADCAST, 1)
    sock.bind(("0.0.0.0",5005))
    sock.settimeout(args.timeout)

    # Adressvariablen erstellen und Vordermann finden, falls vorhanden
    broadcast = netifaces.ifaddresses(args.iface)[netifaces.AF_INET][0]["broadcast"]
    ownaddr = netifaces.ifaddresses(args.iface)[netifaces.AF_INET][0]["addr"]
    frontaddr = send(sock, broadcast, "WHOS", 3)
    backaddr = None

    hupe = Tone()

    # Falls die Option start_idle nicht gesetzt ist, fahre direkt los
    if not args.start_idle:
        p = Process(name="follow_line", target=follow_line, args=follow_line_args)
        p.start()
    else:
        p = Process(name="wait", target=time.sleep, args=(0.1,))
        p.start()

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

                if len(mesg) < 2:
                    mesg.append("")

                if mesg[0] == "STOP":
                    sock.sendto("ACK", (addr[0],5005))
                    if p.name == "follow_line":
                        p.terminate()
                        stop_all_motors()
                        p = Process(name="wait", target=time.sleep, args=(0.1,))
                        p.start()
                    if not backaddr == None:
                        backaddr = propagate(sock, backaddr, "STOP")
                    hupe.play(440,500)

                elif mesg[0] == "START":
                    sock.sendto("ACK", (addr[0],5005))
                    if p.name == "wait":
                        p = Process(name="follow_line", target=follow_line, args=follow_line_args)
                        p.start()
                    if not backaddr == None:
                        backaddr = propagate(sock, backaddr, "START")

                elif mesg[0] == "LOST" and frontaddr == mesg[1]:
                    sock.sendto("ACK", (addr[0],5005))
                    frontaddr = addr[0]

                elif mesg[0] == "WHOS" and backaddr == None:
                    sock.sendto("ACK", (addr[0],5005))
                    backaddr = addr[0]

            # Steuerungsprozess ggf. mit Warteprozess austauschen, wenn Hindernis vorhanden
            if not p.is_alive():
                if p.name == "follow_line":
                    if not backaddr == None:
                        backaddr = propagate(sock, backaddr, "STOP")

                    p = Process(name="wait_barrier", target=wait_barrier, args=(args.distref,1))
                    p.start()

                elif p.name == "wait_barrier":
                    p = Process(name="follow_line", target=follow_line, args=follow_line_args)
                    p.start()

                    if not backaddr == None:
                        backaddr = propagate(sock, backaddr, "START")

    except (KeyboardInterrupt, SystemExit):
        sock.close()
        p.terminate()
        stop_all_motors()
        print "Programm wurde beendet"
