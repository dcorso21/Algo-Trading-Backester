from local_functions.main import global_vars as gl


def build_orders():
    '''
    # Build Orders

    Analyses positions and decides whether or not to buy or sell. 

    Returns DataFrame of orders.

    ## Process:
    ### 1) Updates current positions details relating to the current price

    #### Skip Clause:
    Check Bad Trade Conditions, if met, return blank df. 

    ### 2) Get Sell Orders

    ### 3) Get Buy Orders

    '''
    # 1) Updates current positions details relative to the current price
    update_return_and_pl()

    # Skip Clause:
    if bad_trade_conds():
        return gl.pd.DataFrame()

    # 2) Get Sell Orders
    sell_orders = gl.p_sell_eval.sell_eval()
    log_sent_orders(sell_orders, 'sell')
    # if it is a good time to stop, end the function with only sell orders.
    if (gl.buy_lock == True):
        return sell_orders

    # 3) Get Buy Orders
    buy_orders = gl.p_buy_eval.buy_eval()
    log_sent_orders(buy_orders, 'buy')

    # combine orders
    all_orders = sell_orders.append(buy_orders, sort=False)

    return all_orders


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


def update_return_and_pl():
    '''
    # Update Current Positions Return and PL
    Updates the current positions return and PL columns, as well as the Unreal value in gl.pl_ex

    Returns Nothing. 

    ## Process:

    #### Skip Clause
    If there aren't any current_positions, skip function. 

    ### 1) Calculate percentage return for each position in the 'p_return' column
    ### 2) Calculate the unrealized profit/loss in the 'un_pl' column
    ### 3) Update the current_position global variable to include these newly updated rows
    ### 4) Update the current Unrealized PL from the sum of the 'un_pl' column. 

    '''
    current_positions = gl.current_positions

    if len(current_positions) != 0:

        ret = []
        for x in current_positions.exe_price:
            ret.append(round(((gl.current['close'] - x)/x)*100, 1))

        current_positions['p_return'] = ret
        current_positions['un_pl'] = current_positions.cash * \
            current_positions.p_return*.01

        gl.current_positions = current_positions
        gl.common_ana.update_pl('skip', current_positions['un_pl'].sum())


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

        message = f'PA: signal to {buy_or_sell} {order_qty} shares (cash: {order_cash})'
        gl.logging.info(message)
