from local_functions.main import global_vars as gl


def update_candle(price, volume, ticker, minute, second):
    '''
    # Update Candle
    Updates the global variables: `current` and `current_frame`. 

    Nothing Returned.  

    ## Parameters:{

    - `price`: updated price,

    - `volume`: updated volume,

    - `ticker`: Ticker Symbol of stock,

    - `minute`: Updated Minute,

    - `second`: Updated Second  

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

    # 3) Update global variable `current_frame` with the `add_new_minute()` function.
    add_new_minute(current)


def add_new_minute(current):
    '''
    # Add New Minute
    Retreive `sim_df` up to (but not including) current minute.
    Then, append the `current` variable as the most recent minute 
    and re-save the variable `current_frame`   
    '''
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
    '''
    ## Clone Current Frame
    At the end of each minute, simply pull the `sim_df` variable and copy the needed rows. 

    The cloned `sim_df` is then saved as the `current_frame` variable. 
    '''
    df = gl.sim_df
    ind = df[df.time == gl.current['minute']].index.tolist()[0]
    gl.current_frame = df[:ind+1]
