from local_functions.main import global_vars as gl
from local_functions.main import algo
import time


@ gl.save_on_error
def batch_test(reps=1, mode='internal', stop_at=False, shuffle=True):
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

    ## Notes:
    - This is a master function that uses many others to complete the batch process. 

    ## TO DO:
    - None. 
    '''
    # endregion Docstring
    start = time.time()
    import glob

    print('Starting BATCH test')

    # 1) Retrieve list of csvs in mkt_csvs folder.
    csv_list = glob.glob("mkt_csvs/*.csv")

    # 2) Shuffle list to randomize sample set.
    if shuffle == True:
        gl.random.shuffle(csv_list)

    if stop_at != False:
        csv_list = csv_list[:stop_at]

    print(f'number of stocks: {len(csv_list)}\n')

    # 3) Estimate amount of time to take to execute batch.
    calc_batch_time(len(csv_list), reps)

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
        if stop_at != False:
            if count >= stop_at:
                break
    print('batch complete')

    # 5) Rename folder assets created
    # rename_folders(path)

    realized = batch_frame[batch_frame.flattened == 'True'].real_pl.sum()
    realized = realized + \
        batch_frame[batch_frame.flattened == 'False'].unreal_pl.sum()
    print('total Profit/Loss: ${:.2f}'.format(realized))

    if reps > 1 and mode == 'multiple':
        reps -= 1
        batch_test(reps=reps, mode='multiple')

    duration = (time.time() - start)/60
    print(f'total time elapsed: {duration} minute(s)')


def append_batch_frame(batch_frame, file_name, rep):

    end_time = 'nan'
    if len(gl.filled_orders) != 0:
        end_time = gl.filled_orders.exe_time.tolist()[-1]

    row = {
        'tick_date': file_name+f'_{rep}',
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
        'flattened': str(bool(len(gl.current_positions) == 0)),
    }

    return batch_frame.append(row, sort=False, ignore_index=True)


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
    for rep in range(reps):

        # 1) Trade the csv with the function `test_trade`
        file_name = gl.os.path.basename(file).strip('.csv')
        print(f'now trading: {file_name}')
        algo.test_trade(mode='csv', csv_file=file, batch_path=path)

        # 2) Categorize traded results in subfolders of batch.
        if len(gl.filled_orders) == 0:
            subfolder = 'untraded'
        elif gl.pl_ex['unreal'] == 0:
            subfolder = 'resolved'
        else:
            subfolder = 'unresolved'
        full_path = path / subfolder / f'{file_name}_{rep}'
        # 3) Save all temp_assets with `save_documentation` function.
        save_documentation(full_path)

        # 4) Update Batch Frame with `append_batch_frame` function.
        batch_frame = append_batch_frame(batch_frame, file_name, rep)

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

    ## Notes:
    - will automatically calculate seconds, minutes or hours based on duration. 

    '''
    # endregion Docstring
    increment = 'seconds'
    ex_time = 85 * num_of_stocks * reps

    if ex_time >= 60:
        increment = 'minutes'
        ex_time = ex_time / 60
        if ex_time >= 60:
            ex_time = ex_time / 60
            increment = 'hours'
    ex_time = round(ex_time, 2)
    print(f'expected time to batch: {ex_time} {increment}')


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

    batch_frame.to_csv(path / 'batch_overview.csv')
    gl.plotr.plot_batch_overview(batch_frame, path)
    save_batch_index(path)
    return batch_frame


def save_batch_index(path):

    folders = []
    for (dirpath, dirnames, filenames) in gl.os.walk(str(path)):
        folders.extend(dirnames)
        break

    collapsible = ''
    for folder in folders:
        direct = path / folder
        tick_dates = []
        # sublist = ''
        # individual stocks
        for (dirpath, dirnames, filenames) in gl.os.walk(str(direct)):
            if len(dirnames) != 0:
                tick_dates.extend(dirnames)
                links = []
                # log.html links.
                for tick_date in tick_dates:
                    if len(tick_date) != 0:
                        links.append(
                            (str(direct / tick_date / 'log.html'), tick_date))
                        sublist = ''
                        for link in set(links):
                            sublist = sublist + \
                                (f'<li><a href="{link[0]}">{link[1]}</a></li>')
            break
        folder_and_num = folder.capitalize() + ' ' + str(len(links))
        collapsible = collapsible + \
            f'<li><span class="opener">{folder_and_num}</span><ul>{sublist}</ul></li>'

    collapsible

    template_path = str(
        gl.directory / 'batch_design' / 'batch_index_template.html')
    with open(template_path, 'r') as template:
        template = template.read()

    date, batch_name = gl.os.path.split(path)
    date = gl.os.path.split(date)[1]

    batch_name = batch_name.replace(',', ':')
    batch_name = batch_name.replace('_', ' ').capitalize()

    asset_path = str(gl.directory / 'batch_design' / 'assets')

    template = template.replace('^^^doc_name^^^', batch_name)
    template = template.replace('^^^date^^^', date)
    template = template.replace('^^^list_items^^^', collapsible)
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
