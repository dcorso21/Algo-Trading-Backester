from local_functions.main import global_vars as gl


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

    gl.current = current
    add_new_minute(current, 'current_frame')


def add_new_minute(current, file_name):

    new_minute = {'time': [current['minute']],
                  'ticker': [current['ticker']],
                  'open': [current['open']],
                  'high': [current['high']],
                  'low': [current['low']],
                  'close': [current['close']],
                  'volume': [current['volume']]
                  }

    new_minute = gl.pd.DataFrame(new_minute)

    df = gl.sim_df
    ind = df[df.time == current['minute']].index.tolist()[0]
    df = df[:ind]
    gl.current_frame = df.append(new_minute, sort=False)


def clone_current_frame():
    df = gl.sim_df
    ind = df[df.time == gl.current['minute']].index.tolist()[0]
    gl.current_frame = df[:ind+1]
