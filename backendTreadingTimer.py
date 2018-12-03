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
import threading

#timeEachState = {"idle":0, "working":0, "error":0}
ArrayStates=[]
ArrayTimes=[]
StatesProportions=[]

timeX = 2
timeY = 3
timeExceeded = False

serverAlarms = ["The system has been in Idle for "+str(timeX)+"seconds !",
                "The system has been in Error for "+str(timeY)+"seconds !"]

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

c.execute("""CREATE TABLE pallet_history (
            Time TIMESTAMP,
	        ValveCount INTEGER,
	        CylinderCount INTEGER,
	        SpringCount INTEGER,
	        TotalCount INTEGER
            )""")

c.execute("""CREATE TABLE totalTime (
            State TEXT,
	        StateTotalTime INTEGER,
	        DynTime INTEGER
	        )""")

# Adds 6 fixed rows
for i in range(6):
    with conn:
        c.execute("INSERT INTO workstation_pallets VALUES ("+str(i)+", null)")

with conn:
    c.execute("INSERT INTO totalTime VALUES(:State,:StateTotalTime,:DynTime)", {'State':"Idle", 'StateTotalTime':0, 'DynTime':0})
    c.execute("INSERT INTO totalTime VALUES(:State,:StateTotalTime,:DynTime)", {'State':"Working", 'StateTotalTime':0, 'DynTime':0})
    c.execute("INSERT INTO totalTime VALUES(:State,:StateTotalTime,:DynTime)", {'State':"Error", 'StateTotalTime':0, 'DynTime':0})

@app.route('/<string:page_name>/')
def static_page(page_name):
    allowed_pages = ['index', 'polling', 'robots', 'state', 'events', 'dashboard', 'history']
    if page_name in allowed_pages:
        return render_template('{0}.html'.format(page_name))
    else:
        return render_template('error.html'), 404

# Handler for post state from raspberry pie.  Message format eg. json={"state":"Working"}
@app.route('/workstation/state', methods=['POST','GET'])
def stateHandler():

    global timeEachState
    global timeExceeded
    global ArrayStates
    global ArrayTimes
    global StatesProportions

    def updateTotalTime(state, time1):
        with conn:
            c.execute("SELECT StateTotalTime FROM totalTime WHERE State=:State", {'State': state})
            totalT = c.fetchone()
            #print("Total T = ", totalT[0])
            totTime = totalT[0] + time1.seconds
            c.execute("UPDATE totalTime SET StateTotalTime=:StateTotalTime, DynTime=:DynTime WHERE State=:State",
                      {'StateTotalTime': totTime,'DynTime':totTime,'State':state})
            return totTime

    # Function to add a state to the SQL table
    def addStateSQL(state, time):
        # previousState = getCurrentState
        # if(previousState[0][0] != state):
        # with conn:
        c.execute("INSERT INTO workstation VALUES (null, :State, :Time)", {'State': state,'Time':time})


    #Function to compute the time spent on each state
    def TimeSpentInEachState(TabStates, TabTimes):

        #Initialize the time counters
        W, I, E = 0, 0, 0

        #Counting the time spent on each state
        for i in range(len(TabStates)-1):
            if TabStates[i]=="Working":
                W = W + ((TabTimes[i + 1] - TabTimes[i]).seconds)
            elif TabStates[i]=="Idle":
                I = I + ((TabTimes[i + 1] - TabTimes[i]).seconds)
            elif TabStates[i]=="Error":
                E = E + ((TabTimes[i + 1] - TabTimes[i]).seconds)

        #Return the times spent on each element (0:time spent in Working)
        return [W, I, E, (W+I+E)]

    # Handle the GET and POST requests and update the HMI
    if request.method=='POST':
        content = request.json
        #print ("(Post Req) Updated State recieved: ", content)
        newState=content["state"]
        #now = datetime.datetime.now()
        #time= now.isoformat()
        time= datetime.now().isoformat()



        ####### New Stuff
        if(getLastStateFromSQL()):
            currentState = getLastStateFromSQL()[0]
            if(currentState):
                statetime = datetime.strptime(currentState[2],'%Y-%m-%dT%H:%M:%S.%f')
                time1 = datetime.now() - statetime
                totalTime = updateTotalTime(currentState[1],time1)

        ####




        addStateSQL(newState, time)
        cnvMsg = {'state': newState, 'serverTime':time}
        cnvMsg_str = json.dumps(cnvMsg)
        ArrayStates.append(newState)
        ArrayTimes.append(datetime.strptime(time,'%Y-%m-%dT%H:%M:%S.%f'))
        StatesProportions=(TimeSpentInEachState(ArrayStates, ArrayTimes))
        #print(StatesProportions)
        timeExceeded = False
        return cnvMsg_str
    elif request.method=='GET':
        #print ("(GET Request) Workstation State:")
        time = datetime.now().isoformat()
        cnvMsg = getLastStateFromSQL()
        cnvMsg_str = json.dumps(cnvMsg)
        return cnvMsg_str

@app.route('/workstation/allstates', methods= ['GET'])
def statesHandler():
    c = conn.cursor()
    c.execute("SELECT * FROM workstation")
    time = datetime.now().isoformat()
    cnvMsg = c.fetchall()
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
        #print(PalletsArray)
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
        #print ("(Post Req) New Event: " , content)
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

