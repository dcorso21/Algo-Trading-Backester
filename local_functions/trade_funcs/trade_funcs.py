from local_functions.main import global_vars as gl

'''
Purpose of this sheet:

1. Update Fills

2. Update Real PL

'''


def execute_direct(orders):
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


def exe_orders(orders):
    '''
    # Core Function: Executing Orders
    ## 1) Takes suggested orders and puts them through a simluation 
       to see whether or not they would be filled.

    ## 2) If there are new fills, update the 'filled_orders' and 'current_positions' vars.  
    '''
    if gl.loop_feedback == False:
        return

    # EXECUTIONS
    new_fills = execute_direct(orders)

    if len(new_fills) != 0:
        reset_buy_clock(new_fills)
        update_filled_orders(new_fills)
        update_current_positions(new_fills)


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
        gl.common_ana.update_pl(realized, unrealized)
    gl.common_ana.update_ex()


def reset_buy_clock(new_fills):
    if len(new_fills[new_fills['buy_or_sell'] == 'BUY']) != 0:
        gl.buy_clock = 10
