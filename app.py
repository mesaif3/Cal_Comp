import os

from json import loads, dumps
from cs50 import SQL
from flask import Flask, flash, redirect, render_template, request, session
from flask_session import Session
from tempfile import mkdtemp
from werkzeug.exceptions import default_exceptions, HTTPException, InternalServerError
from werkzeug.security import check_password_hash, generate_password_hash

from helpers import apology, session_required, Calendar, days, colors

"""
Todo:
1) select which calendars you want to see #done
2) add color selectors per calendar #done
3) add sql to save data #done
4) host it externally
5) custom colors
"""

SESSIONS = "sessions"
USERS = "users"
SESSION_USERS = "session_users"

# Configure application
app = Flask(__name__)

# Ensure templates are auto-reloaded
app.config["TEMPLATES_AUTO_RELOAD"] = True


# Ensure responses aren't cached
@app.after_request
def after_request(response):
    response.headers["Cache-Control"] = "no-cache, no-store, must-revalidate"
    response.headers["Expires"] = 0
    response.headers["Pragma"] = "no-cache"
    return response


# Configure session to use filesystem (instead of signed cookies)
app.config["SESSION_FILE_DIR"] = mkdtemp()
app.config["SESSION_PERMANENT"] = False
app.config["SESSION_TYPE"] = "filesystem"
Session(app)

# Configure CS50 Library to use SQLite database
uri = os.getenv("DATABASE_URL")
if uri.startswith("postgres://"):
    uri = uri.replace("postgres://", "postgresql://")
db = SQL(uri)
# pgloader --no-ssl-cert-verification sessions.db postgresql://qszjzfyfycymmb:b8e925ef3948e3573262de3898981adb988c357159ecc20de19d11f842ff84bd@ec2-63-32-248-14.eu-west-1.compute.amazonaws.com:5432/d1ugqh51mo7jpt?sslmode=require
# export API_KEY=value
# Make sure API key is set
# if not os.environ.get("API_KEY"):
#     raise RuntimeError("API_KEY not set")

@app.route("/",methods=["GET","POST"])
@session_required
def index():
    # returns a combined calendar
    # session["session_id"] = 1243
    # session["session_name"] = "test"
    # session["people"] = get_people()
    # if not session.get("active_people",None):
    #     session["active_people"] = list(session["people"].values())

    def combine(people):
        combined = Calendar()

        if len(people) == 0:
            return combined

        for person in people:
            combined += person
        return combined

    if request.method == "POST":
        id_list = request.form.getlist('to_show')
        session["active_people"] = []
        for id in id_list:
            session["active_people"].append(session['people'][int(id)])

        return render_template("index.html", people=session["active_people"], combined=combine(session["active_people"]),  days=days) ### id_people_dict=session['people'], removed

    return render_template("index.html", people=session["active_people"], combined=combine(session["active_people"]),  days=days) ### id_people_dict=session['people'], removed


# A page to prompt the user for a session ID to join
@app.route("/join_session", methods=["GET", "POST"])
def join_session(this_route="/join_session"):
    """Log user in"""

    # Forget any user_id but maintains flashes
    flashes = session.get("_flashes", [])
    session.clear()
    session["_flashes"] = flashes

    # User reached route via POST (as by submitting a form via POST)
    if request.method == "POST":
        if not('#' in request.form.get("session_info")):
            return insert_flash(this_route,"invalid format", 403)

        SName,SID = request.form.get("session_info").split("#")

        # Ensure username was submitted
        if not SID:
            return insert_flash(this_route,"must provide session id", 403)

        if not SName or SName == "__badname__":
            return insert_flash(this_route,"invalid session name", 403)

        # query database for session_id
        search = db.execute(f"SELECT * FROM {SESSIONS} WHERE (session_id = ?) and (session_name = ?)", SID, SName)

        # checks the validity of the search query
        if len(search) != 1:
            return insert_flash(this_route,"session id not found", 403)

        # Remember which user has logged in
        session["session_id"] = SID
        session["session_name"] = SName
        session["people"] = get_people()
        session["active_people"] = list(session["people"].values())
        print(session["session_id"])
        print(session["session_name"])
        print(session["people"])
        print(session["active_people"])
        # Redirect user to home page
        return redirect("/")

    # User reached route via GET (as by clicking a link or via redirect)

    return render_template("join_session.html")


# logs the user out of their current session
@app.route("/logout")
def logout():
    """Log user out"""

    # Forget any user_id
    session.clear()

    # Redirect user to login form
    return redirect("/")


# prompts the user for a name and id to create a new session
@app.route("/new_session", methods=["GET", "POST"])
def new_session(this_route="/new_session", code=200):

    if request.method == "POST":

        SName = request.form.get("session_name")
        # session name check
        if not SName or SName == "__badname__" or '#' in SName:
            return insert_flash(this_route, "Please Enter a valid Session Name")

        # creates a new session with the given name and an unused id
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

        session["session_id"] = SID
        session["session_name"] = SName
        session["people"] = {}
        session["active_people"] = []

        return redirect("/")
    return render_template("new_session.html"), code

