from local_functions.main import global_vars as gl


def update_files():
    gl.sec_mom = update_second_momentum()
    update_return_and_pl()
    update_volumes()
    update_volas()
    update_momentum()
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

    with gl.pd.option_context('mode.chained_assignment', None):
        current_frame['dvol'] = current_frame.close.values * \
            current_frame.volume.values

    volumes['fail_check'] = len(
        current_frame[current_frame['dvol'] < gl.config['misc']['minimum_volume']]) >= 3
    current_dvol = current['volume'] * current['close']

    volumes['extrap_current'] = (current_dvol / (current['second']+1))*60
    if current['second'] == 59:
        volumes['mean'] = current_frame.dvol.mean()
        volumes['minimum'] = current_frame.dvol.min()
        volumes['safe_capital_limit'] = volumes['minimum'] / 4
        # Differential is a percentage difference in volume from the first five minutes.
        if volumes['mean'] == 0:
            volumes['differential'] = 0
        else:
            volumes['differential'] = (
                current_frame.tail(5).dvol.mean() - current_frame.head(5).dvol.mean()) / current_frame.head(5).dvol.mean()
        if len(current_frame) >= 3:
            volumes['three_min_min'] = current_frame.tail(3).dvol.min()
            volumes['three_min_mean'] = current_frame.tail(3).dvol.mean()
            if len(current_frame) >= 5:
                volumes['five_min_mean'] = current_frame.tail(5).dvol.mean()
                volumes['five_min_min'] = current_frame.tail(5).dvol.min()
                if len(current_frame) >= 10:
                    volumes['ten_min_mean'] = current_frame.tail(
                        10).dvol.mean()
                    volumes['ten_min_min'] = current_frame.tail(10).dvol.min()

        v_dict = volumes.copy()
        v_dict['time'] = gl.common.get_current_timestamp()
        row = gl.pd.DataFrame(v_dict, index=[len(gl.volume_frame)])
        gl.volume_frame = gl.volume_frame.append(row, sort=False)

    gl.volumes = volumes


def update_volas():
    # region Docstring
    '''
    # Update Volas
    Updates the volas global variable
    '''
    # endregion Docstring

    volas = gl.volas
    volas['current'] = gl.common.get_volatility(
        [gl.current['high']], [gl.current['low']])[0]

    cf = gl.current_frame
    if len(gl.current_frame) == 0:
        cf = cf.drop(gl.current_frame.index[-1])

    cf['vola'] = gl.common.get_volatility(cf['high'], cf['low'])

    volas['mean'] = cf.vola.mean()
    volas['three_min'] = cf.tail(3).vola.mean()
    volas['five_min'] = cf.tail(5).vola.mean()
    volas['ten_min'] = cf.tail(10).vola.mean()

    if volas['mean'] == 0:
        volas['differential'] = 0
    else:
        volas['differential'] = (cf.tail(5).vola.mean() -
                                 cf.head(5).vola.mean()) / cf.head(5).vola.mean()

    if gl.current['second'] == 59:
        v_dict = volas.copy()
        v_dict['time'] = gl.common.get_current_timestamp()
        row = gl.pd.DataFrame(v_dict, index=[len(gl.volas_frame)])
        gl.volas_frame = gl.volas_frame.append(row)

    if volas['scaler'] == 'nan':
        ideal_vola = gl.configure.misc['ideal_volatility']
        scaler = volas['five_min'] / ideal_vola
        if scaler > 1:
            scaler = 1 - (scaler - 1)
        else:
            scaler = 1
        volas['scaler'] = scaler

    gl.volas = volas


'''----- Momentum -----'''

@ gl.log_funcs.tracker
def update_second_momentum():
    sec_mom = gl.sec_mom
    last = gl.last['close']
    current = gl.current['close']
    if last == 'nan':
        return 0

    if sec_mom == 0:
        if current > last:
            sec_mom = 1
        elif current < last:
            sec_mom = -1
    elif sec_mom < 0:
        if current <= last:
            sec_mom -= 1
        else:
            sec_mom = +1
    else:
        if current >= last:
            sec_mom += 1
        else:
            sec_mom = -1
    return sec_mom


