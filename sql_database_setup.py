from json import loads, dumps
from cs50 import SQL
from helpers import Calendar, apology
"""
        CREATE TABLE sessions(
        session_id INTEGER NOT NULL,
        session_name TEXT NOT NULL,
        PRIMARY KEY(session_id)
        );

        CREATE TABLE users(
        user_id INTEGER NOT NULL,
        user_name TEXT NOT NULL,
        user_schedule TEXT NOT NULL,
        user_color VARCHAR(20),
        PRIMARY KEY(user_id)
        );

        CREATE TABLE session_users(
        session_id INTEGER REFERENCES sessions(session_id) ON UPDATE CASCADE ON DELETE CASCADE,
        user_id INTEGER REFERENCES users(user_id) ON UPDATE CASCADE ON DELETE CASCADE,
        user_name TEXT NOT NULL,
        PRIMARY KEY(session_id, user_id)
        );
"""
db = SQL("sqlite:///sessions.db")

def main():

    # db.execute("DROP TABLE session_users2")
    # db.execute("DROP TABLE sessions2")
    # db.execute("DROP TABLE users2")
    db.execute("DROP TABLE session_users2")
    db.execute("DROP TABLE sessions2")
    db.execute("DROP TABLE users2")

    db.execute("CREATE TABLE sessions (session_id INTEGER PRIMARY KEY AUTOINCREMENT, session_name TEXT NOT NULL)")

    db.execute("CREATE TABLE users (user_id INTEGER PRIMARY KEY AUTOINCREMENT, user_name TEXT NOT NULL, user_schedule TEXT NOT NULL, user_color VARCHAR(20))")

    db.execute("CREATE TABLE session_users (session_id INTEGER REFERENCES sessions2(session_id) ON UPDATE CASCADE ON DELETE CASCADE, user_id INTEGER REFERENCES users(user_id) ON UPDATE CASCADE ON DELETE CASCADE, user_name TEXT NOT NULL, PRIMARY KEY (session_id, user_id))")



    # db.execute("INSERT INTO sessions2 (session_id, session_name) SELECT session_id, session_name FROM sessions")

    # db.execute("INSERT INTO users2 (user_id, user_name, user_schedule, user_color) SELECT user_id, user_name, user_schedule, user_color FROM users")

    # db.execute("INSERT INTO session_users2 (session_id, user_id, user_name) SELECT session_id, user_id, user_name FROM sessions session_users")

def get_unused_id_from(location:str):
    match location:
        case "sessions":
            lookfor = "session"
        case "users":
            lookfor = "user"
        case _:
            return 0

    column_names = db.execute("SELECT * FROM ? LIMIT 1", location)[0].keys()

    id_column = f"{lookfor}_id"
    name_column = f"{lookfor}_name"

    if not (id_column in column_names and name_column in column_names):
        return apology("did you change the database names, dummy?", 403)

    empty_spot = db.execute(f"SELECT {id_column} FROM {location} WHERE {name_column}='__badname__' LIMIT 1")
    if empty_spot:
        return empty_spot[0]
    return (db.execute(f"SELECT MAX({id_column}) FROM {location}")[0].get(f'MAX({id_column})', 0) + 1)

def reset():
    db.execute("DROP TABLE session_users")
    db.execute("DROP TABLE sessions")
    db.execute("DROP TABLE users")

    db.execute("CREATE TABLE sessions (session_id INTEGER NOT NULL, session_name TEXT NOT NULL, PRIMARY KEY (session_id))")

    db.execute("CREATE TABLE users (user_id INTEGER NOT NULL, user_name TEXT NOT NULL, user_schedule TEXT NOT NULL, user_color VARCHAR(20), PRIMARY KEY (user_id))")

    db.execute("CREATE TABLE session_users (session_id INTEGER REFERENCES sessions(session_id) ON UPDATE CASCADE ON DELETE CASCADE, user_id INTEGER REFERENCES users(user_id) ON UPDATE CASCADE ON DELETE CASCADE, user_name TEXT NOT NULL, PRIMARY KEY (session_id, user_id))")



    saif = Calendar({}, name="Saif", id=1)
    julie = Calendar({}, name="Julie", id=2)
    alice = Calendar({"Friday": {"10": "Alice", "11": "Alice", "12": "Alice", "13": "Alice", "5": "Alice", "6": "Alice", "7": "Alice", "8": "Alice", "9": "Alice"}, "Monday": {"10": "Alice", "6": "Alice", "7": "Alice", "8": "Alice", "9": "Alice"}, "Saturday": {"10": "Alice", "11": "Alice", "5": "Alice", "6": "Alice", "7": "Alice", "8": "Alice", "9": "Alice"}, "Sunday": {"10": "Alice", "6": "Alice", "7": "Alice", "8": "Alice", "9": "Alice"}, "Thursday": {"10": "Alice", "11": "Alice", "12": "Alice", "13": "Alice", "14": "Alice", "6": "Alice", "7": "Alice", "8": "Alice", "9": "Alice"}, "Tuesday": {"10": "Alice", "11": "Alice", "5": "Alice", "6": "Alice", "7": "Alice", "8": "Alice", "9": "Alice"}, "Wednesday": {"10": "Alice", "11": "Alice", "12": "Alice", "13": "Alice", "5": "Alice", "6": "Alice", "7": "Alice", "8": "Alice", "9": "Alice"}}, "Alice", id=3)

    saif.load("calendars/cal_2.csv")
    julie.load("calendars/cal_short.csv")

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

main()