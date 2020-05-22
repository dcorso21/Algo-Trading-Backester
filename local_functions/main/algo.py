# LOCAL FUNCTIONS #############
from local_functions.main import global_vars as gl
import time


def test_trade(config='last', mode='csv', csv_file='first', batch_dir=False):
    # region Docstring
    '''
    # Test Trade
    Main Function for testing algo. Runs through a stock based on configuration file. 

    ## Parameters:{
    ####    `config`: str, key-word, choices are: last, pick or the actual config file. 
    ####    `mode`: csv or live trading
    ####    `csv_file`: name of csv if csv trading. 
    ####    `batch_path`: directory of batch.  
    ## }
    '''
    # endregion Docstring

    start_time = time.time()
    gl.configure.master_configure(config=config,
                                  mode=mode, csv_file=csv_file, batch_dir=batch_dir)

    gl.screen.pick_stock_direct(mode)
    if gl.stock_pick == 'nan':
        return

    while True:

        gl.gather.update_direct()          # Updates Info...
        orders = gl.analyse.analyse()      # Analyse and build orders
        gl.trade_funcs.exe_orders(orders)  # Execute orders.

        if gl.loop_feedback == False:
            break

    gl.save_all()

    result = '\n{}: R: ${:.2f}, U: ${:.2}, @: {} ({})'
    duration = '{} s'.format(int(time.time() - start_time))
    last_min = gl.current['minute']
    if gl.pl_ex['real']+gl.pl_ex['unreal'] > 0:
        result = gl.color_format(result, 'green')
    elif gl.pl_ex['real']+gl.pl_ex['unreal'] < 0:
        result = gl.color_format(result, 'red')
    else:
        result = gl.color_format(result, 'yellow')

    gl.clear_output(4)

    print(result.format(gl.stock_pick.split('_')[-1],
                        float(gl.pl_ex['real']),
                        float(gl.pl_ex['unreal']),
                        last_min,
                        duration
                        ))
