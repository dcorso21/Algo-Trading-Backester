from local_functions.analysis.ana_indicators import common

import pandas as pd
import json
import logging


def update_momentum(current_frame):

    # ideally, these are the increments for aggregation.
    ideal_list = [5, 10, 15, 20, 25, 30]

    # we have to reset the index so that the index isn't all zeros.
    # this is necessary because we need to use indexes later on
    df = current_frame.reset_index()

    # dfz is the momentum dataframe
    dfz = pd.DataFrame()

    # don't do anything unless the df is at least 5 rows long.
    if len(df) > ideal_list[0]:

        # momentum swings from up to down, so I name this push and pull yin and yang.
        yin = 'start'
        yang = 'start'

        # specifies a starting index.
        offset = 0
        fresh = True
        if len(df) > 15:

            mom_df = pd.read_csv('temp_assets/analysis/daily_eval.csv')
            offset = mom_df.index.to_list()[-2]
            mom_df = mom_df.iloc[:offset]
            fresh = False

        last_offset = offset

        # circular dictionary :
        # each time the momentum swings, the yin and yang switch.
        mom_dict = {
            'hi': 'li',
            'li': 'hi'
        }

        loop = True
        while loop:

            agg_list = []

            # this process looks at how many rows are left and adds to the list those which will fit in the remainder
            for x in ideal_list:
                if int((len(df)-last_offset) / x) != 0:
                    agg_list.append(x)

            # if the length of the agg_list is 0,
            # break the loop..
            if len(agg_list) == 0:
                break

            # if there are still lengths in the list -  go ahead.
            elif len(agg_list) != 0:

                # main part of loop -  get the agg periods in a df
                dfx, yin, yang = many_lengths(agg_list, offset, yin, yang, df)

                if len(dfx) == 0:
                    loop = False

                # Make sure that a new high or low isnt passed while looking for the opposite.
                dfx = dfx[dfx[yang] == dfx[yang].tolist()[0]]

                yins = dfx[yin].tolist()
                last_yin = yins[0]

                # goes through high/low indexer and picks the one that is greatest
                # and stays the greatest
                for x in yins:
                    if x > (last_yin + 4):
                        break
                    last_yin = x

                offset = last_yin

                if offset == last_offset:
                    offset = offset + 1

                trends = {'hi': 'uptrend', 'li': 'downtrend'}

                duration = (offset - last_offset)

                start_time = df[df.index == last_offset].time.to_list()[0]
                end_time = df[df.index == offset].time.to_list()[0]
                trend = trends[yin]

                if trend == 'uptrend':
                    high = df[df.time == end_time].high.to_list()[0]
                    low = df[df.time == start_time].low.to_list()[0]
                    color = '#fcba03'
                else:
                    high = df[df.time == start_time].high.to_list()[0]
                    low = df[df.time == end_time].low.to_list()[0]
                    color = '#e336a4'

                row = pd.DataFrame({'start_time': [start_time], 'end_time': [end_time], 'duration': [duration],
                                    'trend': [trend], 'high': [high], 'low': [low], 'color': [color]})

                last_offset = offset
                yin = mom_dict[yin]
                yang = mom_dict[yang]
                dfz = dfz.append(row, sort=False)

        if len(dfz) != 0:

            dfz['volatility'] = common.get_volatility(
                dfz.high.astype(float), dfz.low.astype(float))

            if fresh == False:
                dfz = mom_df.append(dfz, sort=False)

            dfz = dfz.reset_index().drop(columns=['index'])
            dfz.to_csv('temp_assets/analysis/daily_eval.csv')


def many_lengths(agg_list, offset, yin, yang, df):

    # this if statement is to start the momentum tracking.
    # you send in variable yin and yang as 'start
    # momentum is based on first open and close.

    if yin == 'start':
        o = df.open.to_list()[0]
        c = df.close.to_list()[0]

        # if candle green
        if o < c:
            # yin is momentum, and its going up...
            yin = 'hi'
            yang = 'li'
        elif c < o:
            yin = 'li'
            yang = 'hi'

    dfx = pd.DataFrame()

    for x in agg_list:

        y = x + offset
        if len(df) >= y:

            row = simplify_candles(df, offset, y)
            dfx = dfx.append(row, sort=False)

        else:
            break

    return dfx, yin, yang


def simplify_candles(df, start_index, end_index):

    df_slice = df.iloc[int(start_index):int(end_index+1), :]

    if len(df_slice) != 0:

        o = df_slice.open.tolist()[0]
        oi = df_slice.index.tolist()[0]

        h = df_slice.drop(start_index).high.max()
        hi = df_slice[df_slice['high'] == h].index.tolist()[0]

        l = df_slice.drop(start_index).low.min()
        li = df_slice[df_slice['low'] == l].index.tolist()[0]

        c = df_slice.close.tolist()[-1]
        ci = df_slice.index.tolist()[-1]

        minute = [o, h, l, c, oi, hi, li, ci]

        dfx = pd.DataFrame(minute).T
        dfx = dfx.rename(
            columns={0: 'o', 1: 'h', 2: 'l', 3: 'c', 4: 'oi', 5: 'hi', 6: 'li', 7: 'ci'})

        return dfx


def aggregate_df(agg_num, df):

    #agg_num = 11
    last_ind = 0
    dfx = pd.DataFrame()

    for x in range(1, int(len(df)/agg_num)+1):
        ind = x*agg_num + 1
        dfx = dfx.append(simplify_candles(df, last_ind, ind), sort=False)
        last_ind = ind

    if (len(dfx) * agg_num) != len(df):
        left = len(df) - len(dfx)
        dfx = dfx.append(simplify_candles(
            df, len(df)-left, len(df)), sort=False)

    return dfx
