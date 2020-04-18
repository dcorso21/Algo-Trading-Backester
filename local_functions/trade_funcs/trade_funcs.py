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

    # EXECUTIONS
    new_fills = execute_direct(orders)

    if len(new_fills) != 0:
        reset_buy_clock(new_fills)
        update_filled_orders(new_fills)
        update_current_positions(new_fills)


def execute_direct(orders):
    '''
    # Redirect for executing orders.  
    '''
    if gl.trade_mode == 'csv':
        return gl.sim_exe.run_trade_sim(orders)
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
        gl.buy_clock = 25


def queue_order_center(orders):

    q_orders = gl.queued_orders

    ready = gl.pd.DataFrame()
    if len(orders) != 0:
        ready = orders[orders['queue_spec'] == None]

    if len(q_orders) != 0:
        q_orders = q_orders.reset_index(drop=True)

        drop_indexes = []
        for row in q_orders.index:
            qs = q_orders.at[row, 'queue_spec']

            if qs[0:4] == 'time':
                qs = int(qs.split(':')[1]) - 1
                q_orders.at[row, 'queue_spec'] = qs
                if qs == 0:
                    ready = ready.append(q_orders.iloc[row], sort=False)
                    drop_indexes.append(row)

            if qs[0:4] == 'fill':
                order_id = int(qs.split(':')[1])
                if len(gl.filled_orders) != 0:
                    if qs in gl.filled_orders.order_id.tolist():
                        ready = ready.append(q_orders.iloc[row], sort=False)
                        drop_indexes.append(row)

        q_orders.drop(drop_indexes)

    for_q = gl.pd.DataFrame()
    if len(orders) != 0:
        for_q = orders[orders['queue_spec'] != None]
        if len(for_q) != 0:
            q_orders = q_orders.append(for_q, sort=False)

    gl.queued_orders = q_orders

    return gl.order_tools.format_orders(ready)
