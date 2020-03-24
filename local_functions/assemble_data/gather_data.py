from local_functions.main import global_vars as gl
from local_functions.analysis.ana_indicators import common
import pandas as pd
import json


def update_candle(price, volume, ticker, minute, second):
    '''Inputs--
    prices: list of prices simulating real time updates from the historical_funcs: create_second_data.'''

    if second == 0:
        o, h, l, c = price, price, price, price
    else:
        prev = gl.current

        o, h, l, c = prev['open'], prev['high'], prev['low'], prev['close']

        if price > h:
            h = price
        if price < l:
            l = price
    c = price
    v = volume

    current = {'open': o,
               'high': h,
               'low': l,
               'close': c,
               'volume': v,
               'second': second,
               'minute': minute,
               'ticker': ticker}

    common.save_dict_to_csv(current, r'temp_assets\current.csv')

    add_new_minute(current)


def add_new_minute(current):

    new_minute = {'time': [current['minute']],
                  'ticker': [current['ticker']],
                  'open': [current['open']],
                  'high': [current['high']],
                  'low': [current['low']],
                  'close': [current['close']],
                  'volume': [current['volume']]
                  }
    dfx = pd.DataFrame(new_minute)
    current_frame = gl.current_frame.append(dfx, sort=False)
    current_frame.to_csv(r'temp_assets/charts/current_frame.csv')
