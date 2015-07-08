import sys, argparse, socket
from multiprocessing import Process
from ev3.ev3dev import Motor
from autonomes_fahren import *

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
parser.add_argument( "-ip", dest="ip", type=str, default="127.0.0.1" )
args = parser.parse_args( sys.argv[1:] )
fl_args = (args.Vref, args.colmax, args.colmin, args.distref, args.lKp, args.lKi, args.lKd, args.dKp, args.dKi, args.dKd)

# IP-Adresse des Verfolgers berechnen
purs_ip = args.ip.split(".")
purs_ip = purs_ip[0] + "." + purs_ip[1] + "." purs_ip[2] + "." + str( abs( int(purs_ip[3] - 1 ) )

# Socket erstellen und an eigene IP binden
sock = socket.socket(type=socket.SOCK_DGRAM)
sock.bind((args.ip, 5005))
sock.settimeout(0.6)

# Fahrt beginnen, Steuerungsprozess wird parallel gestartet
p = Process( name="follow_line", target=follow_line, args=fl_args)
p.start()

# Vielleicht muessen Motoren manuell gestoppt werden
# ml = Motor(port=Motor.PORT.A)
# mr = Motor(port=Motor.PORT.B)

# Endlosschleife, darin erfolgt die Kommunikation und die Verwaltung des Steuerungsprozesses
while True:
    try:
        mesg, addr = sock.recvfrom(1024)
    except socket.timeout:
        mesg = "Nothing"

    # Falls kein ACK empfangen wurde, gehen wir von einem STOP aus
    if not mesg.startswith("ACK") and mesg != "Nothing":
        sock.sendto("ACK", addr)
        if p.name() == "follow_line":
            p.terminate()
            # ml.stop()
            # mr.stop()

    # Der Steuerungsprozess wird ggf. mit Warteprozess ausgetauscht, wenn Hindernis vorhanden
    if not p.is_alive():
        if p.name() == "follow_line":

            # Drei Versuche, ein STOP an den Verfolger zu senden
            for i in range(0,3):
                sock.sendto("STOP", (purs_ip, 5005))

                try:
                    mesg, addr = sock.recvfrom(1024)
                except socket.timeout:
                    pass

                if mesg.startswith("ACK"):
                    break

            # Warteprozess wird gestartet; dieser wartet, bis Hindernis verschwindet
            p = Process(name="wait_barrier", target=wait_barrier, args=(0.5*args.distref,))
            p.start()

        else:
            # Hindernis ist weg (den Warteprozess war tot), es kann weitergefahren werden
            p = Process(name="follow_line", target=follow_line, args=fl_args)
            p.start()

