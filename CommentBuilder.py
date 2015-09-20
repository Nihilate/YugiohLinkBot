# File name: CommentBuilder.py
# Description: Builds comments used to reply to bot requests.

import re
import requests
import TCGCardnameHandler
import OCGHandler

#
#  Builds a reply using a given string (usually the submission text or comment text).
#  isSubmission is whether the text is from a comment or submission (which changes the reply slightly)
#
def buildReply(commentText, isSubmission):

    #track which cards have been added so we above posting multiple of the same cards
    foundCards = []
    commentReply = ''

    commentText = re.sub(r"^>(.*?)(\n|$)", "", commentText, flags=re.MULTILINE)

    #add replies from {small} calls and {{large}} calls
    commentReply = commentReply + buildSmallRequests(commentText, foundCards)
    commentReply = commentReply + buildLargeRequests(commentText, foundCards)

    #if there were cars found, build the footer (and header)
    if (commentReply != ''):
        if (isSubmission == True):
            commentReply = "**Cards found in this post's main text:**\n\n" + commentReply
        commentReply = commentReply + buildCommentFooter()
        commentReply = removeErrata(commentReply)

    return commentReply

#
#  CONVERTS ALL TEXT IN THE REPLY TO UPPERCASE or lowercase (except for links, which will break otherwise)
#
def convertCase(capitalise, reply):
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

#
#  Converts /!? to HTML character codes to placate the ravenous API
#
def convertToSpecialCharacters(input):
    return input.replace('/', '%2F').replace('!', '%21').replace('?', '%3F').replace('&amp;', '%26')

#
#  Converts /!? back from HTML character codes to make sure we post the correct title in our post
#
def convertFromSpecialCharacters(input):
    return input.replace('%2F', '/').replace('%21', '!').replace('%3F', '?').replace('%26', '&amp;')

#
#  Cards with errata have a dirty great <!--@@@ ERRATA WARNING @@@--> in their card text. We want to remove that.
#
def removeErrata(input):
    for match in re.finditer("(\<!--[^}]*--\>)", input, re.S):
        input = input.replace(match.group(1), '')
    return input

#
#  Gets the card image for a given cardname
#
def requestImage(cardName):
    return requests.get("http://yugiohprices.com/api/card_image/" + cardName)

#
#  Builds the entries for small card requests
#
def buildSmallRequests(text, foundCards):
    reply = ''

    for match in re.finditer("(?<=(?<!\{)\{)([^{}]*)(?=\}(?!\}))", text, re.S):
        print("(N) Searching for: " + match.group(1))
        searchedCard = match.group(1)
        
        #tries to fix the case on the card name, converts special characters, and adds special YGO naming conventions
        cardName = TCGCardnameHandler.findCardname(searchedCard)

        #if card has already been searched this comment
        if(cardName in foundCards):
            print("Card already exists in comment.")
            continue

        #if nothing found
        if(cardName is not None):
            #if it finds a card image, it means it's a legit card, therefore we can build the other URLs too
            cardImageRequest = requestImage(convertToSpecialCharacters(cardName))

            #if the request is valid
            if (cardImageRequest.status_code == 200):
                print("Card found: " + cardName)
                foundCards.append(cardName)
                
                #build the comment
                reply += buildSmallCardComment(cardName, cardImageRequest)
                reply += "  \n"
            else:
                print("Card not found.")
        else:
            cardData = OCGHandler.get_data_of_closest(searchedCard)
            
            if (cardData is not None):
                cardName = cardData['name']

                #if card has already been searched this comment
                if(cardName in foundCards):
                    print("Card already exists in comment.")
                    break
                
                print("Card found: " + cardName)
                foundCards.append(cardName)
                
                #build the comment
                reply += buildSmallOCGCardComment(cardData)
                reply += "  \n"
            else:
                print("Card not found.")
            

    #add a horizontal rule once we're done
    if(reply != ''):
        reply = reply + '***\n'

    return reply

#
#  Builds the entries for small card requests
#
def buildLargeRequests(text, foundCards):
    reply = ''

    for match in re.finditer("\{{2}([^}]*)\}{2}", text, re.S):
        print("(E) Searching for: " + match.group(1))
        searchedCard = match.group(1)
        
        #tries to fix the case on the card name, converts special characters, and adds special YGO naming conventions
        cardName = TCGCardnameHandler.findCardname(searchedCard)
        
        #if card has already been searched this comment
        if(cardName in foundCards):
            print("Card already exists in comment.")
            continue

        #if nothing found
        if(cardName is not None):
            #if it finds a card image, it means it's a legit card, therefore we can build the other URLs too
            cardImageRequest = requestImage(convertToSpecialCharacters(cardName))

            #if the request is valid
            if (cardImageRequest.status_code == 200):
                print("Card found: " + cardName)
                foundCards.append(cardName)
                
                #build the comment
                reply += buildLargeCardComment(cardName, cardImageRequest)
                reply += "  \n"
            else:
                print("Card not found.")
        else:
            cardData = OCGHandler.get_data_of_closest(searchedCard)
            
            if (cardData is not None):
                cardName = cardData['name']

                #if card has already been searched this comment
                if(cardName in foundCards):
                    print("Card already exists in comment.")
                    break
                
                print("Card found: " + cardName)
                foundCards.append(cardName)
                
                #build the comment
                reply += buildLargeOCGCardComment(cardData)
                reply += "  \n"
            else:
                print("Card not found.")
            

    #add a horizontal rule once we're done
    if(reply != ''):
        reply = reply + '***\n'

    return reply

