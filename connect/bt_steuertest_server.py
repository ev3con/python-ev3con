import time
from connect import *

tgl = True
bth = BTHost()

print "Server gestartet"

while True:
    bth.accept_requests()

    start_time = time.time()
    if tgl:
        bth.send2all("on")
    else:
        bth.send2all("off")
    end_time = time.time()

    print "Sendezeit: " + str( end_time - start_time ) + " Sekunden"
    tgl = not tgl
    time.sleep(0.5)
