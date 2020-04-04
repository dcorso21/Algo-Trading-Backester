from local_functions.main import global_vars as gl


import pandas as pd
import logging
import json


def pricing_eval():
    if len(gl.current_frame) < 5:
        return ana_first_mins()

    elif volatile_downtrend() and bottom_of_candle():
        return True

    return False


def ana_first_mins():
    df = gl.current_frame
    day_open = df.open.to_list()[0]
    low = df.low.min()
    c_price = df.close.to_list()[-1]

    # If the price is less than current price...
    if c_price < day_open:
        # If the price is closer to the low than the high price.
        if (day_open - c_price) > (c_price - low):
            # gl.logging.info('chart looks good via ana_first_mins')
            return True

    return False


def volatile_downtrend():
    mom_frame = gl.mom_frame
    if len(mom_frame) == 0:
        return False
    last_index = mom_frame.index.to_list()[-1]
    trend = mom_frame.at[last_index, 'trend']
    vola = mom_frame.at[last_index, 'volatility']
    if (trend == 'downtrend') and (vola > 5):  # gl.volas['mean']):
        # gl.logging.info('chart looks good via vola_downtrend')
        return True
    return False


def bottom_of_candle():
    '''
    # Bottom of Candle
    Returns a True/False

    True if price is closer to the low of the candle than the high. 
    '''
    current = gl.current

    # If its more than
    if current['second'] >= 30:
        # If the distance from the price to the high is greater than the distance from the price to the low.
        # In other words, if price is closer to low than high.
        if (current['close'] - current['low']) < (current['high'] - current['close']):
            return True
        return False

    df = gl.current_frame.tail(2)
    low = df.low.min()
    high = df.high.max()
    # If the distance from the price to the high is greater than the distance from the price to the low.
    # In other words, if price is closer to low than high.
    if (current['close'] - low) < (high - current['close']):
        return True
    return False


def find_uptrends():

    df = gl.current_frame
    dfx = pd.DataFrame()
    count = 0
    last_min = {}

    for o, h, l, c, m in zip(df.open.astype(float), df.high.astype(float), df.low.astype(float), df.close.astype(float), df.time):

        # if green candle:
        if o <= c:
            count += 1
            if count == 1:
                start_min = {'open': o,
                             'high': h,
                             'low': l,
                             'close': c,
                             'time': m}
        else:
            count = 0

        #
        if count > 1:
            if (h < last_min['high']) and (l <= last_min['low']):
                count = 0

        last_min = {'open': o,
                    'high': h,
                    'low': l,
                    'close': c,
                    'time': m}

        if count >= 3:

            volatility = (
                (last_min['high'] - start_min['low'])/start_min['low'])*100

            row = {'pattern': ['uptrend'],
                   'start_min': [start_min['time']],
                   'end_min': [last_min['time']],
                   'duration': [count],
                   'volatility': [round(volatility, 2)]}
            row = pd.DataFrame(row)
            dfx = dfx.append(row)

    slim_df = pd.DataFrame()

    time_list = dfx.start_min
    time_list = list(dict.fromkeys(time_list))

    for time in time_list:
        dfz = dfx[dfx.start_min == time]
        slim_df = slim_df.append(dfz.tail(1))

    return slim_df


def find_downtrends():

    df = gl.current_frame
    dfx = pd.DataFrame()
    count = 0
    last_min = {}

    for o, h, l, c, m in zip(df.open.astype(float), df.high.astype(float), df.low.astype(float), df.close.astype(float), df.time):
        # if red candle:
        if o >= c:
            count += 1
            if count == 1:
                start_min = {'open': o,
                             'high': h,
                             'low': l,
                             'close': c,
                             'time': m}
        else:
            count = 0

        #
        if count > 1:
            if (h > last_min['high']) and (l >= last_min['low']):
                count = 0

        last_min = {'open': o,
                    'high': h,
                    'low': l,
                    'close': c,
                    'time': m}

        if count >= 3:

            volatility = (
                (last_min['high'] - start_min['low'])/start_min['low'])*100

            row = {'pattern': ['downtrend'],
                   'start_min': [start_min['time']],
                   'end_min': [last_min['time']],
                   'duration': [count],
                   'volatility': [round(volatility, 2)]}
            row = pd.DataFrame(row)
            dfx = dfx.append(row)

    slim_df = pd.DataFrame()

    time_list = dfx.start_min
    time_list = list(dict.fromkeys(time_list))

    for time in time_list:
        dfz = dfx[dfx.start_min == time]
        slim_df = slim_df.append(dfz.tail(1))

    return slim_df


def red_green():
    r_g = []
    current_frame = gl.current_frame
    for o, c in zip(current_frame.open, current_frame.close):

        val = 0
        if o < c:
            val = 1
        elif o > c:
            val = 2
        red_or_green = {0: 'doji',
                        1: 'green',
                        2: 'red'}

        r_g.append(red_or_green[val])

    return r_g
