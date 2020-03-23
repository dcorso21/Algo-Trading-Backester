from local_functions.analysis.ana_indicators.p_eval import common_eval_funcs as common

import pandas as pd
import logging


def create_sells(qty, current, current_frame):

    ticker = current_frame.ticker.tolist()[-1]
    timestamp = common.get_timestamp(
        current_frame.time.tolist()[-1], current['second'])
    exe_price = round(current['close'], 3)
    cash_value = round(qty * exe_price, 2)

    columns = {'ticker': [ticker], 'send_time': [timestamp], 'buy_or_sell': [
        'SELL'], 'cash': [cash_value], 'qty': [qty], 'exe_price': [exe_price]}

    df = pd.DataFrame(columns)
    return df


def create_buys(cash_value, current, current_frame, offset, exe_price):

    ticker = current_frame.at[0, 'ticker']
    timestamp = common.get_timestamp(
        current_frame.time.tolist()[-1], current['second'])

    qty = common.cash_to_shares(cash_value, exe_price)
    cash_value = round(qty * exe_price, 2)

    columns = {'ticker': [ticker], 'send_time': [timestamp], 'buy_or_sell': [
        'BUY'], 'cash': [cash_value], 'qty': [qty], 'exe_price': [exe_price]}

    df = pd.DataFrame(columns)
    return df
