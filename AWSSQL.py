from json import loads, dumps
from cs50 import SQL
from helpers import Calendar, apology
import os
from dotenv import load_dotenv
import re

load_dotenv()
# Configure CS50 Library to use SQLite database
uri = os.environ.get("SQLALCHEMY_DATABASE_URI")
# print(uri)
keynames = re.findall("[{](\w*)[}]",uri)
for key in keynames:
    uri = re.sub("{"+key+"}", os.environ.get(key), uri)
# print(uri)
db = SQL(uri) 
db._autocommit=False



# db.execute("CREATE TABLE sessions (session_id INTEGER NOT NULL, session_name TEXT NOT NULL, PRIMARY KEY (session_id))")

# db.execute("CREATE TABLE users (user_id INTEGER NOT NULL, user_name TEXT NOT NULL, user_schedule TEXT NOT NULL, user_color VARCHAR(20), PRIMARY KEY (user_id))")

# db.execute("CREATE TABLE session_users (session_id INTEGER REFERENCES sessions(session_id) ON UPDATE CASCADE ON DELETE CASCADE, user_id INTEGER REFERENCES users(user_id) ON UPDATE CASCADE ON DELETE CASCADE, user_name TEXT NOT NULL, PRIMARY KEY (session_id, user_id))")



saif = Calendar({}, name="Saif", id=1)
julie = Calendar({}, name="Julie", id=2)
alice = Calendar({"Friday": {"10": "Alice", "11": "Alice", "12": "Alice", "13": "Alice", "5": "Alice", "6": "Alice", "7": "Alice", "8": "Alice", "9": "Alice"}, "Monday": {"10": "Alice", "6": "Alice", "7": "Alice", "8": "Alice", "9": "Alice"}, "Saturday": {"10": "Alice", "11": "Alice", "5": "Alice", "6": "Alice", "7": "Alice", "8": "Alice", "9": "Alice"}, "Sunday": {"10": "Alice", "6": "Alice", "7": "Alice", "8": "Alice", "9": "Alice"}, "Thursday": {"10": "Alice", "11": "Alice", "12": "Alice", "13": "Alice", "14": "Alice", "6": "Alice", "7": "Alice", "8": "Alice", "9": "Alice"}, "Tuesday": {"10": "Alice", "11": "Alice", "5": "Alice", "6": "Alice", "7": "Alice", "8": "Alice", "9": "Alice"}, "Wednesday": {"10": "Alice", "11": "Alice", "12": "Alice", "13": "Alice", "5": "Alice", "6": "Alice", "7": "Alice", "8": "Alice", "9": "Alice"}}, "Alice", id=3)

# saif.load("calendars/cal_2.csv")
# julie.load("calendars/cal_short.csv")

sess_id = {"0": {"session_name": "saif", "people": [saif]},
        "1": {"session_name": "julie", "people": [julie]},
        "2": {"session_name": "combined", "people": [saif, julie, alice]},
        "1241": {"session_name": "The Jungl", "people": []}}

for id in list(sess_id.keys()):
    db.execute("INSERT INTO sessions (session_id, session_name) VALUES(?,?)", id, sess_id[id]['session_name'])

for id in ['2']:
    for person in sess_id[id]["people"]:
        db.execute("INSERT INTO users (user_id, user_name, user_schedule, user_color) VALUES(?,?,?,?)", person.id, person.name, dumps(person.schedule), person.color)

for id in list(sess_id.keys()):
    for person in sess_id[id]["people"]:
        db.execute("INSERT INTO session_users (session_id, user_id, user_name) VALUES(?,?,?)", id, person.id, person.name)
