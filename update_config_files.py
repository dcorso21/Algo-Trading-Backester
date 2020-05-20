
if __name__ == '__main__':
    from config.ipy_creator import update_all
    from local_functions.main.global_vars import get_algo_config_repo
    import os
    from pathlib2 import Path
    path = Path(os.getcwd())
    repo = get_algo_config_repo()
    update_all(path, repo)

    
