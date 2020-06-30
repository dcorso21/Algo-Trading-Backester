from local_functions.main import global_vars as gl
from local_functions.main import algo
import glob
import time
from pathlib import Path

# region Global Vars


starting_msg = '''\033[94m
<><><><><><><><><><><><><><><><><><><><>
\033[96m
--------\033[00m Starting Batch Test {} \033[96m--------\n
\033[00mLoaded Configuration\n
\033[94m-->\033[00m {}\n
\033[94m-->\033[00m number of stocks: {}\n
\033[94m-->\033[00m expected time to batch: {}
\033[96m
----------------------------------------
\033[94m
<><><><><><><><><><><><><><><><><><><><>\n
\033[00m'''

ending_message = '''\033[94m
/////////////////////////////////////////
\033[96m
<><><><><><>\033[00m BATCH COMPLETE \033[96m<><><><><><>\n
\033[94m-->\033[00m Profit/Loss: real: ${}, unreal: ${}\n
\033[94m-->\033[00m time elapsed: {}
\033[96m
<><><><><><><><><><><><><><><><><><><><>
\033[94m
/////////////////////////////////////////
\033[00m'''

# batch name
b_name = ''
# number of batches
num_of_batches = 0
# batch_num
b_num = 0
# batch path, including batch name (more formatted)
b_dir = ''
# batch frame
b_frame = gl.pd.DataFrame()
# current stock being traded in batch.
b_tick_date = ''
# number of seconds expected for a stock.
expected_time_per_stock = 0


b_configs = []
b_current_config = ''
b_csvs = []

# endregion Global Vars


@ gl.save_on_error
def batch_test(reps=1, mode='multiple', stop_at=False,
               shuffle=True, config_setting='default',
               first_run=True, create_compare='config',
               inherit_csvs=False):
    # region Docstring
    '''
    # Batch Test
    Function for doing testing in large chunks.

    Returns Nothing, but creates detailed folders in the results folder.

    ## Parameters:{
    ####    `reps`: integer, number of repetitions.
    - Can either repeat the function recursively or repeat each stock. Depends on `mode`.

    ####    `mode`: 'internal' or 'multiple'
    - 'internal' means that `reps` will repeat the same stock multiple times inside the same call of `batch_test`
    - 'multiple' means that `reps` will recursively loop back and call `batch_test` again.

    ####    `stop_at`: integer to cut off list at. Defaults to `False` which will enable entire list.
    ####    `shuffle`: bool - defaults to `True`.
    ####    `config_setting`: pick shows a selection, default picks config.json
    ####    `first_run`: true unless running recursively
    ####    `create_compare`: config - compares with config as labels. also allows `date` and `time`
    ####    `inherit_csvs`: config - compares with config as labels. also allows `date` and `time`
    - Means that list of stocks will be shuffled to randomize testing.

    ## }

    ## Process:

    ### 1) Retrieve list of csvs in mkt_csvs folder.
    ### 2) Shuffle list to randomize sample set.
    ### 3) Estimate amount of time to take to execute batch with `calc_batch_time`.
    ### 4) Test each file in file list.
    ### 5) Rename folder assets created
    ### 6) Potentially recursively call function again

    '''
    # endregion Docstring
    global b_csvs, b_configs, b_frame, b_current_config
    global num_of_batches

    if first_run:
        num_of_batches = reps

    #  <<< Gets Configuration Files >>>
    get_batch_configs(config_setting, reps, first_run)

    #  <<< time starts after config is picked >>>
    start = time.time()

    #  <<< Creates/Gets Directory for Batch >>>
    get_batch_dir()

    # <<< Get CSVs >>>
    get_b_csvs(stop_at, shuffle, first_run, inherit_csvs)

    #  <<< Starting Message >>>
    num_of_stocks = len(b_csvs)
    ex_time = calc_batch_time(reps)
    msg = starting_msg.format(b_num,
                              b_current_config,
                              num_of_stocks,
                              ex_time)
    print(msg)

    #  <<< Trade >>>
    batch_loop(reps, mode)

    realized = round(float(b_frame.real_pl.sum()), 2)
    unrealized = round(float(b_frame.unreal_pl.sum()), 2)

    if realized >= 0:
        realized = gl.color_format(realized, 'green')
    else:
        realized = gl.color_format(realized, 'red')
    if unrealized >= 0:
        unrealized = gl.color_format(unrealized, 'green')
    else:
        unrealized = gl.color_format(unrealized, 'red')

    duration = time.time() - start
    duration = agg_time(duration)

    print(ending_message.format(realized,
                                unrealized,
                                duration))

    # Run Another Batch Test
    if reps > 1 and mode == 'multiple':
        # global batch_configs
        # discard = batch_configs.pop(0)
        reps -= 1
        batch_test(reps=reps, mode='multiple',
                   stop_at=stop_at, shuffle=shuffle, config_setting=False, first_run=False)

    else:
        b_csvs = []
        if create_compare != False:
            if num_of_batches > 1:
                compare_batches(compare=create_compare)


