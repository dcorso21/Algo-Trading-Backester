from local_functions.main import global_vars as gl


def analyse():
    # region Docstring
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
    # endregion Docstring

    # Skip Clause ---
    # If feedback is false, dont run the function, return the blank df...
    if gl.buy_lock == True:
        if len(gl.current_positions) == 0:
            gl.loop_feedback = False
            return gl.pd.DataFrame()

    # 1) Analyse Daily Chart - Only when there has been an update...
    if gl.current['close'] != gl.last['close']:
        gl.update_docs.update_files()
        # only necessary to evaluate if there are no current positions.
        if len(gl.current_positions) == 0:
            day_pricing_eval()

    # 2) Build Orders
    orders = gl.order_eval.build_orders()

    return orders


'''----- Day Analysis -----'''


def day_pricing_eval():
    # region Docstring
    '''
    # Day Pricing Evaluation
    Decides if it is a good time to place a starting position. 

    Updates the global variable `chart_response`

    ## Process:

    ### 1) References `day_pricing_analysis_methods` function,
    this function contains all of the different methods for checking if its a good time to buy. 

    ## Notes:
    - At the moment, it has two methods, based on the amount of time into market. 

    ## TO DO:
    - Item
    '''
    # endregion Docstring

    pmeths = day_pricing_analysis_methods

    # if first 5 minutes check this function.
    if len(gl.current_frame) < 5:
        response = pmeths('closer_to_low_than_open')
    else:
        response = False
        if pmeths('volatile_downtrend') and pmeths('bottom_of_candle'):
            response = True

    gl.chart_response = response


def day_pricing_analysis_methods(method):
    # region Docstring
    '''
    # Day Pricing Analysis Methods
    Master Function for accessing any of the pricing methods.  

    Returns True/False from function named. 

    ## Parameters:{
    ####    `method`: string of name of function to call.  
    ## }

    ## Process:

    ### 1) String references the function from a dictionary, 
    ### then calls it and returns a bool. 

    ## Notes:
    - Notes

    ## TO DO:
    - Item
    '''
    # endregion Docstring
    def closer_to_low_than_open():
        # region Docstring
        '''
        # Closer to Low than Open
        Compares open price to current price and checks two conditions:
        - it is less than open
        - it is closer to the low than the open.  

        Returns Bool
        '''
        # endregion Docstring
        df = gl.current_frame
        day_open = df.open.to_list()[0]
        low = df.low.min()
        c_price = df.close.to_list()[-1]

        # If the price is less than open...
        if c_price < day_open:
            # If the price is closer to the low than the high price.
            if (day_open - c_price) > (c_price - low):
                # gl.logging.info('chart looks good via ana_first_mins')
                return True

        return False

    def volatile_downtrend():
        # region Docstring
        '''
        # Volatile Downtrend
        Checks to see there is currently a volatile downtrend happening. 
        This is based on the `mom_frame` variable.

        Return Bool

        ## TO DO:
        - relate volatility with flexibility. 
        '''
        # endregion Docstring
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
        # region Docstring
        '''
        # Bottom of Candle
        True if price is closer to the low of the candle than the high. 

        Returns a True/False

        Note:
        - if less than 30 seconds in to candle, aggregate last candle with current. 
        '''
        # endregion Docstring

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


'''----- Year Analysis -----'''
