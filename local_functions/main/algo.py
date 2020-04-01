# LOCAL FUNCTIONS ###############
from local_functions.main import global_vars as gl


def main_algo():

    gl.reset.reset_variables()
    # each minute in df
    for row in range(len(gl.sim_df)):

        # first, get second data for fake 'real-time' pricing.
        prices, volumes, ticker, minute = gl.hist.create_second_data(gl.sim_df,
                                                                     row, mode='momentum')

        gl.logging.info(f'  {minute}')
        gl.sys.stdout.write(f'\rcurrent minute : {minute}')
        gl.sys.stdout.flush()

        # each second, update current candle and assess patterns, consider trading.
        for price, volume, second in zip(prices, volumes, range(0, 60)):

            gl.gather.update_candle(price, volume, ticker, minute, second)
            orders = gl.ana.analyse()
            gl.trade_funcs.exe_orders(orders)

        # End of Minute
        gl.gather.clone_current_frame()
        # gl.candles.chart_candles()
        gl.logging.info('minute complete\n')

        if minute == '11:05:00':
            break

    gl.save_all()
    print('\ndone')
