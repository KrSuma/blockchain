import os
from binance.client import Client
from datetime import datetime, timedelta
import time
from itertools import count
from itertools import count
import json

API_LIVE = "y49HDNWtWZ2YdQ3lmYrnBfDwv4eTShZEIrgHljYE2MPPmazEiaaw7KzFmS69xJLl"
SECRET_LIVE = "kXCDDLPdUbI3YeLbrgqWqmWR4QebYhtkQL9UydBIVd5CrOO8CB71KDtH7tEf9njv"

SPOT_TEST = "InTPDoHI8blAlKARL9KygcMujUod5KFnZGZhxKz596OG2Q193h2txTA1vOablbDk"
SPOT_SECRET = "7rroq47B9IO0mm31RtlPwhLQ8tDAJijKHL5YBMtrQpkfVls5J74IUA4ykY7jdBto"

TESTNET = True

# authenticate
if TESTNET:
    client = Client(SPOT_TEST, SPOT_SECRET)
    client.API_URL = "https://testnet.binance.vision/api"
else:
    client = Client(API_LIVE, SECRET_LIVE)

"""
VARIABLES
"""

# select what to pair the coins with
PAIR_WITH = 'USDT'
# define size of each trade
QUANTITY = 100
# list of pairs to exclude
FIATS = ['EURUSDT', 'GBPUSDT', 'JPYUSDT', 'USDUSDT', 'DOWN', 'UP']

# the amount of time in MINUTES to calculate the differnce from the current price
TIME_DIFFERENCE = 5
# the difference in % between the first and second checks for the price, by default set at 10 minutes apart.
CHANGE_IN_PRICE = 3
# define in % when to sell a coin that's not making a profit
STOP_LOSS = 3
# define in % when to take profit on a profitable coin
TAKE_PROFIT = 6

"""
COINS TRACKED
"""
coins_bought = {}
coins_bought_file_path = 'coins_bought.json'

# use separate files for testnet and live
if TESTNET:
    coins_bought_file_path = 'testnet_' + coins_bought_file_path

# if saved coins_bought json file exists then load it
if os.path.isfile(coins_bought_file_path):
    with open(coins_bought_file_path) as file:
        coins_bought = json.load(file)

"""
FUNCTIONS
"""


def get_price():
    initial_price = {}
    prices = client.get_all_tickers()

    for coin in prices:
        # return USDT pairs, exclude margin symbols
        if PAIR_WITH in coin['symbol'] and all(item not in coin['symbol'] for item in FIATS):
            initial_price[coin['symbol']] = { 'price': coin['price'], 'time': datetime.now()}

    return initial_price


def wait_for_price():
    volatile_coins = {}
    initial_price = get_price()

    while initial_price['BNBUSDT']['time'] > datetime.now() - timedelta(minutes=TIME_DIFFERENCE):
        print(f'not enough time has passed yet...')
        time.sleep(60 * TIME_DIFFERENCE)
    else:
        last_price = get_price()

        for coin in initial_price:
            threshold_check = (float(initial_price[coin]['price']) -
                               float(last_price[coin]['price'])) / float(last_price[coin]['price']) * 100
            if threshold_check > CHANGE_IN_PRICE:
                volatile_coins[coin] = threshold_check
                volatile_coins[coin] = round(volatile_coins[coin], 3)

                print(f'{coin} has gained ')