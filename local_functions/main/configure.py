from local_functions.main import global_vars as gl


master = {}
metaconfig = {}
misc = {}
sim_settings = {}
sell_conditions = []
buy_conditions = []


def master_configure(config, mode, csv_file, batch_dir):
    # region Docstring
    '''
    # Master Configure
    function for configuring everything that needs it before the trading starts. 

    #### Returns nothing, prints confirmation

    ## Parameters:{
    ####    `config`: str, or github content file for config.json.
    ####    `mode`: 'csv' or 'live'
    ####    `csv_file`: only needed if `mode` == 'csv'
    ####    `batch_path`: filepath to current batch path. 
    ## }
    '''
    # endregion Docstring
    gl.batch_dir = batch_dir
    reset_variables(mode, csv_file)
    load_configuration(config)
    set_conditions()
    print('settings configured')


def default_configuration():
    global misc, sim_settings, master

    config_path = str(gl.directory / 'local_functions' /
                      'main' / 'config.json')
    with open(config_path, 'r') as f:
        config = f.read()

    master = gl.json.loads(config)

    misc = master['misc']
    sim_settings = master['sim_settings']
    gl.config = master.copy()


def get_sim_df(csv_file):
    m = gl.pd.read_csv(csv_file)
    m['open'] = m.open.astype(float)
    m['high'] = m.high.astype(float)
    m['low'] = m.low.astype(float)
    m['close'] = m.close.astype(float)
    m['volume'] = m.volume.astype(float).astype(int)
    # Re-Order
    m = m[['ticker', 'time', 'open', 'high', 'low', 'close', 'volume']]
    return m


def reset_variables(mode, csv_file):
    # region Docstring
    '''
    # Reset Variables
    resets all the variables from `global_variables.py` 
    so that you can rerun the algo infinitely. 

    #### Returns nothing, prints message

    ## Parameters:{
    ####    `mode`: str, sets `gl.mode`
    ####    `csv_file`: str, name of csv file to trade. 
    ## }
    '''
    # endregion Docstring
    global master
    master = {}
    gl.config = master.copy()

    if mode == 'csv':
        gl.csv_indexes = []
        gl.sim_df = get_sim_df(csv_file)
        gl.csv_name = gl.os.path.basename(csv_file).strip('.csv')

    gl.order_count = 0

    gl.pos_update = False
    gl.loop_feedback = True
    gl.buy_lock = False
    gl.sell_out = False
    gl.chart_response = False
    gl.sec_mom = 0

    gl.order_specs = gl.pd.DataFrame()
    gl.queued_orders = gl.pd.DataFrame()
    gl.open_orders = gl.pd.DataFrame()
    gl.pl_ex_frame = gl.pd.DataFrame()
    gl.volume_frame = gl.pd.DataFrame()
    gl.volas_frame = gl.pd.DataFrame()
    gl.cancelled_orders = gl.pd.DataFrame()
    gl.open_cancels = {}

    gl.current_positions = gl.pd.DataFrame()
    gl.filled_orders = gl.pd.DataFrame()
    gl.current_frame = gl.pd.DataFrame()
    gl.mom_frame = gl.pd.DataFrame()
    gl.sup_res_frame = gl.pd.DataFrame()
    gl.log = gl.pd.DataFrame()
    gl.tracker = gl.pd.DataFrame({
        'time': [],
        'variable': [],
        'value': [],
    })

    # PL and Exposure
    gl.sys.dont_write_bytecode = True

    pl_ex = {
        'unreal': 0,
        'min_unreal': 0,
        'max_unreal': 0,
        'real': 0,
        'min_real': 0,
        'max_real': 0,
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

    # last_current
    last = {
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
    gl.last = last

    # volas
    volas = {
        'differential': 'nan',
        'current': 'nan',
        'three_min': 'nan',
        'five_min': 'nan',
        'ten_min': 'nan',
        'mean': 'nan',
        'scaler': 'nan'
    }

    gl.volas = volas
    # volumes
    volumes = {
        'safe_capital_limit': 'nan',
        'differential': 'nan',
        'mean': 'nan',
        'minimum': 'nan',
        'extrap_current': 'nan',
        'three_min_mean': 'nan',
        'three_min_min': 'nan',
        'five_min_mean': 'nan',
        'five_min_min': 'nan',
        'ten_min_mean': 'nan',
        'ten_min_min': 'nan',
    }

    gl.volumes = volumes
    gl.close_sup_res = [float('nan'), float('nan')]

    print('variables reset')


def load_configuration(config):
    # region Docstring
    '''
    # Configure Settings
    takes config.json file and sets global parameters based on entries.

    #### Returns nothing

    ## Parameters:{
    ####    `config`: str or github contentfile. 
    -           'default': exits the function without changing any settings.  
    -           'pick': brings up a popup to let users choose
    -           'last': chooses the last created file on github
    ## }
    '''
    # endregion Docstring
    default_configuration()

    if config == 'default':
        return
    if config == 'last':
        config = gl.get_downloaded_configs()[0]
    elif config == 'pick':
        config = gl.pick_config_file()
        if config == 'default':
            return

    # By now, the config object should be a filepath to the custom config.
    import json
    with open(config, 'r') as f:
        config = f.read()
    raw_config = json.loads(config)
    config = json.loads(config)

    global master

    if master['metaconfig']['lock_defaults'] == True:

        for field in config['defaults'].keys():
            if field == True:
                del config[field]

        defaults = config.pop('defaults')
        metadata = config.pop('metadata')

    def replace_fields(config, master):

        for key in config.keys():
            if (type(config[key]) == dict) and (key in master.keys()):
                replace_fields(config[key], master[key])
            else:
                target_type = type(master[key])
                master[key] = target_type(config[key])

        return master

    master = replace_fields(config, master)
    master['defaults'] = defaults
    master['metadata'] = metadata
    gl.config = master.copy()


def set_conditions():
    global buy_conditions, sell_conditions

    def get_active_conditions(conditions):
        active = [(conditions[cond]['priority'], cond)
                  for cond in conditions.keys() if conditions[cond]['active']]
        return [cond[1] for cond in sorted(active)]

    sell_conditions = get_active_conditions(master['sell_conditions'])
    buy_conditions = get_active_conditions(master['buy_conditions'])

    # print(f'sell_conditions: {sell_conditions}')
