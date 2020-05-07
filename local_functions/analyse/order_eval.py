from local_functions.main import global_vars as gl


def build_orders():
    # region Docstring
    '''
    # Build Orders

    Returns Dataframe of orders. 

    Analyses positions and decides whether or not to buy or sell. 

    Returns DataFrame of orders.

    ## Process:
    ### 1) Checks auto-refresh cancelled orders. 

    #### Skip Clause:
    Check Bad Trade Conditions, if met, return blank df. 

    ### 2) Get Sell Orders

    ### 3) Get Buy Orders

    '''
    # endregion Docstring

    # 1) Checks auto-refresh cancelled orders.
    refreshed = check_auto_refresh()
    if len(refreshed) != 0:
        return refreshed

    # Skip Clause:
    if bad_trade_conds():
        return gl.pd.DataFrame()

    # 2) Get Sell Orders
    sell_orders = sell_eval()
    # if it is a good time to stop, end the function with only sell orders.
    if (gl.buy_lock == True):
        return sell_orders

    # 3) Get Buy Orders
    buy_orders = buy_eval()

    # combine orders
    all_orders = sell_orders.append(buy_orders, sort=False)

    return all_orders


def sell_eval():
    # region Docstring
    '''
    # Sell Evaluation
    Evaluates whether or not it would be a good time to sell, based on a number of SELL CONDIIONS.

    Returns a DataFrame of Sell Orders

    ## Process:
    #### Skip Clause:
    If there are no current positions, there is nothing to sell ---> return empty DataFrame

    ### 1) List Sell Conditions from 'sell_conditions.py' ORDER IS IMPORTANT
    ### 2) Loop through list of Sell Conditions.
    If a condition is met, it will return a DataFrame with a sell order, and the loop will be broken. 
    return ---> Sells DataFrame
    '''
    # endregion Docstring

    # If nothing to sell, return blank df
    if len(gl.current_positions) == 0:
        return gl.pd.DataFrame()

    sell_conds = gl.controls.sell_conditions

    for condition in sell_conds:
        sells = sell_conditions(condition)
        if len(sells) != 0:
            gl.log_funcs.log_sent_orders(sells, 'SELL')
            break
    return sells


