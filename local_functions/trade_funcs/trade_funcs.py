from local_functions.main import global_vars as gl


def exe_orders(orders):
    '''
    # Core Function: Executing Orders
    ## 1) Takes suggested orders and puts them through a simluation 
       to see whether or not they would be filled.

    ## 2) If there are new fills, update the 'filled_orders' and 'current_positions' vars.  
    '''
    if gl.loop_feedback == False:
        return

    # Queue Orders
    orders = queue_order_center(orders)

    cancel_ids = check_cancel()

    # EXECUTIONS
    new_fills, cancelled_orders = execute_direct(orders, cancel_ids)

    if len(new_fills) != 0:
        reset_buy_clock(new_fills)
        update_filled_orders(new_fills)
        update_current_positions(new_fills)

    if len(cancelled_orders) != 0:
        gl.cancelled_orders = gl.cancelled_orders.append(
            cancelled_orders, sort=False)


def execute_direct(orders, cancel_ids):
    '''
    # Redirect for executing orders.  
    '''
    if gl.trade_mode == 'csv':
        return gl.sim_exe.sim_execute_orders(orders, cancel_ids)
    else:
        return live_executions(orders)


def live_executions(new_orders):
    '''    
    Live Equivalent to sim_executions
    '''
    def live_get_open_orders():
        pass

    def live_cancellation():
        pass

    def live_send_orders(new_orders):
        pass

    live_send_orders(new_orders)
    live_get_open_orders()
    live_cancellation()


def update_filled_orders(new_fills):
    '''
    # Update Filled Orders
    Simple function to append new fills to existing 'filled_orders' global variable. 

    '''
    filled_orders = gl.filled_orders
    filled_orders = filled_orders.append(new_fills, sort=False)
    gl.filled_orders = filled_orders


def update_current_positions(new_fills):
    '''
    # Update Current Positions
    Takes current positions and adds new fills. Function then calculates which positions are still active. 
    e.g.: if you have two positions open, then sell one half, this will sort out the remaining position. 
    '''

    df = new_fills
    df = gl.current_positions.append(df, sort=False)
    df = df.reset_index(drop=True)

    buys = df[df['buy_or_sell'] == 'BUY']
    sells = df[df['buy_or_sell'] == 'SELL']
    realized = 0

    if len(sells) != 0:
        for qty, price in zip(sells.qty, sells.exe_price):
            remainder = qty
            while remainder > 0:

                first_row = buys.index.tolist()[0]
                # if there are more shares sold than the one row
                # calculate the remainder and drop the first row...
                if (buys.at[first_row, 'qty'] - remainder) <= 0:
                    realized += (price - buys.at[first_row,
                                                 'exe_price']) * buys.at[first_row, 'qty']
                    diff = int(remainder - buys.at[first_row, 'qty'])
                    buys = buys.drop(first_row)
                    # I use this workaround because the loop is based on this value
                    # If the value happens to be zero, the loop will break.
                    remainder = diff
                # if the shares sold are not greater than the row's qty
                # calculate the new row's value, stop the loop...
                elif (buys.at[first_row, 'qty'] - remainder) > 0:
                    realized += (price -
                                 buys.at[first_row, 'exe_price']) * remainder
                    buys.at[first_row, 'qty'] = buys.at[first_row,
                                                        'qty'] - remainder
                    remainder = 0

    current_positions = buys
    gl.current_positions = current_positions
    if realized != 0:
        if len(current_positions) == 0:
            unrealized = 0
        else:
            unrealized = 'skip'
        gl.common.update_pl(realized, unrealized)
    gl.common.update_ex()


def reset_buy_clock(new_fills):
    if len(new_fills[new_fills['buy_or_sell'] == 'BUY']) != 0:
        gl.buy_clock = 10


def queue_order_center(orders):

    q_orders = gl.queued_orders

    if len(q_orders) != 0:
        q_orders = q_orders.reset_index(drop=True)

        drop_indexes = []
        for row in q_orders.index:
            qs = q_orders.at[row, 'queue_spec']

            # Redundant check.
            # if qs == None:
            #     drop_indexes.append(row)
            #     continue

            if qs[0:4] == 'time':
                qs = int(qs.split(':')[1]) - 1
                q_orders.at[row, 'queue_spec'] = qs
                if qs == 0:
                    ready = ready.append(q_orders.iloc[row], sort=False)
                    drop_indexes.append(row)

            elif qs[0:4] == 'fill':
                # 'x' here is a character passed on the last partition of any order.
                # Because of partial fills, multiple filled orders may have the same name.
                order_id = str(qs.split(':')[1])+'x'
                if len(gl.filled_orders) != 0:
                    if order_id in gl.filled_orders.order_id.tolist():
                        ready = ready.append(q_orders.iloc[row], sort=False)
                        drop_indexes.append(row)

        q_orders.drop(drop_indexes)

    for_q = gl.pd.DataFrame()
    if len(orders) != 0:
        for_q = orders[orders['queue_spec'] != 'nan']
        if len(for_q) != 0:
            q_orders = q_orders.append(for_q, sort=False)

    gl.queued_orders = q_orders

    ready = gl.pd.DataFrame()
    if len(orders) != 0:
        ready = orders[orders['queue_spec'] == 'nan']

    return gl.order_tools.format_orders(ready)


def check_cancel():
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

    open_orders = gl.open_orders

    if len(open_orders) == 0:
        return open_orders

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
            gl.log_funcs.log('cancellation sent (time out)')
            drop_indexes.append(index)

        # Price Drop
        elif (((100 - xp)*.01)*exe_price) > gl.current['close']:
            gl.log_funcs.log('cancellation sent (price drop)')
            drop_indexes.append(index)

        # Price Spike
        elif (((100 + xp)*.01)*exe_price) < gl.current['close']:
            gl.log_funcs.log('cancellation sent (price spike)')
            drop_indexes.append(index)

    if len(drop_indexes) != 0:
        gl.cancelled_orders = gl.cancelled_orders.append(
            open_orders.iloc[drop_indexes], sort=False)

    # return list of order ids for cancellation.
    return open_orders.drop(index=drop_indexes).order_id.to_list()
