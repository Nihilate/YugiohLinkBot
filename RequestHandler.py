import re
import traceback

from CommentBuilder import buildRequestComment
from CommentBuilder import getSignature

class RequestHandler(object):
    # Normal - e.g. {Blue-Eyes White Dragon}
    normalRequestQuery = re.compile("(?<=(?<!\{)\{)([^{}]*)(?=\}(?!\}))")
    # Expanded - e.g. {{Blue-Eyes White Dragon}}
    expandedRequestQuery = re.compile("\{{2}([^}]*)\}{2}")

    
    def __init__(self):
        pass

    def getNormalRequests(self, comment):
        return self.normalRequestQuery.findall(comment)

    def getExpandedRequests(self, comment):
        return self.expandedRequestQuery.findall(comment)
        
    def buildResponse(self, comment):
        try:
            reply = ''
            normalRequests = self.getNormalRequests(comment)
            expandedRequests = self.getExpandedRequests(comment)

            #If there are 10 or more expanded requests, turn them all into normal requests
            #Reddit has a 10k character limit
            if (len(normalRequests) + len(expandedRequests)) >= 10:
                normalRequests.extend(expanded)
                expandedRequests = []

            for card in normalRequests:
                requestComment = buildRequestComment(card, False)
                if requestComment:
                    reply += requestComment + '\n\n'

            for card in expandedRequests:
                requestComment = buildRequestComment(card, True)
                if requestComment:
                    reply += requestComment + '\n\n'

            if reply:
                reply += '---\n\n' + getSignature()
                return reply
            else:
                return None
        except:
            traceback.print_exc()