def sell_conditions(condition):
    # region Docstring
    '''
    # Sell Conditions
    Master Function that holds all Selling condition functions for trading. 

    ## Parameters:{
    ####    `condition`: string that names the name of the sell conditions function to be accessed ## } ## Process: ### 1) 
    ## Notes:
    -  All Parameters for sell conditions are controlled in `local_functions.main.controls`

    ## TO DO:
    - Item
    '''
    # endregion Docstring

    def dollar_risk_check():
        # region Docstring
        '''
        # Dollar Risk Check
        ### Sell Condition 
        Checks to see if the unreal and real add up to the risk amount noted in conditions. 
        '''
        # endregion Docstring
        d_risk = gl.pl_ex['unreal'] + gl.pl_ex['unreal']
        if d_risk <= gl.controls.dollar_risk:
            everything = gl.current_positions.qty.sum()
            exe_price = 'current_price'
            sells = gl.order_tools.create_orders(
                'SELL', everything, exe_price, auto_renew=5)
            gl.log_funcs.log('----> dollar risk triggered, selling all.')
            return sells
        return []

    def percentage_gain():
        # region Docstring
        '''
        # Percentage_Gain
        A Sell Condition function that will create a sell order based on a percentage gain of `current_positions` overall.  

        Returns a DataFrame of Sell Orders. 

        ## Notes:
        - Notes

        ## TO DO:
        - Item
        '''
        # endregion Docstring
        avg = gl.common.get_average()
        perc = gl.controls.percentage_gain_params['perc_gain']
        if gl.current['close'] >= (avg * (1 + .01 * perc)):
            # sell all
            everything = gl.current_positions.qty.sum()
            exe_price = 'bid'
            sells = gl.order_tools.create_orders('SELL', everything, exe_price)
            gl.log_funcs.log('----> over 3 perc gain triggered.')
            return sells
        sells = gl.pd.DataFrame()
        return sells

    def target_unreal():
        # region Docstring
        '''
        # Target_Unreal
        ### Sell Condition 
        Looks at current unreal PL and if it gets over a certain amount, creates sell order(s). 

        Returns DataFrame of Sell Orders. 

        ## Parameters:{
        ####    All Parametes are controlled in `local_functions.main.controls`
        ## }

        '''
        # endregion Docstring
        target_unreal_amount = gl.controls.target_unreal_params['target_unreal']
        unreal = gl.pl_ex['unreal']
        if unreal >= target_unreal_amount:
            # sell all
            qty = gl.current_positions.qty.sum()
            exe_price = 'bid'
            sells = gl.order_tools.create_orders('SELL', qty, exe_price)

            gl.log_funcs.log(f'----> unreal hits trigger: {unreal}')
            return sells

        return gl.pd.DataFrame()

    def exposure_over_account_limit():
        # region Docstring
        '''
        # exposure_over_account_limit
        ### Sell Condition 
        Looks at current exposure and if it gets over the account limit, creates sell order(s). 

        Returns DataFrame of Sell Orders. 

        ## Parameters:{
        ####    All Parametes are controlled in `local_functions.main.controls`
        ## }

        '''
        # endregion Docstring
        available_capital = gl.account.get_available_capital()
        exposure = gl.pl_ex['last_ex']
        if exposure > available_capital:
            # half
            qty = int(gl.current_positions.qty.sum()/2)
            exe_price = 'bid'
            sells = gl.order_tools.create_orders('SELL', qty, exe_price)

            gl.log_funcs.log('----> over-exposed sell half.')
        else:
            sells = gl.pd.DataFrame()
        return sells

    def timed_exit():
        # region Docstring
        '''
        ## Timed Exit
        ### Sell Condition
        If the current minute is 11:00:00, then sell EVERYTHING. 

        Returns a Sells DataFrame

        ## Parameters:{
        ####    All Parametes are controlled in `local_functions.main.controls`
        ## }
        '''
        # endregion Docstring
        exit_time = gl.controls.timed_exit_params['time']
        exit_time = gl.pd.to_datetime(exit_time).timestamp()

        current_time = gl.current['minute']
        current_time = gl.pd.to_datetime(current_time).timestamp()

        if (current_time >= exit_time) or (gl.sell_out == True):
            qty = gl.current_positions.qty.sum()
            pmethod = 'extrapolate'
            sells = gl.order_tools.create_orders(
                'SELL', qty, pmethod, auto_renew=5)

            gl.log_funcs.log('Sell to Stop...')
            gl.buy_lock = True
            gl.sell_out = True
        else:
            sells = gl.pd.DataFrame()
        return sells

    conditions = {

        'percentage_gain': percentage_gain,
        'dollar_risk_check': dollar_risk_check,
        'target_unreal': target_unreal,
        'exposure_over_account_limit': exposure_over_account_limit,
        'timed_exit': timed_exit,

    }

    return conditions[condition]()


