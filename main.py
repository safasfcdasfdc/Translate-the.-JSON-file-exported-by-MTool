import os
from task_queue_processor import process_task_queue
from config_loader import load_config
from main_function import main_function
from logger import setup_logging

if __name__ == "__main__":
    # 获取脚本所在目录
    script_directory = os.path.dirname(os.path.abspath(__file__))
    config_path = os.path.join(script_directory, 'config.yaml')

    # 检查是否存在 Task Queue.yaml 文件
    task_queue_file = os.path.join(script_directory, 'Task Queue.yaml')
    if os.path.exists(task_queue_file):
        print("Task Queue.yaml 文件存在，开始处理任务队列...")
        process_task_queue()
    else:
        print("Task Queue.yaml 文件不存在，加载配置继续正常工作流程。")
        config = load_config(config_path)
        setup_logging(config)  # 设置日志系统
        main_function(config)
    print("程序执行完毕。")