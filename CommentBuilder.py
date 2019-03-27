import CardDataHandler
import DatabaseHandler
import re
import pprint
import traceback

MONSTER_CARD_TEMPLATE_NORMAL = ('{name}{image} - {wikia}{infosyntax}{pricedata}')


MONSTER_CARD_TEMPLATE_EXPANDED = ('{name}{image} - {wikia}{infosyntax}{pricedata}\n\n'
                                '^({leveltype}{level}{cardtype}{types}{pendulum_scale}{attribute})  \n'
                                '^({stats})\n\n'
                                '{text}\n\n'
                                '{att}{defn_type}{defn}')
    
SPELL_CARD_TEMPLATE_NORMAL = ('{name}{image} - {wikia}{infosyntax}{pricedata}')

SPELL_CARD_TEMPLATE_EXPANDED = ('{name}{image} - {wikia}{infosyntax}{pricedata}\n\n'
                                '^({cardtype}{cardproperty})  \n'
                                '^({stats})\n\n'
                                '{text}')

SIGNATURE = '^^To ^^use: ^^{Normal} ^^or ^^{{Expanded}} ^^| [^^Issues?](http://www.reddit.com/message/compose/?to=Nihilate) ^^| [^^Source](https://github.com/Nihilate/YugiohLinkBot)'

def getSignature():
    return SIGNATURE

def formatCardData(card, isExpanded):
    try:
        if isExpanded:
            requestStats = DatabaseHandler.getStats(card['name'])
            
            if card['cardtype'].lower() == 'monster':
                return MONSTER_CARD_TEMPLATE_EXPANDED.format(
                    name = '[**{}**]'.format(card['name']),
                    image = '({})'.format(card['image']) if card['image'] else '(http://i.imgur.com/paNkvJ5.jpg)',
                    wikia = '[Yugipedia]({})'.format(card['wikia']),
                    infosyntax = ', ' if card['pricedata'] else '',
                    pricedata = '[($)]({})'.format(card['pricedata']) if card['pricedata'] else '',
                    leveltype = '**{}**: '.format(card['leveltype']) if card['leveltype'] else '',
                    level = '{}, '.format(card['level']) if card['level'] else '',
                    cardtype = '**Category**: {}, '.format(card['cardtype'].title()),
                    types = '**Type**: {}, '.format(' / '.join(str(i[1]) for i in enumerate(card['types']))),
                    pendulum_scale = '**Pendulum Scale**: {}, '.format(card['pendulum_scale']) if card['pendulum_scale'] else '',
                    attribute = '**Attribute**: {}'.format(card['attribute'].upper()),
                    text = '>{}'.format(card['text']),
                    att = '>**ATK**: {}'.format(card['att']),
                    defn_type = ', **{}**: '.format(card['defn_type']) if card['defn_type'] is not None else '',
                    defn = '{}'.format(card['def']) if card['def'] is not None else '',
                    stats = '**Stats**: {total} requests - {percentage}% of all requests'.format(
                        total=requestStats['total'],
                        percentage=str(round(requestStats['totalAsPercentage'],2))))
            else:
                return SPELL_CARD_TEMPLATE_EXPANDED.format(
                    name = '[**{}**]'.format(card['name']),
                    image = '({})'.format(card['image']) if card['image'] else '(http://i.imgur.com/paNkvJ5.jpg)',
                    wikia = '[Yugipedia]({})'.format(card['wikia']),
                    infosyntax = ', ' if card['pricedata'] else '',
                    pricedata = '[($)]({})'.format(card['pricedata']) if card['pricedata'] else '',
                    cardtype = '**Category**: {}, '.format(card['cardtype'].title()),
                    cardproperty = '**Property**: {}'.format(card['property']),
                    text = '>{}'.format(card['text']),
                    stats = '**Stats**: {total} requests - {percentage}% of all requests'.format(
                        total=requestStats['total'],
                        percentage=str(round(requestStats['totalAsPercentage'],2))))
        else:
            if card['cardtype'].lower() == 'monster':
                return MONSTER_CARD_TEMPLATE_NORMAL.format(
                    name = '[**{}**]'.format(card['name']),
                    image = '({})'.format(card['image']) if card['image'] else '(http://i.imgur.com/paNkvJ5.jpg)',
                    wikia = '[Yugipedia]({})'.format(card['wikia']),
                    infosyntax = ', ' if card['pricedata'] else '',
                    pricedata = '[($)]({})'.format(card['pricedata']) if card['pricedata'] else '')
            else:
                return SPELL_CARD_TEMPLATE_NORMAL.format(
                    name = '[**{}**]'.format(card['name']),
                    image = '({})'.format(card['image']) if card['image'] else '(http://i.imgur.com/paNkvJ5.jpg)',
                    wikia = '[Yugipedia]({})'.format(card['wikia']),
                    infosyntax = ', ' if card['pricedata'] else '',
                    pricedata = '[($)]({})'.format(card['pricedata']) if card['pricedata'] else '')
    except:
        traceback.print_exc()

def buildRequestComment(cardname, isExpanded):
    data = CardDataHandler.getCardData(cardname)
    if data:
        return formatCardData(data, isExpanded)
    else:
        return None
