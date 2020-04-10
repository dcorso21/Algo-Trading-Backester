from local_functions.main import global_vars as gl
from local_functions.main import algo
import time


def append_batch_frame(batch_frame, file_name, rep):

    end_time = 'nan'
    if len(gl.filled_orders) != 0:
        end_time = gl.filled_orders.exe_time.tolist()[-1]

    row = {
        'tick_date': file_name+f'_{rep}',

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
    for rep in range(reps):
        file_name = file.split('\\')[1].strip('.csv')
        print(f'now trading: {file_name}')
        algo.test_trade(mode='csv', csv_file=file)
        if gl.pl_ex['unreal'] == 0:
            subfolder = 'resolved\\'
        else:
            subfolder = 'unresolved\\'
        full_path = path + subfolder + f'{file_name}_{rep}'
        save_documentation(full_path)
        batch_frame = append_batch_frame(batch_frame, file_name, rep)

    return batch_frame


def calc_batch_time(csv_list, reps, stop_at):
    increment = 'seconds'
    num_of_stocks = len(csv_list)
    if stop_at != False:
        num_of_stocks = stop_at
    ex_time = 48 * num_of_stocks * reps

    if ex_time >= 60:
        increment = 'minutes'
        ex_time = ex_time / 60
        if ex_time >= 60:
            ex_time = ex_time / 60
            increment = 'hours'

    print(f'expected time to batch: {ex_time} {increment}')


def manage_batch_frame(batch_frame, path):
    batch_frame.set_index('tick_date')
    gl.batch_frame = batch_frame
    batch_frame.to_csv(path + 'batch_overview.csv')
    gl.plotr.plot_batch_overview(batch_frame, path)
    return batch_frame


def batch_test(reps=1, mode='internal', stop_at=False, shuffle=True):
    start = time.time()
    import glob

    print('Starting BATCH test')

    csv_list = glob.glob("mkt_csvs/*.csv")

    if shuffle == True:
        gl.random.shuffle(csv_list)

    print(f'number of stocks found: {len(csv_list)}\n')
    calc_batch_time(csv_list, reps, stop_at)

    path = get_batch_path()
    batch_frame = gl.pd.DataFrame()
    count = 0

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
    rename_folders(path)

    if reps > 1 and mode == 'multiple':
        reps -= 1
        batch_test(reps=reps, mode='multiple')

    duration = (time.time() - start)/60
    print(f'total time elapsed: {duration} minute(s)')


def save_documentation(path):
    import shutil

    directory = 'C:\\Users\\19374\\Documents\\Python\\Algorithmic Trading\\'
    src = directory+('temp_assets')
    dst = directory + path
    move = shutil.copytree(src, dst)


def get_batch_path():

    import datetime
    import os

    timestamp = datetime.datetime.today()
    today = timestamp.strftime(r'%m-%d-%Y')
    today_results = f'results\\{today}'
    batch_num = 1
    for x, folder, z in os.walk(today_results):
        if len(folder) != 0:
            batch_num += len(folder)
        break

    time = timestamp.strftime(r'%I,%M_%p')
    # time = f'({time})'
    path = today_results + f'\\batch_{batch_num}_{time}\\'
    return path


def rename_folders(path):
    import glob
    for folder in ['resolved', 'unresolved']:
        full_path = path + folder
        if gl.os.path.exists(full_path):
            num_of_folders = len(glob.glob(full_path + '\\*'))
            gl.os.rename(full_path, path + f'{folder}_{num_of_folders}')
