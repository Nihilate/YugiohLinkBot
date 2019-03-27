# -*- coding:utf-8 -*-

from functools import lru_cache
import requests
from urllib.parse import quote_plus
from Util import process_string, timing
from pyquery import PyQuery as pq
from DatabaseHandler import getClosestTCGCardname
import traceback
import re
import pprint
import difflib

WIKI_URL = 'https://yugipedia.com/wiki/'
TCG_BASE_URL = 'http://yugiohprices.com/api'
OCG_BASE_URL = 'https://yugipedia.com/api.php'

BREAK_TOKEN = '__BREAK__'

def sanitiseCardname(cardname):
    return cardname.replace('/', '%2F')

@lru_cache(maxsize=128)
def getOCGCardURL(searchText):
    try:
        searchResults = requests.get(OCG_BASE_URL + '?action=query&list=search&srsearch=' + searchText + '&srlimit=50&format=json')
    except:
        traceback.print_exc()
        return None

    data = searchResults.json()['query']['search']

    titles = [item['title'].lower() for item in data]

    results = difflib.get_close_matches(searchText.lower(), titles, 1, 0.85)

    if results:
        for item in data:
            if item['title'].lower() == results[0]:
                return getWikiaURL(item['title']) 

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
        traceback.print_exc()
        return None
    else:
        response.connection.close()
        if response.ok:
            json = response.json()
            if json.get('status', '') == 'success':
                json['data']['image'] = getTCGCardImage(cardName);
                return json['data']

def getOCGCardData(url):
    try:
        html = requests.get(url)
        ocg = pq(html.text)

        card = ocg('.cardtable')
        statuses = ocg('.cardtablestatuses')

        data = {
            'image': (card.find('td.cardtable-cardimage').eq(0)
                      .find('img').eq(0).attr('data-src')),
            'name': (card.find('th.cardtable-header').eq(0).text()),
            'type': ('trap' if card.find('a[title="Trap Card"]') else
                     ('spell' if card.find('a[title="Spell Card"]') else
                      ('monster' if card.find('th a[title="Type"]') else
                       'other')))
        }

        if (data['type'] == 'monster'):
            data['monster_attribute'] = (card.find('th a[title="Attribute"]')
                                         .eq(0).parents('tr').eq(0)
                                         .find('td a').eq(0).text())

            data['monster_types'] = [monster_type.strip() for monster_type in (process_string(
                card.find('th a[title="Type"]').eq(0).parents('tr').eq(0)
                .find('td').eq(0).text())).split('/')]

            if 'Link' in data['monster_types']:
                data['monster_level'] = ' / '.join(str(process_string(
                    card.find('th a[title="Link Arrow"]').eq(0).parents('tr').eq(0)
                    .find('td a').text())).split(' '))
            elif 'Xyz' in data['monster_types']:
                data['monster_level'] = int(process_string(
                    card.find('th a[title="Rank"]').eq(0).parents('tr').eq(0)
                    .find('td a').eq(0).text()))
            else:
                data['monster_level'] = int(process_string(
                    card.find('th a[title="Level"]').eq(0).parents('tr').eq(0)
                    .find('td a').eq(0).text()))

            if 'Pendulum' in data['monster_types']:
                data['pendulum_scale'] = int(process_string(
                    card.find('th a[title="Pendulum Scale"]').eq(0).parents('tr').eq(0)
                    .find('td a').eq(1).text()))
            else:
                data['pendulum_scale'] = None
            
            atk_def = (card.find('th a[title="ATK"]').eq(0)
                       .parents('tr').eq(0).find('td').eq(0).text()).split('/')
     
            data['monster_attack'] = process_string(atk_def[0])
            data['monster_defense'] = process_string(atk_def[1])
     
        elif (data['type'] == 'spell' or data['type'] == 'trap'):
            data['spell_trap_property'] = (
                card.find('th a[title="Property"]').eq(0).parents('tr').eq(0)
                .find('td a').eq(0).text())

        if (data['type'] == 'monster'):
            for i, m_type in enumerate(data['monster_types']):
                data['monster_types'][i] = data['monster_types'][i].strip()

        description_element = card.find('.cardtablespanrow').html()        
        description_element = re.sub(r'</dt>', ': </dt>' + BREAK_TOKEN, description_element)
        description_element = re.sub(r'</dd>', '</dd>' + BREAK_TOKEN, description_element)
        description_element = re.sub(r'<br ?/?>', BREAK_TOKEN, description_element)
        description_element = re.sub(r'<a href=[^>]+>', '', description_element)
        description_element = re.sub(r'</a>', '', description_element)
        description_element = pq(description_element).text()
        
        data['description'] = process_string(description_element)     
        data['description'] = data['description'].replace(BREAK_TOKEN, '\n')
        data['description'] = re.sub(r':(?=\w)', ': ', data['description'])
        data['description'] = re.sub(r'\.(?=\w)', '. ', data['description'])

        return data
        
    except:
        traceback.print_exc()
        return None