def batch_loop(reps, mode):
    # region Docstring
    '''
    # Batch Loop

    Core of the process in the `batch_test` function.
    To be used for each csv file.

    Returns an updated `batch_frame`

    ## Parameters:{
    ####    `reps`: integer, repetitions, variable from `batch_test` function.
    ####    `file`: string, csv file name.
    ####    `path`: string, directory for saving files.
    ####    `batch_frame`: DataFrame of each stock tested in `batch_test`
    ## }

    ## Process:

    ### 1) Trade the csv with the function `test_trade`
    ### 2) Categorize traded results in subfolders of batch.
    ### 3) Save all temp_assets with `save_documentation` function.
    ### 4) Update Batch Frame with `append_batch_frame` function.

    ## Notes:
    - Notes

    ## TO DO:
    - Item
    '''
    # endregion Docstring
    global b_configs, b_frame

    b_frame = gl.pd.DataFrame()

    if mode == 'multiple':
        reps = 1
    reps = list(range(reps))
    # reps.reverse()

    for csv in b_csvs:

        for rep in reps:

            config = b_configs[0]

            # 1) Trade the csv with the function `test_trade`
            file_name = gl.os.path.basename(csv).strip('.csv')
            gl.stock_pick = file_name
            stock_index = b_csvs.index(csv)
            time_remaining = expected_time_per_stock * \
                len(b_csvs[stock_index:])
            now_trading = '\ntrading: {}, {} left, ({}%)'
            print(now_trading.format(file_name,
                                     agg_time(time_remaining),
                                     int((stock_index / len(b_csvs)) * 100)))
            algo.test_trade(config=config, mode='csv',
                            csv_file=csv, batch_dir=b_dir)

            subfolder = folder_status()
            stock_and_rep = f'{file_name}_{rep}'
            stock_path = b_dir / subfolder / stock_and_rep

            save_documentation(stock_path)
            append_batch_frame(stock_and_rep)

        add_to_batch_index()
        add_to_batches_html()


def agg_time(duration, round_to_dec=2):
    # region Docstring
    '''
    # Aggregate Time
    takes a duration in seconds and aggregates it into
    seconds, minutes or hours based on the number of seconds

    #### Returns string with the durating and increment. ex: '6 minutes'

    ## Parameters:{
    ####    `duration`: int, amount of seconds
    ####    `round_to_dec`: int, amount decimals to round in final.
    ## }
    '''
    # endregion Docstring
    increment = 'secs'
    if duration >= 60:
        increment = 'mins'
        duration /= 60
        if duration >= 60:
            increment = 'hours'
            duration /= 60
    duration = round(duration, round_to_dec)
    agg_time = f'{duration} {increment}'
    return agg_time


