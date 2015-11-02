import CardDataHandler
import DatabaseHandler
import re
import pprint

MONSTER_CARD_TEMPLATE_NORMAL = ('{name}{image} - {wikia}{infosyntax}{pricedata}')


MONSTER_CARD_TEMPLATE_EXPANDED = ('{name}{image} - {wikia}{infosyntax}{pricedata}\n\n'
                                '^({leveltype}{level}{cardtype}{types}{attribute})  \n'
                                '^({stats})\n\n'
                                '{text}\n\n'
                                '{att}{defn}')
    
SPELL_CARD_TEMPLATE_NORMAL = ('{name}{image} - {wikia}{infosyntax}{pricedata}')

SPELL_CARD_TEMPLATE_EXPANDED = ('{name}{image} - {wikia}{infosyntax}{pricedata}\n\n'
                                '^({cardtype}{cardproperty})  \n'
                                '^({stats})\n\n'
                                '{text}')

BASE_SIGNATURE = '^^To ^^use: ^^{Normal} ^^or ^^{{Expanded}}) ^^| [^^Issues?](http://www.reddit.com/message/compose/?to=Nihilate) ^^| [^^Source](https://github.com/Nihilate/YugiohLinkBot)'
FLAVOUR_SIGNATURE = ' ^^| [^^\/u/TheDungeonCrawler ^^is ^^the ^^winner ^^of ^^the ^^scavenger ^^hunt](https://www.reddit.com/r/yugioh/comments/3kxin5/yugioh_arcv_episode_73_discussion_the_crawling/cv1hcw1)'
SIGNATURE = BASE_SIGNATURE + FLAVOUR_SIGNATURE

def getSignature():
    return SIGNATURE

def formatCardData(card, isExpanded):
    if isExpanded:
        requestStats = DatabaseHandler.getStats(card['name'])
        
        if card['cardtype'].lower() == 'monster':
            return MONSTER_CARD_TEMPLATE_EXPANDED.format(
                name = '[**{}**]'.format(card['name']),
                image = '({})'.format(card['image']) if card['image'] else 'http://i.imgur.com/paNkvJ5.jpg',
                wikia = '[Wikia]({})'.format(card['wikia']),
                infosyntax = ', ' if card['pricedata'] else '',
                pricedata = '[($)]({})'.format(card['pricedata']) if card['pricedata'] else '',
                leveltype = '{}: '.format(card['leveltype']),
                level = '{}, '.format(card['level']),
                cardtype = 'Category: {}, '.format(card['cardtype'].title()),
                types = 'Type: {}, '.format(' / '.join(str(i[1]) for i in enumerate(card['types']))),
                attribute = 'Attribute: {}'.format(card['attribute'].upper()),
                text = '>{}'.format(card['text']),
                att = '>ATK: {}, '.format(card['att']),
                defn = 'DEF: {}'.format(card['def']),
                stats = 'Stats: {total} requests - {percentage}% of all requests'.format(
                    total=requestStats['total'],
                    percentage=str(round(requestStats['totalAsPercentage'],2))))
        else:
            return SPELL_CARD_TEMPLATE_EXPANDED.format(
                name = '[**{}**]'.format(card['name']),
                image = '({})'.format(card['image']) if card['image'] else 'http://i.imgur.com/paNkvJ5.jpg',
                wikia = '[Wikia]({})'.format(card['wikia']),
                infosyntax = ', ' if card['pricedata'] else '',
                pricedata = '[($)]({})'.format(card['pricedata']) if card['pricedata'] else '',
                cardtype = 'Category: {}, '.format(card['cardtype'].title()),
                cardproperty = 'Property: {}'.format(card['property']),
                text = '>{}'.format(card['text']),
                stats = 'Stats: {total} requests - {percentage}% of all requests'.format(
                    total=requestStats['total'],
                    percentage=str(round(requestStats['totalAsPercentage'],2))))
    else:
        if card['cardtype'].lower() == 'monster':
            return MONSTER_CARD_TEMPLATE_NORMAL.format(
                name = '[**{}**]'.format(card['name']),
                image = '({})'.format(card['image']) if card['image'] else 'http://i.imgur.com/paNkvJ5.jpg',
                wikia = '[Wikia]({})'.format(card['wikia']),
                infosyntax = ', ' if card['pricedata'] else '',
                pricedata = '[($)]({})'.format(card['pricedata']) if card['pricedata'] else '')
        else:
            return SPELL_CARD_TEMPLATE_NORMAL.format(
                name = '[**{}**]'.format(card['name']),
                image = '({})'.format(card['image']) if card['image'] else 'http://i.imgur.com/paNkvJ5.jpg',
                wikia = '[Wikia]({})'.format(card['wikia']),
                infosyntax = ', ' if card['pricedata'] else '',
                pricedata = '[($)]({})'.format(card['pricedata']) if card['pricedata'] else '')

def buildRequestComment(cardname, isExpanded):
    data = CardDataHandler.getCardData(cardname)
    if data:
        return formatCardData(data, isExpanded)
    else:
        return None
