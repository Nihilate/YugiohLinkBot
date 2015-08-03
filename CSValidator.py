# File name: CSValidator.py
# Description: Comment/submission validator. Used to make sure that a given comment or submission is a valid target for the bot.

import sqlite3

sqlConn = sqlite3.connect('comments.db', 15)
sqlCur = sqlConn.cursor()

#
#  Checks if the bot has already posted in this comment chain (to avoid malicious infinite replies)
#  Requires an instance of our Reddit connection so it can check comments other than the one its given
#
def isBotAParent(prawInstance, comment, username):
    try:
        if (comment.is_root == True and comment.author.name != username):
            return False
        elif (comment.author.name == username):
            return True
    except AttributeError:
        print("Found deleted comment in chain.")

    # There's a bizzare bug involving deleted submissions/comments that I can't diagnose, this should fix the edge cases 
    # Worst case scenario is that a couple of people get missed
    try:
        return isBotAParent(prawInstance, prawInstance.get_info(thing_id=comment.parent_id), username)
    except:
        return True
#
#  Checks if a submission is a valid target for the bot
#
def isValidSubmission(submission):
    #ignore submissions we've already checked
    sqlCur.execute('SELECT * FROM oldcomments WHERE ID=?', [submission.id])
    if sqlCur.fetchone():
        return False

    #ignore deleted threads
    try:
        author = submission.author.name
    except AttributeError:
        return False

    return True

#
#  Checks if a comment is a valid target for the bot
#
def isValidComment(prawInstance, comment, username):
    #ignore comments we've already checked
    sqlCur.execute('SELECT * FROM oldcomments WHERE ID=?', [comment.id])
    if sqlCur.fetchone():
        return False
    
    #ignore deleted comments
    try:
        author = comment.author.name
    except AttributeError:
        return False

    #ignore our own comments
    if (author == username):
        return False

    #ignore bot loops and add them to "already seen" pile 
    if (isBotAParent(prawInstance, comment, username) == True):
        print("DANGER - someone is replying directly to the bot!\n")
        try:
            sqlCur.execute('INSERT INTO oldcomments VALUES(?)', [comment.id])
            sqlConn.commit()
        except:
            if sqlConn:
                sqlConn.rollback()
        return False

    return True