def get_b_csvs(stop_at, shuffle, first_run, inherit_csvs):

    global b_csvs
    path_to_json = Path.cwd() / 'results' / 'batch_csvs.json'

    if not first_run:
        return

    if inherit_csvs != False:
        if inherit_csvs == 'pick':
            response = input('\ninherit csvs?\ninput [Y/n]:')
            if response.upper() == 'Y':
                inherit_csvs = True
        if inherit_csvs == True:
            with open(path_to_json, 'r') as f:
                text = f.read()
            b_csvs = gl.json.loads(text)
            return
    # 1) Retrieve list of csvs in mkt_csvs folder.
    csv_list = glob.glob("mkt_csvs/*.csv")

    # 2) Shuffle list to randomize sample set.
    if shuffle == True:
        gl.random.shuffle(csv_list)

    if stop_at != False:
        csv_list = csv_list[:stop_at]

    b_csvs = csv_list

    text = gl.json.dumps(csv_list, indent=2)

    with open(path_to_json, 'w') as f:
        f.write(text)
        f.close()


def append_batch_frame(full_stock_name):
    # region Docstring
    '''
    # Append Batch Frame
    takes new info from last batch and attaches it to the `batch_frame` df.

    Returns updated `batch_frame` df
    ## Parameters:{
    ####    `batch_frame`: df of batch results,
    ####    `file_name`: name of stock traded for frame,
    ####    `rep`: repetition of stock's batch execution,
    ####    `config`: name of json setting for configuration of batch,
    ## }
    '''
    # endregion Docstring

    end_time = 'nan'
    if len(gl.filled_orders) != 0:
        end_time = gl.filled_orders.exe_time.tolist()[-1]

    status = folder_status()

    row = {
        'tick_date': full_stock_name,
        'avg_vola': gl.volas['mean'],

        'real_pl': gl.pl_ex['real'],
        'min_real': gl.pl_ex['min_real'],
        'max_real': gl.pl_ex['max_real'],

        'unreal_pl': gl.pl_ex['unreal'],
        'max_unreal': gl.pl_ex['max_unreal'],
        'min_unreal': gl.pl_ex['min_unreal'],

        'max_ex': gl.pl_ex['max_ex'],

        '#_ords': len(gl.filled_orders),
        'end_time': end_time,
        'status': status,
    }
    global b_frame
    b_frame = b_frame.append(row, sort=False, ignore_index=True)


def get_batch_configs(config_setting, reps, first_run):
    # region Docstring
    '''
    # Pick Batch Configs
    picks a configuration.json file for use from the github repo.

    redefines global variable `batch_configs` with a list of configs to use.

    ## Parameters:{
    ####    `config_setting`: str,
    - 'pick' will ask for user to choose,
    - 'last' will select the most recent file,
    - 'default' will use the given settings in `configure.py`

    ####    `reps`: number of repetitions,
    ## }
    '''
    # endregion Docstring

    global b_configs, b_current_config

    def extract_name(config_path):
        config_name = gl.os.path.basename(config_path)
        config_name = config_name.rstrip('.json').replace('_', '.', 2).split('_', 1)[
            1].replace('_', ' ').title()
        return config_name

    if not first_run:
        del b_configs[0]
        b_current_config = b_configs[0]
        if b_current_config != 'default':
            b_current_config = extract_name(b_current_config)
        return

    elif config_setting == 'default':
        b_configs = [config_setting]*reps
    elif config_setting == 'last':
        b_configs = gl.get_downloaded_configs()
        b_configs = [b_configs[0]]*reps

    elif config_setting == 'pick':
        configs = gl.get_downloaded_configs()
        gl.show_available_configurations()
        prompt = f'\ninput {reps} indexes for files.\nUse -1 for default.\nindexes:'
        picks = input(prompt).split(',')
        picks = map(int, picks)
        picks = list(picks)
        cs = []
        for index in picks:
            if index == -1:
                cs.append('default')
            else:
                cs.append(configs[index])
        b_configs = cs
        # b_configs.reverse()

    b_current_config = b_configs[0]
    if b_current_config != 'default':
        b_current_config = extract_name(b_current_config)


