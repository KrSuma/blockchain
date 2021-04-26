from datetime import datetime
from itertools import count
import time

import MetaTrader5 as mt5

CRYPTO = 'BTCUSD'

# price threshold (%)
PRICE_THRES = 3
STOP_LOSS = 5
TAKE_PROFIT = 8

BUY = mt5.ORDER_TYPE_BUY
SELL = mt5.ORDER_TYPE_SELL
ORDER_TYPE = BUY

# init
mt5.initialize()

# acc number
account_num = 44830337
authorized = mt5.login(account_num)

if authorized:
    print(f'connected to MT5 account #{account_num}')
    print(f'price threshold set to 3%')
    print(f'stop loss at 5%')
    print(f'take profit at 8%\n')
else:
    print(f'failed to connect at account #{account_num}, error code: {mt5.last_error()}')

# equity
account_info = mt5.account_info()
if account_info is None:
    raise RuntimeError('could not load the account equity level')
else:
    equity = float(account_info[10])


# functions
def get_dates():
    """
    use dates to define thr ange of our dataset in the 'get_data()'
    :return: time
    """
    today = datetime.today()
    utc_from = datetime(year=today.year, month=today.month, day=today.day - 1)
    return utc_from, datetime.now()


def get_data():
    """
    download one day of 10 minute candles data, along with buy/sell price of coin
    :return: price range
    """
    utc_from, utc_to = get_dates()
    return mt5.copy_rates_range(CRYPTO, mt5.TIMEFRAME_M10, utc_from, utc_to)


def get_current_prices():
    """
    return current buy and sell prices
    :return: prices
    """
    current_buy_price = mt5.symbol_info_tick(CRYPTO)[2]
    current_sell_price = mt5.symbol_info_tick(CRYPTO)[1]
    return current_buy_price, current_sell_price


def diff_candles(candles):
    return (candles['close'][-1] - candles['close'][-2]) / candles['close'][-2] * 100


def trade():
    """
    determine if we should trade and if so, send requests to MT5
    :return: none
    """
    utc_from, utc_to = get_dates()
    candles = get_data()
    current_buy_price, current_sell_price = get_current_prices()

    # calc the % difference between the current price and the close price of the previous candle
    diff = diff_candles(candles)

    # check if a position has already been placed
    positions = mt5.positions_get(symbol=CRYPTO)
    orders = mt5.orders_get(symbol=CRYPTO)
    symbol_info = mt5.symbol_info(CRYPTO)

    if diff > PRICE_THRES:
        print(f'dif 1: {CRYPTO}, {diff}')
        # check if increase level is sustaining
        time.sleep(8)

        # check the diff again
        candles = mt5.copy_rates_range(CRYPTO, mt5.TIMEFRAME_M10, utc_from, utc_to)
        diff = diff_candles(candles)
        if diff > PRICE_THRES:
            print(f'dif 2: {CRYPTO}, {diff}')
            price = mt5.symbol_info_tick(CRYPTO).bid
            print(f'{CRYPTO} is up {str(diff)}% in the last 5 minutes opening BUY position')

            # trade request
            if not mt5.initialize():
                raise RuntimeError(f'MT% initialize failed, error code {mt5.last_error()}')

            # check that theres no open positions or orders
            if len(positions) == 0 and len(orders) < 1:
                if symbol_info is None:
                    print(f'{CRYPTO} not found, can not call order_check()')
                    mt5.shutdown()

                if not symbol_info.visible:
                    print(f'{CRYPTO} is not visible, trying to switch on')
                    if not mt5.symbol_select(CRYPTO, True):
                        print('symbol_select({}) failed, exit', CRYPTO)

                # represents 5% equity, min order 0.01 BTC, increase share if retcode = 10
                lot = float(round(((equity / 20) / current_buy_price), 2))

                # definition of stop/loss
                if ORDER_TYPE == BUY:
                    stop = price - (price * STOP_LOSS) / 100
                    take = price + (price * TAKE_PROFIT) / 100
                else:
                    stop = price + (price * STOP_LOSS) / 100
                    take = price - (price * TAKE_PROFIT) / 100

                request = {
                    'action': mt5.TRADE_ACTION_DEAL,
                    'symbol': CRYPTO,
                    'volume': lot,
                    'type': ORDER_TYPE,
                    'price': price,
                    'sl': stop,
                    'tp': take,
                    'magic': 66,
                    'comment': 'python-buy',
                    'type_time': mt5.ORDER_TIME_GTC,
                    'type_filling': mt5.ORDER_FILLING_IOC,
                }

                result = mt5.order_send(request)

                print(f'order_send(): by {CRYPTO} {lot} lots at {price}')

                if result.retcode != mt5.TRADE_RETCODE_DONE:
                    print(f'order_send() failed, retcode={result.retcode}')

                print(f' order_send done, {result}')
                print(f' opened position with POSITION_TICKET={result.order}')

            else:
                print(f'BUY signal detected, but {CRYPTO} has {len(positions)} active trade')

        else:
            pass

    else:
        if orders or positions:
            print('buying sig detected but theres already and active trade')
        else:
            print(f'diff is only: {str(diff)}%, attempting again...')


if __name__ == '__main__':
    print('Press CTRL-C to stop\n')
    for i in count():
        trade()
        time.sleep(1)
        print(f'iteration {i}')


