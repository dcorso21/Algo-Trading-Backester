from local_functions.main import global_vars as gl


def analyse():
    '''
    # Core Function: Analyse

    Looks at daily (and eventually yearly chart) and decides whether its a good time to trade. 
    Then uses that info, plus info on current positions to create new orders (if any).

    Returns Orders DataFrame.

    ## Process:

    #### Skip Clause:
    If the global variable loop_feedback is set to false, return a blank df.  

    ### 1) Analyse Daily Chart

    ### 2) Build Orders 
    '''

    # Skip Clause ---
    # If feedback is false, dont run the function, return the blank df...
    if gl.buy_lock == True:
        if len(gl.current_positions) == 0:
            gl.loop_feedback = False
            return gl.pd.DataFrame()

    # 1) Analyse Daily Chart - Only when there has been a price update...
    if gl.current['close'] != gl.last['close']:
        ana_day()

    # 2) Build Orders
    orders = gl.order_eval.build_orders()

    return orders


'''----- Day Analysis -----'''


def ana_day():
    '''
    # Analyse Day Chart
    Updates files and looks for patterns in the daily chart. 

    Updates Global chart_response boolean. 

    ## Process:

    ### 1) Runs update_files function
    Updates momentum, supports, resistances and volatility analysis. 

    ### 2) Evaluates current price info with the pricing_eval function. 

    ### 3) Evaluates current volume info with the volume_eval function. 

    ### 4) Based on these assessments, set the global variable chart_response as True or False. 

    '''
    # 1) Runs update_files function
    gl.d_update_docs.update_files()

    # 2) Evaluates current price info with the pricing_eval function.
    p_eval = day_pricing_eval()

    # 3) Evaluates current volume info with the volume_eval function.
    if len(gl.current_frame) >= 5:
        v_eval = day_volume_eval()

    # 4) Based on these assessments, set the global variable chart_response as True or False.
    if p_eval:  # and v_eval:
        gl.chart_response = True

    else:
        gl.chart_response = False


def day_pricing_eval():

    pmeths = pricing_analysis_methods

    if len(gl.current_frame) < 5:
        return pmeths('closer_to_low_than_open')

    elif pmeths('volatile_downtrend') and pmeths('bottom_of_candle'):
        return True

    return False


def day_volume_eval():
    vmeth = volume_analysis_methods
    return vmeth('volume_min_check')


def day_pricing_analysis_methods(method):
    def closer_to_low_than_open():
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

    methods = {
        'closer_to_low_than_open': closer_to_low_than_open,
        'volatile_downtrend': volatile_downtrend,
        'bottom_of_candle': bottom_of_candle,
    }

    return methods[method]()


def day_volume_analysis_methods(method):

    def volume_min_check():
        mins_back = 5
        minimum_volume = 100000
        current_frame = gl.current_frame

        if len(current_frame) < mins_back:
            mins_back = len(current_frame)

        df = current_frame.tail(mins_back)

        # drop current row...
        if len(df) != 0:
            df = df.head(mins_back-1)

        vols = df.volume.values
        closes = df.close.values

        dvol = list(float(close)*float(vol)
                    for close, vol in zip(closes, vols))

        if sorted(dvol)[0] > minimum_volume:
            return True
        return False

    methods = {
        'volume_min_check': volume_min_check,
    }

    return methods[method]()


'''----- Year Analysis -----'''