def calc_batch_time(reps):
    # region Docstring
    '''
    # Calculate Batch Time
    function for estimating time it will take to run the `batch_test`.

    prints the expected wait time.

    ## Parameters:{
    ####    `num_of_stocks`: integer, number of stocks in batch test.
    ####    `reps`: integer, number of repetitions in batch test.
    ## }

    '''
    # endregion Docstring

    # gl.datetime.datetime.datetime()
    start_time = gl.pd.to_datetime('09:30:00').timestamp()

    if b_current_config == 'default':
        path = str(gl.directory / 'local_functions' / 'main' / 'config.json')
    else:
        path = b_configs[0]
    with open(path, 'r') as f:
        config = f.read()

    config = gl.json.loads(config)
    end_time = config['misc']['hard_stop']

    end_time = gl.pd.to_datetime(end_time).timestamp()
    minutes = (end_time - start_time) / 60
    mult = 1
    global expected_time_per_stock
    expected_time_per_stock = mult * minutes
    wait_time = expected_time_per_stock * len(b_csvs) * reps
    wait_time = agg_time(wait_time)

    return wait_time


def add_to_batch_index():
    # region Docstring
    '''
    # Add to Batch Index
    Adds stock to batch index plot.
    '''
    # endregion Docstring
    global b_frame
    b_frame.set_index('tick_date')
    gl.batch_frame = b_frame
    save_batch_index()


def save_batch_index():
    # region Docstring
    '''
    # Save Batch Index
    Saves an html file of the batch results

    Returns nothing, simply saves a file
    ## Parameters:{
    ####    `path`: path to batch index,
    ####    `batch_frame`: global variable for batch results,
    ## }
    '''
    # endregion Docstring
    global b_dir, b_frame

    folders = []
    for (dirpath, dirnames, filenames) in gl.os.walk(str(b_dir)):
        folders.extend(dirnames)
        break

    breakdown = ''
    sep = ''
    for folder in folders:
        direct = b_dir / folder
        tick_dates = []
        # sublist = ''
        # individual stocks
        for (dirpath, dirnames, filenames) in gl.os.walk(str(direct)):
            number = 0
            if len(dirnames) != 0:
                # stocks
                number = len(dirnames)
            break
        folder_and_num = folder.capitalize() + ': ' + str(number)
        if len(breakdown) != 0:
            sep = ', '
        breakdown = breakdown + sep + folder_and_num
    # menus
    date, batch_name = gl.os.path.split(b_dir)
    date = gl.os.path.split(date)[1]
    date_and_info = f'{date}<br><br>{breakdown}'

    template_path = str(
        gl.directory / 'batch_design' / 'batch_index_template.html')
    with open(template_path, 'r') as template:
        template = template.read()

    batch_name = batch_name.replace(',', ':').capitalize()
    b, c, t, p = batch_name.split('_')
    batch_name = f'{b} {c} @ {t} {p}'
    # batch_name = batch_name.replace()

    asset_path = str(gl.directory / 'batch_design' / 'assets')

    plot = gl.plotr.plot_batch_overview(b_frame)

    def link_to_log(tick_date, path):
        for root, dirs, files in gl.os.walk(path):
            if tick_date in dirs:
                root = gl.os.path.basename(root)
                link = str(gl.Path(root) / tick_date / 'log.html')
                break
        return f'<a href="{link}">{tick_date}</a>'

    batch_table = gl.frame_to_html(b_frame, 'batch_frame')
    for ticker in b_frame.tick_date:
        batch_table = batch_table.replace(ticker, link_to_log(ticker, b_dir))

    batches_link = str(gl.directory / 'batches.html')

    template = template.replace('^^^batches_link^^^', batches_link)

    template = template.replace('^^^doc_name^^^', batch_name)
    template = template.replace('^^^plot^^^', plot)
    template = template.replace('^^^batch_table^^^', batch_table)
    template = template.replace('^^^date^^^', date_and_info)
    template = template.replace('^^^asset_path^^^', asset_path)

    save_name = str(b_dir / 'batch_index.html')

    if gl.os.path.exists(save_name):
        with open(save_name, 'w') as file:
            file.write(template)
    else:
        with open(save_name, 'x') as file:
            file.write(template)


