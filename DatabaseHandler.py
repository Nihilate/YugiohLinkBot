'''
DatabaseHandler.py
Handles all connections to the database. The database runs on PostgreSQL and is connected to via psycopg2.
'''

from functools import lru_cache
import psycopg2
import traceback
import requests
import json
import difflib
from Util import timing

DBNAME = ''
DBUSER = ''
DBPASSWORD = ''
DBHOST = ''

TCGArray = []

url = r.get_authorize_url('Roboragi', 'identity edit privatemessages read submit vote', True)
import webbrowser
webbrowser.open(url)

try:
    import Config
    DBNAME = Config.dbname
    DBUSER = Config.dbuser
    DBPASSWORD = Config.dbpassword
    DBHOST = Config.dbhost
except ImportError:
    pass

conn = psycopg2.connect("dbname='" + DBNAME + "' user='" + DBUSER + "' host='" + DBHOST + "' password='" + DBPASSWORD + "'")
cur = conn.cursor()

#Sets up the database and creates the databases if they haven't already been made.
def setup():
    try:
        conn = psycopg2.connect("dbname='" + DBNAME + "' user='" + DBUSER + "' host='" + DBHOST + "' password='" + DBPASSWORD + "'")
    except:
        print("Unable to connect to the database")

    cur = conn.cursor()

    #Create cardname table
    try:
        cur.execute('CREATE TABLE cardnames (id SERIAL PRIMARY KEY, name varchar(320))')
        conn.commit()
    except Exception as e:
        #traceback.print_exc()
        cur.execute('ROLLBACK')
        conn.commit()

    #Create requests table
    try:
        cur.execute('CREATE TABLE requests (id SERIAL PRIMARY KEY, name varchar(320), requester varchar(50), subreddit varchar(50), requesttimestamp timestamp DEFAULT current_timestamp)')
        conn.commit()
    except Exception as e:
        #traceback.print_exc()
        cur.execute('ROLLBACK')
        conn.commit()

    #Create comments table
    try:
        cur.execute('CREATE TABLE comments (commentid varchar(16) PRIMARY KEY, commenter varchar(50), subreddit varchar(50), hadRequest boolean, requesttimestamp timestamp DEFAULT current_timestamp)')
        conn.commit()
    except Exception as e:
        #traceback.print_exc()
        cur.execute('ROLLBACK')
        conn.commit()

@timing
def updateTCGCardlist():
    try:
        global TCGArray
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

@lru_cache(maxsize=128)
def getClosestTCGCardname(searchText):
    try:
        global TCGArray

        closestCard = difflib.get_close_matches(searchText, TCGArray, 1, 0.75)

        if closestCard:
            return closestCard[0]
        else:
            return None
        
    except:
        traceback.print_exc()
        print("Error finding cards.")
        return None

setup()
updateTCGCardlist();
