# db.execute("""CREATE TABLE sessions 
#            (session_id INTEGER PRIMARY KEY AUTOINCREMENT, 
#            session_name TEXT NOT NULL)""")

# db.execute("""CREATE TABLE users 
#            (user_id INTEGER PRIMARY KEY AUTOINCREMENT, 
#            user_name TEXT NOT NULL, 
#            user_schedule TEXT NOT NULL, 
#            user_color VARCHAR(20))""")

# db.execute("""CREATE TABLE session_users 
#            (session_id INTEGER REFERENCES sessions2(session_id) ON UPDATE CASCADE ON DELETE CASCADE, 
#            user_id INTEGER REFERENCES users(user_id) ON UPDATE CASCADE ON DELETE CASCADE, 
#            user_name TEXT NOT NULL, 
#            PRIMARY KEY (session_id, user_id))""")

import firebase_admin
from firebase_admin import credentials,firestore
class Session:
    def __init__(self, session_name, session_id):
        self.session_name = session_name
        self.session_id = session_id

    def to_dict(self):
        return {"session_name":self.session_name,"session_id":self.session_id}
    
    def __repr__(self):
        return f"Session(\
                session_name={self.session_name},\
                session_id={self.session_id}\
            )"
    
class Session_user:
    def __init__(self, user_name, session_id):
        self.user_name = user_name
        self.session_id = session_id

    def to_dict(self):
        return {"user_name":self.user_name,"session_id":self.session_id}
    
    def __repr__(self):
        return f"Session(\
                user_name={self.user_name},\
                session_id={self.session_id}\
            )"
    


cred = credentials.Certificate("serviceAccountKey.json")
firebase_admin.initialize_app(cred)
db = firestore.client()

SESSIONS = "sessions"
USERS = "users"
SESSION_USERS = "session_users"

s1 = Session("session1","1")
s2 = Session("session2","2")
sessions_ref = db.collection(SESSIONS)
for s in [s1,s2]:
    sessions_ref.document(s.session_id).set(s.to_dict())

docs = sessions_ref.where("session_name", "==", "session1").stream()
for doc in docs:
    print(f"{doc.id} => {doc.to_dict()}")
"""
# query database for session_id
search = db.execute(f"SELECT * FROM {SESSIONS} WHERE (session_id = ?) and (session_name = ?)", SID, SName)
def search_database(db,SID,SName):
    # Create a reference to the collection
    sessions_ref = db.collection(SESSIONS)

    # Construct the query
    return sessions_ref.where("session_id", "==", SID).where("session_name", "==", SName)









# creates a new session with the given name and an unused id
def create_session(db,SName):
    # Create a reference to the collection
    sessions_ref = db.collection(SESSIONS)

    # Construct the query
    sessions_ref.where("session_name", "==", SName)

    db.execute(f"INSERT INTO {SESSIONS} (session_name) VALUES(?)", SName)
    query = db.execute(f"SELECT * FROM {SESSIONS} ORDER BY session_id DESC LIMIT 1")[0]
    SID = query['session_id']
    SName2 = query['session_name']


# check if the correct session was found
if SName2 != SName or db.execute(f"SELECT * FROM {SESSION_USERS} WHERE (session_id=?)",SID):
    print(query)
    print(SName2)
    print(SName)
    print(db.execute(f"SELECT * FROM {SESSION_USERS} WHERE (session_id=?)",SID))
    return apology("error in creating session", 403)

# remove each person in the to_delete list from the cached session and the session's database
    all_people.pop(person.id)
    db.execute(f"DELETE FROM {SESSION_USERS} WHERE (user_id = ?) and (session_id = ?)", person.id, session["session_id"])

# searches the database for the user
    person = db.execute(f"SELECT * FROM {USERS} WHERE (user_id = ?) and (user_name = ?)", CalID, CalName)

else:# if they dont
    new_person = Calendar(name=CalName, schedule={})
    db.execute(f"INSERT INTO {USERS} (user_name, user_schedule, user_color) VALUES(?,?,?)", new_person.name, dumps(new_person.schedule), new_person.color)
    new_person = Calendar().load(SQL_query=db.execute(f"SELECT * FROM {USERS} ORDER BY user_id DESC LIMIT 1"))

# add new person to the list of people in this session
session["active_ids"] += [new_person.id]
db.execute(f"INSERT INTO {SESSION_USERS} (session_id, user_id, user_name) VALUES(?,?,?)", session["session_id"], new_person.id, new_person.name)
return redirect(f"/calendar_info/{new_person.name}/{new_person.id}")



# get raw data on people
people = db.execute(f"SELECT * FROM {USERS} WHERE user_id IN (SELECT user_id FROM {SESSION_USERS} WHERE session_id = ?) ORDER BY user_id ASC", session["session_id"])
"""