@app.route("/del_calendar", methods=["POST", "GET"])
@session_required
def del_calendar():

    if request.method == "POST":
        # get a list of things to delete
        to_delete = request.form.getlist("to_delete")

        # skip the process if there is nothing to delete
        if not to_delete:
            return redirect("/")

        # re-format the to_delete list into their objects ###(could be id's instead i think)
        for person in to_delete:
            person = session["people"][int(person.split("#")[1])]

            # remove each person in the to_delete list from the cached session and the session's database
            session["people"].pop(person.id)
            db.execute(f"DELETE FROM {SESSION_USERS} WHERE (user_id = ?) and (session_id = ?)", person.id, session["session_id"])

        # check to make sure the data update was done correctly
        db_people = get_people()
        for id in set().union(session["people"].keys(),db_people.keys()):
            if session["people"][id] != db_people[id]:
                return apology("UH OH! editing the data failed")


        session["active_people"] = list(session["people"].values())
        # confirm to the user that the people were removed
        flash(f"{[person for person in to_delete]} {'was' if len(to_delete) == 1 else 'were'} removed from the room!")
        return redirect("/")

    # renders the page to remove users from the room
    return render_template("del_calendar.html")


# prompts the user for a name to create a new calendar with that name
@app.route("/add_calendar", methods=["POST", "GET"])
@session_required
def add_calendar(this_route="/add_calendar"):

    if request.method == "POST":
        CalName = request.form.get("calendar_name")

        # Ensure a name was written
        if not CalName or CalName=="__badname__":
            return insert_flash(this_route,"Please Enter a name!")

        # Check if the user already exists
        if '#' in CalName:
            try:
                CalName, CalID = CalName.split('#')
                CalID = int(CalID)
            except:
                return insert_flash(this_route, "That's not a valid user!")

            person = db.execute(f"SELECT * FROM {USERS} WHERE (user_id = ?) and (user_name = ?)", CalID, CalName)

            # if one specific entry was not found or is already in the room, prompt the user again
            if len(person) != 1:
                return insert_flash(this_route,"User not found :(")

            elif CalID in list(session["people"].keys()):
                return insert_flash(this_route, "This user is already in the room!")

        # Assemple a new object for the person
            else: #if he exists
                person = person[0]
                new_person = Calendar().load(person)
        else:# if he doesnt
            new_person = Calendar(name=CalName, schedule={})
            db.execute(f"INSERT INTO {USERS} (user_name, user_schedule, user_color) VALUES(?,?,?)", new_person.name, dumps(new_person.schedule), new_person.color)
            new_person = Calendar().load(SQL_query=db.execute(f"SELECT * FROM {USERS} ORDER BY user_id DESC LIMIT 1"))

        # add new person to the list of people in this session
        session["people"][new_person.id] = new_person
        session["active_people"].append(new_person)
        print(SESSION_USERS)
        db.execute(f"INSERT INTO {SESSION_USERS} (session_id, user_id, user_name) VALUES(?,?,?)", session["session_id"], new_person.id, new_person.name)
        return redirect(f"/calendar_info/{new_person.name}/{new_person.id}")

    return render_template("add_calendar.html")


# displays the calendar of the chosen name
@app.route("/calendar_info/<string:PName>/<int:PID>", methods=["POST", "GET"])
@session_required
def Calendar_info(PName, PID):

    person = session["people"].get(PID, None)

    # looks for the person through the session
    if not person:
        return apology("user not found", 403)

    # on update
    if request.method == "POST":

        # Ensures a schedule update occurs
        if not request.form.get("schedule"):
            return apology("missing schedule?", 403)

        user_update = loads(request.form.get("schedule"))
        if not user_update:
            return apology("missing schedule?", 403)
        person.schedule = user_update["Schedule"]

        # checks for a new color
        if request.form.get('myColor'):
            person.color = request.form.get('myColor')

        # update database
        db.execute(f"UPDATE {USERS} SET user_schedule = ?, user_color = ? WHERE user_id = ?", dumps(person.schedule), person.color, person.id)
        # feedback message to confirm with user
        flash(f"{person.name} has been updated!")
    return render_template("calendar_info.html", person=person, days=days, colors=colors, custom_color="D32AE1")


# gets the list of calendars in the current session
def get_people():
    # get raw data on people
    people = db.execute(f"SELECT * FROM {USERS} WHERE user_id IN (SELECT user_id FROM {SESSION_USERS} WHERE session_id = ?)", session["session_id"])

    # convert raw data into a list of Calendar objects
    people = list(map(lambda person: Calendar().load(person), people))

    # convert list of objects into a dictionary {id:object}
    if people:
        return {person.id:person for person in people}
    else:
        return {}

# def get_unused_id_from(location:str):
#     match location:
#         case f"{SESSIONS}":
#             lookfor = "session"
#         case f"{USERS}":
#             lookfor = "user"
#         case _:
#             return 0

#     column_names = db.execute("SELECT * FROM ? LIMIT 1", location)[0].keys()

#     id_column = f"{lookfor}_id"
#     name_column = f"{lookfor}_name"

#     if not (id_column in column_names and name_column in column_names):
#         return apology("did you change the database names, dummy?", 403)

#     empty_spot = db.execute(f"SELECT {id_column} FROM {location} WHERE {name_column}='__badname__' LIMIT 1")
#     if empty_spot:
#         return empty_spot[0]
#     return (db.execute(f"SELECT MAX({id_column}) FROM {location}")[0].get(f'MAX({id_column})', 0) + 1)

def insert_flash(this_route='/', message="page refreshed", code=0):
    flash(message)
    return redirect(this_route)

def errorhandler(e):
    """Handle error"""
    if not isinstance(e, HTTPException):
        e = InternalServerError()
    return apology(e.name, e.code)


# Listen for errors
for code in default_exceptions:
    app.errorhandler(code)(errorhandler)
