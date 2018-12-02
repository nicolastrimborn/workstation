#!/usr/bin/env python

#Declaration of the libraries
import requests
import sys
import time
import json
#import explorerhat

#Import of the libraries for multithreading
from threading import Thread

#Print the system version
print (sys.version)

#Declaration of the global variables
Mode = 0
Workstation = []
State = "Idle"
Alarm = "No alarm"

#Class to create a thread for running parallel applications
class CreateThread(Thread):
		
	#Constructor of the class with a Thread_name and default parameters for a Workstation
	def __init__(self, Thread_Name):
		Thread.__init__(self)
		self.Thread_Name = Thread_Name
		self.touched = [False] * 8
		
	#Main method of the thread for choosing the behaviour
	def run(self):
		#if self.Thread_Name=="ActionsHandler":
		#	self.ActionsHandler()
		if self.Thread_Name=="RequestsPoster":
			self.RequestsPoster()
		
	#Main method for handle the actions
	#def ActionsHandler(self):
		#self.traffic()
		#explorerhat.touch.pressed(self.explorerhat_handler)
		#explorerhat.touch.released(self.explorerhat_handler)
		#explorerhat.pause()
			
	#Main method for posting the message
	def RequestsPoster(self):
	
		#Process running in a parallel thread
		while True:
		
			#Post request
			try:
				#r = requests.post("http://127.0.0.1:5000/monitoring", json={"state":State, "workstation":Workstation, "time":time.time()})
				r = requests.post("http://127.0.0.1:5000/workstation/state", json={"state":State})
				time.sleep(0.2)
				r = requests.post("http://127.0.0.1:5000/workstation/event", json={"event":Alarm})
			except:
				print("Server not connected at 127.0.0.1, posting thread aborted, the workstation runs standalone !")
								
			#Set the polling time
			time.sleep(2)
		
	#Function to manage the traffic of the lights depending on the current state
	def traffic(self):
		""""if State=="Idle":
			explorerhat.light[1].on()
			explorerhat.light[2].off()
			explorerhat.light[3].off()
		elif State=="Error":
			explorerhat.light[1].off()
			explorerhat.light[2].blink(0.5, 0.5)
			explorerhat.light[3].off()
		elif State=="Working":
			explorerhat.light[1].off()
			explorerhat.light[2].off()
			explorerhat.light[3].blink(1, 1)
				
	#Handler of the explorerhat		
	def explorerhat_handler(self, channel, event):
	
		#Declaration of the variables used as global variables, needs to be precised explicitely in Python
		global Mode
		global Workstation
		global State
		global Alarm
			
		#Specify the touch event
		self.touched[channel - 1] = True

		#Check for a press event
		if (event=="press"):

			#Check if we press the first button
			if channel==1:
			
				#Check the three possible modes for the button
				Mode = Mode + 1
				if Mode > 2:
					Mode = 0
				
				#Print and inform about the current mode of the button
				if Mode==0:
					print("Current actions of the main button : B2 = Add spring ; B3 = Add cylinder ; B4 = Add valve")
				elif Mode==1:
					print("Current actions of the main button : B2 = Force Idle ; B3 = Force Error ; B4 = Force Working")
				elif Mode==2:
					print("Current actions of the main button : B2 = Remove ; B3 = No action ; B4 = Reset system")
					
			#Check if we press the second button
			elif channel==2:
				if Mode==0:
					print("Add a spring")
					if (len(Workstation)) < 5:
						Workstation.append("Spring")
					else:
						print("Impossible to add a pallet, the workstation is full !")
					State = "Working"
					self.traffic()
				elif Mode==1:
					print("Force the state to Idle")
					State = "Idle"
					self.traffic()
				elif Mode==2:
					if (len(Workstation))==0:
						print("Impossible to remove a pallet because the workstation is empty !")
					else:
						print("Remove a pallet")
						Workstation.pop(0)
					if (len(Workstation))==0:
						State = "Idle"
						self.traffic()
					else:
						State = "Working"
						self.traffic()

			#Check if we press the third button
			elif channel==3:
				if Mode==0:
					print("Add a cylinder")
					if (len(Workstation)) < 5:
						Workstation.append("Cylinder")
					else:
						print("Impossible to add a pallet, the workstation is full !")
					State = "Working"
					self.traffic()
				elif Mode==1:
					print("Force the state to Error")
					State = "Error"
					self.traffic()

			#Check if we press the fourth button
			elif channel==4:
				if Mode==0:
					print("Add a valve")
					if (len(Workstation)) < 5:
						Workstation.append("Valve")
					else:
						print("Impossible to add a pallet, the workstation is full !")
					State = "Working"
					self.traffic()
				elif Mode==1:
					print("Force the state to Working")
					State = "Working"
					self.traffic()
				elif Mode==2:
					print("Reset the whole system, pallets removed and station goes into Idle state")
					State = "Idle"
					Workstation = []
					self.traffic()

		#Check for a release event
		if (event=="release"):
			self.touched[0] = False
			self.touched[1] = False
			self.touched[2] = False
			self.touched[3] = False
			self.touched[4] = False
			self.touched[5] = False
			self.touched[6] = False
			self.touched[7] = False

"""			
# Creation of the threads (Thread_Name)
#thread_1 = CreateThread("ActionsHandler")
thread_2 = CreateThread("RequestsPoster")

# Starting of the threads
#thread_1.start()
thread_2.start()

# Wait for the ending of the threads
#thread_1.join()
thread_2.join()