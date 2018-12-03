'''
Trigger an alarm every time the workstation goes to error - pi
Trigger an event everytime the workstation starts or gets reset - pi
If the workstation has 5 pallets trigger an alarm - pi
If the workstation has 6 pallets trigger an alarm - pi
If the workstation is y amount of time idle, trigger an alarm - server
If the workstation is x amount of time idle, trigger an alarm - server
'''

from flask import Flask, render_template
from flask import request
import json
from datetime import datetime
import sqlite3
import time

#Import of the libraries for multithreading
from threading import Thread

timeEachState = {"idle":0, "working":0, "error":0}

timeX = 5
timeY = 10

app = Flask(__name__)
conn = sqlite3.connect(':memory:', check_same_thread=False)
c = conn.cursor()

c.execute("""CREATE TABLE workstation (
	        Key INTEGER PRIMARY KEY,
	        State TEXT,
	        Time TIMESTAMP 
            )""")

c.execute("""CREATE TABLE workstation_pallets (
	        Slot INTEGER PRIMARY KEY,
	        Content TEXT
            )""")

c.execute("""CREATE TABLE event (
            Key INTEGER PRIMARY KEY,
	        AlarmID INTEGER,
	        Event TEXT,
	        Time TIMESTAMP
            )""")

# Adds 6 fixed rows
for i in range(6):
    with conn:
        c.execute("INSERT INTO workstation_pallets VALUES ("+str(i)+", null)")

