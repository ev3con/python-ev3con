from connect import *

bts = BTserver()

#try:
while True:
    data = bts.receive()
    print type(data)
    print data

#except:
#    bts.close()
