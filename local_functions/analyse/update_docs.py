from local_functions.main import global_vars as gl


def update_files():
    # region Docstring
    '''
    # Update Daily Analysis Files
    Updates the `mom_frame`, `volas`, `volumes` and `sup_res_frame` global variables. 

    ## Details.

    `volas` (volatility dictionary) is updated every second. 

    `volumes` (volumes dictionary) is updated every second. 

    `mom_frame` (momentum analysis) and `sup_res_frame` (supports/resistances) are updated each minute

    ##### Note: Order does not really matter here. 

    '''
    # endregion Docstring

    update_return_and_pl()
    update_volumes()
    update_volas()

    if gl.current['second'] == 59:
        update_momentum()
        if len(gl.mom_frame) != 0:
            update_supports_resistances()


'''----- Current Positions -----'''


def update_return_and_pl():
    # region Docstring
    '''
    # Update Current Positions Return and PL
    Updates the current positions return and PL columns, as well as the Unreal value in gl.pl_ex

    Returns Nothing. 

    ## Process:

    #### Skip Clause
    If there aren't any current_positions, skip function. 

    ### 1) Calculate percentage return for each position in the 'p_return' column
    ### 2) Calculate the unrealized profit/loss in the 'un_pl' column
    ### 3) Update the current_position global variable to include these newly updated rows
    ### 4) Update the current Unrealized PL from the sum of the 'un_pl' column. 

    '''
    # endregion Docstring

    current_positions = gl.current_positions

    if len(current_positions) != 0:
        exe_prices = current_positions.exe_price.values

        current_positions['p_return'] = gl.np.around(
            (((gl.current['close'] - exe_prices) / exe_prices)*100), decimals=2)

        # 1) Calculate percentage return for each position in the 'p_return' column
        # ret = []
        # for x in current_positions.exe_price:
        #     ret.append(round(((gl.current['close'] - x)/x)*100, 1))

        # current_positions['p_return'] = ret

        # 2) Calculate the unrealized profit/loss in the 'un_pl' column
        current_positions['un_pl'] = current_positions.cash.values * \
            current_positions.p_return.values*.01

        # 3) Update the current_position global variable to include these newly updated rows
        gl.current_positions = current_positions

        # 4) Update the current Unrealized PL from the sum of the 'un_pl' column.
        gl.common.update_pl('skip', current_positions['un_pl'].sum())


'''----- Volas & Volumes -----'''


def update_volumes():
    # region Docstring
    '''
    # Update Volumes
    Updates the global `volumes` dictionary

    Returns nothing.  

    ## Notes:
    - Uses the `current_frame` global variable for volume units, 
    - Converts to dollar volume for user comprehension based on close price. 

    ## TO DO:
    - Item
    '''
    # endregion Docstring
    volumes = gl.volumes

    current = gl.current
    current_frame = gl.current_frame
    last_row = current_frame.index.to_list()[-1]
    current_frame = current_frame.drop(last_row)

    current_frame['dvol'] = current_frame.loc[:, 'close'] * \
        current_frame.loc[:, 'volume']

    current_dvol = current['volume'] * current['close']

    volumes['extrap_current'] = (current_dvol / (current['second']+1))*60
    if current['second'] == 59:
        volumes['mean'] = current_frame.dvol.mean()
        volumes['minimum'] = current_frame.dvol.min()
        volumes['safe_capital_limit'] = volumes['minimum'] / 4
        if len(current_frame) >= 3:
            volumes['three_min_min'] = current_frame.tail(3).dvol.min()
            volumes['three_min_mean'] = current_frame.tail(3).dvol.mean()
            if len(current_frame) >= 5:
                volumes['five_min_mean'] = current_frame.tail(5).dvol.mean()
                volumes['differential'] = (
                    volumes['five_min_mean'] - current_frame.head(5).mean()) / current_frame.head(5).mean()
                volumes['five_min_min'] = current_frame.tail(5).dvol.min()
                if len(current_frame) >= 10:
                    volumes['ten_min_mean'] = current_frame.tail(
                        10).dvol.mean()
                    volumes['ten_min_min'] = current_frame.tail(10).dvol.min()

    gl.volumes = volumes


