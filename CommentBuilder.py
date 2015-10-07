from CardHandler import getCard
import re
import pprint

MONSTER_CARD_TEMPLATE_NORMAL = ('{name}{image} - {wikia}{infosyntax}{pricedata}')


MONSTER_CARD_TEMPLATE_EXPANDED = ('{name}{image} - {wikia}{infosyntax}{pricedata}\n\n'
                                '^({leveltype}{level}{cardtype}{types}{attribute})\n\n'
                                '{text}\n\n'
                                '{att}{defn}')
    
SPELL_CARD_TEMPLATE_NORMAL = ('{name}{image} - {wikia}{infosyntax}{pricedata}')

SPELL_CARD_TEMPLATE_EXPANDED = ('{name}{image} - {wikia}{infosyntax}{pricedata}\n\n'
                                '^({cardtype}{cardproperty})\n\n'
                                '{text}')

BASE_SIGNATURE = '^^To ^^use: ^^{Normal} ^^or ^^{{Expanded}}) ^^| [^^Issues?](http://www.reddit.com/message/compose/?to=Nihilate) ^^| [^^Source](https://github.com/Nihilate/YugiohLinkBot)'
FLAVOUR_SIGNATURE = ' ^^| [^^\/u/TheDungeonCrawler ^^is ^^the ^^winner ^^of ^^the ^^scavenger ^^hunt](https://www.reddit.com/r/yugioh/comments/3kxin5/yugioh_arcv_episode_73_discussion_the_crawling/cv1hcw1)'
SIGNATURE = BASE_SIGNATURE + FLAVOUR_SIGNATURE

def addSeparator():
    return '\n\n'

def getFormattedCard(card, isExpanded):
    if isExpanded:
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
                defn = 'DEF: {}'.format(card['def']))
        else:
            return SPELL_CARD_TEMPLATE_EXPANDED.format(
                name = '[**{}**]'.format(card['name']),
                image = '({})'.format(card['image']) if card['image'] else 'http://i.imgur.com/paNkvJ5.jpg',
                wikia = '[Wikia]({})'.format(card['wikia']),
                infosyntax = ', ' if card['pricedata'] else '',
                pricedata = '[($)]({})'.format(card['pricedata']) if card['pricedata'] else '',
                cardtype = 'Category: {}, '.format(card['cardtype'].title()),
                cardproperty = 'Property: {}'.format(card['property']),
                text = '>{}'.format(card['text']))
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

def buildComment(comment):
    reply = ''
    normal = []
    expanded = []
    
    for match in re.finditer("(?<=(?<!\{)\{)([^{}]*)(?=\}(?!\}))", comment, re.S):
        card = getCard(match.group(1))
        if (card['name'] not in (str(i[1]['name']) for i in enumerate(normal))) and (card['name'] not in (str(i[1]['name']) for i in enumerate(expanded))):
            normal.append(card)
        else:
            print("Card already exists in comment.")
    for match in re.finditer("\{{2}([^}]*)\}{2}", comment, re.S):
        card = getCard(match.group(1))
        if (card['name'] not in (str(i[1]['name']) for i in enumerate(normal))) and (card['name'] not in (str(i[1]['name']) for i in enumerate(expanded))):
            expanded.append(card)
        else:
            print("Card already exists in comment.")

    if (len(normal) + len(expanded)) >= 6:
        normal.extend(expanded)
        expanded = []

    for expandedRequest in expanded:
        reply += getFormattedCard(expandedRequest, True) + addSeparator()

    for normalRequest in normal:
        reply += getFormattedCard(normalRequest, False) + addSeparator()

    if reply != '':
        reply += SIGNATURE

    return reply

pprint.pprint(buildComment('{{sword hunter}} {{red eyes black dragon}} {{sword hunter}} {{scapegoat}} {{jam breeding machine}} {{blue eyes white dragon}} {{gadget soldier}}'))
