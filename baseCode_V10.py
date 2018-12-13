#!/usr/bin/env python

'''
AL0 = Trigger an alarm every time the workstation goes to error - pi
AL1 = Trigger an event everytime the workstation starts or gets reset - pi
AL2 = If the workstation has 5 pallets trigger an alarm - pi
AL3 = If the workstation has 6 pallets trigger an alarm - pi
'''

#Declaration of the libraries
import requests
import sys
import time
import json
import explorerhat

#Print the system version
print (sys.version)

#Declaration of the endpoints
StateEP="http://192.168.0.11:5000/workstation/state"
PalletsEP="http://192.168.0.11:5000/workstation/pallets"
EventEP="http://192.168.0.11:5000/workstation/event"
ErrorMsg="Server not connected at 192.168.0.11:5000, posting thread aborted, the workstation runs standalone !"

#Declaration of the global variables
FlagInitialization = True
Workstation = []
State = "Idle"
Alarms = ["The system has gone into error state !",
"The system has gone into idle state !",
"The system has 5 pallets on his workstation !",
"The system is full and has 6 pallets on his workstation !"]

#Initialization of the buttons
touched = [False] * 8

#Function to initialize the behaviour of the Raspberry pi
def initialization():
	postingmessage()
	sendalarm(1)
	
#Function to manage the traffic of the lights depending on the current state
def traffic(State):
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
	global Workstation
	global State
	
	#Posting the messages when the function is called
	try:
		r = requests.post(StateEP, json={"state":State})
		r = requests.post(PalletsEP, json={"workstation":Workstation})
		print("Message posted")
	except:
		print(ErrorMsg)
		
#Function to send an alarm
def sendalarm(alID):
	r = requests.post(EventEP, json={"AlarmID":alID,"AlarmText":Alarms[alID]})

#Function to count the number of elements in the workstation
def countingElements():

	#Declqrqtion of the global variable
	global Workstation
	
	#Initialize the counting elements
	s, c, v = 0, 0, 0
	
	#Iterate over the eleöents and count it
	for i in range(len(Workstation)):
		if Workstation[i] == "Spring":
			s = s + 1
		elif Workstation[i] == "Cylinder":
			c = c + 1
		elif Workstation[i] == "Valve":
			v = v + 1
	
	#Return the result of the counting
	return [s, c, v, s+c+v]
			
	
#Handler of the explorerhat		
def explorerhat_handler(channel, event):

	#Declaration of the variables used as global variables, needs to be precised explicitely in Python
	global Workstation
	global State

	#Specify the touch event
	touched[channel - 1] = True

	#Check for a press event
	if (event=="press"):

		#Check if we press the first button
		if channel==1:
			print("Reset the whole system, pallets removed and station goes into Idle state")
			if State!="Idle":
				sendalarm(1)
			State = "Idle"
			Workstation = []
			postingmessage()
			traffic(State)
		#Check if we press the second button
		elif channel==2:
			print("Force the state to Idle")
			if State!="Idle":
				sendalarm(1)
			State = "Idle"
			postingmessage()
			traffic(State)
		elif channel==3:
			print("Force the state to Error")
			if State!="Error":
				sendalarm(0)
			State = "Error"
			postingmessage()
			traffic(State)
		elif channel==4:
			print("Force the state to Working")
			State = "Working"
			postingmessage()
			traffic(State)
		elif channel==5:
			print("Add a spring")
			if (len(Workstation)) < 6:
				Workstation.append("Spring")
				if (len(Workstation)) == 5:
					sendalarm(2)
				if (len(Workstation)) == 6:
					sendalarm(3)
			else:
				print("Impossible to add a pallet, the workstation is full !")
			State = "Working"
			postingmessage()
			traffic(State)
		elif channel==6:
			print("Add a cylinder")
			if (len(Workstation)) < 6:
				Workstation.append("Cylinder")
				if (len(Workstation)) == 5:
					sendalarm(2)
				if (len(Workstation)) == 6:
					sendalarm(3)
			else:
				print("Impossible to add a pallet, the workstation is full !")
			State = "Working"
			postingmessage()
			traffic(State)
		elif channel==7:
			print("Add a valve")
			if (len(Workstation)) < 6:
				Workstation.append("Valve")
				if (len(Workstation)) == 5:
					sendalarm(2)
				if (len(Workstation)) == 6:
					sendalarm(3)
			else:
				print("Impossible to add a pallet, the workstation is full !")
			State = "Working"
			postingmessage()
			traffic(State)
		elif channel==8:
			if (len(Workstation))==0:
				print("Impossible to remove a pallet because the workstation is empty !")
			else:
				print("Remove a pallet")
				Workstation.pop(0)
			if (len(Workstation))==5:
				sendalarm(2)
			if (len(Workstation))==0:
				if State!="Idle":
					sendalarm(1)
				State = "Idle"
				postingmessage()
				traffic(State)
			else:
				State = "Working"
				postingmessage()
				traffic(State)

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

if FlagInitialization:
	initialization()
	FlagInitialization = False
	
traffic(State)
explorerhat.touch.pressed(explorerhat_handler)
explorerhat.touch.released(explorerhat_handler)
explorerhat.pause()