
import os
import yaml
from file_processor import process_file
from config_loader import load_config
from main_function import main_function
from token_bucket import TokenBucket

# 加载 Task Queue.yaml 文件
def load_task_queue(file_path):
    with open(file_path, 'r', encoding='utf-8') as file:
        task_queue = yaml.safe_load(file)
    print("任务队列加载成功: ", task_queue)
    return task_queue.get('tasks', [])

# 标记任务为已完成
def mark_task_completed(task_queue, completed_task):
    for task in task_queue:
        if task == completed_task:
            task['completed'] = True
    with open('Task Queue.yaml', 'w', encoding='utf-8') as file:
        yaml.dump({'tasks': task_queue}, file)
    print("任务标记为已完成: ", completed_task)

# 动态加载速率限制配置
def get_rate_limit_config(config, translation_module):
    if translation_module == 'auto':
        if config['Web_Translation']:
            translation_module = config['Web_Translation_config'].get('Web_caiyun', {}).get('translator_type', 'Web_caiyun')
        elif config['API_translation']:
            translation_module = config['API_translation_config'].get('API_tencent', {}).get('translator_type', 'API_tencent') or                                  config['API_translation_config'].get('API_caiyun', {}).get('translator_type', 'API_caiyun')
    if translation_module == 'caiyun_web':
        translation_module = 'Web_caiyun'
    if translation_module in config['API_translation_config']:
        return config['API_translation_config'][translation_module]
    elif translation_module in config['Web_Translation_config']:
        return config['Web_Translation_config'][translation_module]
    else:
        raise ValueError(f"Unknown translation module: {translation_module}")

# 处理单个任务
def process_task(task, config):
    print("开始处理任务: ", task)
    file_path = task['file_processed_path']
    translation_module = task['translation_module']
    batch_size = task['batch_size']
    multiple_text_tasks = task['Multiple_text_tasks']
    single_text_tasks = task['Single_text_tasks']
    
    # 生成 progress_path，例如在文件路径基础上添加 .progress
    progress_path = file_path + '.progress'
    
    # 获取当前任务的速率限制配置
    rate_limit_config = get_rate_limit_config(config, translation_module)
    
    # 初始化 TokenBucket
    capacity = rate_limit_config.get('capacity', 10)
    fill_rate = rate_limit_config.get('fill_rate', 5)
    token_bucket = TokenBucket(capacity, fill_rate)
    
    # 使用现有的文件处理函数
    for _ in range(multiple_text_tasks):
        process_file(file_path, token_bucket, progress_path, config, batch_size)
    
    for _ in range(single_text_tasks):
        process_file(file_path, token_bucket, progress_path, config, 1)

# 任务队列处理器
def process_task_queue():
    print("任务队列处理器开始...")
    script_directory = os.path.dirname(os.path.abspath(__file__))
    task_queue_file = os.path.join(script_directory, 'Task Queue.yaml')
    if os.path.exists(task_queue_file):
        task_queue = load_task_queue(task_queue_file)
        
        # 加载配置
        config_path = os.path.join(script_directory, 'config.yaml')
        config = load_config(config_path)
        
        for task in task_queue:
            if task.get('completed'):
                print("任务已完成，跳过: ", task)
                continue
            
            process_task(task, config)
            
            # 标记任务为已完成
            mark_task_completed(task_queue, task)
    else:
        print("Task Queue.yaml 文件不存在，继续正常工作流程。")
        # 如果没有任务队列文件，加载正常配置继续工作
        config_path = os.path.join(script_directory, 'config.yaml')
        config = load_config(config_path)
        main_function(config)
