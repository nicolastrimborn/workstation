from flask import Flask, render_template
from flask import request
import json
import datetime
import sqlite3

###################################### SQL DB and Tables################################################################
app = Flask(__name__)
conn = sqlite3.connect(':memory:', check_same_thread=False)
c = conn.cursor()

c.execute("""CREATE TABLE workstation (
	        Key INTEGER PRIMARY KEY,
	        State text,
	        Time timestamp
            )""")

c.execute("""CREATE TABLE workstation_pallets (
	        Key INTEGER PRIMARY KEY,
	        Content text,
	        Time timestamp
            )""")

c.execute("""CREATE TABLE event (
            Key INTEGER PRIMARY KEY,
	        Event text,
	        Time timestamp
            )""")

c.execute("""CREATE TABLE pallet_transaction (
	        PalletID INTEGER PRIMARY KEY,
	        Contents TEXT NOT NULL,
	        QtyFlow INTEGER,
	        Time timestamp
            )""")

#creating sample data
with conn:
    #now = datetime.datetime.now()
    #time= now.isoformat()
    time = datetime.datetime.now()
    c.execute("INSERT INTO workstation VALUES (null, :State, :Time)", {'State': "Error", 'Time': time})
    c.execute("INSERT INTO workstation VALUES (null, :State, :Time)", {'State': "Idle", 'Time': time})
    c.execute("INSERT INTO workstation VALUES (null, :State, :Time)", {'State': "Working", 'Time': time})
    c.execute("INSERT INTO workstation_pallets VALUES (null, :Content, :Time)", {'Content': "Spring", 'Time': time})
    c.execute("INSERT INTO workstation_pallets VALUES (null, :Content, :Time)", {'Content': "valve", 'Time': time})
    c.execute("INSERT INTO event VALUES (null, :Event, :Time)", {'Event': "test Alarm", 'Time': time})
    c.execute("INSERT INTO pallet_transaction VALUES (null, :Contents, :QtyFlow, :Time)", {'Contents': "Spring", 'QtyFlow': 1, 'Time': time})
""""
Dates=["2018-11-29T00:10:00.891869",
       "2018-11-29T00:44:00.891869",
       "2018-11-29T01:30:00.891869",
       "2018-11-29T02:08:00.891869",
       "2018-11-29T02:13:00.891869",
       "2018-11-29T02:47:00.891869",
       "2018-11-29T03:00:00.891869",
       "2018-11-29T03:19:00.891869",
       "2018-11-29T03:23:00.891869",
       "2018-11-29T04:27:00.891869",
       "2018-11-29T07:29:00.891869",
       "2018-11-29T07:51:00.891869",
       "2018-11-29T08:09:00.891869",
       "2018-11-29T08:19:00.891869",
       "2018-11-29T09:32:00.891869",
       "2018-11-29T11:37:00.891869",
       "2018-11-29T11:41:00.891869",
       "2018-11-29T13:33:00.891869",
       "2018-11-29T13:44:00.891869",
       "2018-11-29T14:33:00.891869",
       "2018-11-29T14:44:00.891869",
       "2018-11-29T16:03:00.891869",
       "2018-11-29T16:22:00.891869",
       "2018-11-29T16:42:00.891869",
       "2018-11-29T17:18:00.891869",
       "2018-11-29T17:23:00.891869",
       "2018-11-29T17:25:00.891869",
       "2018-11-29T17:40:00.891869",
       "2018-11-29T18:46:00.891869",
       "2018-11-29T22:24:00.891869",
       "2018-11-29T23:13:00.891869",
       "2018-11-29T23:17:00.891869",
       "2018-11-29T24:41:00.891869",
       "2018-11-30T00:09:00.891869"]

States=["Working",
        "Idle",
        "Error",
        "Error",
        "Idle",
        "Working",
        "Idle",
        "Idle",
        "Error",
        "Idle",
        "Error",
        "Error",
        "Working",
        "Error",
        "Working",
        "Error",
        "Error",
        "Idle",
        "Error",
        "Error",
        "Idle",
        "Idle",
        "Idle",
        "Error",
        "Idle",
        "Working",
        "Working",
        "Error",
        "Working",
        "Working",
        "Working",
        "Error",
        "Idle",
        "Idle"]

def add_data_SQL(tablename,list_data):
    with conn:
        if tablename=="current_state":
            c.execute("INSERT INTO workstation VALUES (null, :State, :ServerTime)", {'State': list_data[0], 'ServerTime': list_data[1]})
        elif tablename=="pallet_transaction":
            c.execute("INSERT INTO pallet_transaction VALUES (null, :Content, :QtyFlow, :ServerTime)", {'Content': list_data[0], 'QtyFlow': list_data[1], 'ServerTime': list_data[2]})

for i in range(len(Dates)):
    add_data_SQL("current_state",[States[i],Dates[i]])
"""

###################################### JSON ENDPOINTS ##################################################################
@app.route('/<string:page_name>/')
def static_page(page_name):
    allowed_pages = ['index', 'polling', 'robots', 'state', 'events', 'dashboard']
    if page_name in allowed_pages:
        return render_template('{0}.html'.format(page_name))
    else:
        return render_template('error.html'), 404
    #return render_template('%s.html' % page_name)