def update_volas():
    '''
    # Update Volatility Variable
    Updates the global variable `volas`
    '''

    cf = gl.current_frame

    # make volatility column
    cf['vola'] = gl.common.get_volatility(
        cf['high'], cf['low'])

    # calculate volatilities for different time increments
    cf['three_vola'] = cf.vola.rolling(3).mean()
    cf['five_vola'] = cf.vola.rolling(5).mean()
    cf['ten_vola'] = cf.vola.rolling(10).mean()

    volas = {
        'current': cf['vola'].tolist()[-1],
        'mean': cf.vola.mean(),
        'three_min': cf['three_vola'].tolist()[-1],
        'five_min': cf['five_vola'].tolist()[-1],
        'ten_min': cf['ten_vola'].tolist()[-1],
    }

    if len(cf) > 5:
        volas['differential'] = (cf.tail(5).vola.mean() -
                                 cf.head(5).vola.mean()) / cf.head(5).vola.mean()

    # set ideal volatility

    ideal_vola = gl.controls.misc['ideal_volatility']

    scaler = volas['five_min'] / ideal_vola

    if scaler > 1:
        scaler = 1 - (scaler - 1)
    else:
        scaler = 1

    volas['scaler'] = scaler

    # save json file
    gl.volas = volas


'''----- Momentum -----'''
# region Momentum


def update_momentum():
    # region Docstring
    '''
    # Update Momentum
    Updates the global variable `mom_frame`

    ### Details:
    The momentum frame analyses trends on the daily chart. 

    From this frame, we can update supports and resistances (`sup_res_frame` variable). 
    from another sheet.    

    ## Process:
    #### Skip Clause:
    If there are less than 5 minutes in the `current_frame`, ---> return without doing anything.  

    ### 1) Define Starting Variables. 
    ### 2) Under certain conditions, pick up where last left off with global mom_frame. 
    There have to have been at least 15 minutes elapsed and 3 momentum shifts to use the previous version of the mom_frame. 
    ### 3) Loop through each trend on chart and add the trend to the mom_frame. Below is the loop procedure:

    - (3.1) Create list of aggregation values based on how many rows are left in the current_frame. 

     If there are no aggregation periods to attempt, BREAK LOOP. 

    - (3.2) Scan each length in aggregation list to find duration of each trend

    - (3.3) Retreive index from the end of the new trend.

    - (3.4) Append new row with trend to the `mom_frame`

    - (3.5) Update values for next cycle in loop. 

    ### 4) Replace global `mom_frame` variable with newly made DataFrame. 

    '''
    # endregion Docstring
    # 1) Define Starting Variables. #####################################################
    df = gl.current_frame.reset_index(drop=True)
    # don't do anything unless the df is at least 5 rows long.
    if len(df) < 5:
        return

    dfz = gl.pd.DataFrame()
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
        agg_list = new_agg_list(df, last_offset)

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

        dfz['volatility'] = gl.common.get_volatility(
            dfz.high.astype(float), dfz.low.astype(float))

        if fresh == False:
            dfz = mom_df.append(dfz, sort=False)

        dfz = dfz.reset_index(drop=True)
        gl.mom_frame = dfz


def new_agg_list(df, last_offset):
    '''
    ## New Aggregation List

    Returns List of Aggregation times to look for trend with. 

    ### Process:
    #### 1) Takes the index from the end of the last trend and calculates the remaining rows in the current_frame.

    #### 2) takes an ideal list of aggregation lengths and makes a new list 

    - only including the values that would fit in the remainder.

    NOTE: I tested this with Numpy arrays, and this method is somehow faster. Do not know why.   
    '''

    # ideally, these are the increments for aggregation.
    ideal_list = [5, 10, 15, 20, 25, 30]

    agg_list = []
    # this process looks at how many rows are left and adds to the list those which will fit in the remainder
    for x in ideal_list:
        if int((len(df)-last_offset) / x) != 0:
            agg_list.append(x)

    if len(agg_list) == 0:
        if (len(df) - last_offset)/2 >= 2:
            agglist = [2]

    return agg_list


def get_new_offset(yin, last_offset, dfx):
    '''
    # Get New Offset

    Takes the end of the new trend and sets that 
    index as the new `offset`  - or beginning - of the next trend. 

    ---> returns the new offset index value.  

    ## Process:
    ### 1) Make a list of the `yins` index values. 
    - depending on the current trend, we could be looking for the high indexes or low indexes. The `yin` variable makes this flexible. 

    ### 2) Loop through each `yin` index value to find which one is highest. 
    - If a value is the highest for a certain amount of minutes without being superceded, BREAK LOOP. 

    ### 3) Once the new trend is found ---> return the end index as the next trend's `offset` 
    '''
    # 1) Make a list of the 'yins' index values.
    yins = dfx[yin].tolist()
    last_yin = yins[0]

    # 2) Loop through each 'yin' index value to find which one is highest.
    for y in yins:
        if y > (last_yin + 4):
            break
        last_yin = y

    # End of trend, start of next trend...
    offset = last_yin

    # just making sure it doesn't get stuck in the same minute...
    if offset == last_offset:
        offset += 1

    # 3) Once the new trend is found ---> return the end index as the next trend's 'offset'
    return offset