def getPricesURL(cardName):
    return "http://yugiohprices.com/card_price?name=" + cardName.replace(" ", "+")

def getWikiaURL(cardName):
    return WIKI_URL + cardName.replace(" ", "_")

def formatTCGData(data):
    try:
        formatted = {}
        
        formatted['name'] = data['name']
        formatted['wikia'] = getWikiaURL(data['name'])
        formatted['pricedata'] = getPricesURL(data['name'])
        formatted['image'] = data['image']
        formatted['text'] = re.sub('<!--(.*?)-->', '', data['text'].replace('\n\n', '  \n'))
        formatted['cardtype'] = data['card_type']
        
        if formatted['cardtype'].lower() == 'monster':
            formatted['attribute'] = data['family'].upper()
            formatted['types'] = data['type'].split('/')

            formatted['level'] = data['level']
            formatted['att'] = data['atk']
            formatted['def'] = data['def']

            if 'link' in ' '.join(str(i[1]).lower() for i in enumerate(formatted['types'])):
                formatted['leveltype'] = None
                formatted['level'] = None
                formatted['def'] = None
            elif 'xyz' in ' '.join(str(i[1]).lower() for i in enumerate(formatted['types'])):
                formatted['leveltype'] = 'Rank'
            else:
                formatted['leveltype'] = 'Level'
        else:
            formatted['property'] = data['property']

        return formatted
    except:
        traceback.print_exc()
        return None

def formatOCGData(data):
    try:
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

            formatted['level'] = data['monster_level']
            formatted['att'] = data['monster_attack']
            formatted['defn_type'] = 'DEF'
            formatted['def'] = data['monster_defense']

            formatted['pendulum_scale'] = data['pendulum_scale']

            if 'link' in ' '.join(str(i[1]).lower() for i in enumerate(formatted['types'])):
                formatted['leveltype'] = 'Link Arrows'
                formatted['defn_type'] = 'LINK'
            elif 'xyz' in ' '.join(str(i[1]).lower() for i in enumerate(formatted['types'])):
                formatted['leveltype'] = 'Rank'
            else:
                formatted['leveltype'] = 'Level'
        else:
            formatted['property'] = data['spell_trap_property']

        return formatted
    except:
        traceback.print_exc()
        return None

def getCardData(searchText):
    try:
        cardName = getClosestTCGCardname(searchText)
        
        if (cardName): #TCG
            print('Searching YGOPrices for: ' + searchText)
            tcgData = getTCGCardData(sanitiseCardname(cardName))

            formattedData = formatTCGData(tcgData)

            if formattedData:
                print("(TCG) Found: " + tcgData['name'])
            else:
                print ("Card not found.")
                
            return formattedData
        else: #OCG
            print('Searching Yugipedia for: ' + searchText)
            wikiURL = getOCGCardURL(searchText)

            if not wikiURL:
                wikiURL = getWikiaURL(searchText)
            
            if (wikiURL):
                ocgData = getOCGCardData(wikiURL)               
                formattedData = formatOCGData(ocgData)

                if formattedData:
                    print("(OCG) Found: " + ocgData['name'])
                    return formattedData
                else:
                    return None
    except:
        traceback.print_exc()
        return None
