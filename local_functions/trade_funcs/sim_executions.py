from local_functions.main import global_vars as gl


def sim_execute_orders(new_orders, cancel_ids):
    # region Docstring
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
    # endregion Docstring

    cancelled_orders = sim_cancel_orders(cancel_ids)

    open_orders = gl.open_orders

    # 2) Add New Orders to Open
    if len(new_orders) != 0:
        current = gl.current
        new_orders['price_check'] = [-1] * len(new_orders)
        new_orders['wait_duration'] = [-1] * len(new_orders)
        vminute, vstart = current['minute'], current['volume']
        new_orders['vol_start'] = [f'{vminute},{vstart}'] * len(new_orders)

        open_orders = open_orders.append(new_orders, sort=False)
        open_orders = open_orders.reset_index(drop=True)

    if len(open_orders) == 0:
        gl.open_orders = open_orders
        return gl.pd.DataFrame(), cancelled_orders

    # Update the wait time. This is CRUCIAL.
    open_orders['wait_duration'] = open_orders.wait_duration + 1

    # 3) Check Price Requirement
    open_orders, potential_fills = sim_progress_open_orders(open_orders)

    # if there are no potential fills,
    # update the open_orders and return - dont bother checking volume...
    if len(potential_fills) == 0:
        filled_orders = gl.pd.DataFrame()
        gl.open_orders = open_orders
        return filled_orders, cancelled_orders

    # 4) Check Volume Requirement
    filled_orders, open_orders = vol_check(potential_fills, open_orders)

    # 5) format filled.
    current = gl.current
    gl.open_orders = open_orders

    if len(filled_orders) != 0:
        drop_columns = ['price_check', 'vol_start',
                        'wait_duration', 'cancel_spec']
        filled_orders = filled_orders.drop(drop_columns, axis=1).dropna()
        exe_time = gl.common.get_timestamp(
            current['minute'], current['second'])
        filled_orders['exe_time'] = [exe_time] * len(filled_orders)

    return filled_orders, cancelled_orders


def sim_progress_open_orders(open_orders):
    '''
    # Sim Progress Open Orders
    Iterates through each open order in the `open_orders` DataFrame.  
    '''
    lag = gl.configure.sim_settings['execution_lag']
    price_offset = gl.configure.sim_settings['execution_price_offset']

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

        # Reset to 0
        else:
            open_orders.at[index, 'price_check'] = 0

    # RESET STARTING VOLUME
    vminute, vstart = current['minute'], current['volume']

    open_orders.loc[(open_orders['price_check'].values == 0),
                    'vol_start'] = f'{vminute},{vstart}'

    # there is potential for these orders to be filled.
    potential_fills = open_orders[open_orders['price_check'] >= lag].index

    return open_orders, potential_fills


def vol_check(potential_fills, open_orders):

    min_chunk_cash = gl.configure.sim_settings['vol_min_chunk_cash']
    offset_multiplier = gl.configure.sim_settings['vol_offset_multiplier']

    filled_orders = gl.pd.DataFrame()

    # for each potential fill.
    for index in potential_fills:

        exe_price = open_orders.at[index, 'exe_price']
        vol_start = open_orders.at[index, 'vol_start']
        qty = open_orders.at[index, 'qty']

        current = gl.current
        # if the volume has increased since last time, but is in the same minute
        # also, if the change is bigger than qty, then add the index for fill.

        vminute, vstart = vol_start.split(',')

        # Define the vol_passed variable
        # (Amount traded since order has been open)
        vol_passed = current['volume'] - float(vstart)
        if vminute != current['minute']:
            # Add volume from previous minute if order has rolled over.
            vol_passed = vol_passed + gl.current_frame.volume.to_list()[-2]

        # Entire order gets filled.
        if vol_passed >= qty*offset_multiplier:
            fill = open_orders[open_orders.index == index]
            with gl.pd.option_context('mode.chained_assignment', None):
                fill['order_id'] = fill.order_id.apply(lambda i: str(i)+'x')

            filled_orders = filled_orders.append(fill, sort=False)
            open_orders = open_orders.drop(index)

        # Partial order fill.
        elif int(vol_passed / offset_multiplier) >= (min_chunk_cash / exe_price):
            fill = open_orders[open_orders.index == index]
            fill_qty = int(vol_passed / offset_multiplier)
            with gl.pd.option_context('mode.chained_assignment', None):
                fill['qty'] = fill_qty
            filled_orders = filled_orders.append(fill, sort=False)

            # Redefine remainder of order
            vminute = current['minute']
            vstart = current['volume']
            open_orders.at[index, 'vol_start'] = f'{vminute},{vstart}'
            remainder = qty - fill_qty
            open_orders.at[index, 'qty'] = remainder

    return filled_orders, open_orders


def sim_cancel_orders(new_cancel_ids, wait_time=1):

    # This is a dictionary with the key being the order id
    # and the value being the wait time.
    open_cancels = gl.open_cancels

    if len(new_cancel_ids) == 0 and len(open_cancels) == 0:
        return []
        # return gl.pd.DataFrame()

    open_orders = gl.open_orders

    # If there are no open orders, log any orders that were awaiting cancellation.
    if len(open_orders) == 0:
        if len(open_cancels.keys()) != 0:
            gl.log_funcs.log(
                msg=f'orders filled before cancellation: {list(open_cancels.keys())}')
            gl.open_cancels = {}
            return []

    cancelled_ids = []
    expired = []
    # update wait times and make list of cancels that reached wait_time.
    for order in open_cancels.keys():
        if order in open_orders.order_id.to_list():
            open_cancels[order] = open_cancels[order] + 1
            if open_cancels[order] == wait_time:
                cancelled_ids.append(order)

        else:
            open_ids = open_orders.order_id.to_list()
            gl.log_funcs.log(
                msg=f'id filled before cancellation: {order}, open ids: {open_ids}')
            expired.append(order)

    # Cancel Expired ids
    for x in expired:
        del open_cancels[x]

    # add new ids to open_cancels dictionary
    for order_id in new_cancel_ids:
        open_cancels[order_id] = 0

    cancelled_orders = []
    if len(cancelled_ids) != 0:
        cancelled_orders = open_orders[open_orders.order_id.isin(
            cancelled_ids)]
        cancelled_orders['status'] = [
            'successfully cancelled'] * len(cancelled_orders)
        open_orders = open_orders[~ open_orders.order_id.isin(cancelled_ids)]

        gl.log_funcs.log(f'successfully cancelled: {cancelled_ids}')

    gl.open_cancels = open_cancels
    gl.open_orders = open_orders

    return cancelled_orders
