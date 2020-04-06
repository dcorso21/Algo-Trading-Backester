from local_functions.main import global_vars as gl


main_list = ['algo.py', 'global_vars.py']
refresh_list = ['gather_data.py']
analyse_list = ['analyse.py', 'common_ana.py']
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
    minute = gl.current['minute']
    sec = gl.current['second']
    func_name = gl.sys._getframe(1).f_code.co_name
    line_number = gl.sys._getframe(1).f_lineno
    file_name = gl.sys._getframe(1).f_code.co_filename
    file_name = file_name.split('\\')[-1]

    core = find_core(file_name)

    new_row = {

        'minute': [minute],
        'second': [sec],
        'message': [msg],
        'core': [core],
        'file': [file_name],
        'function': [func_name],
        'line': [line_number],

    }

    df = gl.pd.DataFrame(new_row)
    df = df.set_index('minute')

    # return df

    # with open('temp_assets/log.csv', 'a') as f:
    #     df.to_csv(f, header=False)

    df.to_csv('temp_assets/log.csv', mode='a', header=False)