#Message format e.g json={"state":"Working"}
@app.route('/workstation/state', methods=['POST'])
def updateState():
    content = request.json
    #print ("(Post Req) Updated State recieved: ", content)
    newState=content["state"]
    #now = datetime.datetime.now()
    #time= now.isoformat()
    time= datetime.datetime.now()
    change_state(newState, time)
    cnvMsg = {'state': newState, 'serverTime':time}
    cnvMsg_str = json.dumps(cnvMsg)
    return cnvMsg_str

@app.route('/workstation/state', methods=['GET'])
def getWSState():
    #print ("(GET Request) Workstation State:")
    cnvMsg = get_State()
    cnvMsg_str = json.dumps(cnvMsg)
    #print(cnvMsg)
    return cnvMsg_str

@app.route('/workstation/states', methods=['GET'])
def getWSStateAll():
    #print ("(GET Request) Workstation State:")
    cnvMsg = get_States_All()
    cnvMsg_str = json.dumps(cnvMsg)
    #print(cnvMsg)
    return cnvMsg_str

#Message format eg. json={"event":"Error State"}
@app.route('/workstation/event', methods=['POST'])
def newEvent():
    content = request.json
    #print ("(Post Req) New Event: " , content)
    newEvent=content["event"]
    #now = datetime.datetime.now()
    #time= now.isoformat()
    time= datetime.datetime.now()
    cnvMsg = {'event': newEvent, 'serverTime':time}
    cnvMsg_str = json.dumps(cnvMsg)
    return cnvMsg_str

@app.route('/workstation/event', methods=['GET'])
def getEvents():
    #print ("(Get Req) Send WS Events:")
    cnvMsg = get_Events()
    cnvMsg_str = json.dumps(cnvMsg)
    #print(cnvMsg)
    return cnvMsg_str

@app.route('/workstation/pallets', methods=['GET'])
def getPallets():
    #print ("(Get Req) Send WS Pallets:")
    cnvMsg = get_Pallets()
    cnvMsg_str = json.dumps(cnvMsg)
    #print(cnvMsg)
    return cnvMsg_str

@app.route('/workstation/pallets', methods=['POST'])
def addPallet():
    content = request.json
    #print ("(Post Req) Add Pallet: ", content)
    newPallet=content["contents"]
    #now = datetime.datetime.now()
    #time= now.isoformat()
    time= datetime.datetime.now()
    add_Pallets(newPallet, time)
    cnvMsg = {'Pallet': newPallet, 'serverTime':time}
    cnvMsg_str = json.dumps(cnvMsg)
    return cnvMsg_str

###################################### SQL Methods #####################################################################

def change_state(state, time):
    with conn:
        c.execute("INSERT INTO workstation VALUES (null, :State, :Time)", {'State': state,'Time':time})

def get_State():
    c = conn.cursor()
    # c.execute("SELECT * FROM workstation WHERE State=:state", {'state': 'Idle'})
    # c.execute("SELECT * FROM workstation WHERE 1")
    c.execute("SELECT * FROM workstation ORDER BY Key DESC LIMIT 1")
    return c.fetchall()

def get_States_All():
    c = conn.cursor()
    # c.execute("SELECT * FROM workstation WHERE State=:state", {'state': 'Idle'})
    c.execute("SELECT * FROM workstation WHERE 1")
    #c.execute("SELECT * FROM workstation ORDER BY Key DESC LIMIT 1")
    return c.fetchall()

def addEvent(event, time):
    with conn:
        c.execute("INSERT INTO event VALUES (null, :Event, :Time)", {'Event': event,'Time':time})

def get_Events():
    c = conn.cursor()
    c.execute("SELECT * FROM event")
    return c.fetchall()

def get_Pallets():
    c = conn.cursor()
    c.execute("SELECT * FROM workstation_pallets")
    return c.fetchall()

def add_Pallets(newPallet, time):
    with conn:
        c.execute("INSERT INTO workstation_pallets VALUES (null, :Content, :Time)", {'Content': newPallet, 'Time': time})

def get_first_item(table):
        c = conn.cursor()
        c.execute("SELECT Time FROM "+table+" ORDER BY Time DESC LIMIT 1")
        return c.fetchall()

def get_last_item(table):
    c = conn.cursor()
    # c.execute("SELECT * FROM workstation WHERE State=:state", {'state': 'Idle'})
    # c.execute("SELECT * FROM workstation WHERE 1")
    c.execute("SELECT Time FROM "+table+" ORDER BY Time DESC LIMIT 1")
    return c.fetchall()

def total_time(table):
    

if __name__ == '__main__':
    app.run(host= '127.0.0.1')
    conn.close()

"""
#REST endpoints
@app.route('/monitoring', methods=['POST'])
def newWSState():
    print ("Workstation Changed State")
    content = request.json
    print (content)
    newState=content["state"]
    now = datetime.datetime.now()
    time= now.isoformat();
    change_state(newState,time)
    cnvMsg = {'state': newState, "serverTime":time}
    cnvMsg_str = json.dumps(cnvMsg)
    return cnvMsg_str

"""