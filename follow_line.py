# follow_line.py - Automatische Linienverfolung mit Abstandshaltung
# 9. Juni 2015 - Patrick Ziegler, TU Dresden
#
# Dieses Skript stellt einen Machbarkeitstest der gleichzeitigen
# Regelung von Linienverfolgung und Abstandshaltung dar. Es wurde
# nicht die Library von topikatchu, sondern 'python-ev3dev' von
# Denis Demidov verwendet!
# Ein Schleifenzyklus dauert in der Regel 7-8 ms, in unregelmaessigen
# Abstaenden dauert der Schleifendurchlauf bis zu 40 ms.
#
# Beispielhafte Verwendung:
# python follow_line.py --Vref 350 --lKp 2 --lKd 8 --dKp 3

import sys, time, traceback, argparse
from ev3dev import *

class PID:
    def __init__(self, Kp=0.0, Ki=0.0, Kd=0.0):
        self.Kp = Kp
        self.Ki = Ki
        self.Kd = Kd
        self.lasterror = 0.0
        self.integral = 0.0
        self.derivative = 0.0
        self.correction = 0.0

    def calc(self, error, limit=None):
        self.integral = 0.5 * self.integral + error
        self.derivative = error - self.lasterror
        self.preverr = error
        self.correction = self.Kp * error + self.Ki * self.integral + self.Kd * self.derivative

        if limit == None:
            return self.correction

        if abs(self.corr_line) < abs(limit):
            return self.correction

        return (self.correction / abs(self.correction)) * limit

if __name__ == "__main__":
    sound.beep()
    start_t = 0.0

    parser = argparse.ArgumentParser(sys.argv[0])
    parser.add_argument('--Vref', dest='Vref', type=float, default=350)
    parser.add_argument('--lKp', dest='lKp', type=float, default=2.0)
    parser.add_argument('--lKi', dest='lKi', type=float, default=0.0)
    parser.add_argument('--lKd', dest='lKd', type=float, default=8.0)
    parser.add_argument('--dKp', dest='dKp', type=float, default=3.0)
    parser.add_argument('--dKi', dest='dKi', type=float, default=0.0)
    parser.add_argument('--dKd', dest='dKd', type=float, default=0.0)
    args = parser.parse_args(sys.argv[1:])

    pid_line = PID(args.lKp, args.lKi, args.lKd)
    pid_dist = PID(args.dKp, args.dKi, args.dKd)
    corr_line = 0.0
    corr_dist = 0.0

    ml = large_motor(OUTPUT_A)
    mr = large_motor(OUTPUT_B)
    ml.polarity = 'inversed'
    mr.polarity = 'inversed'
    ml.speed_regulation_enabled = 'on'
    mr.speed_regulation_enabled = 'on'

    cs = color_sensor()
    cs.mode = 'COL-REFLECT'
    colmax = 55 # Reflexion auf Tisch, ermittelt in BAR I/48
    colmin = 5 # Reflexion auf Linie, ermittelt in BAR I/48

    us = ultrasonic_sensor()
    us.mode = 'US-DIST-CM'
    distref = 200

    try:
        ml.run_forever(speed_sp=int(args.Vref))
        mr.run_forever(speed_sp=int(args.Vref))

        while True:
            start_t = time.time()

            # die Farbwerte werden automatisch auf Bereich [0,100] abgebildet, Differzenz zu 50 ist Fehler fuer PID
            corr_line = pid_line.calc( 50 - ( ( cs.value() - colmin ) / ( colmax - colmin ) ) * 100, 2*args.Vref )
            corr_dist = pid_dist.calc( distref - us.value(), 2*args.Vref )

            # es soll nicht auf Hindernis zubeschleunigt werden
            if corr_dist < 0:
                corr_dist = 0

            if corr_line > 0: # im dunklen Bereich
                ml.run_forever( speed_sp = int( args.Vref - corr_dist ) )
                mr.run_forever( speed_sp = int( args.Vref - corr_dist - corr_line ) )
            elif corr_line < 0: # im hellen Bereich
                ml.run_forever( speed_sp = int( args.Vref - corr_dist + corr_line ) )
                mr.run_forever( speed_sp = int( args.Vref - corr_dist ) )

            print "Zyklusdauer: " + str(time.time() - start_t) + "s"

    except:
        ml.stop()
        mr.stop()

        print traceback.format_exc()
        print "Programm wurde beendet"
