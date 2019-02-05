import time
from app import app, db, models
from app.views.functions.userfunctions import getAllUsers, getUserObject
import datetime

def monitor_deletions():
    while(True):
        users = getAllUsers()

        for i in users:
            if i.flaggedForDeletion and i.timestamp < datetime.datetime.now() - datetime.timedelta(seconds=60):
                db.session.delete(i)

        db.session.commit()

        time.sleep(30)

        print("CHECKING WOOOOO")
