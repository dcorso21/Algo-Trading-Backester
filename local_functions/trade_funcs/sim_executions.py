from local_functions.main import global_vars as gl

'''
Purpose of this module:

1. Simulate Market conditions like slippage and execution lag.

2. Place orders in queue to be executed
'''


def run_trade_sim(new_orders):
    '''
    # Run Trade Simulation

    Simulates the lag and execution conditions that would prevent an order from being filled instantly. 
    While these orders are awaiting fill they are kept in the gl.open_orders variable. 

    Returns 'Filled Orders' DF. 

    ## Process
    ### 1) Cancel Orders
    Drops open_orders that have been standing or 'open' for over a certain amount of seconds.

    ### 2) Add New Orders to Open_Orders
    Makes new columns used for fill simulation. 

    ### 3) Check Price Requirement and Lag
    Checks to see if price is at or above (for sell) or below (for buy) bid price
    for the amount of lag seconds -  minimum. 

    ### 4) Check Volume Requirement
    Sees if quantity asked has filled (transpired) during the wait duration of the time the order has been open. 

    ### 5) Return Filled Orders and Updates Remaining Current_frame var. 

    '''
    open_orders = gl.open_orders

    # 1) Cancel Orders
    open_orders = check_cancel(open_orders)
    # open_orders = cancel_at_wait_duration(open_orders, cancel_second=5)

    # 2) Add New Orders to Open
    if len(new_orders) != 0:
        new_orders['price_check'] = -1
        new_orders['vol_start'] = -1
        new_orders['wait_duration'] = -1
        open_orders = open_orders.append(new_orders, sort=False)
        # Re - Index
        open_orders = open_orders.reset_index(drop=True)

    if len(open_orders) == 0:
        gl.open_orders = open_orders
        return gl.pd.DataFrame()

    # 3) Check Price Requirement
    open_orders, potential_fills = sim_progress_open_orders(
        open_orders, lag=2, price_offset=0.01)

    # if there are no potential fills,
    # update the open_orders and return - dont bother checking volume...
    if len(potential_fills) == 0:
        filled_orders = gl.pd.DataFrame()
        gl.open_orders = open_orders
        return filled_orders

    # 4) Check Volume Requirement
    fill_indexes, open_orders = vol_check(potential_fills, open_orders)

    if len(fill_indexes) == 0:
        filled_orders = gl.pd.DataFrame()
        gl.open_orders = open_orders
        return filled_orders

    # 5) Return Filled Orders and Update Remaining Current_frame var.
    current = gl.current

    filled_orders = open_orders.iloc[fill_indexes, :]
    columns = ['ticker', 'send_time',
               'buy_or_sell', 'cash', 'qty', 'exe_price']
    filled_orders = filled_orders[columns]
    filled_orders['exe_time'] = gl.pd.Series(gl.common_ana.get_timestamp(
        current['minute'], current['second']))
    filled_orders = filled_orders.dropna()
    open_orders = open_orders.drop(index=fill_indexes)
    gl.open_orders = open_orders

    gl.log_funcs.log(
        f'new_fills: {len(filled_orders)}, open: {len(open_orders)}')

    return filled_orders


def sim_progress_open_orders(open_orders, lag, price_offset):
    '''
    # Sim Progress Open Orders
    Iterates through each open order in the `open_orders` DataFrame.  
    '''

    current = gl.current

    # UPDATE PRICE CHECK VALUE
    for price, buyorsell, index in zip(open_orders.exe_price, open_orders.buy_or_sell, open_orders.index):

        # if it is a buy order and if the price is BENEATH the exe_price (and the offset)...
        # add one to the value.
        if (buyorsell == 'BUY') and (current['close'] <= (price - price_offset)):
            open_orders.at[index, 'price_check'] += 1

        # if it is a sell order and if the price is ABOVE the exe_price (and the offset)...
        # add one to the value.
        elif buyorsell == 'SELL' and (current['close'] >= (price + price_offset)):
            open_orders.at[index, 'price_check'] += 1

        else:
            if open_orders.at[index, 'price_check'] != 0:
                open_orders.at[index, 'price_check'] = 0

    # SET STARTING VOLUME
    for price_check, index in zip(open_orders.price_check, open_orders.index):

        if price_check == 1:
            open_orders.at[index, 'vol_start'] = current['volume']

    # there is potential for these orders to be filled.
    potential_fills = open_orders[open_orders['price_check'] >= lag]

    return open_orders, potential_fills


def vol_check(potential_fills, open_orders):
    fill_indexes = []
    for index, vol_start, qty in zip(potential_fills.index, potential_fills.vol_start, potential_fills.qty):

        current = gl.current
        # if the volume has increased since last time, but is in the same minute
        # also, if the change is bigger than qty, then add the index for fill.
        if (current['volume'] > vol_start) & ((current['volume'] - vol_start) > qty):
            fill_indexes.append(index)

        elif current['volume'] < vol_start:

            if current['volume'] > qty:
                fill_indexes.append(index)
            else:
                open_orders.at[index, 'vol_start'] = 0
    return fill_indexes, open_orders


def check_cancel(open_orders):
    '''
    # Check Cancellation Requirements
    Each buy or sell order has a `cancel_spec` column, specifying when to cancel if necessary. 

    Returns updated `open_orders` frame without cancelled orders. 

    ## Process: 

    - #### Skip Clause:
    If there are no open orders, then return without doing anything. 

    ### 1) Reset the index so we can keep track of index values.

    ### 2) Loop over each open order and check to see if the Cancel Conditions are met. 
    - defines cancellation specifications. 
    - checks time cancellation spec
    - checks price cancellation spec

    ### 3) If the row meets either condition, add it to a list of indexes. 

    ### 4) Return `open_orders` without the indexes that meet cancellation requirements.  
    '''
    if len(open_orders) == 0:
        return open_orders

    # Update the wait time. This is CRUCIAL.
    open_orders['wait_duration'] = open_orders.wait_duration + 1

    # 1) Reset the index so we can keep track of index values.

    open_orders = open_orders.reset_index(drop=True)
    df = open_orders

    drop_indexes = []
    for cancel_spec, exe_price, duration, index in zip(df.cancel_spec,
                                                       df.exe_price,
                                                       df.wait_duration,
                                                       df.index):
        # Example cancel_spec : r'p:%1,t:5'
        xptype = cancel_spec.split(',')[0].split(':')[1][0]
        xp = float(cancel_spec.split(',')[0].split(':')[1].split(xptype)[1])
        xtime = int(cancel_spec.split(',')[1].split(':')[1])

        # Time Out
        if duration >= xtime:
            gl.log_funcs.log('order cancelled (time out)')
            drop_indexes.append(index)

        # Price Drop
        elif (((100 - xp)*.01)*exe_price) > gl.current['close']:
            gl.log_funcs.log('order cancelled (price drop)')
            drop_indexes.append(index)

        # Price Spike
        elif (((100 + xp)*.01)*exe_price) < gl.current['close']:
            gl.log_funcs.log('order cancelled (price spike)')
            drop_indexes.append(index)

    return open_orders.drop(index=drop_indexes)
