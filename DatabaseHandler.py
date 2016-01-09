'''
DatabaseHandler.py
Handles all connections to the database. The database runs on PostgreSQL and is connected to via psycopg2.
'''

from functools import lru_cache
import psycopg2
import traceback
import json
import requests
import difflib
from Util import timing

import Config

#Sets up the database and creates the databases if they haven't already been made.
def setup():
    #Create cardname table
    try:
        cur.execute('CREATE TABLE cardnames (id SERIAL PRIMARY KEY, name varchar(320))')
        conn.commit()
    except Exception as e:
        cur.execute('ROLLBACK')
        conn.commit()

    #Create requests table
    try:
        cur.execute('CREATE TABLE requests (id SERIAL PRIMARY KEY, name varchar(320), requester varchar(50), subreddit varchar(50), requesttimestamp timestamp DEFAULT current_timestamp)')
        conn.commit()
    except Exception as e:
        cur.execute('ROLLBACK')
        conn.commit()

    #Create comments table
    try:
        cur.execute('CREATE TABLE comments (commentid varchar(16) PRIMARY KEY, commenter varchar(50), subreddit varchar(50), hadRequest boolean, requesttimestamp timestamp DEFAULT current_timestamp)')
        conn.commit()
    except Exception as e:
        cur.execute('ROLLBACK')
        conn.commit()

@timing
def updateTCGCardlist():
    global TCGArray

    try:
        numOfChanges = 0

        #gets the cardname list from the server
        print("Updating card set.")
        req = requests.get("http://yugiohprices.com/api/card_names")
        cardnameList = json.loads(json.dumps(req.json()))

        #for each card, if it's not in the database, add it
        for card in cardnameList:
            cur.execute("select exists(select * from cardnames where name = %s)", (card,))
            if not cur.fetchone()[0]:
                try:
                    cur.execute("insert into cardnames (name) values (%s)", (card,))
                    conn.commit()
                    numOfChanges += 1
                except:
                    cur.execute('ROLLBACK')
                    conn.commit()

        if (not TCGArray) or (numOfChanges > 0):
            print('Building array.')
            cur.execute("select name from cardnames")
            cardnames = cur.fetchall()

            TCGArray = []
            
            for card in cardnames:
                TCGArray.append(card[0])

        print('Card set updated. Number of changes = ' + str(numOfChanges) + '.')
            
    except:
        traceback.print_exc()
        print('Card updating failed.')

# Adds a comment to the "already seen" database. Also handles submissions, which have a similar ID structure.
def addComment(commentid, requester, subreddit, hadRequest):
    try:
        subreddit = str(subreddit).lower()
        
        cur.execute('INSERT INTO comments (commentid, commenter, subreddit, hadRequest) VALUES (%s, %s, %s, %s)', (commentid, requester, subreddit, hadRequest))
        conn.commit()
    except Exception as e:
        traceback.print_exc()
        cur.execute('ROLLBACK')
        conn.commit()

#Returns true if the comment/submission has already been checked.
def commentExists(commentid):
    try:
        cur.execute('SELECT * FROM comments WHERE commentid = %s', (commentid,))
        if (cur.fetchone()) is None:
            return False
        else:
            return True
    except Exception as e:
        traceback.print_exc()
        cur.execute('ROLLBACK')
        conn.commit()
        return True
        
#Adds a request to the request-tracking database.
def addRequest(name, requester, subreddit):
    try:
        subreddit = str(subreddit).lower()

        if ('nihilate' not in subreddit):
            cur.execute('INSERT INTO requests (name, requester, subreddit) VALUES (%s, %s, %s)', (name, requester, subreddit))
            conn.commit()
    except Exception as e:
        traceback.print_exc()
        cur.execute('ROLLBACK')
        conn.commit()

@lru_cache(maxsize=128)
def getClosestTCGCardname(searchText):
    try:
        global TCGArray
        closestCard = difflib.get_close_matches(searchText, TCGArray, 1, 0.95)

        if closestCard:
            return closestCard[0]
        else:
            return None
        
    except:
        traceback.print_exc()
        print("Error finding cards.")
        return None

def getStats(searchText):
    try:
        requestDict = {}
        
        cur.execute("SELECT COUNT(*) FROM requests")
        total = int(cur.fetchone()[0]) + 1
        cur.execute("SELECT COUNT(*) FROM requests WHERE name = %s", (searchText, ))
        requestTotal = int(cur.fetchone()[0]) + 1
        #+1 since we add to requests AFTER we call this
        
        requestDict['total'] = requestTotal

        totalAsPercentage = (float(requestTotal)/total) * 100
        requestDict['totalAsPercentage'] = totalAsPercentage

        return requestDict

    except Exception as e:
        traceback.print_exc()
        cur.execute('ROLLBACK')
        conn.commit()
        return None

TCGArray = []
conn = psycopg2.connect("dbname='" + Config.dbname + "' user='" + Config.dbuser + "' host='" + Config.dbhost + "' password='" + Config.dbpassword + "'")
cur = conn.cursor()

setup()
updateTCGCardlist()
