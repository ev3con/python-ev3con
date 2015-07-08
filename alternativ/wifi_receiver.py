import sys, argparse, socket

parser = argparse.ArgumentParser(sys.argv[0])
parser.add_argument("-ip", dest="LISTEN_IP", type=str, default="127.0.0.1")
args = parser.parse_args(sys.argv[1:])

sock = socket.socket(type=socket.SOCK_DGRAM)
sock.bind((args.LISTEN_IP, 5005))

print "Empfang wird gestartet"

try:
    while True:
        data, addr = sock.recvfrom(1024)
        print data + " " + str(addr)
except:
    print "Programm wird beendet"

