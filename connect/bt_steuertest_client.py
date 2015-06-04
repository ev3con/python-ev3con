import time
from connect import *
from ev3.ev3dev import LED

# Host ist:
# thinkpat - 88:9F:FA:F0:C0:88

btc = BTClient()
btc.connect("thinkpat")

led = LED()
led.left.color=LED.COLOR.GREEN
time.sleep(0.25)
led.left.color=LED.COLOR.RED
time.sleep(0.25)
led.left.off()

print "Beginne Empfang"

while True:
    data = btc.receive()

    if data == "on":
        led.left.on()
    else if data == "off":
        led.left.off()
    else if data == None:
        print "Verbindung zu Server verloren!"
        exit()
