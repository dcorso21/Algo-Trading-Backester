import pandas as pd
import logging
import json

'''
Purpose of this module:

1. Simulate Market conditions like slippage and execution lag. 

2. Place orders in queue to be executed  
'''


def run_trade_sim(new_orders, current):

    cancel_second = 5

    price_offset = 0.0

    # min number of seconds to fill (assuming the price and volume fit too... )
    lag = 2

    open_orders = get_open_orders()

    new_orders['price_check'] = pd.Series(0)
    new_orders['vol_start'] = pd.Series(0)
    new_orders['wait_duration'] = pd.Series(0)

    if len(open_orders) != 0:

        open_orders['wait_duration'] = open_orders['wait_duration']+1

        # CANCEL OVERDUE ORDERS...
        if len(open_orders[open_orders.wait_duration > cancel_second]):
            open_orders = open_orders[open_orders.wait_duration <=
                                      cancel_second]
            logging.info('order cancelled')

    open_orders = open_orders.append(new_orders, sort=False)

    # Re - Index
    open_orders = open_orders.reset_index()
    columns = ['ticker', 'send_time', 'buy_or_sell', 'cash', 'qty',
               'exe_price', 'price_check', 'vol_start', 'wait_duration']
    open_orders = open_orders[columns].dropna()

    # UPDATE THE OPEN ORDERS...
    open_orders = update_open_orders(current, open_orders, lag, price_offset)

    # there is potential for these orders to be filled.
    potential_fills = open_orders[open_orders['price_check'] >= lag]

    if len(potential_fills) != 0:
        fill_indexes, open_orders = vol_check(current, potential_fills, open_orders)

        if fill_indexes != 0:

            filled_orders = open_orders.iloc[fill_indexes, :]
            columns = ['ticker', 'send_time',
                       'buy_or_sell', 'cash', 'qty', 'exe_price']
            filled_orders = filled_orders[columns]
            filled_orders['exe_time'] = [create_timestamp(
                current['minute'], current['second'])]

            filled_orders = filled_orders.dropna()

            open_orders = open_orders.drop(index=fill_indexes)

        else:
            filled_orders = pd.DataFrame()
    else:
        filled_orders = pd.DataFrame()

    ###################################################

    open_orders.to_csv('temp_assets/all_orders/open_orders.csv')

    return filled_orders, open_orders


def create_timestamp(minute, second):

    from datetime import datetime, timedelta
    time = datetime.strptime(minute, '%H:%M:%S')
    time = time+timedelta(seconds=second)
    return time.strftime('%H:%M:%S')


def get_open_orders():

    open_orders = pd.read_csv('temp_assets/all_orders/open_orders.csv')

    if len(open_orders) != 0:
        columns = ['ticker', 'send_time', 'buy_or_sell', 'cash', 'qty',
                   'exe_price', 'price_check', 'vol_start', 'wait_duration']
        open_orders = open_orders[columns]

    return open_orders


def update_open_orders(current, open_orders, lag, price_offset):
    # UPDATE PRICE CHECK VALUE
    for price, buyorsell, index in zip(open_orders.exe_price, open_orders.buy_or_sell, open_orders.index):

        logging.info('TF/SE: price check = {}'.format(open_orders.at[index, 'price_check']))

        if (buyorsell == 'BUY') and (current['close'] <= (price - price_offset)):
            open_orders.at[index, 'price_check'] += 1

        elif buyorsell == 'SELL' and (current['close'] >= (price + price_offset)):
            open_orders.at[index, 'price_check'] += 1

        else:
            if open_orders.at[index, 'price_check'] != 0:
                open_orders.at[index, 'price_check'] = 0

    # SET STARTING VOLUME
    for price_check, index in zip(open_orders.price_check, open_orders.index):

        if price_check == 1:
            open_orders.at[index, 'vol_start'] = current['volume']

    return open_orders

def vol_check(current, potential_fills, open_orders):
    fill_indexes = []
    for index, vol_start, qty in zip(potential_fills.index, potential_fills.vol_start, potential_fills.qty):

        # if the volume has increased since last time, but is in the same minute
        # also, if the change is bigger than qty, then add the index for fill.
        if (current['volume'] > vol_start) & ((current['volume'] - vol_start) > qty):
            fill_indexes.append(index)

        elif current['volume'] < vol_start:

            if current['volume'] > qty:
                fill_indexes.append(index)
            else:
                open_orders.at[index, 'vol_start'] = 0
    return fill_indexes, open_orders
