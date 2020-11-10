print('\nimporting libraries\n')
from local_functions.main import batch_testing as batch

batch_params = {
    'stop_at': 1,                         # Default = False
    # 'reps': 1,                              # Default = 1
    # 'mode': 'internal',                   # Default = 'multiple'
    # 'shuffle': False,                     # Default = True
    # 'create_compare': True,               # Default = False
    # 'config_setting': 'pick',             # Default = 'default'
    # 'first_run': False,                   # Default = True
    'inherit_csvs':  True,
    'debug_plot':  True,
}

compare_params = {
    'num_to_compare':2,
    # 'pick_most_recent':False,
    'compare':'time',
    # 'overwrite':True,
    # 'min_stock_in_batch':50,
}


batch.batch_test(**batch_params)
# batch.standard_year_test()
# batch.compare_batches(**compare_params)
# batch.gl.save_worst_performers()
# batch.delete_results(min_stock_count=100)