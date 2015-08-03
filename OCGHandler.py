from django.core.management.base import BaseCommand
from pyquery import PyQuery as pq
from os.path import basename, splitext
from urlparse import urlparse
import urllib2
import re
import requests

from OCGHelpers import process_string
 
#WIKI_URL = Variable.objects.get(identifier='wiki-url').get()

WIKI_URL = 'http://yugioh.wikia.com/wiki'
BREAK_TOKEN = '__BREAK__'

def get_wiki_data(identifier):
 
    #Q = pq(url=(u'{}/{}'.format(WIKI_URL, identifier)))
    Q = pq(url=identifier)
    
    card = Q('.cardtable')
    #print(card)
    statuses = Q('.cardtablestatuses')
 
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

def get_data_of_closest(cardname):
    try:
        searchURL = 'http://yugioh.wikia.com/api/v1/Search/List?query="' + cardname + '"&limit=1'
        searchResults = requests.get(searchURL)
        data = get_wiki_data(searchResults.json()['items'][0]['url'])
        return data
    except:
        return None
