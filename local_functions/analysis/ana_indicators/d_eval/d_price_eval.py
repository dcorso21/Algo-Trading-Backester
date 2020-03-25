from local_functions.main import global_vars as gl


import pandas as pd
import logging
import json


def pricing_eval():
    binary = False
    if red_green()[-1] == 'red':
        binary = True

    return binary


def find_uptrends():

    df = gl.current_frame
    dfx = pd.DataFrame()
    count = 0

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
    current_frame = gl.current_frame()
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
