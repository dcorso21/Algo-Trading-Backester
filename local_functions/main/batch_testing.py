from local_functions.main import global_vars as gl
from local_functions.main import algo
import time

batch_configs = []
batch_csvs = []


@ gl.save_on_error
def batch_test(reps=1, mode='internal', stop_at=False, shuffle=True, config_setting='default', inherit_csvs=False):
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
    start = time.time()
    args = {
        'reps': reps,
        'mode': mode,
        'stop_at': stop_at,
        'shuffle': shuffle,
    }
    print('Starting BATCH test')

    global batch_csvs 

    if inherit_csvs == True:

        csv_list = batch_csvs
    
    else:
        import glob
        # 1) Retrieve list of csvs in mkt_csvs folder.
        csv_list = glob.glob("mkt_csvs/*.csv")

        # 2) Shuffle list to randomize sample set.
        if shuffle == True:
            gl.random.shuffle(csv_list)

        if stop_at != False:
            csv_list = csv_list[:stop_at]
        
        batch_csvs = csv_list

    print(f'number of stocks: {len(csv_list)}\n')

    # 3) Estimate amount of time to take to execute batch.
    calc_batch_time(len(csv_list), reps)

    if config_setting != False:
        pick_batch_configs(config_setting, reps)

    path = get_batch_path()
    batch_frame = gl.pd.DataFrame()
    count = 0

    # 4) Test each file in file list.
    for file in csv_list:
        count += 1
        if mode == 'internal':
            batch_frame = batch_loop(reps, file, path, batch_frame)
        if mode == 'multiple':
            batch_frame = batch_loop(1, file, path, batch_frame)

        batch_frame = manage_batch_frame(batch_frame, path)
        add_to_batches_html(path)
        if stop_at != False:
            if count >= stop_at:
                break
    print('batch complete')

    # 5) Rename folder assets created
    # rename_folders(path)

    realized = batch_frame.real_pl.sum()
    unrealized = batch_frame.unreal_pl.sum()
    result = 'total Profit/Loss: real: ${:.2f}, unreal: ${:.2}'
    print(result.format(float(realized), float(unrealized)))

    duration = time.time() - start
    duration = agg_time(duration)
    print(f'total time elapsed: {duration}')

    if reps > 1 and mode == 'multiple':
        global batch_configs
        discard = batch_configs.pop(0)
        reps -= 1
        batch_test(reps=reps, mode='multiple',
                   stop_at=args['stop_at'], shuffle=args['shuffle'], config_setting=False, inherit_csvs=True)


def agg_time(duration, round_to_dec=2):
    increment = 'seconds'
    if duration >= 60:
        increment = 'minutes'
        duration /= 60
        if duration >= 60:
            increment = 'hours'
            duration /= 60
    duration = round(duration, round_to_dec)
    agg_time = f'{duration} {increment}'
    return agg_time


def append_batch_frame(batch_frame, file_name, rep, config):
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

    if str(config) != 'default':
        config = str(config.name).split('.json')[0]

    end_time = 'nan'
    if len(gl.filled_orders) != 0:
        end_time = gl.filled_orders.exe_time.tolist()[-1]

    status = folder_status()

    row = {
        'tick_date': file_name+f'_{rep}',
        'configuration_file': config,
        'avg_vola': gl.volas['mean'],

        'real_pl': gl.pl_ex['real'],
        'min_real': gl.pl_ex['min_real'],
        'max_real': gl.pl_ex['max_real'],

        'unreal_pl': gl.pl_ex['unreal'],
        'max_unreal': gl.pl_ex['max_unreal'],
        'min_unreal': gl.pl_ex['min_unreal'],

        'max_ex': gl.pl_ex['max_ex'],

        'num_of_orders': len(gl.filled_orders),
        'end_time': end_time,
        'status': status,
    }

    return batch_frame.append(row, sort=False, ignore_index=True)