#Message format eg. json={"counting"[spring.cylinder,valve, total]}
@app.route('/workstation/historic', methods=['POST','GET'])
def historyHandler():
    def addPalletHistorySQL(time, springCount, cylinderCount, valveCount, totalCount):
        with conn:
            c.execute("INSERT INTO pallet_history VALUES (:servertime , :SpringCount, :CylinderCount, :ValveCount, :TotalCount)",
                      {'servertime':time, 'SpringCount': springCount, 'CylinderCount': cylinderCount,'ValveCount':valveCount, 'TotalCount': totalCount})

    def getHistoryFromSQL():
        c = conn.cursor()
        c.execute("SELECT * FROM pallet_history")
        return c.fetchall()

    if request.method=='POST':
        content = request.json
        #print ("(Post Req) Historic" , content)
        springCount = content["counting"][0]
        cylinderCount = content["counting"][1]
        valveCount = content["counting"][2]
        totalCount = content["counting"][3]
        time = datetime.now().isoformat()
        addPalletHistorySQL(time, springCount, cylinderCount, valveCount, totalCount)
        cnvMsg = {'time': time, 'springCount': springCount, 'cylinderCount':cylinderCount, 'valveCount':valveCount}
        cnvMsg_str = json.dumps(cnvMsg)
        return cnvMsg_str

    elif request.method=='GET':
        #print ("(Get Req) Send WS Events:")
        cnvMsg = getHistoryFromSQL()
        cnvMsg_str = json.dumps(cnvMsg)
        #print(cnvMsg)
        return cnvMsg_str

@app.route('/workstation/oeevalues', methods= ['GET'])
def statesProportionHandler():
    def getTotatlTime():
        c = conn.cursor()
        c.execute("SELECT * FROM totalTime")
        totalTimes = c.fetchall()
        print("Test: ", totalTimes)
        return totalTimes

    #print("In StatePorportionHandler")
    #cnvMsg = StatesProportions
    #print(cnvMsg)
    #cnvMsg_str = json.dumps(cnvMsg)
    totalTimes = getTotatlTime()
    #StatesProportions = [totalTimes["Idle"],]

    #StatesProportions = getTotatlTime()
    cnvMsg_str = json.dumps(totalTimes)
    return cnvMsg_str

def checkElapsedTimeAlarms():
    global timeX
    global timeY
    global timeExceeded
    #global timeExceededError

    def get_last_item(table, selectColumn, sortBy):
        c = conn.cursor()
        c.execute("SELECT "+selectColumn+" FROM "+table+" ORDER BY "+sortBy+" DESC LIMIT 1")
        return c.fetchall()

    def get_last2_items(table, selectColumn, sortBy):
        c = conn.cursor()
        c.execute("select * from "+table+" where id=(select max(id)-1 from "+table+")")
        return c.fetchall()

    def getLastStateSQL():
        return get_last_item('workstation','*','time')

    def getLastTwoStatesSQL():
        return get_last2_items('workstation', '*', 'time')

    try:
        lastStateSQL = getLastStateSQL()
        #last2StateSQL = getLastTwoStatesSQL()
        #print (last2StateSQL)
        currentServerTime = datetime.strptime(datetime.now().isoformat(),'%Y-%m-%dT%H:%M:%S.%f')
        lastStateTime = datetime.strptime(lastStateSQL[0][2],'%Y-%m-%dT%H:%M:%S.%f')
        timeInterval = currentServerTime - lastStateTime
        #print (last2StateSQL)

        if (lastStateSQL[0][1] != "Working"):
            if (lastStateSQL[0][1] == "Idle") and (timeInterval.seconds > timeX) and not(timeExceeded):
                with conn:
                    c.execute("INSERT INTO event VALUES (null, :AlarmID, :Event, :Time)", {'AlarmID': 4, 'Event': serverAlarms[0], 'Time':currentServerTime})
                timeExceeded = True

            elif (lastStateSQL[0][1] == "Error") and (timeInterval.seconds > timeY) and not(timeExceeded):
                #print(timeInterval.seconds)
                with conn:
                    c.execute("INSERT INTO event VALUES (null, :AlarmID, :Event, :Time)", {'AlarmID': 5, 'Event': serverAlarms[1], 'Time':currentServerTime})
                timeExceeded = True
    except:
        True

# Function to get the last state on the SQL table
def getLastStateFromSQL():
    c = conn.cursor()
    # c.execute("SELECT * FROM workstation WHERE State=:state", {'state': 'Idle'})
    # c.execute("SELECT * FROM workstation WHERE 1")
    c.execute("SELECT * FROM workstation ORDER BY Key DESC LIMIT 1")
    return c.fetchall()


def checkTotalTime():
    #print("test: ", getLastStateFromSQL())
    if(getLastStateFromSQL()):
        current_state = getLastStateFromSQL()[0]
        #print("test:", current_state)
        if(current_state):
            #print("was here")
            now = datetime.now()
            stateTime = datetime.strptime(current_state[2],'%Y-%m-%dT%H:%M:%S.%f')
            time1 = now - stateTime
            with conn:
                c.execute("SELECT StateTotalTime FROM totalTime WHERE State=:State", {'State': current_state[1]})
                totalT = c.fetchone()
                totalTime1 = totalT[0] + time1.seconds

                c.execute("UPDATE totalTime SET DynTime=:DynTime WHERE State=:State",
                          {'DynTime': totalTime1, 'State':current_state[1]})
            print("test:", totalTime1)

def pollingUpdates():
    checkElapsedTimeAlarms()
    checkTotalTime()
    threading.Timer(0.5, pollingUpdates).start()


if __name__ == '__main__':
    pollingUpdates()
    app.run(host= '192.168.0.11')
    #app.run(host= '127.0.0.1')
    conn.close()

