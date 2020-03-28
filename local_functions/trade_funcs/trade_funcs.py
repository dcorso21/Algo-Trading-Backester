from local_functions.main import global_vars as gl

'''
Purpose of this sheet:

1. Update Fills

2. Update Real PL

'''


def exe_orders(orders):

    # SIMULATE EXECUTIONS
    new_fills = gl.sim_exe.run_trade_sim(orders)

    if len(new_fills) != 0:
        update_filled_orders(new_fills)
        update_current_positions(new_fills)


def update_filled_orders(new_fills):
    filled_orders = gl.filled_orders
    filled_orders = filled_orders.append(new_fills, sort=False)
    gl.filled_orders = filled_orders


def update_current_positions(new_fills):
    '''
    Takes a DF of filled orders and filters out the orders no longer active (current) by looking at the sells. 

    '''

    df = new_fills
    df = gl.current_positions.append(df, sort=False)
    df = df.reset_index()
    columns = ['ticker', 'send_time', 'buy_or_sell',
               'cash', 'qty', 'exe_price', 'exe_time']
    df = df[columns]

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
        gl.common_ana.update_pl(realized, 'skip')
    gl.common_ana.update_ex()
