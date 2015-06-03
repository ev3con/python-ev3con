import time
from ev3.lego import *
from ev3.ev3dev import NoSuchMotorError,NoSuchSensorError
from multiprocessing import Process, Queue

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
		maxval: Maximalwert
		"""
		self.kp=kp
		self.ki=ki
		self.kd=kd
		self.antiwindup=0 #Begrenzen des Integralteils(wenn antiwindup>0)
		self._int_sum=0 #Integralsumme
		self._old=0     #vorheriger Fehler
		self._clock_old=0
		self.avgsize=1
		self.maxval=0
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
		if self.maxval:
			if out>self.maxval : 
				out=self.maxval
			elif  out< -self.maxval : 
				out= -self.maxval
		return out
	@property
	def avgsize(self):
		return self.avgsize
	@avgsize.setter
	def avgsize(self,size):
		if size<=1: self._d_avg=None
		size=int(size)
		self._d_avg=RunningAverage(size)

class DistKeep(UltrasonicSensor):
	"""Berechnet die noetige Aenderung der Geschwindigkeit(dv) um einen konkreten Abstand(soll) einzuhalten"""
	def __init__(self,soll,port_us,kp,ki=0,kd=0,max_dist=2550,**kwargs):
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
		self.max_dist=max_dist
		UltrasonicSensor.__init__(self,int(port_us))
	@property
	def dv(self):
		"""noetige Geschwindigkeitsaenderung"""
		ist=self.dist_cm
		if ist>self.max_dist :
			ist=self.soll
		if ist<-self.max_dist :
			ist = -self.soll
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
	def __init__(self,soll,port_cs,kp,ki=0,kd=0,avgsize=1,**kwargs):
		"""
		INIT-PARAM:
		soll: Soll-Grauwert
		kp,ki,kd:Konstanten des PID-Reglers
		port_cs:Port des FarbSensors
		avgsize: zu mittelnde Farbwerte( koennte sinnvoll sein wg Schwankungen)
		"""
		#~ MotorControl.__init__(self,port_m)
		self._pid=PID(kp,ki,kd,**kwargs)
		BetterColorSensor.__init__(self,port_cs)
		self.grey_soll=soll
		#~ self.avgsize=avgsize
	
	@property
	def dv(self):
		"""noetige Geschwindigkeitsaenderung"""
		
		grey=self.grey
		
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
	margin: Maximalwert Geschwindigkeit (mit Speedregulation)
	motors: Dictionary mit den jeweiligen Motoren(value) und Ports(key)
	"""
	def __init__(self,avg_speed,all_ports=None,**kwargs):
		"""INIT-Argument: 
			ports: Liste/String der Ports der anzuschliessenden Motoren(default:None -> Alle verfuegbaren werden angeschlossen 
			avg_speed: Mittlere Geschwindigkeit an den Motoren
		"""
		self.avg_speed=avg_speed
		self.margin=2000 # 
		self.motors = {}
		self.inverted=False
		if not all_ports :
			self.attach_all_motors()
		else:
			for port in all_ports:
				try :
					motor = Motor(port=port)
					self.motors[port]=motor
				except NoSuchMotorError:
					print("Kein Motor an "+port+" gefunden")
		for k in kwargs:
			v = kwargs[k]
			if (v != None):
				setattr(self, k, v)		
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
	"""Kontrolliert die Geschwindigkeit(Multithreading) der einzelnen Motoren um einen Abstand und die Linie zu halten, erweitert MotorControl
	INIT-PARAM:
	
	"""
	def __init__(self,dist_set,line_set,left_ports,right_ports,avg_speed,**kwargs):
				
		MotorControl.__init__(self,avg_speed)
				
		self.left = []
		self.right = []
		for l in left_ports:
			self.left.append(l)
		for r in right_ports:
			self.right.append(r)
		self.line = LineKeep(**line_set)
		self.dist = DistKeep(**dist_set)
		
	def start(self):
		
		#~ self.run = True
		dv_dist= Queue(1)
		dv_line= Queue(1)
		
		self.process_l = Process(target = self.run_line,args = [self.line,dv_line])
		self.process_d = Process(target = self.run_dist,args = [self.dist,dv_dist])
		self.process_s = Process(target = self.run_speed,args = [dv_dist,dv_line])
		self.process_s.start()
		self.process_l.start()
		self.process_d.start()
		
		
	def stop(self):
		#~ self.run=False
		self.process_d.terminate()
		self.process_l.terminate()
		self.process_s.terminate()
		self.stop_motors()
		
	def run_dist(self,distkeep,conn):
		#~ print('ne')
		while  True:
			
			dv=distkeep.dv
			if conn.empty() :
				print('dv')
				conn.put(dv)
			
	def run_line(self,linekeep,conn):
		while True:
			dv=linekeep.dv
			if conn.empty() : conn.put(dv)
			
	def run_speed(self,conn_d,conn_l):
		dv_d=0
		dv_l=0
		while True:
			if not conn_d.empty(): 
				dv_d = conn_d.get()
				print(dv_d)
			if not conn_l.empty(): dv_l = conn_l.get()
			#~ print('l')
			self.set_speed(-dv_d-dv_l,self.left)
			self.set_speed(-dv_d+dv_l,self.right)
		#~ self.terminate()
