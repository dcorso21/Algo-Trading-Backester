from local_functions.analysis.ana_indicators.p_eval import common_eval_funcs as common
from local_functions.analysis.ana_indicators.p_eval import order_tools as o_tools
from local_functions.analysis.ana_indicators.p_eval import order_creators as create

##################################################
##################################################
# START POSITION...


def starting_position(current, current_frame):
    trade = True
    cash = o_tools.get_available_capital() * .01
    buys = o_tools.create_buys(
        cash, current, current_frame, current['close'])
    return trade, buys

##################################################
##################################################
# SIZE IN...


def drop_below_average(current, current_frame, avg, max_vola):

    drop_below_average = common.get_inverse_perc(max_vola)

    if current['close'] < (avg * drop_below_average):
        trade = True
        cash = 5

        exe_price = create.suggest_price()

        buys = o_tools.create_buys(
            cash, current, current_frame, 'ASK', current['close'])

    return trade, buys
