import argparse
import os
import sys
import logging
from time import perf_counter
from tkinter import Tk, filedialog
from config_loader import load_config
from logger import setup_logging
from file_processor import process_file
from token_bucket import TokenBucket

def get_script_directory():
    """
    获取脚本所在目录
    :return: 脚本目录路径
    """
    if getattr(sys, 'frozen', False):
        return os.path.dirname(sys.executable)
    else:
        return os.path.dirname(os.path.abspath(__file__))

def main_function(config):
    """
    主函数
    """
    script_directory = get_script_directory()
    default_config_path = os.path.join(script_directory, 'config.yaml')

    parser = argparse.ArgumentParser(description='翻译脚本')
    parser.add_argument('--config', default=default_config_path, help='配置文件的路径')
    args = parser.parse_args()

    config = load_config(args.config)
    logging_handlers = setup_logging(config)

    root = Tk()
    root.withdraw()
    file_path = filedialog.askopenfilename()
    if not file_path:
        print("未选择文件。")
        return

    file_directory = os.path.dirname(file_path)

    start_time = perf_counter()
    if config.get('enable_logging', False):
        logging.info("翻译任务开始。")

    progress_path = f"{file_path}.progress"
    
    # 获取任务循环次数
    recurring_task = config.get('recurring_task', False)
    
    # 获取当前使用的翻译模块配置
    current_module = None
    if config['Web_Translation']:
        current_module = config['Web_Translation_config'].get('Web_caiyun')
    elif config['API_translation']:
        current_module = config['API_translation_config'].get('API_tencent') or \
                         config['API_translation_config'].get('API_caiyun')
    
    if current_module and current_module.get('enable', False):
        token_bucket = TokenBucket(current_module['capacity'], current_module['fill_rate'])
        multiple_tasks = current_module.get('Multiple_text_tasks', 1)
        single_tasks = current_module.get('Single_text_tasks', 1)
        batch_size = current_module.get('batch_size', 1)

        task_completed = False
        while recurring_task and not task_completed:
            task_completed = True
            for _ in range(max(1, multiple_tasks)):
                process_file(file_path, token_bucket, progress_path, config, batch_size=batch_size)
                if _ + 1 == multiple_tasks:
                    for _ in range(max(1, single_tasks)):
                        process_file(file_path, token_bucket, progress_path, config, batch_size=1)
                        if _ + 1 == single_tasks:
                            task_completed = True
                            break
                    if task_completed:
                        break

    if os.path.exists(progress_path):
        os.remove(progress_path)
        print(f"删除文件: {progress_path}")

    end_time = perf_counter()
    total_time = end_time - start_time
    if config.get('enable_logging', False):
        logging.info(f"翻译任务完成，总时间: {total_time:.2f} 秒.")
    print(f"翻译任务完成，总时间: {total_time:.2f} 秒.")