def update_momentum():
    if gl.current['second'] != 59 or len(gl.current_frame) < 2:
        return

    df = gl.current_frame

    # Reverse the frame to start from last minute
    df = df.iloc[::-1].reset_index(drop=True)

    df['higher'] = df.rolling(2).high.apply(func=(
        lambda x: (x[0] <= x[1])
    ), raw=True)

    df['lower'] = df.rolling(2).low.apply(func=(
        lambda x: (x[0] >= x[1])
    ), raw=True)

    trends = []
    for h, l in zip(df.higher, df.lower):
        if h == 1 and l == 0:
            trends.append('downtrend')
        elif h == 1 and l == 1:
            trends.append('pennant')
        elif h == 0 and l == 1:
            trends.append('uptrend')
        elif h == 0 and l == 0:
            trends.append('rpennant')
        else:
            trends.append('nan')

    df['trend'] = trends
    # gl.tab_df(df)

    cf, tf = identify_trends(df, gl.pd.DataFrame(), df)
    # tf = fill_trend_gaps(df, tf)
    tf = tf.reset_index(drop=True)
    highs, lows = [], []

    for index in tf.index:
        row = dict(tf.iloc[index])
        start_high = df[df.time == row['start_time']].high.to_list()[0]
        start_low = df[df.time == row['start_time']].low.to_list()[0]
        end_high = df[df.time == row['end_time']].high.to_list()[0]
        end_low = df[df.time == row['end_time']].low.to_list()[0]

        if 'pennant' in row['trend']:
            highs.append([start_high, end_high])
            lows.append([start_low, end_low])
        else:
            if row['trend'] == 'uptrend':
                highs.append(end_high)
                lows.append(start_low)
            elif row['trend'] == 'downtrend':
                highs.append(start_high)
                lows.append(end_low)
            else:
                highs.append('nan')
                lows.append('nan')

    tf['high'] = highs
    tf['low'] = lows
    # gl.tab_df(tf)
    mom_frame = tf.sort_values(by='start_time')
    mom_frame['volatility'] = gl.common.get_volatility(
        mom_frame.high, mom_frame.low, convert=True)
    durations = []
    for start_time, end_time in zip(mom_frame.start_time, mom_frame.end_time):
        durations.append(gl.common.get_duration(
            start_time, end_time, convert_to_timestamp=True))
    mom_frame['duration'] = durations
    gl.mom_frame = mom_frame


def identify_trends(cf, tf, full_df):
    cf = cf.reset_index(drop=True)
    end_point = dict(cf.iloc[0])
    # take the rest from that minute onwards
    cf = cf.iloc[1:]
    cf = cf.reset_index(drop=True)
    trend = cf.trend.to_list()[0]
    count = 1
    last_time = end_point['time']
    new_trend = True
    for t, time, index in zip(cf.trend, cf.time, cf.index):
        # If Trend has stopped
        if t != trend:
            # If it a pennant trend, and has not been at least 3 mins
            if ('pennant' in trend) and (count < 3):
                next_trend = end_point['trend']
                extend = False
                extension = {
                    'pennant': 'uptrend',
                    'rpennant': 'downtrend',
                    'uptrend': 'downtrend',
                    'downtrend': 'uptrend',
                }
                if len(tf) == 0:
                    break
                elif next_trend == extension[trend]:
                    if next_trend == 'uptrend':
                        if cf.at[index-1, 'high'] > full_df[full_df.time == tf.end_time.to_list()[-1]].high.to_list()[0]:
                            trend = extension[next_trend]
                        elif 'r' not in trend:
                            trend = extension[next_trend]
                        else:
                            # Extend Trend
                            tf = tf.reset_index(drop=True)
                            tf.at[tf.index.to_list()[-1],
                                  'start_time'] = last_time
                            new_trend = False
                    elif next_trend == 'downtrend':
                        new_low = cf.at[index-1, 'low']
                        next_low = full_df[full_df.time ==
                                           tf.end_time.to_list()[-1]].low.to_list()[0]
                        if new_low < next_low:
                            trend = extension[next_trend]
                        elif 'r' in trend:
                            trend = extension[next_trend]
                        else:
                            # Extend Trend
                            tf = tf.reset_index(drop=True)
                            tf.at[tf.index.to_list()[-1],
                                  'start_time'] = last_time
                            new_trend = False
                else:
                    trend = extension[next_trend]

            break
        count += 1
        last_time = time

    # Continue Trend
    extend = False
    if len(tf) != 0:
        next_trend = tf.trend.to_list()[-1]
        if trend == next_trend:
            if trend == 'uptrend':
                new_trend_high = end_point['high']
                next_trend_high = full_df[full_df.time ==
                                          tf.end_time.to_list()[-1]].high.values[0]
                if new_trend_high > next_trend_high:
                    tf = tf.reset_index(drop=True)
                    tf = tf.drop(tf.index.to_list()[-1])
                    tf.at[tf.index.to_list()[-1], 'start_time'] = end_point['time']
                else:
                    extend = True
            elif trend == 'downtrend':
                new_trend_low = end_point['low']
                next_trend_low = full_df[full_df.time ==
                                         tf.end_time.to_list()[-1]].low.values[0]
                if new_trend_low < next_trend_low:
                    tf = tf.reset_index(drop=True)
                    tf = tf.drop(tf.index.to_list()[-1])
                    tf.at[tf.index.to_list()[-1], 'start_time'] = end_point['time']
                else:
                    extend = True
            else:
                extend = True

    if extend:
        tf = tf.reset_index(drop=True)
        tf.at[tf.index.to_list()[-1], 'start_time'] = last_time
        new_trend = False

    if new_trend:
        row = {
            'start_time': [last_time],
            'end_time': [end_point['time']],
            'trend': [trend],
        }
        trend_info = gl.pd.DataFrame(row)
        tf = tf.append(trend_info, sort=False)

    if last_time == cf.time.to_list()[-1]:
        return cf, tf
    else:
        left = cf[index - 1:]
        cf, tf = identify_trends(left, tf, full_df)
    return cf, tf


