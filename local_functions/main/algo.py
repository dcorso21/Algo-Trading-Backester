# LOCAL FUNCTIONS #############
from local_functions.main import global_vars as gl
import time


def test_trade(mode='csv', csv_file='first'):

    start_time = time.time()
    gl.reset.reset_variables(mode=mode, csv_file=csv_file)

    gl.screen.pick_stock_direct(mode)
    if gl.stock_pick == 'nan':
        return

    while True:

        gl.gather.update_direct()  # Updates Info...
        orders = gl.ana.analyse()  # Analyse and build orders
        gl.trade_funcs.exe_orders(orders)  # Execute orders.

        if gl.loop_feedback == False:
            break

    gl.save_all()
    print('\ndone')

    duration = time.time() - start_time
    print(f'\nalgo finished in {duration} second(s)\n')


def append_batch_frame(batch_frame, file_name, rep):

    # 'min_real': gl.pl_ex['min_unreal'],
    # 'max_real': gl.pl_ex['max_unreal'],
    # 'max_unreal': gl.pl_ex['max_unreal'],
    # 'min_unreal': gl.pl_ex['min_unreal'],
    row = {
        'rep': rep,

        'tick_date': file_name,

        'real_pl': gl.pl_ex['real'],

        'unreal_pl': gl.pl_ex['unreal'],

        'max_ex': gl.pl_ex['max_ex'],

        'num_of_orders': len(gl.filled_orders),
        'end_time': gl.filled_orders.exe_time.tolist()[-1],
        'flattened': str(bool(len(gl.current_positions) == 0)),
    }

    return batch_frame.append(row, sort=False, ignore_index=True)


def batch_loop(reps, file, path, batch_frame):
    for rep in range(reps):
        file_name = file.split('\\')[1].strip('.csv')
        print(f'now trading: {file_name}')
        test_trade(mode='csv', csv_file=file)
        full_path = path + f'{file_name}_{rep}'
        save_documentation(full_path)
        batch_frame = append_batch_frame(batch_frame, file_name, rep)

    return batch_frame


def batch_test(reps=1, mode='internal'):
    start = time.time()
    import glob

    print('Starting BATCH test')

    csv_list = glob.glob("mkt_csvs/*.csv")
    print(f'number of stocks found: {len(csv_list)}\n')

    path = get_batch_path()

    batch_frame = gl.pd.DataFrame()

    for file in csv_list:
        if mode == 'internal':
            batch_frame = batch_loop(reps, file, path, batch_frame)
        if mode == 'multiple':
            batch_frame = batch_loop(1, file, path, batch_frame)

    print('batch test done')
    batch_frame.set_index('tick_date')
    gl.batch_frame = batch_frame
    batch_frame.to_csv(path + 'batch_overview.csv')

    if reps > 1 and mode == 'multiple':
        reps -= 1
        batch_test(reps=reps, mode='multiple')

    duration = (time.time() - start)
    print(f'total time elapsed: {duration}')


def save_documentation(path):
    import shutil

    # path = f'results\\{today}\\batch {batch_count}'
    directory = 'C:\\Users\\19374\\Documents\\Python\\Algorithmic Trading\\'
    src = directory+('temp_assets')
    dst = directory + path
    move = shutil.copytree(src, dst)
    # old_name = destination + ('\\temp_assets')
    # new_name = destination + (f'\\{csv_file}')
    # os.rename(old_name, new_name)


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
