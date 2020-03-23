from local_functions.analysis.ana_indicators.p_eval import common_eval_funcs as common


def drop_below_average(current, avg, max_vola):

    drop_below_average = common.get_inverse_perc(max_vola)

    if current['close'] < (avg * drop_below_average):
        trade = True

    return trade
