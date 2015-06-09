import sys, time, traceback, argparse, math
from ev3dev import *

class PID:
    def __init__(self, Kp=0.0, Ki=0.0, Kd=0.0):
        self.Kp = Kp
        self.Ki = Ki
        self.Kd = Kd
        self.lasterror = 0.0
        self.integral = 0.0
        self.derivative = 0.0
        self.corr_follow = 0.0

    def calc(self, error, limit=None):
        self.integral = 0.5 * self.integral + error
        self.derivative = error - self.lasterror
        self.preverr = error
        self.corr_follow = self.Kp * error + self.Ki * self.integral + self.Kd * self.derivative

        if limit == None:
            return self.corr_follow

        if abs(self.corr_follow) < abs(limit):
            return self.corr_follow

        return (self.corr_follow / abs(self.corr_follow)) * limit

if __name__ == "__main__":
    sound.beep()
    start_t = 0.0

    parser = argparse.ArgumentParser(sys.argv[0])
    parser.add_argument('--Vref', dest='Vref', type=float, default=300)
    parser.add_argument('--fKp', dest='fKp', type=float, default=4.0)
    parser.add_argument('--fKi', dest='fKi', type=float, default=0.0)
    parser.add_argument('--fKd', dest='fKd', type=float, default=9.0)
    parser.add_argument('--dKp', dest='dKp', type=float, default=0.0)
    parser.add_argument('--dKi', dest='dKi', type=float, default=0.0)
    parser.add_argument('--dKd', dest='dKd', type=float, default=0.0)
    args = parser.parse_args(sys.argv[1:])

    pid_follow = PID(args.fKp, args.fKi, args.fKd)
    pid_dist = PID(args.dKp, args.dKi, args.dKd)
    corr_follow = 0.0
    corr_dist = 0.0

    ml = large_motor(OUTPUT_A)
    mr = large_motor(OUTPUT_B)
    ml.polarity = 'inversed'
    mr.polarity = 'inversed'
    ml.speed_regulation_enabled = 'on'
    mr.speed_regulation_enabled = 'on'

    cs = color_sensor()
    cs.mode = 'COL-REFLECT'
    colref = 18

    us = ultrasonic_sensor()
    us.mode = 'US-DIST-CM'
    distref = 20

    try:
        ml.run_forever(speed_sp=int(args.Vref))
        mr.run_forever(speed_sp=int(args.Vref))

        while True:
            start_t = time.time()

            corr_follow = pid_follow.calc(colref - cs.value(), 2*args.Vref)
            corr_dist = pid_dist.calc(distref - us.value(), 2*args.Vref)

            if corr_dist > 0:
                corr_dist = 0

            if corr_follow > 0: # im dunklen Bereich
                ml.run_forever( speed_sp = int(args.Vref - corr_dist) )
                mr.run_forever( speed_sp = int(args.Vref - corr_dist - corr_follow) )
            elif corr_follow < 0: # im hellen Bereich
                ml.run_forever( speed_sp = int(args.Vref - corr_dist + corr_follow) )
                mr.run_forever( speed_sp = int(args.Vref - corr_dist) )

            print "Schleifendauer: " + str(time.time() - start_t) + "s"

    except:
        ml.stop()
        mr.stop()

        print traceback.format_exc()
        print "Programm wurde beendet"
