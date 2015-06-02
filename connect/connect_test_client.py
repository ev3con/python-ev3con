import time
from connect import *

btc = BTclient("88:9F:FA:F0:C0:88")
zahl = 0.0

#try:
while True:
    btc.send("Test eins zwo %f" % zahl )
    zahl = zahl + 1
    time.sleep(1)

#except:
#    btc.close()