#Class to create a thread for running parallel applications
class CreateThread(Thread):

    #Constructor of the class with a Thread_name and default parameters for a Workstation
    def __init__(self, Thread_Name):
        Thread.__init__(self)
        self.Thread_Name = Thread_Name

    #Main method of the thread for choosing the behaviour
    def run(self):
        if self.Thread_Name=="Thread1":

            @app.route('/<string:page_name>/')
            def static_page(page_name):
                allowed_pages = ['index', 'polling', 'robots', 'state', 'events', 'dashboard']
                if page_name in allowed_pages:
                    return render_template('{0}.html'.format(page_name))
                else:
                    return render_template('error.html'), 404

            # Handler for post state from raspberry pie.  Message format eg. json={"state":"Working"}
            @app.route('/workstation/state', methods=['POST','GET'])
            def stateHandler():

                global timeEachState

                # Function to add a state to the SQL table
                def addStateSQL(state, time):
                    # previousState = getCurrentState
                    # if(previousState[0][0] != state):
                    # with conn:
                    c.execute("INSERT INTO workstation VALUES (null, :State, :Time)", {'State': state,'Time':time})

                # Function to get the last state on the SQL table
                def getStateFromSQL():
                    c = conn.cursor()
                    # c.execute("SELECT * FROM workstation WHERE State=:state", {'state': 'Idle'})
                    # c.execute("SELECT * FROM workstation WHERE 1")
                    c.execute("SELECT * FROM workstation ORDER BY Key DESC LIMIT 1")
                    return c.fetchall()

                # Handle the GET and POST requests and update the HMI
                if request.method=='POST':
                    content = request.json
                    print ("(Post Req) Updated State recieved: ", content)
                    newState=content["state"]
                    #now = datetime.datetime.now()
                    #time= now.isoformat()
                    time= datetime.now().isoformat()
                    addStateSQL(newState, time)
                    cnvMsg = {'state': newState, 'serverTime':time}
                    cnvMsg_str = json.dumps(cnvMsg)
                    #if Flag:
                    #    #Specialcomputation for the beggining
                    #else:
                    #    #Normalcomputation
                    #    Flag=False
                    #    timeEachState[newState] = timeEachState[newState] + time
                    return cnvMsg_str
                elif request.method=='GET':
                    #print ("(GET Request) Workstation State:")
                    time = datetime.now().isoformat()
                    cnvMsg = getStateFromSQL()
                    cnvMsg_str = json.dumps(cnvMsg)
                    return cnvMsg_str

            @app.route('/workstation/pallets', methods=['POST','GET'])
            def WorkstationHandler():

                def get_Pallets():
                    c = conn.cursor()
                    c.execute("SELECT * FROM workstation_pallets")
                    return c.fetchall()

                def updatePallets(PalletsArray):
                    with conn:
                        for i in range(6):
                            try:
                                c.execute("UPDATE workstation_pallets SET Content = :Contents WHERE Slot =:Index", {'Contents': PalletsArray[i], 'Index': i})

                            except:
                                c.execute("UPDATE workstation_pallets SET Content = :Contents WHERE Slot =:Index", {'Contents': 'Empty', 'Index': i})

                if request.method=='POST':
                    content = request.json
                    PalletsArray=content["workstation"]
                    print(PalletsArray)
                    updatePallets(PalletsArray)
                    time= datetime.now().isoformat()
                    cnvMsg = {'workstation': 'empty','serverTime':time}
                    cnvMsg_str = json.dumps(cnvMsg)
                    return cnvMsg_str
                elif request.method=='GET':
                    cnvMsg = get_Pallets()
                    cnvMsg_str = json.dumps(cnvMsg)
                    #print(cnvMsg)
                    return cnvMsg_str

            #Message format eg. json={"event":"Error State"}
            @app.route('/workstation/event', methods=['POST','GET'])
            def eventHandler():
                def addEventSQL(alID, alarmText, time):
                    with conn:
                        c.execute("INSERT INTO event VALUES (null, :AlarmID, :Event, :Time)", {'AlarmID': alID, 'Event': alarmText, 'Time':time})

                def getEventFromSQL():
                    c = conn.cursor()
                    c.execute("SELECT * FROM event")
                    return c.fetchall()

                if request.method=='POST':
                    content = request.json
                    print ("(Post Req) New Event: " , content)
                    alarmID = content["AlarmID"]
                    AlarmText = content["AlarmText"]
                    time = datetime.now().isoformat()
                    addEventSQL(alarmID, AlarmText, time)
                    cnvMsg = {'alarmID': alarmID, 'event': AlarmText, 'serverTime':time}
                    cnvMsg_str = json.dumps(cnvMsg)
                    return cnvMsg_str

                elif request.method=='GET':
                    #print ("(Get Req) Send WS Events:")
                    cnvMsg = getEventFromSQL()
                    cnvMsg_str = json.dumps(cnvMsg)
                    #print(cnvMsg)
                    return cnvMsg_str

            if __name__ == '__main__':
                app.run(host= '192.168.0.11')
                #app.run(host= '127.0.0.1')
                conn.close()

        elif self.Thread_Name=="Thread2":
            self.checkTimeInState()

    def checkTimeInState(self):

        global timeX
        global timeY

        def get_last_item(table, selectColumn, sortBy):
            c = conn.cursor()
            c.execute("SELECT "+selectColumn+" FROM "+table+" ORDER BY "+sortBy+" DESC LIMIT 1")
            return c.fetchall()

        def getCurrentTime():
            return get_last_item('workstation','*','time')

        while True:
            getCurrentTime()
            try:
                if(getCurrentTime()[0][1] != "Working"):
                    currentTime = datetime.strptime(datetime.now().isoformat(),'%Y-%m-%dT%H:%M:%S.%f')
                    lastStateTime = datetime.strptime(getCurrentTime()[0][2],'%Y-%m-%dT%H:%M:%S.%f')
                    if((currentTime - lastStateTime).seconds > timeX ):


            except:
                print("stuck")
            time.sleep(1)

# Creation of the threads (Thread_Name)
thread_1 = CreateThread("Thread1")
thread_2 = CreateThread("Thread2")

# Starting of the threads
thread_1.start()
thread_2.start()

# Wait for the ending of the threads
thread_1.join()
thread_2.join()