from local_functions.main import global_vars as gl
from functools import wraps


def log(msg=''):
    # region Docstring
    '''
    # Log
    Custom logger to csv. 
    Automatically makes rows for minute, second, file, function, and line of the algorithm. 

    Returns Nothing. 

    ## Parameters:{
    ####    `msg`: message to be logged. 
    ## }

    ## Notes:
    - Log is saved as a global variable DF until the end of test, 
    then is converted to a csv with the other frames. 

    ## TO DO:
    - Item
    '''
    # endregion Docstring
    current = gl.current
    file_name = gl.sys._getframe(1).f_code.co_filename
    file_name = gl.os.path.basename(file_name)

    new_row = {
        'minute': [current['minute']],
        'second': [current['second']],
        'message': [msg],
        'file': [file_name],
        'function': [gl.sys._getframe(1).f_code.co_name],
        'line': [gl.sys._getframe(1).f_lineno],
    }

    df = gl.pd.DataFrame(new_row)
    df = gl.log.append(df, sort=False)

    if len(df) == 1:
        df.columns = ['minute', 'second',
                      'message', 'file', 'function', 'line']

    gl.log = df


def log_sent_orders(orders):
    # region Docstring
    '''
    # Log Sent Orders
    takes orders and order types and logs a message 

    of the amount of shares and cash being bought/sold

    ## Parameters:{

    orders: df of new prospective orders,

    buy_or_sell: order type - string 'buy' or 'sell'

    }
    '''
    # endregion Docstring
    if len(orders) != 0:
        orders = orders.reset_index()
        for index in orders.index:
            order = dict(orders.iloc[index])
            buy_or_sell = order['buy_or_sell']
            if buy_or_sell == 'BUY':
                cash = order['cash_or_qty']
                qty = '~{}'.format(int(cash / gl.current_price()))
            else:
                qty = order['cash_or_qty']
                cash = '~{}'.format(round(qty * gl.current_price(), 2))
            message = f'Signal to {buy_or_sell} {qty} shares (cash: {cash})'
            gl.log_funcs.log(message)


def log_filled_and_open(new_fills):
    nfids, oids = [], []
    nf, oo = False, False
    if len(new_fills) != 0:
        nfids = new_fills.order_id.tolist()
        nf = True
    if len(gl.open_orders) != 0:
        oids = gl.open_orders.order_id.tolist()
        oo = True

    if nf:
        gl.log_funcs.log(f'new_fill_ids: {nfids}, still open: {oids}')


# region UNUSED


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


# endregion UNUSED
