# LOCAL FUNCTIONS #############
from local_functions.main import global_vars as gl
import time


def test_trade():

    start_time = time.time()
    gl.reset.reset_variables()

    # gl.screen.pick_stock()
    # if gl.stock_pick == 'nan':
    #     return

    while True:

        # Updates Current and Current_frame variables...
        gl.gather.csv_refresh()
        orders = gl.ana.analyse()
        gl.trade_funcs.exe_orders(orders)

        if gl.loop_feedback == False:
            break

    gl.save_all()
    print('\ndone')

    duration = time.time() - start_time
    print(f'algo finished in {duration} second(s)')
