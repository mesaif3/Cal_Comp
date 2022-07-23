import os
import requests
import urllib.parse

import csv
from flask import redirect, render_template, request, session
from functools import wraps
from json import loads

days = ["Monday", "Tuesday", "Wednesday",
        "Thursday", "Friday", "Saturday", "Sunday"]

colors=[
  "primary",
  "success",
  "info",
  "warning",
  "danger",
  "dark"]

def apology(message, code=400):
    """Render message as an apology to user."""
    def escape(s):
        """
        Escape special characters.

        https://github.com/jacebrowning/memegen#special-characters
        """
        for old, new in [("-", "--"), (" ", "-"), ("_", "__"), ("?", "~q"),
                         ("%", "~p"), ("#", "~h"), ("/", "~s"), ("\"", "''")]:
            s = s.replace(old, new)
        return s
    return render_template("apology.html", top=code, bottom=escape(message)), code


def session_required(f):
    """
    Decorate routes to require login.

    https://flask.palletsprojects.com/en/1.1.x/patterns/viewdecorators/
    """
    @wraps(f)
    def decorated_function(*args, **kwargs):
        if session.get("session_id") is None:
            return redirect("/join_session")
        return f(*args, **kwargs)
    return decorated_function

def get_times(cal):
    times = set()
    for day in days:
        for time in list(cal.schedule[day].keys()):
            times.add(time)
    return list(times)

class Calendar:
    def __init__(self, schedule={}, name='', id=-1, color="primary"):
        def emptyschedule():
            for day in days:
                schedule[day] = {}
            return schedule

        self.color = color
        self.name = name if name else "__badname__"
        self.id = id
        self.schedule = schedule
        for day in days:
            if not(day in schedule.keys()):
                 self.schedule = emptyschedule()
                 break


    # return Calendar as a table

    def __str__(self):
        # return tb(self.aslist(), headers=days)
        return f"{self.name}#{self.id:04d}"

    def __eq__(self, other):
        truth_table = {
        self.name == other.name,
        self.id == other.id,
        self.color == other.color,
        self.schedule == other.schedule
        }
        return truth_table == {True}


    # Calendar + Calendar = new Calendar
    def __add__(self, otherCalendar):
        temp_time = set()
        for time in (get_times(self)+get_times(otherCalendar)):
            temp_time.add(time)
        temp_time = list(temp_time)
        temp_time.sort(key=int)

        temp_week = {}
        temp_day = {}
        for day in days:
            for time in temp_time:
                temp_day[time] = (
                    f'{self.schedule[day].get(time,"")}, {otherCalendar.schedule[day].get(time,"")}').strip(", ")
            temp_week[day] = temp_day
            temp_day = {}
        temp_week["Times"] = get_times(self)
        return Calendar(schedule=temp_week)

    # loads a schedule into the Calandar from an SQL query
    def load(self, SQL_query):
        if type(SQL_query) == list:
            SQL_query = SQL_query[0]

        self.schedule = loads(SQL_query["user_schedule"])
        self.name     = SQL_query["user_name"]
        self.id       = int(SQL_query["user_id"])
        self.color    = SQL_query["user_color"]

        return self

    # converts from dictionary of dictionaries to dictionary of lists
    def aslist(self):
        temp_week = {}
        temp_week["Time"] = get_times(self)
        for day in days:
            temp_week[day] = list(self.schedule[day].values())
        return temp_week


