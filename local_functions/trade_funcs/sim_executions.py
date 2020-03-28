from local_functions.main import global_vars as gl

'''
Purpose of this module:

1. Simulate Market conditions like slippage and execution lag.

2. Place orders in queue to be executed
'''


def run_trade_sim(new_orders):

    price_offset = 0.0
    # min number of seconds to fill (assuming the price and volume fit too... )
    lag = 2

    open_orders = gl.open_orders

    open_orders = cancel_at_wait_duration(open_orders, cancel_second=5)

    if len(new_orders) != 0:
        new_orders['price_check'] = gl.pd.Series(0)
        new_orders['vol_start'] = gl.pd.Series(0)
        new_orders['wait_duration'] = gl.pd.Series(0)
        open_orders = open_orders.append(new_orders, sort=False)
        # Re - Index
        open_orders = open_orders.reset_index()
        columns = ['ticker', 'send_time', 'buy_or_sell', 'cash', 'qty',
                   'exe_price', 'price_check', 'vol_start', 'wait_duration']
        open_orders = open_orders[columns].dropna()

    if len(open_orders) == 0:
        filled_orders = gl.pd.DataFrame()
        gl.open_orders = open_orders
        return filled_orders

    # UPDATE THE OPEN ORDERS...
    open_orders = sim_progress_open_orders(open_orders, lag, price_offset)

    # there is potential for these orders to be filled.
    potential_fills = open_orders[open_orders['price_check'] >= lag]

    # if there are no potential fills,
    # update the open_orders and return - dont bother checking volume...
    if len(potential_fills) == 0:
        filled_orders = gl.pd.DataFrame()
        gl.open_orders = open_orders
        return filled_orders

    fill_indexes, open_orders = vol_check(potential_fills, open_orders)

    if len(fill_indexes) == 0:
        filled_orders = gl.pd.DataFrame()
        gl.open_orders = open_orders
        return filled_orders

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

    return filled_orders


def sim_progress_open_orders(open_orders, lag, price_offset):

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

    return open_orders


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


def cancel_at_wait_duration(open_orders, cancel_second=5):

    if len(open_orders) != 0:
        open_orders['wait_duration'] = open_orders['wait_duration']+1
        # CANCEL OVERDUE ORDERS...
        old_len = len(open_orders)
        open_orders = open_orders[open_orders.wait_duration <=
                                  cancel_second]
        new_len = len(open_orders)
        if old_len != new_len:
            gl.logging.info('TF/SE 21.136 order cancelled')

        # gl.logging.info(len(open_orders))

    return open_orders
