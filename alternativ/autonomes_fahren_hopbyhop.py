import sys, time, argparse, socket, netifaces
from multiprocessing import Process
from autonomes_fahren import *

def wait(cycledelay=0.03):
    while True:
        time.sleep(cycledelay)

def send(sock, ip="127.0.0.1", mesg="spameggsausageandspam", tries=3):
    for i in range(0,tries):
        sock.sendto(mesg, (ip,5005))
        try:
            mesg, addr = sock.recvfrom(1024)
        except socket.timeout:
            pass
        if mesg.startswith("ACK"):
            return

if __name__ == "__main__":
    parser = argparse.ArgumentParser( sys.argv[0] )
    parser.add_argument( "-Vref", dest="Vref", type=float, default=350 )
    parser.add_argument( "-colmax", dest="colmax", type=float, default=63.0 )
    parser.add_argument( "-colmin", dest="colmin", type=float, default=7.0 )
    parser.add_argument( "-distref", dest="distref", type=float, default=30.0 ) # Abstand in cm
    parser.add_argument( "-waitmax", dest="waitmax", type=float, default=1.0 )
    parser.add_argument( "-cycledelay", dest="cycledelay", type=float, default=0.0 )
    parser.add_argument( "-lKp", dest="lKp", type=float, default=3.5 )
    parser.add_argument( "-lKi", dest="lKi", type=float, default=0.0 )
    parser.add_argument( "-lKd", dest="lKd", type=float, default=2.0 )
    parser.add_argument( "-dKp", dest="dKp", type=float, default=30.0 )
    parser.add_argument( "-dKi", dest="dKi", type=float, default=0.0 )
    parser.add_argument( "-dKd", dest="dKd", type=float, default=0.0 )
    parser.add_argument( "-pursuer", dest="pursuer", type=str, default=None )
    args = parser.parse_args( sys.argv[1:] )

    # Sammlung der Argumente fuer die Funktion follow_line
    follow_line_args = (args.Vref, args.colmax, args.colmin, args.distref, args.waitmax, args.cycledelay, args.lKp, args.lKi, args.lKd, args.dKp, args.dKi, args.dKd)

    # Socket erstellen und an eigene IPs (inkl. Broadcast) binden
    sock = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
    sock.setsockopt(socket.SOL_SOCKET, socket.SO_BROADCAST, 1)
    sock.bind(("0.0.0.0", 5005))
    sock.settimeout(0.25)

    # IP-Adresse des Verfolgers bestimmen, falls nicht explizit angegeben
    if args.pursuer == None:
        try:
            args.pursuer = netifaces.ifaddresses("wlan0")[netifaces.AF_INET][0]["addr"].split(".")
            args.pursuer = args.pursuer[0] + "." + args.pursuer[1] + "." + args.pursuer[2] + "." + str( int( args.pursuer[3]) + 1 )
        except IndexError:
            print "Kann Adresse des Verfolgers nicht bestimmen!"
            sys.exit(1)

    # Fahrt beginnen, dazu wird Steuerungsprozess parallel gestartet
    p = Process(name="follow_line", target=follow_line, args=follow_line_args)
    p.start()

    # Endlosschleife, darin erfolgt die Kommunikation und die Verwaltung des Steuerungsprozesses
    while True:
        try:
            mesg, addr = sock.recvfrom(16)
        except socket.timeout:
            mesg = "None"

        print "Empfangene Nachricht: " + mesg

        if mesg.startswith("STOP") and p.name == "follow_line":
            p.terminate()
            stop_all_motors()
            p = Process(name="wait", target=wait, args=(0.03,))
            p.start()

        elif mesg.startswith("START") and p.name == "wait"
            p.terminate()
            p = Process(name="follow_line", target=follow_line, args=follow_line_args)
            p.start()

        if not mesg.startswith("ACK"):
            sock.sendto("ACK", (addr[0],5005)) # vlt. geht auch sock.sendto("ACK", addr) ?
            send(sock, args.pursuer, mesg, 3)

        # Der Steuerungsprozess wird ggf. mit Warteprozess ausgetauscht, wenn Hindernis vorhanden
        if not p.is_alive():
            if p.name == "follow_line":
                send(sock, args.pursuer, "STOP", 3)

                # Warten, bis Hindernis verschwunden
                p = Process(name="wait_barrier", target=wait_barrier, args=(args.distref,))
                p.start()

            elif p.name == "wait_barrier"::
                # Hindernis ist weg, sende START
                p = Process(name="follow_line", target=follow_line, args=follow_line_args)
                p.start()

                send(sock, args.pursuer, "START", 3)
