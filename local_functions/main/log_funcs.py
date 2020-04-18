from local_functions.main import global_vars as gl
from functools import wraps

main_list = ['algo.py', 'global_vars.py']
refresh_list = ['gather_data.py']
analyse_list = ['analyse.py', 'common.py']
daily_list = ['daily_ana.py', 'd_price_eval.py',
              'd_update_docs.py', 'momentum.py',
              'supports_resistances.py', 'volas.py']
yearly_list = []
position_list = ['position_ana.py', 'order_tools.py',
                 'p_buy_eval.py', 'p_sell_eval.py',
                 'buy_conditions.py', 'sell_conditions.py']
trade_list = ['sim_executions.py', 'trade_funcs.py']

file_core_dict = {
    'main': main_list,
    'refresh_info': refresh_list,
    'analysis': analyse_list,
    'daily analysis': daily_list,
    'yearly analysis': yearly_list,
    'position analysis': position_list,
    'trade_funcs': trade_list,
}


def find_core(file_name):
    found = False
    for file_list, key in zip(file_core_dict.values(),
                              file_core_dict.keys()):
        if file_name in file_list:
            found = True
            core = key
    if not found:
        core = 'file not in log_funcs dict'
    return core


def log(msg=''):
    '''
    # Log
    Custom logger to csv. 
    Automatically makes rows for minute, second, file, function, line and `core` of the algorithm. 
    '''
    current = gl.current
    file_name = gl.sys._getframe(1).f_code.co_filename
    file_name = file_name.split('\\')[-1]
    core = find_core(file_name)

    new_row = {
        'minute': [current['minute']],
        'second': [current['second']],
        'message': [msg],
        'core': [core],
        'file': [file_name],
        'function': [gl.sys._getframe(1).f_code.co_name],
        'line': [gl.sys._getframe(1).f_lineno],
    }

    df = gl.pd.DataFrame(new_row)
    df = gl.log.append(df, sort=False)

    if len(df) == 1:
        df.columns = ['minute', 'second', 'message',
                      'core', 'file', 'function', 'line']

    gl.log = df


def append_efficiency_row(function, run_time):
    '''
    # Append Efficiency Row
    to be used with the `log_efficiency` decorator function. 
    '''
    current = gl.current
    new_row = {
        'minute': [current['minute']],
        'second': [current['second']],
        'function': [function],
        'run_time': [run_time],
    }

    df = gl.pd.DataFrame(new_row)
    df = df.set_index('minute')
    df.to_csv('temp_assets/efficiency_log.csv', mode='a', header=False)


# decorator
def log_efficiency(orig_func):
    @ wraps(orig_func)
    def wrapper(*args, **kwargs):
        import time
        then = time.time()
        result = orig_func(*args, **kwargs)

        function = orig_func.__name__
        # function = gl.sys._getframe(2).f_code.co_name
        run_time = time.time() - then
        append_efficiency_row(function, run_time)
        return result
    return wrapper


# decorator
def run_timeit(orig_func):
    @ wraps(orig_func)
    def wrapper(*args, **kwargs):
        import inspect
        import timeit
        lines = inspect.getsource(orig_func)
        decorator = len(lines.split('\n')[0]) + 1
        lines = lines[decorator:]
        return timeit.timeit(lines, number=1000000)
    return wrapper


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

        message = f'Signal to {buy_or_sell} {order_qty} shares (cash: {order_cash})'
        gl.log_funcs.log(message)
