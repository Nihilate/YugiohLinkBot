import praw
import re
import time

import traceback

import Config
import DatabaseHandler
from RequestHandler import RequestHandler
from SubmissionProcessor import SubmissionProcessor

class YugiohLinkBot(object):

    def __init__(self, subredditList):
        self.subredditList = subredditList
        self.requestHandler = RequestHandler()

        #Set up reddit
        self.reddit = praw.Reddit(Config.useragent)
        self.reddit.set_oauth_app_info(client_id=Config.appid, client_secret=Config.appsecret, redirect_uri=Config.redirecturi)
        self.reddit.refresh_access_information(Config.refreshtoken)
        print("Connected to Reddit")

        self.submissionProcessor = SubmissionProcessor(self.reddit, subredditList, self.requestHandler)

        self.submissionsLastProcessed = 0
        self.updateTime = time.time()

    def run(self):
        try:
            print("Starting stream")
            commentStream = praw.helpers.comment_stream(self.reddit, self.subredditList, limit=1000, verbosity=0)

            for comment in commentStream:
                
                if ((time.time() - self.updateTime) > Config.tcgUpdateInterval * 60 * 60):
                    DatabaseHandler.updateTCGCardlist()
                    self.updateTime = time.time()

                if ((time.time() - self.submissionsLastProcessed) > Config.submissionProcessingInterval * 60 * 60):
                    self.submissionProcessor.processSubmissions(100)
                    self.submissionsLastProcessed = time.time()
                
                #print("Found comment")
                #If we've already seen this comment, ignore it
                if DatabaseHandler.commentExists(comment.id):
                    continue

                #If the post has been deleted, getting the author will return an error
                try:
                    author = comment.author.name
                except Exception as e:
                    continue

                #If this is one of our own comments, ignore it
                if (author == 'YugiohLinkBot'):
                    continue

                reply = self.requestHandler.buildResponse(comment.body)                

                try:
                    if reply:
                        cards = re.findall('\[\*\*(.+?)\*\*\]\(', reply)
                        for card in cards:
                            DatabaseHandler.addRequest(card, author, comment.subreddit)
                        
                        DatabaseHandler.addComment(comment.id, author, comment.subreddit, True)
                        #comment.reply(reply)
                        print("Comment made.\n")
                    else:
                        if ('{' in comment.body and '}' in comment.body):
                            print('')
                        DatabaseHandler.addComment(comment.id, author, comment.subreddit, False)
                except Exception as e:
                    print("Reddit probably broke when replying:" + str(e) + '\n')
                    
        except Exception as e:
            print("Error with comment stream: " + str(e))
            traceback.print_exc()
