from flask import Flask, render_template
from flask import request
import json
from datetime import datetime
import time
import sqlite3

app = Flask(__name__)
conn = sqlite3.connect(':memory:', check_same_thread=False)
c = conn.cursor()

c.execute("""CREATE TABLE workstation (
	        Key INTEGER PRIMARY KEY,
	        State text,
	        Time timestamp
            )""")

c.execute("""CREATE TABLE workstation_pallets (
	        Slot INTEGER PRIMARY KEY,
	        Content text
            )""")

for i in range(6):
    with conn:
        c.execute("INSERT INTO workstation_pallets VALUES ("+str(i)+", null)")

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
        return cnvMsg_str
    elif request.method=='GET':
        #print ("(GET Request) Workstation State:")
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


if __name__ == '__main__':
    app.run(host= '192.168.0.11')
    #app.run(host= '127.0.0.1')
    conn.close()