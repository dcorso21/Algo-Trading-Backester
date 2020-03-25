from local_functions.main import global_vars as gl


def build_orders():

    update_return_and_pl()

    # get sell orders
    sell_orders = gl.p_sell_eval.sell_eval()
    log_sent_orders(sell_orders, 'sell')

    # if it is a good time to stop, end the function with only sell orders.
    if (gl.loop_feedback == False):
        return sell_orders

    # get buy orders
    buy_orders = gl.p_buy_eval.buy_eval()
    log_sent_orders(buy_orders, 'buy')

    # combine orders
    all_orders = sell_orders.append(buy_orders, sort=False)

    return all_orders


def update_return_and_pl():

    current_positions = gl.current_positions()

    if len(current_positions) != 0:

        ret = []
        for x in current_positions.exe_price:
            ret.append(round(((gl.current()['close'] - x)/x)*100, 1))

        current_positions['p_return'] = ret
        current_positions['un_pl'] = current_positions.cash * \
            current_positions.p_return*.01
        current_positions.to_csv(gl.filepath['current_positions'])


def log_sent_orders(orders, buy_or_sell):
    if len(orders) != 0:
        message = 'PA: signal to {} {} shares'.format(
            buy_or_sell, orders.qty.sum())
        gl.logging.info(message)
