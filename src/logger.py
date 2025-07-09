import logging
import os 

def setup_logger():
    logs_dir_path = os.path.join(os.path.dirname(__file__),'..' ,'logs')
    logs_dir_path = os.path.abspath(logs_dir_path)

    if not os.path.exists(logs_dir_path):
        os.makedirs(logs_dir_path)

    logging.basicConfig(
        level=logging.INFO,
        format="%(asctime)s - %(levelname)s - %(message)s",
        handlers=[
            logging.FileHandler(os.path.join(logs_dir_path, 'app.log')),
            logging.StreamHandler()
        ]
    )