def save_documentation(full_stock_path):
    # region Docstring
    '''
    # Save Documentation
    Saves all files in the `temp_assets` folder to given path.
    In this case, the custom path is the one made for the batch test.

    returns nothing, but saves everything to the given path.

    ## Parameters:{
    ####    `full_stock_path`: folder to save to.
    ## }

    '''
    # endregion Docstring
    # import shutil

    # directory = gl.directory
    # src = directory / 'temp_assets'
    # dst = full_stock_path
    # move = shutil.copytree(src, dst)

    gl.save_all(full_stock_path)
    # save one config per directory.
    if not gl.os.path.exists(b_dir / 'config.json'):
        gl.save_config(b_dir)


def get_batch_dir(subfolder=None, overwrite=False):
    # region Docstring
    '''
    # Get Batch String
    Get name of new folder to put all of batch results.

    updates the global `b_num` and `b_path`

    ## Process:

    ### 1) Get current day's date to file the batch under.
    ### 2) Number the batch based on number of previous batches in the current day's folder.
    ### 3) Make Timestamp to be used in folder name.
    ### 4) Return Full Path.

    '''
    # endregion Docstring
    import datetime
    import os
    global b_num, b_dir

    # 1) Get current day's date to file the batch under.
    timestamp = datetime.datetime.today()
    today = timestamp.strftime(r'%m-%d-%Y')
    time = timestamp.strftime(r'%I,%M_%p')

    today_results = gl.directory / 'results'
    if subfolder != None:
        today_results /= subfolder
    today_results /= today

    if overwrite:
        if os.path.exists(today_results):
            # gets the most recent dir of today's results
            b_dir = today_results / list(os.walk(today_results))[0][1][-1]
            return

    # 2) Number the batch based on number of previous batches in the current day's folder.
    b_num = 1
    for x, folder, z in os.walk(today_results):
        if len(folder) != 0:
            b_num += len(folder)
        break

    folder_name = f'batch_{b_num}_{time}'
    if subfolder != None:
        folder_name = f'{subfolder}_{b_num}_{time}'

    b_dir = today_results / folder_name
    gl.os.makedirs(b_dir)


def rename_folders(path):
    # region Docstring
    '''
    # Rename Folders
    Renames batch folders with the number of stocks that fall into each category.

    categories are: ['resolved', 'unresolved']

    ## Parameters:{
    ####    `path`: path that folders are located in.
    ## }
    '''
    # endregion Docstring
    import glob
    for folder in ['resolved', 'unresolved']:
        full_path = path / folder
        if gl.os.path.exists(full_path):
            num_of_folders = len(glob.glob(str(full_path / '*')))
            gl.os.rename(full_path, path / f'{folder}_{num_of_folders}')


def folder_status():
    # region Docstring
    '''
    # Folder Status
    Checks to see which folder the current batch test file will be allocated to

    Returns name of subfolder (str)
    '''
    # endregion Docstring
    if len(gl.filled_orders) == 0:
        subfolder = 'untraded'
    elif gl.pl_ex['unreal'] == 0:
        subfolder = 'resolved'
    else:
        subfolder = 'unresolved'
    return subfolder


def add_to_batches_html():
    # region Docstring
    '''
    # Add to Batches Html
    Checks to see if the current path is in the current `batches.html` file.
    If not, will refresh the file with the `refresh_batches_html` function.

    #### Returns nothing
    '''
    # endregion Docstring
    path = str(b_dir)
    with open('batches.html', 'r') as f:
        doc = f.read()
    if path not in doc:
        refresh_batches_html()


