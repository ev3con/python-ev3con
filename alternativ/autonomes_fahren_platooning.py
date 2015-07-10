import sys, time, argparse, socket, netifaces
from multiprocessing import Process
from autonomes_fahren import *

def wait(cycledelay=0.03):
    while True:
        time.sleep(cycledelay)

if __name__ == "__main__":
    parser = argparse.ArgumentParser( sys.argv[0] )
    parser.add_argument( "-Vref", dest="Vref", type=float, default=350 )
    parser.add_argument( "-colmax", dest="colmax", type=float, default=63.0 )
    parser.add_argument( "-colmin", dest="colmin", type=float, default=7.0 )
    parser.add_argument( "-distref", dest="distref", type=float, default=30.0 )         # Abstand in cm
    parser.add_argument( "-waitmax", dest="waitmax", type=float, default=1.0 )          # Maximale Zuckelzeit
    parser.add_argument( "-cycledelay", dest="cycledelay", type=float, default=0.0 )    # zur Verlaengerung der Zyklusdauer
    parser.add_argument( "-lKp", dest="lKp", type=float, default=3.5 )
    parser.add_argument( "-lKi", dest="lKi", type=float, default=0.0 )
    parser.add_argument( "-lKd", dest="lKd", type=float, default=2.0 )
    parser.add_argument( "-dKp", dest="dKp", type=float, default=30.0 )
    parser.add_argument( "-dKi", dest="dKi", type=float, default=0.0 )
    parser.add_argument( "-dKd", dest="dKd", type=float, default=0.0 )
    parser.add_argument( "-iface", dest="iface", type=str, default="wlan0" )
    args = parser.parse_args( sys.argv[1:] )

    # Sammlung der Argumente fuer die Funktion follow_line
    follow_line_args = (args.Vref, args.colmax, args.colmin, args.distref, args.waitmax, args.cycledelay, args.lKp, args.lKi, args.lKd, args.dKp, args.dKi, args.dKd)

    # Socket erstellen und an eigene IPs (inkl. Broadcast) binden
    sock = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
    sock.setsockopt(socket.SOL_SOCKET, socket.SO_BROADCAST, 1)
    sock.bind((socket.INADDR_ANY,5005))
    sock.settimeout(0.25)

    # Adressvariablen erstellen und Leader finden, falls vorhanden
    broadcast = netifaces.ifaddresses(args.iface)[netifaces.AF_INET][0]["broadcast"]
    ownaddr = netifaces.ifaddresses(args.iface)[netifaces.AF_INET][0]["addr"]
    leader = socket.sendto("WHOS", (broadcast,5005))[1][0]
    platoon = []

    # Fahrt beginnen, dazu wird Steuerungsprozess parallel gestartet
    p = Process(name="follow_line", target=follow_line, args=follow_line_args)
    p.start()

    try:
        # Endlosschleife, darin erfolgt die Kommunikation und die Verwaltung des Steuerungsprozesses
        while True:
            try:
                mesg, addr = sock.recvfrom(255)
            except socket.timeout:
                mesg = "None"

            print "Empfangene Nachricht: " + mesg

            mesg = mesg.split(":")

            if mesg[0] == "STOP" and ownaddr in mesg:
                if p.name == "follow_line":
                    p.terminate()
                    stop_all_motors()
                    p = Process(name="wait", target=wait, args=(0.03,))
                    p.start()

            elif mesg[0] == "START" and ownaddr in mesg:
                if not p.name == "follow_line":
                    p.terminate()
                    p = Process(name="follow_line", target=follow_line, args=follow_line_args)
                    p.start()

            elif mesg[0] == "WHOS" and leader == None:
                if not addr[0] in platoon:
                    platoon.append(addr[0])

            elif mesg[0] == "BARRIER":
                socket.sendto("STOP:" + ":".join(platoon(platoon.index(addr[0])+1:)), (broadcast,5005))

            # Der Steuerungsprozess wird ggf. mit Warteprozess ausgetauscht, wenn Hindernis vorhanden
            if not p.is_alive():
                if p.name == "follow_line":
                    if leader == None:
                        sock.sendto("STOP:" + ":".join(platoon), (broadcast,5005))
                        p = Process(name="wait_barrier", target=wait_barrier, args=(args.distref,))
                        p.start()
                    else:
                        sock.sendto("BARRIER", (leader,5005))
                        p = Process(name="wait", target=wait, args=(0.03,))
                        p.start()

                elif p.name == "wait_barrier":
                    p = Process(name="follow_line", target=follow_line, args=follow_line_args)
                    p.start()
                    sock.sendto("START:" + ":".join(platoon), (broadcast,5005))

    except (KeyboardInterrupt, SystemExit):
        sock.close()
        p.terminate()
        stop_all_motors()
        print "Programm wurde beendet"
