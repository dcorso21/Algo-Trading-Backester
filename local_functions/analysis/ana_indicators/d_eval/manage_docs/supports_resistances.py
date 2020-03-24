from local_functions.analysis.ana_indicators import common
from local_functions.main import global_vars as gl


import pandas as pd
import json
import logging


def update_supports_resistances():

    resistances = get_resistances()
    supports = get_supports()

    df = gl.mom_frame
    cf = gl.current_frame

    dfx = pd.DataFrame()

    resistances = refine_resistances(resistances, dfx, df, cf)

    supports = refine_supports(supports, dfx, df, cf)

    dfz = resistances.append(supports, sort=False)

    dfz.to_csv('temp_assets/analysis/supports_resistances.csv')


def refine_resistances(resistances, dfx, df, cf):
    for x in resistances:

        row = df[df.high == x].head(1)
        if row.trend.tolist()[0] == 'uptrend':
            time = row.end_time.tolist()[0]
        else:
            time = row.start_time.tolist()[0]
#         print('time start : {}'.format(time))

        index = cf[cf.time == time].index.tolist()[0]

        remainder = cf.iloc[index:, :]
        higher = remainder[remainder.high.astype(float) > float(x)]

        if len(higher) != 0:

            next_high_index = higher.index.tolist()[0]
            duration = next_high_index - index

            if duration > 8:
                row = {'type': ['resistance'], 'start_time': [
                    time], 'duration': [duration], 'price': [x]}
                add = True
            else:
                add = False

        else:
            row = {'type': ['resistance'], 'start_time': [
                time], 'duration': [len(remainder)], 'price': [x]}
            add = True

        if add == True:
            row = pd.DataFrame(row)
            dfx = dfx.append(row, sort=False)

    if len(dfx) != 0:
        dfx = dfx.sort_values(by='start_time')
    return dfx


def refine_supports(supports, dfx, df, cf):
    for x in supports:

        row = df[df.low == x].head(1)
        if row.trend.tolist()[0] == 'downtrend':
            time = row.end_time.tolist()[0]
        else:
            time = row.start_time.tolist()[0]
#         print('time start : {}'.format(time))

        index = cf[cf.time == time].index.tolist()[0]

        remainder = cf.iloc[index-2:, :]
        lower = remainder[remainder.low.astype(float) < float(x)]

        if len(lower) != 0:

            next_low_index = lower.index.tolist()[0]
            duration = next_low_index - index

            if duration > 8:

                row = {'type': ['support'], 'start_time': [
                    time], 'duration': [duration], 'price': [x]}
                add = True
            else:
                add = False

        else:
            row = {'type': ['support'], 'start_time': [time],
                   'duration': [len(remainder)], 'price': [x]}
            add = True

        if add == True:
            row = pd.DataFrame(row)
            dfx = dfx.append(row, sort=False)

    if len(dfx) != 0:
        dfx = dfx.sort_values(by='start_time')
    return dfx


def get_resistances(current, cent_range=10):

    # volas = pull_json('temp_assets/analysis/volas.json')

    df = pd.read_csv('temp_assets/analysis/daily_eval.csv')

    highs = df[df.high >= current['close']].high.to_list()

    highs = list(dict.fromkeys(highs))

    resistances = set()

    for high in highs:
        added = False

        if len(resistances) == 0:
            resistances.add(high)

        else:
            for resistance in resistances:

                added = eval_resistance(
                    high, resistance, resistances, cent_range)

                if added == True:
                    break

            if added == False:
                resistances.add(high)

    return list(resistances)


def eval_resistance(high, resistance, resistance_set, cent_range):

    cents = (cent_range*.01)/2

    if (high > resistance - cents) and (high < resistance + cents):

        added = True
        if high > resistance:

            resistance_set.discard(resistance)
            resistance_set.add(high)

    else:
        added = False

    return added


def get_supports(current, cent_range=6):

    # volas = pull_json('temp_assets/analysis/volas.json')

    df = pd.read_csv('temp_assets/analysis/daily_eval.csv')

    lows = df[df.low <= current['close']].low.to_list()

    lows = list(dict.fromkeys(lows))

    supports = set()

    for low in lows:
        added = False

        if len(supports) == 0:
            supports.add(low)

        else:
            for support in supports:

                added = eval_support(low, support, supports, cent_range)

                if added == True:
                    break

            if added == False:
                supports.add(low)

    return list(supports)


def eval_support(low, support, support_set, cent_range):

    cents = (cent_range*.01)/2

    if (low > support - cents) and (low < support + cents):

        added = True
        if low < support:

            support_set.discard(support)
            support_set.add(low)

    else:
        added = False

    return added