def df_of_comparisons():
    # region Docstring
    '''
    # DF of Comparisons
    Creates a df of available comparisons by looking at the `results` folder

    #### Returns ex

    ## Parameters:{
    ####    `param`:
    ## }
    '''
    # endregion Docstring

    links = []
    path = gl.directory
    results = str(path / 'results'/'comparison')
    for root, folder, files in gl.os.walk('results'):
        if 'compare.html' in files:
            links.append(gl.os.path.join(root, 'compare.html'))

    def get_comparison_number(compare_name):
        compare_name = compare_name.split(' ')[1]
        return int(compare_name)

    compare_names = []
    dates = []
    for link in links:
        divs = link.split('/')
        if len(divs) == 1:
            divs = divs[0].split('\\')

        divs = divs[2:-1]
        dates.append(divs[0])

        cn = divs[1].title()
        cn = cn.replace(',', ':')
        cn = cn.replace('_', ' ', 1)
        cn = cn.split('_', 1)
        time = cn[1].replace('_', ' ').upper()
        cn = f'{cn[0]} ({time})'
        compare_names.append(cn)

    frame = {
        'link': links,
        'date': dates,
        'compare_name': compare_names,
    }

    df = gl.pd.DataFrame(frame)

    df['c_number'] = df['compare_name'].apply(get_comparison_number)
    df = df.sort_values(by=['date', 'c_number'], ascending=False)
    df = df.drop('c_number', axis=1)
    df = df.reset_index(drop=True)
    return df


def df_of_batches():
    # region Docstring
    '''
    # DF of Batches
    Creates a df of the available batches by looking at batches in results folder   

    #### Returns df
    '''
    # endregion Docstring
    links = []
    configs = []
    path = gl.directory
    results = str(path / 'results')
    for root, folder, files in gl.os.walk('results'):
        if 'batch_index.html' in files:
            configs.append(gl.os.path.join(root, 'config.json'))
            links.append(gl.os.path.join(root, 'batch_index.html'))

    config_names = []
    for c in configs:
        if not gl.os.path.exists(c):
            config_names.append('no configuration file found')
        else:
            with open(c, 'r') as f:
                c = f.read()
            c = gl.json.loads(c)
            metadata = False
            for key in c.keys():
                if key == 'metadata':
                    metadata = True
                    break
            if metadata:
                c_name = c['metadata']['name'].replace('_', ' ').title()
                config_names.append(c_name)
            else:
                config_names.append('Default')

    def get_batch_number(batch_name):
        batch_name = batch_name.split(' ')[1]
        return int(batch_name)

    batch_names = []
    dates = []
    for link in links:
        divs = link.split('/')
        if len(divs) == 1:
            divs = divs[0].split('\\')

        divs = divs[1:-1]
        dates.append(divs[0])

        bn = divs[1].title()
        bn = bn.replace(',', ':')
        bn = bn.replace('_', ' ', 1)
        bn = bn.split('_', 1)
        time = bn[1].replace('_', ' ').upper()
        bn = f'{bn[0]} ({time})'
        batch_names.append(bn)

    frame = {
        'link': links,
        'date': dates,
        'batch_name': batch_names,
        'config': config_names,
    }

    df = gl.pd.DataFrame(frame)

    df['b_number'] = df['batch_name'].apply(get_batch_number)
    df = df.sort_values(by=['date', 'b_number'], ascending=False)
    df = df.drop('b_number', axis=1)
    df = df.reset_index(drop=True)
    return df