def append_mom_row(yin, offset, last_offset, df, dfz):
    '''
    # Append Momentum Row
    Appends latest trend to momentum frame currently being assembled.  

    returns the `dfz` DataFrame with a new trend appended. 

    ## Parameters:{

    - `yin`: str of trend type - either `hi` for high index or `li` for low index. 

    - `offset`: integer value - to be used for the END of the trend duration. 

    - `last_offset`: integer value - to be used for the START of the trend duration. 

    - `df`: DF of Current_frame

    - `dfz`: mom_frame to be appended to. 

    }
    '''
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

    row = gl.pd.DataFrame({'start_time': [start_time], 'end_time': [end_time], 'duration': [duration],
                           'trend': [trend], 'high': [high], 'low': [low], 'color': [color]})

    dfz = dfz.append(row, sort=False)

    return dfz


def pick_up_from_index(df, mom_df, mom_dict):
    '''
    ## Pick up from Index
    Chooses a starting point three trends back to start from. 

    Returns the starting offset index, the trend type (yin and yang) and the mom_df that it will add to.   

    ### Parameters:{

    `df`: current frame DF.

    `mom_df`: mom_frame 

    `mom_dict`: circular dictionary for defining trend type. 

    ### }

    ### Process:
    #### 1) Retreives starting index from 3 trends ago. 
    #### 2) Defines starting trend based on last trend. 
    #### 3) Returns Key Variables.  
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
    '''
    # Many Lengths
    Returns a DataFrame (dfx) of different aggregation periods with index ranges. 

    ## Process:

    ### Start Clause:
    If the `yin` variable passed equals 'start', it means that we are beginning 
    in the first minute and need to see which way the momentum starts. 

    The function bases the direction of the first momentum swing on whether the candle is red or green. 

    ### 1) Loops through each value in aggregation list 
    Passing the start and end indexes through the `simplify_candles()` function. This returns 
    a one-row df each loop.   

    ### 2) Each Row is added to a `dfx`, which is then returned.

    ### 3) Once the next index is found, make sure that the `yang` Value is not superceded in the same period. 
    - For example, if tracking an uptrend, We want to make sure that the price hasn't swung down before going to a new high.
    If such a thing were to happen, this would constitute 2 quick momentum shifts instead of 1.

    '''

    # Start Clause:
    if yin == 'start':
        o = df.open.to_list()[0]
        c = df.close.to_list()[0]

        # if candle green
        if o < c:
            # yin is momentum, and its going up...
            yin = 'hi'
            yang = 'li'
        elif c <= o:
            yin = 'li'
            yang = 'hi'

    dfx = gl.pd.DataFrame()
    # 1) Loops through each value in aggregation list
    for x in agg_list:
        y = x + offset
        if len(df) >= y:
            row = simplify_candles(df, offset, y)
            # 2) Each Row is added to a dfx, which is then returned.
            dfx = dfx.append(row, sort=False)
        else:
            break

    # 3) Once the next index is found, make sure that the 'Yang' Value is not superceded in the same period.
    dfx = dfx[dfx[yang] == dfx[yang].tolist()[0]]
    return dfx, yin, yang


def simplify_candles(df, start_index, end_index):
    '''
    ### Simplify Candles
    Aggregates Candles based on the start and end index values of the DataFrame 

    ---> Returns a one-row DataFrame with the ohlc values for the given range, 
    as well as the indexes for the high and low values.  
    '''

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

        dfx = gl.pd.DataFrame(minute).T
        dfx = dfx.rename(
            columns={0: 'o', 1: 'h', 2: 'l', 3: 'c', 4: 'oi', 5: 'hi', 6: 'li', 7: 'ci'})

        return dfx


def aggregate_df(agg_num, df):
    # region Docstring
    '''
    # aggregate_df
    AS OF NOW AN UNUSED FUNCTION

    Creates aggregation period of minute df. 
    So, it can aggregate candles to create 2 min, 5 min, xmin candles.  

    ## Parameters:{
    ####    `param`: 
    ## }

    ## Process:

    ### 1) 

    ## Notes:
    - Notes

    ## TO DO:
    - Item
    '''
    # endregion Docstring

    last_ind = 0
    dfx = gl.pd.DataFrame()
    for x in range(1, int(len(df)/agg_num)+1):
        ind = x*agg_num + 1
        dfx = dfx.append(simplify_candles(df, last_ind, ind), sort=False)
        last_ind = ind

    if (len(dfx) * agg_num) != len(df):
        left = len(df) - len(dfx)
        dfx = dfx.append(simplify_candles(
            df, len(df)-left, len(df)), sort=False)

    return dfx

# endregion Momentum


'''----- Supports and Resistances -----'''
# region Momentum


def update_supports_resistances():
    # region Docstring
    '''
    # Update Supports and Resistances
    Updates the `sup_res_frame_variable`

    returns nothing.  

    ## Process:

    ### 1) Get list of resistances with `get_resistances` function. 

    ### 2) Get list of supports with `get_supports` function. 

    ### 3) Convert these lists to a DataFrames using 
    the `expand_on_resistances` and  `expand_on_supports`

    ### 4) Combine the 2 dataframes and save as one to the `gl.sup_res_frame`

    ## Notes:
    - Notes

    ## TO DO:
    - Item
    '''
    # endregion Docstring

    # 1) Get list of resistances with `get_resistances` function.
    resistances = get_resistances()
    # 2) Get list of supports with `get_supports` function.
    supports = get_supports()

    # 3) Convert these lists to a DataFrames using
    # the `expand_on_resistances` and  `expand_on_supports`
    resistances = expand_on_resistances(resistances)
    supports = expand_on_supports(supports)

    # 4) Combine the 2 dataframes and save as one to the `gl.sup_res_frame`
    gl.sup_res_frame = resistances.append(supports, sort=False)


def expand_on_resistances(resistances, min_duration=8):
    # region Docstring
    '''
    # Expand on Resistances
    takes list of resistances and refines them down based on duration

    returns a dataframe of resistances with the start time, duration and price.  

    ## Parameters:{
    ####    `resistances`: list of resistance prices. 
    ####    `min_duration`: integer specifying how many minutes a resistance must hold to qualify. 
    ## }

    ## Process:

    ### 1) 

    ## Notes:
    - Notes

    ## TO DO:
    - Perhaps it would be possible to have several different 
    types of resistances to designate by duration. 
    '''
    # endregion Docstring

    mom_frame = gl.mom_frame
    cf = gl.current_frame

    dfx = gl.pd.DataFrame()
    for x in resistances:

        row = mom_frame[mom_frame.high == x].head(1)
        index = row.index.tolist()[0]
        if row.at[index, 'trend'] == 'uptrend':
            time = row.at[index, 'end_time']
        else:
            time = row.at[index, 'start_time']

        start = cf[cf.time == time].index.tolist()[0]

        remainder = cf.iloc[start:, :]
        higher = remainder[remainder.high.astype(float) > float(x)]

        row = {'type': ['resistance'], 'start_time': [
            time], 'duration': [len(remainder)], 'price': [x]}

        # If the resistance hasn't been broken.
        if len(higher) == 0:
            row = gl.pd.DataFrame(row)
            dfx = dfx.append(row, sort=False)
            continue

        next_high_index = higher.index.tolist()[0]
        duration = next_high_index - start

        # If the resistance has been broken but lasted at least the min_duration.
        if duration >= min_duration:
            row['duration'] = duration
            row = gl.pd.DataFrame(row)
            dfx = dfx.append(row, sort=False)
            continue

    if len(dfx) != 0:
        dfx = dfx.sort_values(by='start_time')
    return dfx


def expand_on_supports(supports, min_duration=8):
    # region Docstring
    '''
    # Expand on Supports
    takes list of supports and refines them down based on duration

    returns a dataframe of supports with the start time, duration and price.  

    ## Parameters:{
    ####    `supports`: list of support prices. 
    ####    `min_duration`: integer specifying how many minutes a support must hold to qualify. 
    ## }

    ## Process:

    ### 1) 

    ## Notes:
    - Notes

    ## TO DO:
    - Perhaps it would be possible to have several different 
    types of supports to designate by duration. 
    '''
    # endregion Docstring
    mom_frame = gl.mom_frame
    cf = gl.current_frame

    dfx = gl.pd.DataFrame()
    for x in supports:

        row = mom_frame[mom_frame.low == x].head(1)
        index = row.index.tolist()[0]
        if row.at[index, 'trend'] == 'downtrend':
            time = row.at[index, 'end_time']
        else:
            time = row.at[index, 'start_time']

        start = cf[cf.time == time].index.tolist()[0]

        remainder = cf.iloc[start:, :]
        lower = remainder[remainder.low.astype(float) < float(x)]

        row = {'type': ['support'], 'start_time': [
            time], 'duration': [len(remainder)], 'price': [x]}

        # If the support hasn't been broken.
        if len(lower) == 0:
            row = gl.pd.DataFrame(row)
            dfx = dfx.append(row, sort=False)
            continue

        next_low_index = lower.index.tolist()[0]
        duration = next_low_index - start

        # If the support has been broken but lasted at least the min_duration.
        if duration >= min_duration:
            row['duration'] = duration
            row = gl.pd.DataFrame(row)
            dfx = dfx.append(row, sort=False)
            continue

    if len(dfx) != 0:
        dfx = dfx.sort_values(by='start_time')
    return dfx


def get_resistances(cent_range=5):
    # region Docstring
    '''
    # Get Resistances
    Make a list of price resistances based on `mom_frame` variable  

    Returns a list of prices (resistances)

    ## Parameters:{
    ####    `cent_range`: int, number of cents to use as a buffer 
    ####                to ensure multiple resistances aren't right next to each other.  
    ## }

    ## Process:

    ### 1) Get list of 'highs' from the `mom_frame` global variable. 
    - Ensure there are no duplicates. 

    ### 2) Iterate through each resistance and evaluate whether it should count as a new resistance
    - If it is below a current resistance in the cent range, it will be discarded
    - If it is above a current resistance in the cent range, the old resistance will be discarded

    ### 3) Return a list of resistances.  

    ## Notes:
    - A high will only be added as a resistance if it is higher than one known in the same cent range
    or if it is isolated on its own. 

    ## TO DO:
    - Item
    '''
    # endregion Docstring

    df = gl.mom_frame
    # 1) Get list of 'highs' from the `mom_frame` global variable.
    highs = set(df[df.high >= gl.current['close']].high.to_list())

    resistances = set()

    # 2) Iterate through each resistance and evaluate whether it should count as a new resistance
    for high in highs:

        # if no other resistances have been evaluated, add it to the set.
        if len(resistances) == 0:
            resistances.add(high)
            continue

        nearby_resistance = [resist for resist in resistances if abs(
            resist - high) <= cent_range*.01]

        # if there are no nearby matches, it is a new resistance.
        if len(nearby_resistance) == 0:
            resistances.add(high)
            continue

        # if it is higher than the nearby one, replace old one.
        if high > nearby_resistance[0]:
            resistances.discard(nearby_resistance[0])
            resistances.add(high)

    # 3) return list
    return list(resistances)


def get_supports(cent_range=3):
    # region Docstring
    '''
    # Get supports
    Make a list of price supports based on `mom_frame` variable  

    Returns a list of prices (supports)

    ## Parameters:{
    ####    `cent_range`: int, number of cents to use as a buffer 
    ####                to ensure multiple supports aren't right next to each other.  
    ## }

    ## Process:

    ### 1) Get list of 'highs' from the `mom_frame` global variable. 
    - Ensure there are no duplicates. 

    ### 2) Iterate through each support and evaluate whether it should count as a new support
    - If it is above a current support in the cent range, it will be discarded
    - If it is below a current support in the cent range, the old support will be discarded

    ### 3) Return a list of supports.  

    ## Notes:
    - A high will only be added as a support if it is higher than one known in the same cent range
    or if it is isolated on its own. 

    ## TO DO:
    - Item
    '''
    # endregion Docstring

    mom_frame = gl.mom_frame
    # 1) Get list of 'highs' from the `mom_frame` global variable.
    lows = set(mom_frame[mom_frame.low <= gl.current['close']].low.to_list())

    supports = set()

    # 2) Iterate through each resistance and evaluate whether it should count as a new resistance
    for low in lows:

        # if no other resistances have been evaluated, add it to the set.
        if len(supports) == 0:
            supports.add(low)
            continue

        nearby_support = [support for support in supports if abs(
            support - low) <= cent_range*.01]

        # if there are no nearby matches, it is a new support.
        if len(nearby_support) == 0:
            supports.add(low)
            continue

        # if it is lower than the nearby one, replace old one.
        if low > nearby_support[0]:
            supports.discard(nearby_support[0])
            supports.add(low)

    # 3) return list
    return list(supports)

# endregion Momentum
