# File name: TCGCardnameHandler.py
# Description: Handles the database of YuGiOh cardnames and converts requested strings into cardnames with proper capitalisation and punctuation (which are required by the API).
#              If it can't find the right cardname, it uses a differential search to find the next closest thing.

import requests
import json
import sqlite3
import difflib

#connect to the name database so we have something to fall back on if the API is unavailable
sqlConn = sqlite3.connect('cardnames.db')
sqlCur = sqlConn.cursor()
sqlCur.execute('CREATE TABLE IF NOT EXISTS cards(NAMELOWER TEXT, NAMEREAL TEXT)')
sqlConn.commit()

cardArray = []

#
#  Backs up the card list to a database and adds anything it hasn't seen before.
#
def updateCards():
    #gets the cardname list from the server
    print("Updating card sets.")
    req = requests.get("http://yugiohprices.com/api/card_names")
    cardnameList = json.loads(json.dumps(req.json()))

    #for each card, if it's not in the database, add it
    for card in cardnameList:
        if (sqlCur.execute("SELECT count(*) FROM cards WHERE NAMELOWER = ?", (card.lower(),)).fetchone()[0] == 0):
                print('Adding new card: %s' % card)
                sqlCur.execute('INSERT INTO cards VALUES(?, ?)', (card.lower(), card))
                sqlConn.commit()

    #build the array with all cardnames in it (we need it to be an array for the differential search to work
    buildCardArray()

#
#  Builds an array for use with differential searching.
#
def buildCardArray():
    #clear the current array and rebuild from the database
    print("Building card array.\n")
    cardArray[:] = []
    cardlist = sqlCur.execute("SELECT * FROM cards")

    for card in cardlist:
        cardArray.append(card[0])

#
#  Finds the closest card to a give string and returns its "real" name. Returns None if nothing found.
#
def findCardname(cardname):
    #if the name in lowercase matches something in the lowercase section of the db, return the proper name of that card
    if (sqlCur.execute("SELECT count(*) FROM cards WHERE NAMELOWER = ?", (cardname.lower(),)).fetchone()[0] == 1):
        return sqlCur.execute("SELECT NAMEREAL FROM cards WHERE NAMELOWER = ?", (cardname.lower(),)).fetchone()[0]
    #else use difflib to find the nex closest thing. return none if it can't find anything remotely close
    else:
        closestCardname = difflib.get_close_matches(cardname.lower(), cardArray, 1, 0.95)
        if (len(closestCardname) > 0):
            return sqlCur.execute("SELECT NAMEREAL FROM cards WHERE NAMELOWER = ?", (closestCardname[0],)).fetchone()[0]
        else:
            return None