def html_batches_menu(df, menu_index=1, name='batch'):
    # region Docstring
    '''
    # HTML Batches Menu
    Creates the html elements for the hover dropdown menus in the  `batches.html` file


    #### Returns html text element to be inserted into html. 

    ## Parameters:{
    ####    `df`: dataframe with menu elements
    ####    `df`: menu_index. At the time of writing, there is a batch menu and a comparison menu. T
    #### he menu index creates new classes in css for custom 
    ####    `name`: "batches" or "comparisons"
    ## }
    '''
    # endregion Docstring
    if menu_index == 1:
        menu_index = ''

    drop_down_temp = '''
            <li class="parent{}">
            <!-- Name of List -->
            <a href="#">{}<span class="expand">»</span></a>
            <!-- List of Items -->
            <ul class="child{}">
            {}
            </ul>
            </li>'''

    list_item_temp = '''
            <li class="parent{}">
            <a href="{}">{}</a>
            </li>'''

    html_text = ''

    dates = sorted(set(df.date))
    dates.reverse()

    for date in dates:
        dfx = df[df['date'] == date]
        list_items = ''
        for row in dfx.index:
            link = dfx.at[row, 'link']
            title = dfx.at[row, f'{name}_name']
            list_items += list_item_temp.format(f' parent{menu_index}',
                                                link, title)

        html = drop_down_temp.format(f' parent{menu_index}',
                                     date,
                                     f' child{menu_index}',
                                     list_items)
        html_text += html
    return html_text


def refresh_batches_html():
    # region Docstring
    '''
    # Refresh batches.html
    refreshes the `batches.html` file to include all seen batches in results dir.

    #### Returns nothing, updates file.
    '''
    # endregion Docstring
    path = gl.directory

    batches = df_of_batches()
    comparisons = df_of_comparisons()

    template = str(path / 'batch_design' / 'batches_template.html')
    with open(template, 'r') as file:
        text = file.read()

    if len(batches) == 0:
        text = text.replace('^^^batches_menu^^^', '')
    else:
        batches = html_batches_menu(batches)
        text = text.replace('^^^batches_menu^^^', batches)

    if len(comparisons) == 0:
        text = text.replace('^^^comparisons_menu^^^', '')
    else:
        comparisons = html_batches_menu(
            comparisons, name='compare', menu_index=2)
        text = text.replace('^^^comparisons_menu^^^', comparisons)

    destination = str(path / 'batches.html')
    with open(destination, 'w') as file:
        file.write(text)


