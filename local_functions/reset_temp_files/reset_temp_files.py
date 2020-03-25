from local_functions.main import global_vars as gl


def temp_files():

    # PL and Exposure
    gl.sys.dont_write_bytecode = True

    pl_ex = {
        'unreal': 0,
        'real': 0,
        'last_ex': 0,
        'max_ex': 0
    }

    pl_frame = gl.pd.DataFrame(pl_ex, index=['value']).T
    pl_frame = pl_frame.reset_index().rename(columns={'index': 'type'})
    pl_frame.to_csv(gl.filepath['pl_ex'])

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

    c_frame = gl.pd.DataFrame(current, index=['value']).T
    c_frame = c_frame.reset_index().rename(columns={'index': 'type'})
    c_frame.to_csv(gl.filepath['current'])

    # volas
    volas = {
        'current': 'nan',
        'three_min': 'nan',
        'five_min': 'nan',
        'ten_min': 'nan',
        'mean': 'nan'
    }

    volas_frame = gl.pd.DataFrame(volas, index=['value']).T
    volas_frame = volas_frame.reset_index().rename(columns={'index': 'type'})
    volas_frame.to_csv(gl.filepath['volas'])

    # mom_frame
    mom_frame = gl.pd.DataFrame()
    mom_frame.to_csv(gl.filepath['mom_frame'])

    # # yearly_ana
    # # managed in the yearly_eval file
    # yearly_eval = gl.pd.DataFrame()
    # yearly_eval.to_csv('temp_assets/analysis/yearly_eval.csv')

    # current_frame
    current_frame = gl.pd.DataFrame()
    current_frame.to_csv(gl.filepath['current_frame'])

    # filled_orders
    # managed in the positions_ana file
    filled_orders = gl.pd.DataFrame()
    filled_orders.to_csv(gl.filepath['filled_orders'])

    # open_orders
    # managed in the positions_ana file
    open_orders = gl.pd.DataFrame()
    open_orders.to_csv(gl.filepath['open_orders'])

    # current_positions
    # managed in the positions_ana file
    current_positions = gl.pd.DataFrame()
    current_positions.to_csv(gl.filepath['current_positions'])

    # Logging Notes
    with open('temp_assets/algo.log', 'w'):
        pass

    gl.logging.basicConfig(
        filename='temp_assets/algo.log', level=gl.logging.INFO)
    gl.logging.info('Started\n')
    # mylib.do_something()

    print('files reset')
