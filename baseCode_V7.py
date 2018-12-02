#!/usr/bin/env python

#Declaration of the libraries
import requests
import sys
import time
import json
import explorerhat

#Print the system version
print (sys.version)

#Declaration of the global variables
Mode = 0
Workstation = []
State = "Idle"
		
#Initialization of the buttons
touched = [False] * 8
		
#Function to manage the traffic of the lights depending on the current state
def traffic():
	if State=="Idle":
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

#Function to post the message
def postingmessage():
	
	#Declaration of the variables used as global variables, needs to be precised explicitely in Python
	global Mode
	global Workstation
	global State
	
	try:
		r = requests.post("http://192.168.0.11:5000/workstation/state", json={"state":State})
		r = requests.post("http://192.168.0.11:5000/workstation/pallets", json={"workstation":Workstation})
		print("Message posted")
	except:
		print("Server not connected at 192.168.0.11:5000, posting thread aborted, the workstation runs standalone !")
				
#Handler of the explorerhat		
def explorerhat_handler(channel, event):

	#Declaration of the variables used as global variables, needs to be precised explicitely in Python
	global Mode
	global Workstation
	global State

	#Specify the touch event
	touched[channel - 1] = True

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
				if (len(Workstation)) < 6:
					Workstation.append("Spring")
				else:
					print("Impossible to add a pallet, the workstation is full !")
				State = "Working"
				postingmessage()
				traffic()
			elif Mode==1:
				print("Force the state to Idle")
				State = "Idle"
				postingmessage()
				traffic()
			elif Mode==2:
				if (len(Workstation))==0:
					print("Impossible to remove a pallet because the workstation is empty !")
				else:
					print("Remove a pallet")
					Workstation.pop(0)
				if (len(Workstation))==0:
					State = "Idle"
					postingmessage()
					traffic()
				else:
					State = "Working"
					postingmessage()
					traffic()

		#Check if we press the third button
		elif channel==3:
			if Mode==0:
				print("Add a cylinder")
				if (len(Workstation)) < 6:
					Workstation.append("Cylinder")
				else:
					print("Impossible to add a pallet, the workstation is full !")
				State = "Working"
				postingmessage()
				traffic()
			elif Mode==1:
				print("Force the state to Error")
				State = "Error"
				postingmessage()
				traffic()

		#Check if we press the fourth button
		elif channel==4:
			if Mode==0:
				print("Add a valve")
				if (len(Workstation)) < 6:
					Workstation.append("Valve")
				else:
					print("Impossible to add a pallet, the workstation is full !")
				State = "Working"
				postingmessage()
				traffic()
			elif Mode==1:
				print("Force the state to Working")
				State = "Working"
				postingmessage()
				traffic()
			elif Mode==2:
				print("Reset the whole system, pallets removed and station goes into Idle state")
				State = "Idle"
				Workstation = []
				postingmessage()
				traffic()

	#Check for a release event
	if (event=="release"):
		touched[0] = False
		touched[1] = False
		touched[2] = False
		touched[3] = False
		touched[4] = False
		touched[5] = False
		touched[6] = False
		touched[7] = False

traffic()
explorerhat.touch.pressed(explorerhat_handler)
explorerhat.touch.released(explorerhat_handler)
explorerhat.pause()