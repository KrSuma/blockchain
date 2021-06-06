import os
from binance.client import Client
from datetime import datetime, timedelta
import time
from itertools import count
from itertools import count
import json
import pprint as pp

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

print(f'Time difference = {TIME_DIFFERENCE}')
print(f'Change in price = {CHANGE_IN_PRICE}')
print(f'Stop loss = {STOP_LOSS}')
print(f'Take profit = {TAKE_PROFIT}')

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


# fetch price, update price list
def get_price():
    initial_price = {}
    prices = client.get_all_tickers()

    for coin in prices:
        # return USDT pairs, exclude margin symbols
        if PAIR_WITH in coin['symbol'] and all(item not in coin['symbol'] for item in FIATS):
            initial_price[coin['symbol']] = { 'price': coin['price'], 'time': datetime.now()}

    return initial_price

# calculate price difference using the time difference value we set
def wait_for_price():
    volatile_coins = {}
    initial_price = get_price()

    while initial_price['BNBUSDT']['time'] > datetime.now() - timedelta(minutes=TIME_DIFFERENCE):
        print(f'not enough time has passed yet...')
        pp.pprint(initial_price)
        time.sleep(60 * TIME_DIFFERENCE)
    else:
        last_price = get_price()

        for coin in initial_price:
            threshold_check = (float(initial_price[coin]['price']) -
                               float(last_price[coin]['price'])) / float(last_price[coin]['price']) * 100

            if threshold_check > CHANGE_IN_PRICE:
                volatile_coins[coin] = threshold_check
                volatile_coins[coin] = round(volatile_coins[coin], 3)

                print(f'{coin} has gained {volatile_coins[coin]}% in the last {TIME_DIFFERENCE},'
                      f'calculating volume in {PAIR_WITH}.')

        if len(volatile_coins) < 1:
            print(f'No coins moved more than {CHANGE_IN_PRICE}% in the last {TIME_DIFFERENCE} minute(s).')

        return volatile_coins, len(volatile_coins), last_price


# convert the set buy/sell volume from USDT to each of coins returned
def convert_volume():
    volatile_coins, number_of_coins, last_price = wait_for_price()
    lot_size = {}
    volume = {}

    for coin in volatile_coins:
        try:
            info = client.get_symbol_info(coin)
            step_size = info['filters'][2]['stepSize']
            lot_size[coin] = step_size.index('1') - 1

            if lot_size[coin] < 0:
                lot_size[coin] = 0

        except:
            pass

        volume[coin] = float(QUANTITY / float(last_price[coin]['price']))

        if coin not in lot_size:
            volume[coin] = float('{:.1f}'.format(volume[coin]))
        else:
            volume[coin] = float('{:.{}f'.format(volume[coin], lot_size[coin]))

    return volume, last_price


def trade():
    volume, last_price = convert_volume()
    orders = {}

    for coin in volume:
        if coin not in coins_bought or coins_bought[coin] == None:
            print(f'preparing to buy {volume[coin]} {coin}')

            if TESTNET:
                test_order = client.create_test_order(symbol=coin, side='BUY', type='MARKET', quantity=volume)

            # try to create a real order if the test orders did not raise an exception
            try:
                buy_limit = client.create_order(
                    symbol=coin,
                    side='BUY',
                    type='MARKET',
                    quantity=volume[coin]
                )

            # error handling here in case position cannot be placed
            except Exception as e:
                print(e)

            # run the else block if the position has been placed and return order info
            else:
                orders[coin] = client.get_all_orders(symbol=coin, limit=1)
        else:
            print(f'Signal detected, but there is already an active trade on {coin}')

    return orders, last_price, volume


def update_portfolio(orders, last_price, volume):

    for coin in orders:
        coins_bought[coin] = {
            'symbol': orders[coin][0]['symbol'],
            'orderid': orders[coin][0]['orderId'],
            'timestamp': orders[coin][0]['time'],
            'bought_at': last_price[coin]['price'],
            'volume': volume[coin]
            }

        # save the coins in a json file in the same directory
        with open(coins_bought_file_path, 'w') as file:
            json.dump(coins_bought, file, indent=4)


def sell_coins():
    last_price = get_price()

    for coin in coins_bought:
        # define stop loss and take profit
        TP = float(coins_bought[coin]['bought_at']) + (float(coins_bought[coin]['bought_at']) * TAKE_PROFIT) / 100
        SL = float(coins_bought[coin]['bought_at']) - (float(coins_bought[coin]['bought_at']) * STOP_LOSS) / 100

        # check that the price is above the take profit or below the stop loss
        if float(last_price[coin]['price']) > TP or float(last_price[coin]['price']) < SL:
            print(f"TP or SL reached, selling {coins_bought[coin]['volume']} {coin}...")

            if TESTNET:
                # create test order before pushing an actual order
                test_order = client.create_test_order(symbol=coin, side='SELL', type='MARKET', quantity=coins_bought[coin]['volume'])

            # try to create a real order if the test orders did not raise an exception
            try:
                sell_coins_limit = client.create_order(
                    symbol=coin,
                    side='SELL',
                    type='MARKET',
                    quantity=coins_bought[coin]['volume']
                )

            # error handling here in case position cannot be placed
            except Exception as e:
                print(e)

            # run the else block if the position has been placed and update the coins bought json file
            else:
                coins_bought[coin] = None
                with open(coins_bought_file_path, 'w') as file:
                    json.dump(coins_bought, file, indent=4)
        else:
            print(f'TP or SL not yet reached, not selling {coin} for now...')


"""
MAIN
"""

if __name__ == '__main__':
    print('Press Ctrl-Q to stop the script')
    for i in count():
        orders, last_price, volume = trade()
        update_portfolio(orders, last_price, volume)
        sell_coins()

