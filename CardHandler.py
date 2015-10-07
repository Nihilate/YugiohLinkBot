from functools import lru_cache
import requests
from urllib.parse import quote_plus
from Util import process_string, timing
from pyquery import PyQuery as pq
from DatabaseHandler import getClosestTCGCardname
import traceback
import re
import pprint

TCG_BASE_URL = 'http://yugiohprices.com/api'
OCG_BASE_URL = 'http://yugioh.wikia.com/api/v1'

BREAK_TOKEN = '__BREAK__'

def sanitiseCardname(cardname):
    return cardname.replace('/', '%2F')

@lru_cache(maxsize=128)
def getOCGCardURL(searchText):
    try:
        endPoint = '/Search/List?query='
        resultLimit = '&limit=1'
        searchResults = requests.get(OCG_BASE_URL + endPoint + searchText + resultLimit)
        data = searchResults.json()['items'][0]['url']
        return data
    except:
        return None

@lru_cache(maxsize=128)
def getTCGCardImage(cardName):
    endPoint = '/card_image/'

    try:
        response = requests.get(TCG_BASE_URL + endPoint + quote_plus(cardName))
    except:
        return None
    else:
        response.connection.close()
        if response.ok:
            return response.url

@lru_cache(maxsize=128)
def getTCGCardData(cardName):
    endPoint = '/card_data/'

    try:
        response = requests.get(TCG_BASE_URL + endPoint + quote_plus(cardName))
    except:
        return None
    else:
        response.connection.close()
        if response.ok:
            json = response.json()
            if json.get('status', '') == 'success':
                json['data']['image'] = getTCGCardImage(cardName);
                return json['data']

@lru_cache(maxsize=128)
def getOCGCardData(url):
    try:
        html = requests.get(url)
        ocg = pq(html.text)

        card = ocg('.cardtable')
        statuses = ocg('.cardtablestatuses')

        data = {
            'image': (card.find('td.cardtable-cardimage').eq(0)
                      .find('img').eq(0).attr('src')),
            'name': (card.find('tr.cardtablerow td.cardtablerowdata').eq(0).text()),
            'type': ('trap' if card.find('img[alt="TRAP"]') else
                     ('spell' if card.find('img[alt="SPELL"]') else
                      ('monster' if card.find('th a[title="Type"]') else
                       'other'))),
            'status_advanced': (statuses.find('th a[title="Advanced Format"]')
                                .eq(0).parents('th').next().text()),
            'status_traditional': (
                statuses.find('th a[title="Traditional Format"]').eq(0)
                .parents('th').next().text())
        }

        description_element = (card.find('td table table').eq(0).find('tr').eq(2).find('td').eq(0))
        description_element.html(re.sub(r'<br ?/?>', BREAK_TOKEN, description_element.html()))
        description_element.html(re.sub(r'<a href=[^>]+>', '', description_element.html()))
        description_element.html(re.sub(r'</a>', '', description_element.html()))
        
        data['description'] = process_string(description_element.text())
     
        data['description'] = data['description'].replace(BREAK_TOKEN, '\n')

        try:
            data['number'] = process_string(card.find('th a[title="Card Number"]')
                                            .eq(0).parents('tr').eq(0).find('td a')
                                            .eq(0).text())
        except:
            data['number'] = ''
     
        if (data['type'] == 'monster'):
            data['monster_attribute'] = (card.find('th a[title="Attribute"]')
                                         .eq(0).parents('tr').eq(0)
                                         .find('td a').eq(0).text())
     
            try:
                data['monster_level'] = int(process_string(
                    card.find('th a[title="Level"]').eq(0).parents('tr').eq(0)
                    .find('td a').eq(0).text()))
            except:
                data['monster_level'] = int(process_string(
                    card.find('th a[title="Rank"]').eq(0).parents('tr').eq(0)
                    .find('td a').eq(0).text()))
     
            atk_def = (card.find('th a[title="ATK"]').eq(0)
                       .parents('tr').eq(0).find('td').eq(0).text()).split('/')
     
            data['monster_attack'] = process_string(atk_def[0])
            data['monster_defense'] = process_string(atk_def[1])
     
            data['monster_types'] = (process_string(
                card.find('th a[title="Type"]').eq(0).parents('tr').eq(0)
                .find('td').eq(0).text())).split('/')
     
        elif (data['type'] == 'spell' or data['type'] == 'trap'):
            data['spell_trap_property'] = (
                card.find('th a[title="Property"]').eq(0).parents('tr').eq(0)
                .find('td a').eq(0).text())

        if (data['type'] == 'monster'):
            for i, m_type in enumerate(data['monster_types']):
                data['monster_types'][i] = data['monster_types'][i].strip()

        return data
        
    except:
        traceback.print_exc()
        return None

def getPricesURL(cardName):
    return "http://yugiohprices.com/card_price?name=" + cardName.replace(" ", "+")

def getWikiaURL(cardName):
    return "http://yugioh.wikia.com/wiki/" + cardName.replace(" ", "_")

def formatTCGData(data):
    formatted = {}
    
    formatted['name'] = data['name']
    formatted['wikia'] = getWikiaURL(data['name'])
    formatted['pricedata'] = getPricesURL(data['name'])
    formatted['image'] = data['image']
    formatted['text'] = data['text'].replace('\n\n', '  \n')
    formatted['cardtype'] = data['card_type']
    
    if formatted['cardtype'].lower() == 'monster':
        formatted['attribute'] = data['family'].upper()
        formatted['types'] = data['type'].split('/')

        if 'xyz' in ' '.join(str(i[1]).lower() for i in enumerate(formatted['types'])):
            formatted['leveltype'] = 'Rank'
        else:
            formatted['leveltype'] = 'Level'

        formatted['level'] = data['level']
        formatted['att'] = data['atk']
        formatted['def'] = data['def']
    else:
        formatted['property'] = data['property']

    return formatted

def formatOCGData(data):
    formatted = {}
    
    formatted['name'] = data['name']
    formatted['wikia'] = getWikiaURL(data['name'])
    formatted['pricedata'] = None
    formatted['image'] = data['image']
    formatted['text'] = data['description'].replace('\n', '  \n')
    formatted['cardtype'] = data['type']
    
    if formatted['cardtype'].lower() == 'monster':
        formatted['attribute'] = data['monster_attribute'].upper()
        formatted['types'] = data['monster_types']

        if 'xyz' in ' '.join(str(i[1]).lower() for i in enumerate(formatted['types'])):
            formatted['leveltype'] = 'Rank'
        else:
            formatted['leveltype'] = 'Level'

        formatted['level'] = data['monster_level']
        formatted['att'] = data['monster_attack']
        formatted['def'] = data['monster_defense']
    else:
        formatted['property'] = data['spell_trap_property']

    return formatted

@timing
def getCard(searchText):
    print('Searching for: ' + searchText)
    
    cardName = getClosestTCGCardname(searchText)
    if (cardName): #TCG
        print ("Found: " + cardName + " (TCG)")
        tcgData = getTCGCardData(sanitiseCardname(cardName))
        return formatTCGData(tcgData)
    else: #OCG
        wikiURL = getOCGCardURL(searchText)
        if (wikiURL):
            print ("Found: " + wikiURL.replace('http://yugioh.wikia.com/wiki/', '').replace('_', ' ') + " (OCG)")
            ocgData = getOCGCardData(wikiURL)
            return formatOCGData(ocgData)
        else:
            print ("Card not found.")
