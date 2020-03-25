from local_functions.main import global_vars as gl


def update_candle(price, volume, ticker, minute, second):
    '''Inputs--
    prices: list of prices simulating real time updates from the historical_funcs: create_second_data.'''

    if second == 0:
        o, h, l, c = price, price, price, price
    else:
        prev = gl.current()

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

    gl.save_dict_to_csv(current, gl.filepath['current'])

    add_new_minute(current, gl.filepath['current_frame'])


def add_new_minute(current, file_path):

    new_minute = {'time': [current['minute']],
                  'ticker': [current['ticker']],
                  'open': [current['open']],
                  'high': [current['high']],
                  'low': [current['low']],
                  'close': [current['close']],
                  'volume': [current['volume']]
                  }
    dfx = gl.pd.DataFrame(new_minute)
    updated_frame = gl.daily_ohlc().append(dfx, sort=False)
    updated_frame.to_csv(file_path)
