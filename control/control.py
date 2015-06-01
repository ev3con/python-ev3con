import time
from ev3.lego import *
from ev3.ev3dev import NoSuchMotorError,NoSuchSensorError


class RunningAverage(object):
	"""Klasse zur Berechnung des laufenden Mittelwertes von avg_size vielen  Werten"""
	def __init__(self,avg_size):
		if avg_size<1 : avg_size=1
		self.avg=avg_size*[0]
		self._count=0
	def calc(self,val):
		self.avg[self._count]=val
		self._count+=1
		if self._count>=len(self.avg): 
			self._count=0
		return sum(self.avg)/len(self.avg)

class PID(object):
	"""PID-Controller mit wahlweise Antiwindup und Mittelung von beliebig vielen Differentialwerten"""
	def __init__(self,kp=0,ki=0,kd=0,**kwargs):
		"""
		Init-Argumente:
		kp: Proportionalkonstante (default=0)
		ki: Integralkonstante (default=0)
		kd: Differentialkonstante (default=0)
		
		zusaetzlich moegliche Keyword Argumente:
		antiwindup: Begrenzen des Integralanteils (default=0)
		avgsize: Anzahl der zumittelnden Differentialwerte (default=1)
		"""
		self.kp=kp
		self.ki=ki
		self.kd=kd
		self.antiwindup=0 #Begrenzen des Integralteils(wenn antiwindup>0)
		self._int_sum=0 #Integralsumme
		self._old=0     #vorheriger Fehler
		self._clock_old=0
		self.avgsize=1
		for k in kwargs:
			v = kwargs[k]
			if (v != None):
				setattr(self, k, v)						
	def calc(self,ist,soll):
		"""
		Berechnet den Stellwert
		
		Keyword Argumente:
		ist: Momentanwert
		soll:Sollwert
		
		returns: float
		"""
		clock=time.clock()
		dt=(clock-self._clock_old)*1000 #da ansonsten sehr klein
		error=soll-ist 
		#Integral
		i=self._int_sum+error*dt
		self.int_sum=i
		if self.antiwindup!=0:
			if i>self.antiwindup : 
				i=self.antiwindup
			elif i < -self.antiwindup : 
				i= -self.antiwindup
	    #Differential
		d=(error-self._old)/dt
		if self._d_avg:
			d=self._d_avg.calc(d)
		out=self.kp*error+self.ki*i+self.kd*d
		self._clock_old=clock
		self._old=error
		return out
	@property
	def avgsize(self):
		return self.avgsize
	@avgsize.setter
	def avgsize(self,size):
		if size<=1: self._d_avg=None
		self._d_avg=RunningAverage(size)

class DistKeep(UltrasonicSensor):
	"""Berechnet die noetige Aenderung der Geschwindigkeit(dv) um einen konkreten Abstand(soll) einzuhalten"""
	def __init__(self,soll,kp,ki=0,kd=0,port_us=-1,max_dist=2550,**kwargs):
		"""
		INIT-Argumente:
		soll: gewollter Abstand
		kp: Proportionalkonstante 
		ki: Integralkonstante (default=0)
		kd: Differentialkonstante (default=0)
		port_us: Port des Ultraschallsensors(default=-1 -> Autodetect)
		max_dist: Entfernungen ueber diesem Wert werden ignoriert!(Default: 2550)
		 """
		#~ MotorControl.__init__(self,port_m)
		self.soll = soll
		#print(kwargs)
		self.pid=PID(kp,ki,kd,**kwargs)
		UltrasonicSensor.__init__(self,port_us)
	@property
	def dv(self):
		"""noetige Geschwindigkeitsaenderung"""
		ist=self.dist_cm
		if ist>self.max_dist :
			ist=self.soll
		speed=self.pid.calc(ist,self.soll)
		return int(speed)
	def set_pid(self,**kwargs):
		"""PID-Regler einstellen
		Argumente(sh PID): ki,kp,kd,antiwindup,avgsize """
		for k in kwargs:
			v = kwargs[k]
			if (v != None):
				setattr(self.pid, k, v)
class BetterColorSensor(ColorSensor):
	"""Erweitert die Attribute des Farbsensors"""
	def __init__(self,port=-1,avgsize=1):
		ColorSensor.__init__(self,port)
		self.avg_r=RunningAverage(avgsize)
		self.avg_g=RunningAverage(avgsize)
		self.avg_b=RunningAverage(avgsize)
		
	
	@property
	def grey(self):
		"""gibt den Grauwert aus"""
		return sum(self.rgb)/3
	
	@property
	def color_str(self):
		"""gibt die Farbe als String zurueck nicht als int"""
		return self.colors(self.color)
	
	
	@property
	def avgsize(self):
		"""Anzahl der zu mittelnden Messwerte"""
		return self._avgsize
	@avgsize.setter
	def avgsize(self,size):
		self._avgsize=size
		self.avg_r=RunningAverage(size)
		self.avg_g=RunningAverage(size)
		self.avg_b=RunningAverage(size)
	@property
	def rgb_avg(self):
		"""mittlere RGB"""
		avg_r=self.avg_r.calc(self.rgb[0])
		avg_g=self.avg_g.calc(self.rgb[1])
		avg_b=self.avg_b.calc(self.rgb[2])
		return (avg_r,avg_g,avg_b)		
	@property
	def grey_avg(self):
		"""mittleren Grauwert"""
		return sum(self.rgb_avg)/3
	