def pick_batch_configs(config_setting, reps):
    # region Docstring
    '''
    # Pick Batch Configs
    picks a configuration.json file for use from the github repo. 

    redefines global variable `batch_configs` with a list of configs to use. 

    ## Parameters:{
    ####    `config_setting`: str, 
    - 'pick' will ask for user to choose,
    - 'last' will select the most recent file,
    - 'default' will use the given settings in `controls.py`

    ####    `reps`: number of repetitions, 
    ## }
    '''
    # endregion Docstring
    configs = gl.manage_algo_config_repo('get_files')
    if config_setting == 'last':
        configs = [configs[0]]*reps
    elif config_setting == 'default':
        configs = [config_setting]*reps
    elif config_setting == 'pick':
        num_files = enumerate(configs)
        msg = ''
        for fil in num_files:
            num, x = fil[0], str(fil[1].name)
            x = f'{num}. {x} \n'
            msg = msg + x+'\n'
        msg = f'{msg}\n'
        print(msg)
        prompt = f'input {reps} indexes for files.'
        picks = input(prompt).split(',')
        picks = map(int, picks)
        picks = list(picks)
        cs = []
        for index in picks:
            if index == -1:
                cs.append('default')
            else:
                cs.append(configs[index])
        configs = cs

    global batch_configs
    batch_configs = configs


def batch_loop(reps, file, path, batch_frame):
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
    global batch_configs
    total = reps
    # reps = list(range(1, reps+1))
    # reps.reverse()
    for rep in range(reps):

        # while True:
        #     if len(batch_configs) > rep:
        #         discarded = batch_configs.pop(0)
        #         break

        config = batch_configs[rep]
        # 1) Trade the csv with the function `test_trade`
        file_name = gl.os.path.basename(file).strip('.csv')
        print(f'now trading: {file_name}')
        algo.test_trade(config=config, mode='csv',
                        csv_file=file, batch_path=path)

        # 2) Categorize traded results in subfolders of batch.

        subfolder = folder_status()

        # rep = total - rep

        full_path = path / subfolder / f'{file_name}_{rep}'
        # 3) Save all temp_assets with `save_documentation` function.
        save_documentation(full_path)

        # 4) Update Batch Frame with `append_batch_frame` function.
        batch_frame = append_batch_frame(batch_frame, file_name, rep, config)

    return batch_frame


def calc_batch_time(num_of_stocks, reps):
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
    end_time = gl.controls.misc['hard_stop']
    end_time = gl.pd.to_datetime(end_time).timestamp()
    minutes = (end_time - start_time) / 60
    mult = 1

    time = mult * minutes * num_of_stocks * reps

    time = agg_time(time)

    print(f'expected time to batch: {time}')


def manage_batch_frame(batch_frame, path):
    # region Docstring
    '''
    # Manage Batch Frame
    Saves batch frame to csv and plots the overview of the data to an html file 
    using the `plot_batch_overview` function. 

    ## Parameters:{
    ####    `batch_frame`: DataFrame of info on stocks in batch. 
    ####    `path`: filepath to desired folder. 
    ## }

    '''
    # endregion Docstring
    batch_frame.set_index('tick_date')
    gl.batch_frame = batch_frame
    # batch_frame.to_csv(path / 'batch_overview.csv')
    save_batch_index(path, batch_frame)
    return batch_frame


def save_batch_index(path, batch_frame):
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

    folders = []
    for (dirpath, dirnames, filenames) in gl.os.walk(str(path)):
        folders.extend(dirnames)
        break

    breakdown = ''
    sep = ''
    for folder in folders:
        direct = path / folder
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
    date, batch_name = gl.os.path.split(path)
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

    plot = gl.plotr.plot_batch_overview(batch_frame)

    def link_to_log(tick_date, path):
        for root, dirs, files in gl.os.walk(path):
            if tick_date in dirs:
                root = gl.os.path.basename(root)
                link = str(gl.Path(root) / tick_date / 'log.html')
                break
        return f'<a href="{link}">{tick_date}</a>'

    # batch_frame['tick_date'] = batch_frame.tick_date.apply(lambda x: link_to_log(x, path))

    batch_table = gl.frame_to_html(batch_frame, 'batch_frame')
    for ticker in batch_frame.tick_date:
        batch_table = batch_table.replace(ticker, link_to_log(ticker, path))

    batches_link = str(gl.directory / 'batches.html')

    template = template.replace('^^^batches_link^^^', batches_link)

    template = template.replace('^^^doc_name^^^', batch_name)
    template = template.replace('^^^plot^^^', plot)
    template = template.replace('^^^batch_table^^^', batch_table)
    template = template.replace('^^^date^^^', date_and_info)
    template = template.replace('^^^asset_path^^^', asset_path)

    save_name = str(path / 'batch_index.html')

    if gl.os.path.exists(save_name):
        with open(save_name, 'w') as file:
            file.write(template)
    else:
        with open(save_name, 'x') as file:
            file.write(template)


