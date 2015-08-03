# File name: YGOBot.py
# Description: Creates links to Yu-Gi-Oh! cards on Reddit. Can be evoked on specific subreddits by using curly braces.

'''
TODO
Improve the timer code for re-checking/updating the card database
Improve speed? Current cycling through comments/submissions is awkward. Could use comment streams, bu unsure how to handle submissions at the same time.
'''

import praw
import re
import requests
import json
import traceback
import sqlite3
import time

import TCGCardnameHandler
import CommentBuilder
import CSValidator

'''Configuration'''
USERNAME = ''
PASSWORD = ''
USERAGENT = ''
REDDITAPPID = ''
REDDITAPPSECRET = ''

#List of subreddits to search
SUBREDDIT_LIST = ["nihilate", "yugioh", "YGOBinders", "YGOSales", "yugioh101"]
#Update interval in hours
UPDATE_INTERVAL = 6.00
'''End Configuration'''

#Update cardlist and set the last time the cardlist was updated
TCGCardnameHandler.updateCards()
updateTime = time.time()

#imports username/password info from an external config file
try:
    import YGOconfig
    USERNAME = YGOconfig.username
    PASSWORD = YGOconfig.password
    USERAGENT = YGOconfig.useragent
    REDDITAPPID = YGOconfig.appid
    REDDITAPPSECRET = YGOconfig.appsecret
except ImportError:
    pass

#Connects to the sqlite db
sqlConn = sqlite3.connect('comments.db', 15)
sqlCur = sqlConn.cursor()
sqlCur.execute('CREATE TABLE IF NOT EXISTS oldcomments(ID TEXT)')
sqlConn.commit()

#logs in to reddit
r = praw.Reddit(USERAGENT)
'''r.login(USERNAME, PASSWORD)'''

def login():
    try:
        print('Getting Reddit access token')
        r.set_oauth_app_info(client_id=REDDITAPPID, client_secret=REDDITAPPSECRET, redirect_uri='http://127.0.0.1:65010/' 'authorize_callback')

        client_auth = requests.auth.HTTPBasicAuth(REDDITAPPID, REDDITAPPSECRET)
        post_data = {"grant_type": "password", "username": USERNAME, "password": PASSWORD}
        headers = {"User-Agent": USERAGENT}
        response = requests.post("https://www.reddit.com/api/v1/access_token", auth=client_auth, data=post_data, headers=headers)

        r.set_access_credentials(set(['identity', 'read', 'submit']), response.json()['access_token'])
        print('Access token set\n')
    except:
        print('Error with setting up Reddit')
        