class LineKeep(BetterColorSensor):
	"""Berechnet die noetige Aenderung der Geschwindigkeit(dv) um auf der Linie zu bleiben"""
	def __init__(self,kp,ki=0,kd=0,port_cs=-1,avgsize=1):
		"""
		INIT-PARAM: 
		kp,ki,kd:Konstanten des PID-Reglers
		port_cs:Port des FarbSensors
		avgsize: zu mittelnde Farbwerte( koennte sinnvoll sein wg Schwankungen)
		"""
		#~ MotorControl.__init__(self,port_m)
		self._pid=PID(kp,ki,kd)
		BetterColorSensor.__init__(self,port_cs)
		self.grey_soll=self.grey
		self.avgsize=avgsize
	
	@property
	def dv(self):
		"""noetige Geschwindigkeitsaenderung"""
		if self.avgsize==1:
			grey=self.grey
		else:
			grey=self.grey_avg
		speed=self._pid.calc(grey,self.grey_soll)
		#print(speed)
		return int(speed)
	
	def set_pid(self,**kwargs):
		"""PID-Regler einstellen
		Argumente(sh PID): ki,kp,kd,antiwindup,avgsize """
		for k in kwargs:
			v = kwargs[k]
			if (v != None):
				setattr(self._pid, k, v)

	
class MotorControl(object):
	"""Klasse zum Verbinden und Ansteueren mehrere Motoren gleichzeitg
	
	Attribute:
	avg_speed: Mittlere Geschwindigkeit an den Motoren
	margin: Maximalwert Geschwindigkeit (mit Speedregulation)
	motors: Dictionary mit den jeweiligen Motoren(value) und Ports(key)
	"""
	def __init__(self,ports=None):
		"""INIT-Argument: 
			ports: Liste/String der Ports der anzuschliessenden Motoren(default:None -> Alle verfuegbaren werden angeschlossen 
		"""
		self.avg_speed=0
		self.margin=2000 # 
		self.motors = {}
		self.inverted=False
		if not ports :
			self.attach_all_motors()
		else:
			for port in ports:
				try :
					motor = Motor(port=port)
					self.motors[port]=motor
				except NoSuchMotorError:
					print("Kein Motor an "+port+" gefunden")
				
	def set_speed(self,sp,ports=None):
		"""setzt eine Geschwindigkeit(additiv zur mittleren) und schreibt den Wert an bestimmte/alle Motoren
		
		Keyword Argumente:
		sp=zu setzende Geschwindigkeit
		ports= Portliste/string der anzusteuernden Motoren
		"""
		sp+=self.avg_speed
		if self.inverted : sp=-sp
		if sp > self.margin:
			sp=self.margin
		elif sp< -self.margin:
			sp=self.margin
		if not ports: 
			for m in self.motors.itervalues():
				m.run_forever(sp,speed_regulation=True)
		else :
			try:
				for p in ports:
					print(p)
					self.motors[p].run_forever(sp,speed_regulation=True)
			except KeyError: 
				print("Kein Motor an "+p+" gefunden")
				
	def attach_all_motors(self):
		"""Motoren an allen  Ports finden"""
		self.motors={}
		for port in 'ABCD':
			try:
				motor = Motor(port=port)
				motor.speed_regulation = True	
				self.motors[port]=motor
				break
			except NoSuchMotorError: pass
	def stop_motors(self,ports=None):
		"""Stopt alle Motoren
		
		Keyword Argument:
		ports= Portliste/string der anzusteuernden Motoren
		"""
		if not ports: 
			for m in self.motors.itervalues():
				m.stop()
		else :
			try:
				for p in ports:
					self.motors[p].stop()
			except KeyError:
				print("Kein Motor an "+p+" gefunden")

class TotalControl(MotorControl):
	"""Kontrolliert die Geschwindigkeit der einzelnen Motoren um einen Abstand und die Linie zu halten, erweitert MotorControl"""
	def __init__(self,dist_set,line_set,port_ml,port_mr,ports_m=None,**kwargs):		
		MotorControl.__init__(self,ports_m)
		self.left=()
		self.right=()
		for l in port_ml:
			self.left.append(self.motors[l])
		for r in port_mr:
			self.right.append(self.motors[r])
		line=LineKeep(**line_set)
		dist=DistKeep(**dist_set)
	
	def run(self,r_of_line=True):
		if r_of_line:
			dv_r=-dist.dv-line.dv
			dv_l=-dist.dv+line.dv
		if l_of_line:
			dv_r=-dist.dv+line.dv
			dv_l=-dist.dv-line.dv
		set_speed(sp=dv_l,ports=left)
		set_speed(sp=dv_r,ports=right)

	
