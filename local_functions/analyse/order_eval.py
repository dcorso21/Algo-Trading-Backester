from local_functions.main import global_vars as gl


def build_orders():
    '''
    # Build Orders

    Analyses positions and decides whether or not to buy or sell. 

    Returns DataFrame of orders.

    ## Process:
    ### 1) Checks auto-refresh cancelled orders. 

    #### Skip Clause:
    Check Bad Trade Conditions, if met, return blank df. 

    ### 2) Get Sell Orders

    ### 3) Get Buy Orders

    '''
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
    # If nothing to sell, return blank df
    if len(gl.current_positions) == 0:
        return gl.pd.DataFrame()

    sell_conds = [
        'eleven_oclock_exit',
        'percentage_gain',
        'target_unreal',
        'exposure_over_account_limit',
    ]

    for condition in sell_conds:
        sells = sell_conditions(condition)
        if len(sells) != 0:
            gl.log_funcs.log_sent_orders(sells, 'sell')
            break
        return sells


def sell_conditions(condition):
    # 3 % gain... sell all
    def percentage_gain():
        '''
        ## Percentage Gain
        ### Sell Condition
        If the current price is a certain percentage over the average, then sell EVERYTHING. 

        Returns a Sells DataFrame

        #### Note: 
        If the condition is not met, this returns a blank DF. 
        '''
        avg = gl.common.get_average()
        if gl.current['close'] > (avg * 1.03):
            # sell all
            everything = gl.current_positions.qty.sum()
            exe_price = 'bid'
            sells = gl.order_tools.create_orders('SELL', everything, exe_price)
            gl.log_funcs.log('----> over 3 perc gain triggered.')
            return sells
        sells = gl.pd.DataFrame()
        return sells

    def target_unreal():
        '''
        ## Target Unreal
        ### Sell Condition
        If the amount in unreal is above a specified target, sell EVERYTHING. 

        Returns a Sells DataFrame

        #### Note: 
        If the condition is not met, this returns a blank DF. 
        '''
        target_int = 200
        unreal = gl.pl_ex['unreal']
        if unreal > target_int:
            # sell all
            qty = gl.current_positions.qty.sum()
            exe_price = 'bid'
            sells = gl.order_tools.create_orders('SELL', qty, exe_price)

            gl.log_funcs.log(f'----> unreal hits trigger: {unreal}')
            return sells

        return gl.pd.DataFrame()

    def exposure_over_account_limit():
        '''
        ## Exposure over Account Limit
        ### Sell Condition
        If the amount owned in shares is more than I can afford, immediately sell HALF. 

        Returns a Sells DataFrame

        #### Note: 
        If the condition is not met, this returns a blank DF. 
        '''
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

    def eleven_oclock_exit():
        '''
        ## Eleven O'Clock Exit
        ### Sell Condition
        If the current minute is 11:00:00, then sell EVERYTHING. 

        Returns a Sells DataFrame

        #### Note: 
        If the condition is not met, this returns a blank DF. 
        '''
        if (gl.current['minute'] == '11:00:00') or (gl.sell_out == True):
            qty = gl.current_positions.qty.sum()
            pmethod = 'extrapolate'
            sells = gl.order_tools.create_orders('SELL', qty, pmethod)

            gl.log_funcs.log('Sell to Stop...')
            gl.buy_lock = True
            gl.sell_out = True
        else:
            sells = gl.pd.DataFrame()
        return sells

    conditions = {

        'percentage_gain': percentage_gain,
        'target_unreal': target_unreal,
        'exposure_over_account_limit': exposure_over_account_limit,
        'eleven_oclock_exit': eleven_oclock_exit,

    }

    return conditions[condition]()


def buy_eval():
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
        return buy_conditions('starting_position')

    buy_conds = [
        'aggresive_average',
        'drop_below_average',
    ]

    # 2. Go through each Buy Condition to see if the time is right to sell (this second)
    # Order is important as the first function to yield an order will break the loop and return the DF.
    for condition in buy_conds:
        buys = buy_conditions(condition)
        if len(buys) != 0:
            gl.log_funcs.log_sent_orders(buys, 'buy')
            break
    return buys


def buy_conditions(condition):

    def starting_position():
        '''
        ## Starting Position
        Creates buy order with one percent of available capital at current price. 

        Returns buys DataFrame. 
        '''
        if gl.chart_response == True:
            cash = gl.account.get_available_capital() * .01
            pmeth = 'ask'
            buys = gl.order_tools.create_orders('BUY', cash, pmeth)
            gl.log_funcs.log('---> Sending Starting Position.')
            return buys
        return gl.pd.DataFrame()

    def drop_below_average():
        '''
        ## Drop Below Average
        ### Buy Condition
        Checks to see if the current price is a certain amount below the average price of your current positions. 

        Returns buys DataFrame

        ### Details:
        The drop amount is taken from the volas module with the function: `get_max_vola()`
        '''
        if gl.buy_clock > 0:
            return gl.pd.DataFrame()

        current = gl.current
        max_vola = gl.common.get_max_vola(volas=gl.volas, min_vola=2.5)
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
                gl.log_funcs.log('---> Aggressive Avg Follow.')
                return buys
        return gl.pd.DataFrame()

    conditions = {

        'starting_position': starting_position,
        'drop_below_average': drop_below_average,
        'aggresive_average': aggresive_average,
    }

    return conditions[condition]()


def check_auto_refresh():
    cancelled = gl.cancelled_orders
    if len(cancelled) != 0:
        to_refresh = cancelled[cancelled['auto_refresh']
                               != False].order_id.to_list()
        refreshed = gl.order_specs.iloc[to_refresh]
        return refreshed
    else:
        return []


def bad_trade_conds():
    '''
    # Check for Bad Trade Conditions
    Checks to see if certain conditions are met  

    Returns a True/False Value. TRUE means the conditions are bad for trading (this second)

    ## Conditions:
    ### 1) If there are Open Orders --> return True

    ### 2) if there are NO Current Positions AND the chart response is Bad (False) ---> return True 
    '''
    if len(gl.open_orders) != 0:
        return True

    if (len(gl.current_positions) == 0) and (gl.chart_response == False):
        return True

    return False


def log_sent_orders(orders, buy_or_sell):
    '''
    # Log Sent Orders
    takes orders and order types and logs a message 

    of the amount of shares and cash being bought/sold

    ## Parameters:{

    orders: df of new prospective orders,

    buy_or_sell: order type - string 'buy' or 'sell'

    }
    '''
    if len(orders) != 0:
        order_cash = orders.cash.sum()
        order_qty = orders.qty.sum()

        message = f'Signal to {buy_or_sell} {order_qty} shares (cash: {order_cash})'
        gl.log_funcs.log(message)
