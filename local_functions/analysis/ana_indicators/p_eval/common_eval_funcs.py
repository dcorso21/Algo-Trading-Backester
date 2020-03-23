import datetime
import pandas as pd
import json
import logging


def cash_to_shares(cash, price):

    return (int(cash/price))


def get_timestamp(minute, second):

    from datetime import datetime, timedelta
    time = datetime.strptime(minute, '%H:%M:%S')
    time = time+timedelta(seconds=second)
    return time.strftime('%H:%M:%S')


def get_average(current_positions):

    df = current_positions
    avg = df.cash.sum() / df.qty.sum()
    return avg


def get_exposure(current_positions):

    df = current_positions
    ex = df.cash.sum()

    pls = pull_json('temp_assets/pl_open_closed.json')

    pls['last_ex'] = ex
    if pls['max_ex'] < ex:
        pls['max_ex'] = ex

    save_json(pls, 'temp_assets/pl_open_closed.json')

    return ex, pls


def pull_json(filename):

    json_file = open(filename)
    dictionary = json.load(json_file)
    return dictionary


def save_json(dictionary, filename):

    json_file = json.dumps(dictionary)
    with open(filename, 'w'):
        pass
    f = open(filename, 'w')
    f.write(json_file)
    f.close()


def get_open_orders():

    open_orders = pd.read_csv('temp_assets/all_orders/open_orders.csv')

    return open_orders


def get_max_vola(volas, current):

    volas_list = list(volas.values())
    # get rid of nan values to use max func...
    volas_cleaned = [x for x in volas_list if str(x) != 'nan']

    if len(volas_cleaned) != 0:
        max_vola = max(list(map(int, volas_cleaned)))
    else:
        max_vola = False

    if max_vola == False:
        current_vola = (
            (current['high'] - current['low'])/current['low'])
        max_vola = current_vola

    return max_vola


def get_inverse_perc(percentage_drop):

    drop_percent = (100 - percentage_drop)*.01

    return drop_percent
