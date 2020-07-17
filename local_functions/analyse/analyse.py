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
    # If feedback is false, dont run the function, return the blank list...
    if gl.buy_lock == True:
        if len(gl.current_positions) == 0:
            gl.loop_feedback = False
            return []

    # 1) Analyse Daily Chart - Only when there has been an update...
    if str(gl.current) != str(gl.last) or gl.current['second'] == 59:
        # only necessary to evaluate if there are no current positions.
        gl.update_docs.update_files()
        if len(gl.current_positions) == 0:
            day_eval()

    # 2) Build Orders
    set_trade_mode()
    orders = gl.order_eval.build_orders()
    gl.log_funcs.log_sent_orders(orders)

    return orders

def set_trade_mode():
    if len(gl.current_frame) <= 5:
        strategy = 'mkt_open_chaos'
    else:
        if str(gl.close_sup_res[0]) == 'nan':
            strategy = 'free_fall'
        elif str(gl.close_sup_res[1]) == 'nan':
            strategy = 'breakout_to_new_highs'
        else:
            strategy = 'consolidating'
    
    if strategy != gl.strategy:
        gl.log_funcs.log(f'New Trade Mode: {strategy}')
    
    gl.strategy = strategy




'''----- Day Analysis -----'''


def day_eval():
    # region Docstring
    '''
    # Day Evaluation
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

    # Rule out trading if unnacceptable amount is already lost. 
    if gl.pl_ex['real'] <= gl.configure.misc['dollar_risk']:
        gl.chart_response = False
        gl.buy_lock = True
        gl.log_funcs.log('dollar risk hit: trading stopped')
        return

    # Rule Out trading if not enough Volume
    if gl.config['misc']['volume_check']:
        if len(gl.current_frame) < 2:
            if not day_volume_analysis_methods('early_extrap'):
                return
        else:
            if not day_volume_analysis_methods('worth_trading'):
                gl.chart_response = False
                gl.loop_feedback = False
                gl.log_funcs.log('insufficient volume: trading stopped')
                return
        
    if gl.common.mins_left() <= gl.config['misc']['lookahead_mins']:
        gl.chart_response = False
        gl.loop_feedback = False
        gl.log_funcs.log('insufficient time: trading stopped')
        return 


    gl.update_docs.update_files()
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


def day_volume_analysis_methods(method):
    dvol_min = gl.config['misc']['minimum_volume']
    def worth_trading():
        current_frame = gl.current_frame
        current_frame['dvol'] = current_frame.close.values * \
            current_frame.volume.values

        dvol = current_frame.dvol.astype(float).tolist()
        # don't want to base this on current minute.
        del dvol[-1]

        if min(dvol) >= dvol_min:
            return True
        return False

    def early_exrap():
        sec = gl.current['second']
        cur_dvol = gl.current_frame.volume.values[-1]*gl.current['close']
        extrap = (cur_dvol/(sec+1))*60
        if extrap >= dvol_min:
            return True
        return False

    methods = {
        'worth_trading': worth_trading,
        'early_extrap': early_exrap
    }

    return methods[method]()


'''----- Year Analysis -----'''
