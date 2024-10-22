import os
from json import loads, dumps
from cs50 import SQL
from flask import Flask, flash, redirect, render_template, request, session
from sqlalchemy import true
from werkzeug.exceptions import default_exceptions, HTTPException, InternalServerError

from helpers import apology, session_required, Calendar, days, colors
import re

""
import firebase_admin
from firebase_admin import credentials,firestore
from sql_firebase import *


""

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

app.secret_key = os.environ.get("secret_key")

# Ensure templates are auto-reloaded
app.config["TEMPLATES_AUTO_RELOAD"] = True


# Configure firebase database
my_credentials = {
    "type": os.environ.get("type"),
    "project_id": os.environ.get("project_id"),
    "private_key_id": os.environ.get("private_key_id"),
    "private_key": os.environ.get("private_key").replace(r'\n', '\n'),  # CHANGE HERE
    "client_email": os.environ.get("client_email"),
    "client_id": os.environ.get("client_id"),
    "auth_uri": os.environ.get("auth_uri"),
    "token_uri": os.environ.get("token_uri"),
    "auth_provider_x509_cert_url": os.environ.get("auth_provider_x509_cert_url"),
    "client_x509_cert_url": os.environ.get("client_x509_cert_url")
}
cred = credentials.Certificate(my_credentials)
firebase_admin.initialize_app(cred)
db = firestore.client()


@app.route("/",methods=["GET","POST"])
@session_required
def index():

    all_people = get_people()
    # function to combine all people into a single calendar
    def combine(people):
        combined = Calendar()

        if len(people) == 0:
            return combined

        for person in people:
            combined += person
        return combined

    # display the chosen combined calendar 
    if request.method == "POST":
        session["active_ids"] = list(map(int, request.form.getlist('to_show')))
        active_people = [all_people[id] for id in session.get("active_ids")]

        # feedback for the user
        flash("The calendar has been updated!")

        return render_template("index.html", all_people=all_people, active_people=active_people, combined=combine(active_people),  days=days) ### id_people_dict=session['people'], removed
    
    else:
        active_people = [all_people[id] for id in session.get("active_ids",[])]
        return render_template("index.html", all_people=all_people, active_people=active_people, combined=combine(active_people),  days=days) ### id_people_dict=session['people'], removed


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
        if not SID :
            return insert_flash(this_route,"must provide session id", 403)

        if not SName or SName == "__badname__":
            return insert_flash(this_route,"invalid session name", 403)

        # query database for session_id
        search = search_for_session(db,SID,SName)
        
        # checks the validity of the search query
        if len(search) != 1:
            return insert_flash(this_route,"session id not found", 403)

        # Remember to which session user has logged in
        session["session_id"] = str(int(SID))
        session["session_name"] = SName
        session["active_ids"] = list(get_people().keys())

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

    # Confirm logging out
    flash("You have logged out successfully!")

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
        this_session = create_session(db,SName)

        SID = this_session.session_id

        # initialize the session cookie
        session["session_id"] = SID
        session["session_name"] = SName
        session["active_ids"] = []

        return redirect("/")
    return render_template("new_session.html"), code

@app.route("/del_calendar", methods=["POST", "GET"])
@session_required
def del_calendar():

    all_people = get_people()

    if request.method == "POST":
        # get a list of things to delete
        to_delete = request.form.getlist("to_delete")

        # skip the process if there is nothing to delete
        if not to_delete:
            return redirect("/")

        # re-format the to_delete list into their objects ###(could be id's instead i think)
        for person in to_delete:
            id_to_delete = int(person.split("#")[1])
            person = all_people[id_to_delete]

            # QOL: remove from active list             
            if id_to_delete in session["active_ids"]:
                session["active_ids"].remove(id_to_delete)

            # remove each person in the to_delete list from the cached session and the session's database
            all_people.pop(person.id)
            expel_user(db,user_id=person.id, session_id=session["session_id"])

        # check to make sure the data update was done correctly
        db_people = get_people()
        for id in set().union(all_people.keys(),db_people.keys()):
            if all_people[id] != db_people[id]:
                return apology("UH OH! editing the data failed", code=399, AP=get_people())

        # confirm to the user that the people were removed
        flash(f"{[person for person in to_delete]} {'was' if len(to_delete) == 1 else 'were'} removed from the room!")
        return redirect("/")

    # renders the page to remove users from the room
    return render_template("del_calendar.html", all_people=all_people)


# prompts the user for a name to create a new calendar with that name
@app.route("/add_calendar", methods=["POST", "GET"])
@session_required
def add_calendar(this_route="/add_calendar"):

    all_people = get_people()

    if request.method == "POST":
        # fetch the name of the new user 
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

            # searches the database for the user
            person = search_for_user(db,user_id=CalID,user_name=CalName)

            # if one specific entry was not found or is already in the room, prompt the user again
            if not person:
                return insert_flash(this_route,"User not found :(")

            elif CalID in list(all_people.keys()):
                return insert_flash(this_route, "This user is already in the room!")

        # Assemple a new object for the person
            else: #if he exists
                new_person = person
        else:# if they dont
            new_person = create_new_user(db,user_name=CalName)
            
        # add new person to the list of people in this session
        session["active_ids"] += [new_person.id]
        add_user_to_session(db,session_id=session["session_id"], user=new_person)
        return redirect(f"/calendar_info/{new_person.name}/{new_person.id}")

    return render_template("add_calendar.html", all_people=all_people)


# displays the calendar of the chosen name
@app.route("/calendar_info/<string:PName>/<int:PID>", methods=["POST", "GET"])
@session_required
def Calendar_info(PName, PID):

    all_people = get_people()

    person = all_people.get(PID, None)

    # looks for the person through the session
    if not person:
        return apology("user not found", 403, AP=get_people())

    # on update
    if request.method == "POST":

        # Ensures a schedule update occurs
        if not request.form.get("schedule"):
            return apology("missing schedule?", 403, AP=get_people())

        user_update = loads(request.form.get("schedule"))
        if not user_update:
            return apology("missing schedule?", 403, AP=get_people())
        person.schedule = user_update["Schedule"]

        # checks for a new color
        if request.form.get('myColor'):
            person.color = request.form.get('myColor')

        # update database
        update_users(db, person)
        # feedback message to confirm with user
        flash(f"{person.name} has been updated!")
    return render_template("calendar_info.html", all_people=all_people, person=person, days=days, colors=colors) #, custom_color="D32AE1"


# gets the list of calendars in the current session
def get_people():
    if not session["session_id"]:
        return {}
        
    # get raw data on people
    people = get_users_in_session(db, session_id=session["session_id"])

    # convert raw data into a list of Calendar objects
    people = list(map(lambda person: Calendar().load(person), people))

    # convert list of objects into a dictionary {id:object}
    if people:
        return {person.id:person for person in people}
    else:
        return {}

def insert_flash(this_route='/', message="page refreshed", code=0):
    flash(message)
    return redirect(this_route)

def errorhandler(e):
    """Handle error"""
    if not isinstance(e, HTTPException):
        e = InternalServerError()
    return apology(e.name, e.code, AP=get_people())

# Listen for errors
for code in default_exceptions:
    app.errorhandler(code)(errorhandler)

if __name__ == '__main__':
    app.run(debug=False, host="0.0.0.0",port=8080)
