import os, time
import xml.etree.ElementTree as ET
import aiohttp
import asyncio
from datetime import date, datetime, timedelta
import csv
import numpy as np
import nltk
import pytz
import requests
from nltk.sentiment import SentimentIntensityAnalyzer


from binance.client import Client
from binance.enums import *
from binance.exceptions import BinanceAPIException, BinanceOrderException

from binance.websockets import BinanceSocketManager
from twisted.internet import reactor

from itertools import count

api_key = "w2lpkaAO553dJrZ3Vkizs1e3Buk0YwB2QycVJjIe2LOHDd3hyvX4rcD9u3bOadAH"
api_secret = ""

# authenticate with the client
client = Client(api_key, api_secret)

client.API_URL = 'https://testnet.binance.vision/api'

keywords = {
    'XRP': ['ripple', 'xrp', 'XRP', 'Ripple', 'RIPPLE'],
    'BTC': ['BTC', 'bitcoin', 'Bitcoin', 'BITCOIN'],
    'XLM': ['Stellar Lumens', 'XLM'],
    'BCH': ['Bitcoin Cash', 'BCH'],
    'ETH': ['ETH', 'Ethereum'],
    'BNB': ['BNB', 'Binance Coin'],
    'LTC': ['LTC', 'Litecoin']
}

# the buy amount
QUANTITY = 10
# define what to pair each coin to
PAIRING = "USDT"
# sentient threshold
SENTIMENT_THRESHOLD = 0.5
# define minimum articles for analysis
MIN_ARTICLE = 10
# frequency to run the code
REPEAT_EVERY = 60

CURRENT_PRICE = {}


def ticker_socket(msg):
    """stream financial infp of crypto"""
    if msg['e'] != 'error':
        global CURRENT_PRICE
        CURRENT_PRICE['{0}'.format(msg['s'])] = msg['c']
    else:
        print('error')


# connect o the websocket client and start the socket
bsm = BinanceSocketManager(client)
for coin in keywords:
    conn_key = bsm.start_symbol_ticker_socket(coin + PAIRING)
bsm.start()


def calculate_volume():
    """Calculate the amount of crypto to trade in usdt"""

    while CURRENT_PRICE == {}:
        print('Attempting to connect to the socket...')
        time.sleep(3)
    else:
        volume = {}
        for coin in CURRENT_PRICE:
            volume[coin] = float(QUANTITY / float(CURRENT_PRICE[coin]))
            volume[coin] = float('{:.6f}'.format(volume[coin]))
        return volume


with open('Crypto feeds.csv') as csv_file:
    # open file
    csv_reader = csv.reader(csv_file)
    # remove header
    next(csv_reader, None)
    # create empty list
    feeds = []
    # add each row RSS url to feed list
    for row in csv_reader:
        feeds.append(row[0])


def get_headlines():
    """ returns headlines from csv"""
    headers = {
        'User-Agent': 'Mozilla/5.0 (X11; Ubuntu; Linux x86_64; rv:87.0) Gecko/20100101 Firefox/87.0'
    }
    headlines = {'source': [], 'title': [], 'pubDate' : [] }

    for feed in feeds:
        try:
            r = requests.get(feed, headers=headers, timeout = 7)
            #define the roots for parsing
            root = ET.fromstring(r.text)
            # identify the last headlines
            channel = root.find('channel/item/title').text
            pubDate = root.find('channel/item/pubDate').text
            # append the source and title
            headlines['source'].append(feed)
            # append the date
            headlines['pubDate'].append(pubDate)
            headlines['title'].append(channel.encode('UTF-8').decode('UTF-8'))
            print(channel)
        except:
            print(f'Could not parse {feed}')

    return headlines


def categorise_headlines():
    """arrange the headlines"""
    headlines = get_headlines()
    categorised_headlines = {}
    # create dictionary for each keyword
    for keyword in keywords:
        categorised_headlines['{0}'.format(keyword)] = []

    for keyword in keywords:
        for headline in headlines['title']:
            if any(key in headline for key in keywords[keyword]):
                categorised_headlines[keyword].append(headline)

    return headlines


def analyse_headlines():
    """analyse the headlines scraped"""
    sia = SentimentIntensityAnalyzer()
    categorised_headlines = categorise_headlines()

    sentiment = {}

    for coin in categorised_headlines:
        if len(categorised_headlines[coin]) > 0:
            sentiment['{0}'.format(coin)] = []

            for title in categorised_headlines[coin]:
                sentiment[coin].append(sia.polarity_scores(title))

    return sentiment


def compile_sentiment():
    """arranges every compound value into a list"""
    sentiment = analyse_headlines()
    compiled_sentiment = {}

    for coin in sentiment:
        compiled_sentiment[coin] = []
        for item in sentiment:
            compiled_sentiment[coin] = []
            for item in sentiment[coin]:
                # append each value to each coins dict
                compiled_sentiment[coin].append(sentiment[coin][sentiment[coin].index(item)]['compound'])

    return compiled_sentiment


def compound_average():
    """calculates and returns the average compound sentiment"""
    compiled_sentiment = compile_sentiment()
    headlines_analysed = {}

    for coin in compiled_sentiment:
        headlines_analysed[coin] = len(compiled_sentiment[coin])
        compiled_sentiment[coin] = np.array(compiled_sentiment[coin])
        compiled_sentiment[coin] = np.mean(compiled_sentiment[coin])
        compiled_sentiment[coin] = compiled_sentiment[coin].item()

    return compiled_sentiment, headlines_analysed


def buy():
    """check if sentiment is positive, keyword found"""
    compiled_sentiment, headlines_analysed = compound_average()
    volume = calculate_volume()

    for coin in compiled_sentiment:
        

