#
#  Builds a single entry for a small card request
#
def buildSmallCardComment(cardName, cardImageRequest):
    #Builds the urls
    cardImageURL = cardImageRequest.url
    cardWikiURL = "http://yugioh.wikia.com/wiki/" + cardName.replace (" ", "_")
    cardPriceURL = "http://yugiohprices.com/card_price?name=" + cardName.replace (" ", "+")

    #change the special characters back to normal
    cardName = convertFromSpecialCharacters(cardName)

    return "[" + cardName + "](" + cardImageURL + ") - [Wikia](" + cardWikiURL + "), [($)](" + cardPriceURL + ")"

#
#  Builds a single entry for a small OCG card request
#
def buildSmallOCGCardComment(cardData):
    cardName = cardData['name']
    cardImageURL = cardData['image']
    cardWikiURL = "http://yugioh.wikia.com/wiki/" + cardName.replace (" ", "_")
    cardName = convertFromSpecialCharacters(cardName)

    return "[" + cardName + "](" + cardImageURL + ") - [Wikia](" + cardWikiURL + ")"
    
#
#  Builds a single entry for a large card request
#
def buildLargeCardComment(cardName, cardImageRequest):
    #Builds the urls
    cardImageURL = cardImageRequest.url
    cardWikiURL = "http://yugioh.wikia.com/wiki/" + cardName.replace (" ", "_")
    cardPriceURL = "http://yugiohprices.com/card_price?name=" + cardName.replace (" ", "+")

    cardDataRequest = requests.get("http://yugiohprices.com/api/card_data/" + cardName.replace('/','%2F'))
    if (cardDataRequest.status_code == 200):

        #getting card attributes
        cardLevel = cardDataRequest.json()['data']['level']
        cardType = cardDataRequest.json()['data']['card_type']
        cardSubtype = cardDataRequest.json()['data']['type']
        cardFamily = cardDataRequest.json()['data']['family']
        cardProperty = cardDataRequest.json()['data']['property']
        cardText = (cardDataRequest.json()['data']['text']).replace('\n\n', '  \n')
        cardAttack = cardDataRequest.json()['data']['atk']
        cardDefense = cardDataRequest.json()['data']['def']

        #change the special characters back to normal
        cardName = convertFromSpecialCharacters(cardName) 

        commentReply = ''

        #basic comment header
        commentReply += "[" + cardName + "](" + cardImageURL + ") - [Wikia](" + cardWikiURL + "), [($)](" + cardPriceURL + ")  \n>"

        #if it's a monster
        if (cardAttack != None):
            lvlText = 'LVL: '

            #LVL is called Rank for Xyz monsters (apparently)
            if ('Xyz' in cardSubtype.title()):
                lvlText = 'Rank: '
            
            commentReply += lvlText + str(cardLevel) + ", Category: " + cardType.title() + ", Type: " + cardSubtype.title() + ", Attribute: " + cardFamily.title() + "\n\n>" + cardText + "\n\n>ATK: " + str(cardAttack) + ", DEF: " + str(cardDefense) + "\n\n"
        #if its not a monster
        else:
            commentReply += "Category: " + cardType.title() + ", Property: " + cardProperty + "\n\n>" + cardText + "\n\n"

        return commentReply

#
#  Builds a single entry for a large card request
#
def buildLargeOCGCardComment(cardData):
    cardName = cardData['name']
    cardImageURL = cardData['image']
    cardWikiURL = "http://yugioh.wikia.com/wiki/" + cardName.replace (" ", "_")
    cardName = convertFromSpecialCharacters(cardName)

    commentReply = ''

    #basic comment header
    commentReply += "[" + cardName + "](" + cardImageURL + ") - [Wikia](" + cardWikiURL + ")  \n>"
    
    cardType = cardData['type'].title()
    cardText = cardData['description'].replace('\n', '  \n')
    
    if (cardData['type'] == 'monster'):
        lvlText = 'LVL: '
        cardLevel = cardData['monster_level']
        cardFamily = cardData['monster_attribute']
        cardAttack = cardData['monster_attack']
        cardDefense = cardData['monster_defense']
        cardSubtype = ''
        for i, subtype in enumerate(cardData['monster_types']):
            if (i is not 0):
                cardSubtype += '/'
            cardSubtype += cardData['monster_types'][i]

        if ('Xyz' in cardSubtype):
            lvlText = 'Rank: '

        commentReply += lvlText + str(cardLevel) + ", Category: " + cardType + ", Type: " + cardSubtype + ", Attribute: " + cardFamily + "\n\n>" + cardText + "\n\n>ATK: " + cardAttack + ", DEF: " + cardDefense + "\n\n"
    else:
        cardProperty = cardData['spell_trap_property']
        commentReply += "Category: " + cardType + ", Property: " + cardProperty + "\n\n>" + cardText + "\n\n"

    return commentReply

#
#  Builds the comment footer
#
def buildCommentFooter():
    return "\n^^To ^^use: ^^{Normal} ^^or ^^{{Expanded}} ^^| [^^Issues?](http://www.reddit.com/message/compose/?to=Nihilate) ^^| [^^Source](https://github.com/Nihilate/YugiohLinkBot) ^^| [^^\/u/TheDungeonCrawler ^^is ^^the ^^winner ^^of ^^the ^^scavenger ^^hunt](https://www.reddit.com/r/yugioh/comments/3kxin5/yugioh_arcv_episode_73_discussion_the_crawling/cv1hcw1)"
