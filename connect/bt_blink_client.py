import time
import bluetooth
from ev3.ev3dev import LED

sname = "88:9F:FA:F0:C0:88"
port = 1

socket = bluetooth.BluetoothSocket(bluetooth.RFCOMM)
btdev = bluetooth.discover_devices(duration=5, lookup_names=True)
for dev in btdev:
    if dev[0] == sname:
        while True:
            try:
                socket.connect((sname, port))
                print "Verbunden mit " + dev[0] + " an Port " + str(port)
                break
            except:
                port = port + 1

led = LED()
led.left.color=LED.COLOR.RED
led.left.off()

print "Beginne Empfang"

try:
    while True:
        data = socket.recv(1024)

        print "Empfangene Botschaft: " + data

        if data == "on":
            led.left.on()
        else:
            led.left.off()

except:
    print "Verbindung zu Server verloren!"