@ gl.save_on_error
def compare_batches(num_to_compare=2, pick_most_recent=True, compare='config', overwrite=False):
    # region Docstring
    '''
    # Compare Batches
    Create a new comparison HTML file that will compare any number of batches. 

    #### Returns nothing, creates a new html file in the results folder. 

    ## Parameters:{
    ####    `num_to_compare`: number of batches to compare
    ####    `pick_most_recent`: defaults to true, else you will be presented with a df and pick
    ####    `compare`: field to compare, defaults to config, but `date` and `time` are also available.
    ####    `overwrite`: defaults to False, will overwrite last compare rather than starting a new one. 
    ## }

    '''
    # endregion Docstring

    print('creating batch comparison')
    from local_functions.plotting import plot_results as plotr
    df = df_of_batches()
    links = df.pop('link')
    if pick_most_recent != True:
        if gl.isnotebook():
            display(df)
        else:
            gl.common.all_rows(df)
        prompt = f'''
            please specify the {num_to_compare} 
            indexes of the batches to compare
            separated by commas. 
        '''
        response = input(prompt)
        indexes = list(map(int, response.split(',')))
    else:
        indexes = list(range(num_to_compare))
    links = [links[index] for index in indexes]

    def make_compare_description(df):
        template = '''
        <h2>Comparing the following batches:</h2>
        <p>{}</p>
        '''
        ul = '<ul>{}____{}--------------------------------->{}</ul>'
        batches = ''
        for index in df.index:
            date, name, config = df.iloc[index]
            config = f'<strong>{config}</strong>'
            date = f'<strong>{date}</strong>'
            name = f'<strong>{name}</strong>'
            batches += ul.format(name, date, config)

        return template.format(batches)

    for_comparison = df.iloc[indexes].reset_index(drop=True)
    compare_description = make_compare_description(for_comparison)

    used_configs = for_comparison.config.tolist()

    batch_names = set(for_comparison.batch_name.to_list())
    config_names = dict.fromkeys(batch_names)
    for i, key in enumerate(config_names.keys()):
        config_names[key] = used_configs[i]

    master_df = gl.pd.DataFrame()
    for link, name in zip(links, batch_names):
        batch_df = gl.pull_df_from_html(link)
        batch_df['batch'] = name
        master_df = master_df.append(batch_df)

    color_dict = {}
    value = 70
    val_off = 7
    # hue_start = 75
    hue_start = 0

    res_colors = plotr.get_colors(hue_start_value=hue_start,
                                  num_of_colors=len(batch_names), v=value)
    unres_colors = plotr.get_colors(hue_start_value=hue_start - val_off,
                                    num_of_colors=len(batch_names), s=75 - val_off, v=value - val_off)
    color_values = ((r, u) for r, u in zip(res_colors, unres_colors))

    for batch, color in zip(batch_names, color_values):
        color_dict[batch] = color

    compare_setting = {
        'config': 'config',
        'date': 'date',
        'time': 'batch_name',
    }

    category_labels = ['resolved', 'unresolved']

    batch_category_labels = for_comparison[compare_setting[compare]].to_list()

    category_labels.extend(batch_category_labels)

    resolved = []
    unresolved = []
    batch_steps = []
    for index, batch in enumerate(batch_names):
        # bn_simple = str(batch).split('(')[0]
        step = []
        batch_df = master_df[master_df.batch == batch]
        for status in ['resolved', 'unresolved']:
            dfx = batch_df[batch_df.status == status]
            if len(dfx) == 0:
                continue
            y_values = dfx.real_pl.cumsum()
            y_values += dfx.unreal_pl.cumsum()
            x_values = list(range(len(y_values)))
            labels = dfx.tick_date
            if status == 'resolved':
                color = color_dict[batch][0]
                name = '{} (R)'.format(batch_category_labels[index])
                scatter = plotr.new_line_plot(
                    x_values, y_values, labels, color, True, name=name)
                resolved.append(scatter)
            else:
                color = color_dict[batch][1]
                name = '{} (U)'.format(batch_category_labels[index])
                scatter = plotr.new_line_plot(
                    x_values, y_values, labels, color, False, name=name)
                unresolved.append(scatter)
            step.append(scatter)
        batch_steps.append(step)

    categories = [resolved, unresolved]

    for i in batch_steps:
        categories.append(i)

    plot = plotr.create_batch_compare_graph(categories, category_labels)

    table = gl.frame_to_html(master_df, 'batches')

    asset_path = str(gl.directory / 'batch_design' / 'assets')
    template = str(gl.directory / 'batch_design' /
                   'batch_compare_template.html')
    batches_link = str(gl.directory / 'batches.html')

    with open(template, 'r') as f:
        template = f.read()

    template = template.replace('^^^date^^^', compare_description)
    template = template.replace('^^^plot^^^', plot)
    template = template.replace('^^^batch_table^^^', table)
    template = template.replace('^^^asset_path^^^', asset_path)
    template = template.replace('^^^batches_link^^^', batches_link)
    template = template.replace('^^^doc_name^^^', 'Batch Compare')

    get_batch_dir(subfolder='comparison', overwrite=overwrite)

    dest = b_dir / 'compare.html'

    if overwrite:
        file_mode = 'w'
    else:
        file_mode = 'x'

    with open(dest, file_mode) as f:
        f.write(template)

    refresh_batches_html()

    print('comparison created')


def delete_all_results():
    gl.clear_all_in_folder('results', confirm=True, print_complete=True)


def manage_batch_results(method):
    methods = {
        'delete': delete_all_results,
    }
    return methods[method]()