def save_documentation(path):
    # region Docstring
    '''
    # Save Documentation
    Saves all files in the `temp_assets` folder to given path. 
    In this case, the custom path is the one made for the batch test. 

    returns nothing, but saves everything to the given path.  

    ## Parameters:{
    ####    `path`: folder to save to.  
    ## }

    '''
    # endregion Docstring
    import shutil

    directory = gl.directory
    src = directory / 'temp_assets'
    dst = path
    move = shutil.copytree(src, dst)


def get_batch_path():
    # region Docstring
    '''
    # Get Batch String
    Get name of new folder to put all of batch results. 

    Returns path.  

    ## Process:

    ### 1) Get current day's date to file the batch under. 
    ### 2) Number the batch based on number of previous batches in the current day's folder. 
    ### 3) Make Timestamp to be used in folder name. 
    ### 4) Return Full Path. 

    '''
    # endregion Docstring
    import datetime
    import os

    # 1) Get current day's date to file the batch under.
    timestamp = datetime.datetime.today()
    today = timestamp.strftime(r'%m-%d-%Y')
    directory = gl.directory
    today_results = directory / 'results' / today

    # 2) Number the batch based on number of previous batches in the current day's folder.
    batch_num = 1
    for x, folder, z in os.walk(today_results):
        if len(folder) != 0:
            batch_num += len(folder)
        break

    # 3) Make Timestamp to be used in folder name.
    time = timestamp.strftime(r'%I,%M_%p')

    # 4) Return Full Path.
    path = directory / 'results' / today / f'batch_{batch_num}_{time}'
    return path


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


def add_to_batches_html(path):
    # region Docstring
    '''
    # Add to Batches Html
    Checks to see if the current path is in the current `batches.html` file. 
    If not, will refresh the file with the `refresh_batches_html` function.

    #### Returns nothing
    '''
    # endregion Docstring
    path = str(path)
    with open('batches.html', 'r') as f:
        doc = f.read()
    if path not in doc:
        refresh_batches_html()


def refresh_batches_html():
    # region Docstring
    '''
    # Refresh batches.html
    refreshes the `batches.html` file to include all seen batches in results dir.

    #### Returns nothing, updates file.
    '''
    # endregion Docstring

    links = []
    path = gl.directory
    results = str(path / 'results')
    for root, folder, files in gl.os.walk('results'):
        if 'batch_index.html' in files:
            links.append(gl.os.path.join(root, 'batch_index.html'))

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
    }

    df = gl.pd.DataFrame(frame)

    df['b_number'] = df['batch_name'].apply(get_batch_number)
    df = df.sort_values(by='b_number', ascending=False)
    df = df.drop('b_number', axis=1)
    df = df.reset_index(drop=True)

    def fill_out_dropdown(date, list_items):
        template = f'''
            <li class="parent">
            <!-- Name of List -->
            <a href="#">{date}<span class="expand">»</span></a>
            <!-- List of Items -->
            <ul class="child">
            {list_items}
            </ul>
            </li>
        '''
        return template

    def create_list_item(link, element_title):
        return f'<li class="parent"><a href="{link}">{element_title}</a></li>'

    html_text = ''

    dates = sorted(set(df.date))
    dates.reverse()

    for date in dates:
        batches = df[df['date'] == date]
        list_items = ''
        for row in batches.index:
            link = batches.at[row, 'link']
            batch_name = batches.at[row, 'batch_name']
            list_item = create_list_item(link=link, element_title=batch_name)
            list_items += list_item
        html = fill_out_dropdown(date, list_items)
        html_text += html

    template = str(path / 'batch_design' / 'batches_template.html')
    with open(template, 'r') as file:
        text = file.read()

    text = text.replace('^^^List^^^', html_text)

    destination = str(path / 'batches.html')
    with open(destination, 'w') as file:
        file.write(text)