def buy_eval():
    # region Docstring
    '''
    # Buy Evaluation
    Evaluation conditions for buying stock. 

    Returns a DataFrame of Buy Orders. 

    ## Process:
    #### Skip Clause:
    If There are bad conditions for buying ---> return a blank DF. 

    ### 1. Check to see if there are any current_positions.
    If there aren't any current_positions, ---> return a starting position buy DF.   

    ### 2. Go through each Buy Condition to see if the time is right to sell (this second)
    Order is important as the first function to yield an order will break the loop and return the DF. 
    '''
    # endregion Docstring

    # Skip Clause:
    # DONT RUN THE CODE IF THESE CONDITIONS ARE MET.
    # If the chart looks bad
    cond1 = (gl.chart_response == False)
    # If there are no current positions.
    cond2 = (len(gl.current_positions) == 0)
    bad_conditions = False
    if cond1 and cond2:
        bad_conditions = True
    if bad_conditions:
        return gl.pd.DataFrame()

    # 1. Check to see if there are any current_positions.
    # If there aren't any current_positions, ---> return a starting position buy DF.
    if len(gl.current_positions) == 0:
        buys = buy_conditions('starting_position')
        gl.log_funcs.log_sent_orders(buys, 'BUY')
        return buys

    buy_conds = gl.controls.buy_conditions

    # 2. Go through each Buy Condition to see if the time is right to sell (this second)
    # Order is important as the first function to yield an order will break the loop and return the DF.
    for condition in buy_conds:
        buys = buy_conditions(condition)
        if len(buys) != 0:
            gl.log_funcs.log_sent_orders(buys, 'BUY')
            break
    return buys


def buy_conditions(condition):
    # region Docstring
    '''
    # Buy Conditions
    Master function that holds all Buy Conditions 

    Returns DataFrame of Buy Orders or blank DF if condition is not met. 

    ## Parameters:{
    ####    `condition`: string that names the name of the buy conditions function to be accessed 
    ## }


    ## Process:

    ### 1) uses dictionary to compare string condition to function name of condition. 

    ## Notes:
    -  All Parameters for sell conditions are controlled in `local_functions.main.controls`


    ## TO DO:
    - Item
    '''
    # endregion Docstring

    def starting_position():
        # region Docstring
        '''
        # Starting Position
        Creates buy order with one percent of available capital.  

        Returns buys DataFrame.

        ## Parameters:{
        ####    All Parametes are controlled in `local_functions.main.controls`
        ## }

        '''
        # endregion Docstring
        if gl.chart_response == True:
            cash = gl.account.get_available_capital() * .01
            pmeth = 'ask'
            buys = gl.order_tools.create_orders('BUY', cash, pmeth)
            gl.log_funcs.log('---> Sending Starting Position.')
            return buys
        return gl.pd.DataFrame()

    def drop_below_average():
        # region Docstring
        '''
        # Drop Below Average
        ### Buy Condition
        Checks to see if the current price is a certain amount below the average price of your current positions. 

        Returns buys DataFrame


        ## Parameters:{
        ####    All Parametes are controlled in `local_functions.main.controls`
        ## }

        ## Notes:
        - The drop amount is taken from the volas module with the function: `get_max_vola()`
        '''
        # endregion Docstring

        if gl.buy_clock > 0:
            return gl.pd.DataFrame()

        params = gl.controls.drop_below_average_params

        current = gl.current
        # min_vola = params['min_vola']
        # max_vola = params['max_vola']

        max_vola = gl.volas['five_min'] / 2
        # max_vola = gl.common.get_max_vola(volas=gl.volas, min_vola=2.5)
        drop_perc = gl.common.get_inverse_perc(max_vola)
        avg = gl.common.get_average()

        if current['close'] < (avg * drop_perc):
            cash = gl.pl_ex['last_ex']
            available = gl.account.get_available_capital() - cash

            if available < 100:
                gl.log_funcs.log('---> No More Capital!')
                return gl.pd.DataFrame()

            if cash > available:
                cash = available

            pmeth = 'current_price'
            buys = gl.order_tools.create_orders('BUY', cash, pmeth)
            gl.log_funcs.log('---> Drop triggers buy.')
            return buys

        return gl.pd.DataFrame()

    def aggresive_average():
        # region Docstring
        '''
        # Aggresive Average
        ### Buy Condition
        Checks to see if the current price is a certain amount below the average price of your current positions. 

        Returns buys DataFrame

        ## Parameters:{
        ####    All Parametes are controlled in `local_functions.main.controls`
        ## }

        '''
        # endregion Docstring
        current = gl.current
        vola = gl.common.get_max_vola(gl.volas, .02)/4
        avg = gl.common.get_average()
        drop_percent = gl.common.get_inverse_perc(vola)
        if (gl.buy_clock <= 0) and (current['close'] <= avg * drop_percent):
            # and if the current price is below the average by 2%
            ex = gl.pl_ex['last_ex']
            cash = (ex*(avg - 1.01*current['close']))/.01*current['close']
            if cash > current['close']:
                pmeth = 'bid'
                buys = gl.order_tools.create_orders('BUY', cash, pmeth)
                gl.log_funcs.log('---> Follow Aggressive Avg.')
                return buys
        return gl.pd.DataFrame()

    conditions = {
        'starting_position': starting_position,
        'drop_below_average': drop_below_average,
        'aggresive_average': aggresive_average,
    }

    return conditions[condition]()


