# LOCAL FUNCTIONS #############
from local_functions.main import global_vars as gl
import time


def test_trade(config='last', mode='csv', csv_file='first', batch_path=False):
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
    gl.controls.master_configure(config=config,
                                 mode=mode, csv_file=csv_file, batch_path=batch_path)

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
    print('\ndone')
    result = '\nP\L: real: ${:.2f}, unreal: ${:.2}'
    print(result.format(float(gl.pl_ex['real']), float(gl.pl_ex['unreal'])))
    

    duration = int(time.time() - start_time)
    print(f'\nalgo finished in {duration} second(s)\n')
