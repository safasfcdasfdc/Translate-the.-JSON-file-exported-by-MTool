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

def main():
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
    
    # 遍历所有翻译模块
    modules = config['API_translation_config']
    modules.update(config['Web_Translation_config'])
    
    task_completed = False

    while recurring_task and not task_completed:
        task_completed = True
        for module_name, module_config in modules.items():
            if module_config.get('enable', False):
                token_bucket = TokenBucket(module_config['capacity'], module_config['fill_rate'])
                
                multiple_tasks = module_config.get('Multiple_text_tasks', 1)
                single_tasks = module_config.get('Single_text_tasks', 1)

                for _ in range(max(1, multiple_tasks)):
                    process_file(file_path, token_bucket, progress_path, config, batch_size=module_config.get('batch_size', 1))
                    if _ + 1 == multiple_tasks:
                        for _ in range(max(1, single_tasks)):
                            process_file(file_path, token_bucket, progress_path, config, batch_size=module_config.get('batch_size', 1))
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

if __name__ == "__main__":
    main()
