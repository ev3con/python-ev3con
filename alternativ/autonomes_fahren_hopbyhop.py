import sys, argparse, socket, time
from multiprocessing import Process
from ev3.ev3dev import Motor
from autonomes_fahren import *

def wait(duration=0.03):
    while True:
        time.sleep(duration)

def send(sock, ip="127.0.0.1", mesg="spameggsausageandspam", tries=3):
    for i in range(0,tries):
        sock.sendto(mesg, (ip,5005))
        try:
            mesg, addr = sock.recvfrom(1024)
        except socket.timeout:
            pass
        if mesg.startswith("ACK"):
            return

# Beim Aufruf uebergebene Argumente verarbeiten
parser = argparse.ArgumentParser( sys.argv[0] )
parser.add_argument( "-Vref", dest="Vref", type=float, default=350 )
parser.add_argument( "-colmax", dest="colmax", type=float, default=63.0 )
parser.add_argument( "-colmin", dest="colmin", type=float, default=7.0 )
parser.add_argument( "-distref", dest="distref", type=float, default=30.0 ) # Abstand in cm
parser.add_argument( "-lKp", dest="lKp", type=float, default=3.5 )
parser.add_argument( "-lKi", dest="lKi", type=float, default=0.0 )
parser.add_argument( "-lKd", dest="lKd", type=float, default=2.0 )
parser.add_argument( "-dKp", dest="dKp", type=float, default=30.0 )
parser.add_argument( "-dKi", dest="dKi", type=float, default=0.0 )
parser.add_argument( "-dKd", dest="dKd", type=float, default=0.0 )
#parser.add_argument( "-pos", dest="pos", type=float, default=1 )
parser.add_argument( "-purs_ip", dest="purs_ip", type=str, default="127.0.0.1" )
args = parser.parse_args( sys.argv[1:] )
fl_args = (args.Vref, args.colmax, args.colmin, args.distref, args.lKp, args.lKi, args.lKd, args.dKp, args.dKi, args.dKd)

# IP-Adresse des Verfolgers berechnen
# purs_ip = "10.42.1.1" + str( int( args.pos - 1 ) )
purs_ip = args.purs_ip

# Socket erstellen und an eigene IP binden
sock = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
sock.setsockopt(socket.SOL_SOCKET, socket.SO_BROADCAST, 1)
sock.bind(("0.0.0.0", 5005))
sock.settimeout(0.25)

# Fahrt beginnen, Steuerungsprozess wird parallel gestartet
p = Process( name="follow_line", target=follow_line, args=fl_args )
p.start()

# Vielleicht muessen Motoren manuell gestoppt werden
ml = Motor(port=Motor.PORT.A)
mr = Motor(port=Motor.PORT.B)

is_follower = False # vlt. besser True?

# Endlosschleife, darin erfolgt die Kommunikation und die Verwaltung des Steuerungsprozesses
while True:
    try:
        mesg, addr = sock.recvfrom(1024)
    except socket.timeout:
        mesg = "Nothing"

    print "Empfangen: " + mesg

    if mesg.startswith("STOP"):
        sock.sendto("ACK", (addr[0],5005))
        if p.name == "follow_line":
            p.terminate()
            is_follower = True
            ml.stop()
            mr.stop()

    elif mesg.startswith("START"):
	p.terminate()
	p = Process( name="follow_line", target=follow_line, args=fl_args )
	p.start()
	send(sock, purs_ip, "START", 3)
    else:
        pass

    # Der Steuerungsprozess wird ggf. mit Warteprozess ausgetauscht, wenn Hindernis vorhanden
    if not p.is_alive():
        if p.name == "follow_line":
            # Hindernis im Weg, sende STOP
            send(sock, purs_ip, "STOP", 3)

            if is_follower:
                # Warten, bis START empfangen
                p = Process(name="wait", target=wait, args=(0.03,))
                p.start()
            else:
                # Warten, bis Hindernis verschwunden
                p = Process(name="wait_barrier", target=wait_barrier, args=(args.distref,))
                p.start()

        else:
            # Hindernis ist weg, sende START
            p = Process(name="follow_line", target=follow_line, args=fl_args)
            p.start()

            send(sock, purs_ip, "START", 3)