def check_auto_refresh():
    # region Docstring
    '''
    # check_auto_refresh
    Checks to see if there are cancelled orders that can be autorefreshed.  

    ## Process:

    ### 1) Retrieves cancelled order ids. 
    - These orders will be dropped from the cancelled_orders frame to 
    avoid repetition. 

    ### 2) Retrieves cash or qty values based on order type. 
    ### 3) Decrease auto-renew value by one for new orders.  
    ### 4) Return Renewed Orders 

    '''
    # endregion Docstring
    cancelled = gl.cancelled_orders
    if len(cancelled) != 0:
        cancelled = cancelled[cancelled.status == 'successfully cancelled']

    if len(cancelled) == 0:
        return []

    # 1) Retrieves cancelled order ids.
    need_renew = cancelled[cancelled['auto_renew'] > 0]
    refresh_ids = need_renew.order_id.to_list()

    if len(refresh_ids) == 0:
        return []

    # ~ is used to negate statement. So cancelled orders are orders that are NOT being refreshed
    gl.cancelled_orders = cancelled[~cancelled.order_id.isin(refresh_ids)]

    need_renew = need_renew.reset_index(drop=True)
    need_renew = need_renew.sort_values(by='order_id')

    cash_or_qty = []
    for index in range(len(need_renew)):
        if need_renew.at[index, 'buy_or_sell'] == 'BUY':
            cash_or_qty.append(need_renew.at[index, 'cash'])
        else:
            cash_or_qty.append(need_renew.at[index, 'qty'])

    o_specs = gl.order_specs
    refresh_df = gl.pd.DataFrame()
    for order_id in need_renew.order_id:
        row = o_specs[o_specs.order_id == order_id].head(1)
        refresh_df = refresh_df.append(row, sort=False)

    # refresh_df = gl.order_specs[gl.order_specs.order_id.isin(refresh_ids)]
    refresh_df = refresh_df.reset_index(drop=True)
    refresh_df = refresh_df.sort_values(by='order_id')

    # 2) Retrieves cash or qty values based on order type.

    # 3) Decrease auto-renew value by one for new orders.
    refresh_df['auto_renew'] = need_renew['auto_renew'] - 1
    refresh_df['cash_or_qty'] = cash_or_qty

    gl.log_funcs.log('refreshing order(s): {}'.format(
        refresh_df.order_id.to_list()))

    # 4) Return Renewed Orders
    return refresh_df


def bad_trade_conds():
    # region Docstring
    '''
    # Check for Bad Trade Conditions
    Checks to see if certain conditions are met  

    Returns a True/False Value. TRUE means the conditions are bad for trading (this second)

    ## Conditions:
    ### 1) If there are Open Orders --> return True

    ### 2) if there are NO Current Positions AND the chart response is Bad (False) ---> return True 
    '''
    # endregion Docstring

    if len(gl.open_orders) != 0:
        return True

    if (len(gl.current_positions) == 0) and (gl.chart_response == False):
        return True

    return False
