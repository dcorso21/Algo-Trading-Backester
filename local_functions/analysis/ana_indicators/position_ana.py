from local_functions.analysis.ana_indicators.p_eval import p_sell_eval as p_sell
from local_functions.analysis.ana_indicators.p_eval import p_buy_eval as p_buy
from local_functions.analysis.ana_indicators.p_eval import common_eval_funcs as common
from local_functions.main import global_vars as gl

import pandas as pd
import json
import logging


def build_orders():

    update_return_and_pl()

    # return a df of sell orders, or a blank df as well as a decision to keep trading past this minute.
    sell_orders = p_sell.sell_eval()

    log_sent_orders(sell_orders, 'sell')

    # conditions to consider buying:

    # 1. if chart looks good.
    cond1 = (gl.chart_response == True)
    # 2. if already in ...
    cond2 = (len(gl.current_positions) != 0)

    if cond1 or cond2:
        buy_orders = p_buy.buy_eval()
        log_sent_orders(buy_orders, 'buy')
        all_orders = sell_orders.append(buy_orders, sort=False)
    else:
        all_orders = sell_orders

    # return all orders, even if it just an empty frame...
    return all_orders


def update_return_and_pl():

    current_positions = gl.current_positions

    ret = []
    for x in current_positions.exe_price:
        ret.append(round(((gl.current['close'] - x)/x)*100, 1))

    current_positions['p_return'] = ret
    current_positions['un_pl'] = current_positions.cash * \
        current_positions.p_return*.01
    current_positions.to_csv(r'temp_assets\all_orders\current_positions.csv')


def log_sent_orders(orders, buy_or_sell):

    if len(orders) != 0:
        message = 'PA: signal to {} {} shares'.format(
            buy_or_sell, orders.qty.sum())
        logging.info(message)
