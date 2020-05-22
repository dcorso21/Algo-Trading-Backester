from local_functions.main import global_vars as gl


def update_direct():
    if gl.trade_mode == 'csv':
        csv_refresh()
    else:
        live_refresh()


def live_refresh():
    pass


def csv_refresh():
    # region Docstring
    '''
    # CSV Refresh Data
    This is a master function for simulated (not real-time) trading. 
    It iterates through each row of the `sim_df` variable.

    Returns nothing, updates `current` and `current_frame` variables. 

    '''
    # endregion Docstring

    sim_df = gl.sim_df
    current = gl.current
    gl.last = current
    last = gl.last
    new_minute = False
    gl.buy_clock -= 1

    # If at the very beginning... get the index of the sim_df.
    if len(gl.csv_indexes) == 0:

        first_ind = sim_df.index.to_list()[0]
        last_ind = sim_df.index.to_list()[-1]
        indexes = {
            'first': first_ind,
            'current': first_ind,
            'last': last_ind
        }
        gl.csv_indexes = indexes
        gl.sim_ticker = sim_df.at[first_ind, 'ticker']
        row = first_ind
        minute = current['minute'] = sim_df.at[first_ind, 'time']
        current['second'] = 0
        # gl.log_funcs.log(f'^^^{minute}')
        new_minute = True
    else:
        row = gl.csv_indexes['current']

        if row == gl.csv_indexes['last']:
            gl.loop_feedback = False
            return

        if last['minute'] == gl.configure.misc['hard_stop']:
            gl.loop_feedback = False
            return

    # Continue Minute...
    if last['second'] == 59:
        new_minute = True
    else:
        minute = current['minute']
        second = current['second'] + 1

    # New Minute...
    if new_minute == True:
        gl.gather.clone_current_frame()
        # Log end of last minute...
        # gl.log_funcs.log(msg='minute complete')
        # Go to next row.
        row = gl.csv_indexes['current'] = gl.csv_indexes['current'] + 1
        gl.minute_prices, gl.minute_volumes = gl.hist.create_second_data(sim_df,
                                                                         row, mode='momentum')
        minute = sim_df.at[row, 'time']
        second = 0
        # New Minute
        gl.sys.stdout.write(f'\rcurrent minute : {minute}')
        gl.sys.stdout.flush()

    price = gl.minute_prices[second]
    volume = gl.minute_volumes[second]
    ticker = gl.sim_ticker

    gl.gather.update_candle(price, volume, ticker, minute, second)


def update_candle(price, volume, ticker, minute, second):
    # region Docstring
    '''
    # Update Candle
    Updates the global variables: `current` and `current_frame`. 

    Nothing Returned.  

    ## Parameters:{
    ####    `price`: updated price,
    ####    `volume`: updated volume,
    ####    `ticker`: Ticker Symbol of stock,
    ####    `minute`: Updated Minute,
    ####    `second`: Updated Second
    ## }

    ## Process:
    ### Start Clause:
    - If it is the first second of the minute, 
    all ohlc values are the current price

    ### 1) Updates high, low, close, and volume values. 
    - If `price` is higher than previous high, high = `price`.
    - If `price` is lower than previous low, low = `price`.

    ### 2) Re-Save global variable `current`
    ### 3) Update global variable `current_frame` with the `add_new_minute()` function. 

    '''
    # endregion Docstring

    # Start Clause:
    if second == 0:
        o, h, l, c = price, price, price, price
    else:
        prev = gl.current

        o, h, l, c = prev['open'], prev['high'], prev['low'], prev['close']

        # 1) Updates open, high, low, close values.
        if price > h:
            h = price
        if price < l:
            l = price
    c = price
    v = volume

    # 2) Re-Save global variable `current`
    current = {'open': o,
               'high': h,
               'low': l,
               'close': c,
               'volume': v,
               'second': second,
               'minute': minute,
               'ticker': ticker}

    gl.current = current
    # if current['second'] == 0:
    #     gl.log_funcs.log(f'^^^{minute}')

    # 3) Update global variable `current_frame` with the `add_new_minute()` function.
    add_new_minute(current)


def add_new_minute(current):
    # region Docstring
    '''
    # Add New Minute

    Retreive `sim_df` up to (but not including) current minute.
    Then, append the `current` variable as the most recent minute 
    and re-save the variable `current_frame` 

    ## Parameters:{
    ####    `current`: dictionary to be appended as new minute.  
    ## }

    '''
    # endregion Docstring

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
    # region Docstring
    '''
    ## Clone Current Frame
    At the end of each minute, simply pull the `sim_df` variable and copy the needed rows. 

    The cloned `sim_df` is then saved as the `current_frame` variable. 
    '''
    # endregion Docstring

    df = gl.sim_df
    ind = df[df.time == gl.current['minute']].index.tolist()[0]
    gl.current_frame = df[:ind+1]
