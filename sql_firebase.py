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
from helpers import Calendar 
from json import dumps
class User(Calendar):
    # def __init__(self,schedule={}, name='', id=-1, color="primary"):
    #     super().__init__(schedule, name, id, color)

    def to_dict(self):
        return {"user_name":self.name,"user_id":int(self.id),"user_schedule":dumps(self.schedule),"user_color":self.color}
        
class Session:
    def __init__(self, session_name:str, session_id:int):
        self.session_name = session_name
        self.session_id = session_id

    def to_dict(self):
        return {"session_name":self.session_name,"session_id":self.session_id}
    
    def __repr__(self):
        return f"Session(\
                session_name={self.session_name},\
                session_id={self.session_id}\
            )"
    
class Session_users:
    def __init__(self, session_id:int=-1, users:dict = {}):
        self.users = users
        self.session_id = session_id

    def to_dict(self):
        this_dict = {"session_id":self.session_id}
        this_dict.update(self.users)
        return this_dict
    
    def from_dict(self, reference_dict):
        self.session_id = int(reference_dict.get("session_id",-1))
        self.users = reference_dict.copy()
        self.users.pop("session_id")
        return self
    
    def __repr__(self):
        users = ""
        for user in self.users:
            users += f",\
                {user.name}#{user.id}"
        return f"Session(\
                session_id={self.session_id}" + users + "\
            )"
    
def get_open_id(collection,id_name):
    try:
        docs = collection.order_by(id_name, direction=firestore.Query.DESCENDING).limit(1).stream()
        return int([doc.id for doc in docs][0])+1
    except:
        return 1

# cred = credentials.Certificate("serviceAccountKey.json")
# firebase_admin.initialize_app(cred)
# db = firestore.client()

SESSIONS = "sessions"
USERS = "users"
SESSION_USERS = "session_users"
# cred = credentials.Certificate("serviceAccountKey.json")
# firebase_admin.initialize_app(cred)
# db = firestore.client()

"""
s1 = Session("session3", 3)
print(get_open_id(sessions_ref,"session_id"))
s2 = Session("session4",get_open_id(sessions_ref,"session_id"))
for s in [s1,s2]:
    sessions_ref.document(str(s.session_id)).set(s.to_dict())
create_session(db=db, SName="bustin")
docs = sessions_ref.stream()
for doc in docs:
    print(f"{doc.id} => {doc.to_dict()}")
"""
def main():
    print("ran main")


# query database for session_id
def search_for_session(db,SID,SName):
    # Create a reference to the collection
    sessions_ref = db.collection(SESSIONS)

    # Construct the query
    docs = sessions_ref.where("session_id", "==", int(SID)).where("session_name", "==", SName).stream()
    return [doc.to_dict() for doc in docs]

# creates a new session with the given name and an unused id
def create_session(db,SName):
    # Create a reference to the collection
    sessions_ref = db.collection(SESSIONS)

    # Create the session object
    SID = get_open_id(db.collection(SESSIONS),"session_id")
    this_session = Session(session_name=SName,session_id=SID)

    # Import this session into the database
    sessions_ref.document(str(this_session.session_id)).set(this_session.to_dict())

    # Verify newly created session has been inserted into the database
    docs = sessions_ref.where("session_id", "==", this_session.session_id).where("session_name", "==", this_session.session_name).stream()
    SList = [doc.to_dict() for doc in docs]
    # print(SList)
    if len(SList) != 1 or SName != SList[0].get("session_name",""):
        return apology("error in creating session", 403)

    # Create a document in session_users for the newly created session
    db.collection(SESSION_USERS).document(str(SID)).set(Session_users(session_id=SID).to_dict())

    # Return session info to be used 
    return this_session

# delete a list of users from a session
def delete_from_session(db,users:dict,session_id:int):
    # Create reference to session_users document based on session_id
    session_users_ref = db.collection(SESSION_USERS).document(str(session_id))

    # Get the users in the current session
    doc = session_users_ref.get()
    if not doc.exists:  
        return
    doc = doc.to_dict()
    session_info = Session_users().from_dict(doc)

    # remove the selected users from the current session_users list
    for user in users:
        # verify if a user is in the session_users list
        if user.name != session_info.users.get(str(user.id),""):
            continue
        session_users_ref.update({str(user.id): firestore.DELETE_FIELD})
    return

def expel_user(db,user_id,session_id):
    session_users_ref = db.collection(SESSION_USERS).document(str(session_id))

    # Get the users in the current session
    doc = session_users_ref.get()
    if not doc.exists:  
        return
    doc = doc.to_dict()
    session_info = Session_users().from_dict(doc)

    if session_info.users.get(str(user_id),None):
        session_users_ref.update({str(user_id): firestore.DELETE_FIELD})
    return

# search for a specific user
def search_for_user(db,user_id,user_name):
    # Create reference to the users collection
    users_ref = db.collection(USERS)

    # Query the database for a specific user
    docs = users_ref.where("user_id", "==", user_id).where("user_name", "==", user_name).stream()
    user = [doc.to_dict() for doc in docs]

    # If one user is not found, return None
    if len(user) != 1:
        return None
    
    # If the user is found, return the user
    return User().load(user[0])

# creates a new user
def create_new_user(db,user_name):
    # Create reference to users collection
    users_ref = db.collection(USERS)

    # Get the user_id
    user_id = get_open_id(users_ref, "user_id")
    user = User(name = user_name, id=user_id)

    # add the User to the Users collection
    users_ref.document(str(user_id)).set(user.to_dict())

    # return the user for use
    return user

# adds a specific user to a specific session
def add_user_to_session(db,session_id:int, user:User|Calendar):
    # Create reference to session_users document based on session_id
    session_users_ref = db.collection(SESSION_USERS).document(str(session_id))

    # update the document and add a new field for the specific user
    session_users_ref.update({str(user.id):user.name})
    return

# gets the unloaded info of users in a specific session
def get_users_in_session(db,session_id):
    # Create reference to session_users document based on session_id
    this_session_users_ref = db.collection(SESSION_USERS).document(str(int(session_id)))

    # Query the database for users in this session
    doc = this_session_users_ref.get()
    if not doc.exists:  
        return []
    doc= doc.to_dict()
    # print(this_session_users_ref)
    # print(doc)
    # print(this_session_users_ref.get())
    session_info = Session_users().from_dict(doc)

    # Query the Users Collection for users that match the user_id
    users=[]
    users_ref = db.collection(USERS)
    for user_id in list(session_info.users.keys()):
        user = users_ref.document(str(user_id)).get().to_dict()
        users.append(user)
    
    # Return a list of the Users in this session
    return users

def update_users(db, user:User|Calendar):

    # Create reference to the user in the users collection
    user_ref = db.collection(USERS).document(str(user.id))

    if type(user) == Calendar:
        user = User(schedule=user.schedule, name=user.name, id=user.id, color=user.color)
    user_ref.set(user.to_dict())
    return

if __name__ == "__main__":
    main()