'''----- Supports and Resistances -----'''


def update_supports_resistances():

    if len(gl.mom_frame) == 0:
        return
    broken_sup = gl.current_price() < gl.close_sup_res[0]
    broken_res = gl.current_price() > gl.close_sup_res[1]
    end_of_minute = gl.current['second'] == 59

    if not broken_sup and not broken_res and not end_of_minute:
        return

    mf = gl.mom_frame
    df = gl.current_frame
    pot_sup, pot_res = [], []
    for index in mf.index:
        row = dict(mf.iloc[index])
        if 'pennant' in row['trend']:
            row['high'] = max(row['high'])
            row['low'] = min(row['low'])
        # Timing
        if row['trend'] == 'downtrend':
            high_time = row['start_time']
            low_time = row['end_time']
        elif row['trend'] == 'uptrend':
            low_time = row['start_time']
            high_time = row['end_time']
        elif row['trend'] == 'pennant':
            high_time = row['start_time']
            low_time = row['start_time']
        elif row['trend'] == 'rpennant':
            high_time = row['end_time']
            low_time = row['end_time']
        pot_sup.append([row['low'], low_time])
        pot_res.append([row['high'], high_time])

    res = gl.update_docs.expand_on_sup_res(price_type='resistance',
                                           significant_prices=pot_res,
                                           current_frame=df,
                                           mom_frame=mf)

    sup = gl.update_docs.expand_on_sup_res(price_type='support',
                                           significant_prices=pot_sup,
                                           current_frame=df,
                                           mom_frame=mf)

    gl.sup_res_frame = sup.append(res, sort=False)

    if len(res) == 0:
        closest_res = float('nan')
    else:
        closest_res = res[(res['status'] == 'active') &
                          (res['start_time'] != gl.current['minute'])].price.min()

    if len(sup) == 0:
        closest_sup = float('nan')
    else:
        closest_sup = sup[(sup['status'] == 'active') &
                          (sup['start_time'] != gl.current['minute'])].price.max()

    gl.close_sup_res = [closest_sup, closest_res]


def expand_on_sup_res(price_type, significant_prices, current_frame, mom_frame, min_duration=8):
    cf = current_frame.reset_index(drop=True)
    if price_type == 'resistance':
        column = 'high'
    elif price_type == 'support':
        column = 'low'

    dfx = gl.pd.DataFrame()
    for price, time in significant_prices:
        start = cf[cf.time == time].index.tolist()[0]

        remainder = cf.iloc[start:]
        if price_type == 'resistance':
            overs = remainder[remainder[column].astype(float) > float(price)]
        elif price_type == 'support':
            overs = remainder[remainder[column].astype(float) < float(price)]

        row = {'type': [price_type],
               'start_time': [time],
               'status': ['active'],
               'duration': [len(remainder)],
               'price': [price]}

        # If the resistance hasn't been broken.
        if len(overs) == 0:
            row = gl.pd.DataFrame(row)
            dfx = dfx.append(row, sort=False)
            continue

        next_over_index = overs.index.tolist()[0]
        duration = next_over_index - start

        # If the resistance has been broken but lasted at least the min_duration.
        if duration >= 3:
            row['duration'] = duration
            row['status'] = 'broken'
            row = gl.pd.DataFrame(row)
            dfx = dfx.append(row, sort=False)

    if len(dfx) != 0:
        dfx = dfx.sort_values(by='start_time')
    return dfx
