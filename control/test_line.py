import unittest
from control import *
from ev3.ev3dev import Key, Lcd
from PIL import Image,ImageDraw,ImageFont
#from util import get_input

class TestOr(unittest.TestCase):
	def test_line(self):
		print('TEST: LINIE FOLGEN')
		k=Key()
		l=Lcd()
		raw_input('Linker Motor an A, rechter an B,Farbsensor an 4?')
		left='A'
		right='B'
		font = ImageFont.load_default()
		#m=MotorControl(right) 
		m=MotorControl(left+right)
		#m.inverted=True
		m_avg_speed=int(raw_input('Mittlere Geschwindigkeit der Motoren\n'))
		print(type(m_avg_speed))
		kp=float(raw_input('KP?\n'))
		ki=float(raw_input('KI?\n'))
		kd=float(raw_input('KD?\n'))
		avg=int(raw_input('Wie viele Farbwerte mitteln?\n'))
		line=LineKeep(kp,ki,kd,4,avg)
		print('USB-Kabel entfernen und RECHTS neben die Linie setzen,sh EV3-Display!')
		l.draw.text((10, 10), "Test: Linie folgen  ", font=font)
		l.draw.text((10, 50), "Start:Nach oben Taste", font=font)
		l.draw.text((10, 90), "Ende : Nach untenTaste", font=font)
		while(True):
			l.update()
			if k.up:break
		m.avg_speed=m_avg_speed
		while(True):
			if k.down:
				l.draw.text((10, 10), "Test beendet  ", font=font)
				m.stop_motors()
				l.update()
				break
			dv=line.dv
			
			l.reset()
			l.draw.text((10, 10), "delta_v:", font=font)
			l.draw.text((10, 30), str(dv), font=font)
			l.update()
		
			m.set_speed(dv,left)
			m.set_speed(-dv,right)
if __name__ == '__main__':
	unittest.main()

