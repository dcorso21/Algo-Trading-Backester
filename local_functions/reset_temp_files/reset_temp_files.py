from local_functions.main import global_vars as gl


def temp_files():

    gl.current_frame = gl.pd.DataFrame()
    gl.daily_ohlc = gl.pd.DataFrame()
    gl.open_orders = gl.pd.DataFrame()
    gl.current_positions = gl.pd.DataFrame()
    gl.filled_orders = gl.pd.DataFrame()
    gl.mom_frame = gl.pd.DataFrame()
    gl.sup_res_frame = gl.pd.DataFrame()

    # PL and Exposure
    gl.sys.dont_write_bytecode = True

    pl_ex = {
        'unreal': 0,
        'real': 0,
        'last_ex': 0,
        'max_ex': 0
    }

    gl.pl_ex = pl_ex

    # current
    current = {
        'open': 'nan',
        'high': 'nan',
        'low': 'nan',
        'close': 'nan',
        'volume': 'nan',
        'second': 'nan',
        'minute': 'nan',
        'ticker': 'nan'
    }

    gl.current = current

    # volas
    volas = {
        'current': 'nan',
        'three_min': 'nan',
        'five_min': 'nan',
        'ten_min': 'nan',
        'mean': 'nan'
    }

    gl.volas = volas

    # mom_frame

    # Logging Notes
    with open('temp_assets/algo.log', 'w'):
        pass

    gl.logging.basicConfig(
        filename='temp_assets/algo.log', level=gl.logging.INFO)
    gl.logging.info('Started\n')
    # mylib.do_something()

    print('files reset')
