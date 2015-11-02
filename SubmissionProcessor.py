import DatabaseHandler
import re
import traceback

class SubmissionProcessor(object):
    def __init__(self, reddit, subredditList, requestHandler):
        self.reddit = reddit
        self.subredditList = subredditList
        self.requestHandler = requestHandler

    def processSubmissions(self, num):
        subreddits = self.reddit.get_subreddit(self.subredditList)
        
        for submission in subreddits.get_new(limit=num):
            #If we've already seen this submission, ignore it
            if DatabaseHandler.commentExists(submission.id):
                continue

            #If the post has been deleted, getting the author will return an error
            try:
                author = submission.author.name
            except Exception as e:
                continue

            #If this is one of our own submissions, ignore it
            if (author == 'YugiohLinkBot'):
                continue

            reply = self.requestHandler.buildResponse(submission.selftext)

            try:
                if reply:
                    cards = re.findall('\[\*\*(.+?)\*\*\]\(', reply)
                    for card in cards:
                        DatabaseHandler.addRequest(card, author, submission.subreddit)

                    if("VENT THREAD" in submission.title):
                        reply = self.convertCase(True, reply)
                    elif("happiness thread" in submission.title):
                        reply = self.convertCase(False, reply)

                    DatabaseHandler.addComment(submission.id, author, submission.subreddit, True)
                    #submission.add_comment(reply)
                    print("Comment made.\n")
                else:
                    if ('{' in submission.selftext and '}' in submission.selftext):
                        print('')
                    DatabaseHandler.addComment(submission.id, author, submission.subreddit, False)
            except Exception as e:
                traceback.print_exc()
                print("Reddit probably broke when replying:" + str(e) + '\n')

    def convertCase(self, capitalise, reply):
        links = []

        #find and store all links using regex
        for match in re.finditer("\((http:[^)]*)\)", reply, re.S):
            links.append(match.group(1))

        #change the case
        if (capitalise == True):
            reply = reply.upper()
        else:
            reply = reply.lower()

        #replace the links with the original ones we stored
        for idx, match in enumerate(re.finditer("\((http:[^)]*)\)", reply, re.I)):
            reply = reply.replace(match.group(1), links[idx])

        return reply
        