# The core function. Rotates through the list of subreddits, finding comments it hasn't already checked, then looking for evocations (curly braces) and finds the relevant cards.
def searchForCards(updateTime):
    try:
        #loops through all subreddits
        for subredditName in SUBREDDIT_LIST:
            subreddit = r.get_subreddit(subredditName)

            #
            #  Checking submissions
            #  Checks the 10 newest submissions for bot calls inside the selfpost text. Ignore /r/MagicTCG because I'm sure they'd hate having their submissions included.
            #
            if (subredditName != 'MagicTCG'):
                for submission in subreddit.get_new(limit=10):

                    #validates that the submission hasn't been checked already and hasn't been deleted
                    if (CSValidator.isValidSubmission(submission) == False):
                        continue

                    try:
                        #builds a reply for the submission's self text and posts it if it turns up something
                        commentReply = CommentBuilder.buildReply(submission.selftext.lower(), True)

                        #if the bot is posting in a vent thread (which are ALL CAPS), make sure the bot talks in CAPS TOO
                        if (commentReply != ''):
                            if("VENT THREAD" in submission.title):
                                commentReply = CommentBuilder.convertCase(True, commentReply)
                            elif("happiness thread" in submission.title):
                                commentReply = CommentBuilder.convertCase(False, commentReply)
                            
                            submission.add_comment(commentReply)
                            print("Comment made.\n")
                            
                    except Exception as e:
                        #if the generated comment is too long, add it to the database and move on
                        traceback.print_exc()
                        print("Error: %s" % (str(e)))

                        try:
                            if ("TOO_LONG" in str(e)):
                                print("Self-post request is too long, adding to database")
                                commentReply = "Hey buddy, I know you want to link a bunch of cards or whatever, but you've tried to link *way* too many. Unlike me, Reddit's software just too mentally and emotionally fragile to deal with more than 10,000 characters, so I can't post a comment that large.\n\nAs a heads up for next time, try using my {normal tags} instead of my {{expanded tags}} - they keep the links but cut off the descriptions, meaning you can post to your hearts content!\n\nNote: replying directly to me with another request will not trigger a response.\n\n***\n" + CommentBuilder.buildCommentFooter()
                                submission.add_comment(commentReply)
                                #add it to the already done pile
                                sqlCur.execute('INSERT INTO oldcomments VALUES(?)', [submission.id])
                                sqlConn.commit()
                            '''else:
                                print("Self-post request has had an error in processing, adding to database")
                                commentReply = "An error has occurred in processing your request. It's (probably) not your fault - sorry for the inconvinience! My developer has been informed, hopefully I'll be fixed soon.\n\n***\n" + CommentBuilder.buildCommentFooter()
                                submission.add_comment(commentReply)'''

                            
                        except sqlite3.Error, e:
                            traceback.print_exc()
                            print("Error adding to database, rolling back.")
                            if sqlConn:
                                sqlConn.rollback()
                        except:
                            traceback.print_exc()
                            print("Error: %s" % (str(e)))
                            
                        continue
                    finally:
                        try:
                            #add the submission id to the "already done" database
                            sqlCur.execute('INSERT INTO oldcomments VALUES(?)', [submission.id])
                            sqlConn.commit()
                        except sqlite3.Error, e:
                            traceback.print_exc()
                            if sqlConn:
                                sqlConn.rollback()
            #
            #  Checking comments
            #  Checks the 50 newest comments for bot calls
            #
            for comment in subreddit.get_comments(limit=50):

                #validates that the bot hasn't already posted in this chain (to avoid infinite loops), that the comment hasn't already been checked and that the comment hasn't been deleted
                if (CSValidator.isValidComment(r, comment, USERNAME) == False):
                    continue
                
                try:
                    #builds a reply for the comment and posts it if it turns up something
                    commentReply = CommentBuilder.buildReply(comment.body, False)

                    #if the bot is posting in a vent thread (which are ALL CAPS), make sure the bot talks in CAPS TOO
                    if (commentReply != ''):
                        if("VENT THREAD" in comment.submission.title):
                            commentReply = CommentBuilder.convertCase(True, commentReply)
                        elif("happiness thread" in comment.submission.title):
                            commentReply = CommentBuilder.convertCase(False, commentReply)

                        #make the reply
                        comment.reply(commentReply)
                        print("Comment made.\n")
                        
                except Exception as e:
                    #if the generated comment is too long, post a "Sorry, too long." comment and move on
                    traceback.print_exc()
                    print("Error: %s" % (str(e)))

                    try:
                        if ("TOO_LONG" in str(e)):
                            print("Comment is too long, adding to database")
                            commentReply = "Hey buddy, I know you want to link a bunch of cards or whatever, but you've tried to link *way* too many. Unlike me, Reddit's software just too mentally and emotionally fragile to deal with more than 10,000 characters, so I can't post a comment that large.\n\nAs a heads up for next time, try using my {normal tags} instead of my {{expanded tags}} - they keep the links but cut off the descriptions, meaning you can post to your hearts content!\n\nNote: replying directly to me with another request will not trigger a response.\n\n***\n" + CommentBuilder.buildCommentFooter()
                            comment.reply(commentReply)

                            #add it to the already done pile
                            sqlCur.execute('INSERT INTO oldcomments VALUES(?)', [comment.id])
                            sqlConn.commit()
                        '''else:
                            print("Comment has had an error in processing, adding to database")
                            commentReply = "An error has occurred in processing your request. It's (probably) not your fault - sorry for the inconvinience! My developer has been informed, hopefully I'll be fixed soon.\n\n***\n" + CommentBuilder.buildCommentFooter()
                            comment.reply(commentReply)'''                    
                    except sqlite3.Error, e:
                        traceback.print_exc()
                        print("Error adding to database, rolling back.")
                        if sqlConn:
                            sqlConn.rollback()
                    except:
                        traceback.print_exc()
                        print("Error: %s" % (str(e)))

                    continue
                        
                finally:
                    try:
                        #add the submission id to the "already done" database
                        sqlCur.execute('INSERT INTO oldcomments VALUES(?)', [comment.id])
                        sqlConn.commit()
                    except sqlite3.Error, e:
                        traceback.print_exc()
                        print("Error adding to database, rolling back.")
                        if sqlConn:
                            sqlConn.rollback()
    except:
        print('Error connecting to Reddit. Trying to login.')
        login()
                

#
#  MAIN LOOP
#
while True:
    #used for checking how long a run of the comments/submissions took
    initTime = time.time()
    
    try:
        #search for cards
        searchForCards(updateTime)

        #  Update the cardname list once every X hours
        if ((time.time() - updateTime) > UPDATE_INTERVAL * 60 * 60):
            TCGCardnameHandler.updateCards()
            updateTime = time.time()
            
    except Exception as e:
        traceback.print_exc()

    #print how long the run took and wait a little while (to avoid spamming Reddit with requests)
    print("Run complete: %0.2fs\n" % (time.time()-initTime))
    time.sleep(5)
