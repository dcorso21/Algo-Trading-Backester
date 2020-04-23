from local_functions.main import global_vars as gl


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

    # 2) Add New Orders to Open
    if len(new_orders) != 0:
        new_orders['price_check'] = [-1] * len(new_orders)
        new_orders['vol_start'] = [-1] * len(new_orders)
        new_orders['wait_duration'] = [-1] * len(new_orders)
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
    filled_orders, open_orders = vol_check(potential_fills, open_orders)

    # 5) Return Filled Orders and Update Remaining Current_frame var.
    current = gl.current
    gl.open_orders = open_orders

    if len(filled_orders) != 0:
        drop_columns = ['price_check', 'vol_start',
                        'wait_duration', 'cancel_spec']
        filled_orders = filled_orders.drop(drop_columns, axis=1).dropna()
        exe_time = gl.common.get_timestamp(
            current['minute'], current['second'])
        filled_orders['exe_time'] = [exe_time] * len(filled_orders)

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

        if price_check == 0:
            vminute, vstart = current['minute'], current['volume']
            open_orders.at[index, 'vol_start'] = f'{vminute},{vstart}'

    # there is potential for these orders to be filled.
    potential_fills = open_orders[open_orders['price_check'] >= lag]

    return open_orders, potential_fills


def vol_check(potential_fills, open_orders, min_chunk_cash=500, offset_multiplier=1.2):
    filled_orders = gl.pd.DataFrame()
    for index, exe_price, vol_start, qty in zip(potential_fills.index,
                                                potential_fills.exe_price,
                                                potential_fills.vol_start,
                                                potential_fills.qty):

        current = gl.current
        # if the volume has increased since last time, but is in the same minute
        # also, if the change is bigger than qty, then add the index for fill.

        vminute, vstart = vol_start.split(',')

        # Define the vol_passed variable
        # (Amount traded since order has been open)
        vol_passed = current['volume'] - vstart
        if vminute != current['minute']:
            # Add volume from previous minute if order has rolled over.
            vol_passed = vol_passed + gl.current_frame.volume.to_list()[-2]

        # Entire order gets filled.
        if vol_passed >= qty*offset_multiplier:
            filled_orders = filled_orders.append(
                open_orders.iloc[index, :], sort=False)
            open_orders.drop(index)

        # Partial order fill.
        elif int(vol_passed / offset_multiplier) >= (min_chunk_cash / exe_price):
            fill = open_orders.iloc[index, :]
            fill_qty = int(vol_passed / offset_multiplier)
            fill['qty'] = fill_qty
            fill['order_id'] = open_orders.at[index, 'order_id'] + 'x'
            filled_orders = filled_orders.append(fill, sort=False)

            # Redefine remainder of order
            vstart = current['minute']
            vminute = current['volume']
            open_orders.at[index, 'vol_start'] = f'{vminute},{vstart}'
            remainder = qty - fill_qty
            open_orders.at[index, 'qty'] = remainder

    return filled_orders, open_orders
