from local_functions.main import global_vars as gl


import pandas as pd
# import json
# import logging


def update_momentum():
    '''
    # Update Momentum
    Updates the global variable 'mom_frame'

    ## Process:
    #### Skip Clause:
    If there are less than 5 minutes in the current_frame, ---> return without doing anything.  

    ### 1) Define Starting Variables. 
    ### 2) Under certain conditions, pick up where last left off with global mom_frame. 
    There have to have been at least 15 minutes elapsed and 3 momentum shifts to use the previous version of the mom_frame. 
    ### 3) Loop through each trend on chart and add the trend to the mom_frame. Below is the loop procedure:

    3.1) Create list of aggregation values based on how many rows are left in the current_frame. 
            # If there are no aggregation periods to attempt, BREAK LOOP. 

    3.2) Scan each length in aggregation list to find duration of each trend

    3.3) Retreive index from the end of the new trend.

    3.4) Append new row with trend to the mom_frame

    3.5) Update values for next cycle in loop. 

    ### 4) Replace global mom_frame variable with newly made DataFrame. 

    '''
    # 1) Define Starting Variables. #####################################################
    df = gl.current_frame.reset_index(drop=True)
    # don't do anything unless the df is at least 5 rows long.
    if len(df) < 5:
        return
    # ideally, these are the increments for aggregation.
    ideal_list = [5, 10, 15, 20, 25, 30]
    dfz = pd.DataFrame()
    # momentum swings from up to down, so I name this push and pull yin and yang.
    yin = 'start'
    yang = 'start'
    # circular dictionary :
    # each time the momentum swings, the yin and yang switch.
    mom_dict = {
        'hi': 'li',
        'li': 'hi'
    }
    # specifies a starting index.
    offset = 0
    fresh = True
    mom_df = gl.mom_frame

    # 2) Under certain conditions, pick up where last left off with global mom_frame.
    if (len(df) > 15) and len(mom_df) > 3:
        offset, yin, yang, mom_df = pick_up_from_index(df, mom_df, mom_dict)
        fresh = False

    last_offset = offset
    loop = True
    # 3) Loop through each trend on chart and add the trend to the mom_frame.
    while loop:
        # 3.1) Create list of aggregation values based on how many rows are left in the current_frame.
        agg_list = new_agg_list(ideal_list, df, last_offset)

        if len(agg_list) == 0:
            break

        # 3.2) Scan each length in aggregation list to find duration of each trend
        dfx, yin, yang = many_lengths(agg_list, offset, yin, yang, df)

        # 3.3) Retreive index from the end of the new trend.
        offset = get_new_offset(yin, last_offset, dfx)

        # 3.4) Append new row with trend to the mom_frame
        dfz = append_mom_row(yin, offset, last_offset, df, dfz)

        # 3.5) Update values for next cycle in loop.
        last_offset = offset
        # reverse yin and yang.
        yin = mom_dict[yin]
        yang = mom_dict[yang]

    # 4) Replace old mom_frame with newly made one.
    if len(dfz) != 0:

        dfz['volatility'] = gl.common_ana.get_volatility(
            dfz.high.astype(float), dfz.low.astype(float))

        if fresh == False:
            dfz = mom_df.append(dfz, sort=False)

        dfz = dfz.reset_index(drop=True)
        gl.mom_frame = dfz


def new_agg_list(ideal_list, df, last_offset):

    agg_list = []

    # this process looks at how many rows are left and adds to the list those which will fit in the remainder
    for x in ideal_list:
        if int((len(df)-last_offset) / x) != 0:
            agg_list.append(x)

    return agg_list


def get_new_offset(yin, last_offset, dfx):

    yins = dfx[yin].tolist()
    last_yin = yins[0]
    # goes through high/low indexer
    # and picks the one that is greatest and stays the greatest
    for y in yins:
        if y > (last_yin + 4):
            break
        last_yin = y

    # End of trend, start of next trend...
    offset = last_yin

    # just making sure it doesn't get stuck in the same minute...
    if offset == last_offset:
        offset += 1

    return offset


def append_mom_row(yin, offset, last_offset, df, dfz):

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

    dfz = dfz.append(row, sort=False)

    return dfz


def pick_up_from_index(df, mom_df, mom_dict):
    '''
    ## Pick up from Index
    Chooses a starting point 
    '''

    pick_up_index = mom_df.index.to_list()[-3]
    pick_up_time = mom_df.at[pick_up_index, 'end_time']
    trend = mom_df.at[pick_up_index, 'trend']
    mom_df = mom_df.iloc[:pick_up_index+1]
    if trend == 'uptrend':
        yin = 'li'
    else:
        yin = 'hi'
    yang = mom_dict[yin]
    offset = df[df.time == pick_up_time].index.to_list()[0]

    return offset, yin, yang, mom_df


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

    # Make sure that a new high or low isnt passed while looking for the opposite.
    dfx = dfx[dfx[yang] == dfx[yang].tolist()[0]]
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
