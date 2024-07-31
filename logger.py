
import logging
import sys

def setup_logging(config):
    """
    设置日志系统
    :param config: 配置字典
    :return: 日志处理器列表
    """
    logging_handlers = []
    log_config = config

    if log_config.get('enable_logging', False):
        log_file_path = log_config.get('log_file_path', 'logfile.log')
        file_handler = logging.FileHandler(log_file_path, mode='a', encoding='utf-8')
        file_handler.setLevel(logging.DEBUG)
        logging_handlers.append(file_handler)
        
        # 仅在 console_output 为 True 时添加控制台日志处理器
        if log_config.get('console_output', False):
            console_handler = logging.StreamHandler(sys.stdout)
            console_handler.setLevel(logging.DEBUG)
            logging_handlers.append(console_handler)

        logging.basicConfig(
            level=logging.DEBUG,  # 修改为DEBUG级别
            format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
            handlers=logging_handlers
        )
    else:
        # 当 enable_logging 为 False 时，禁用所有控制台输出
        logging.basicConfig(
            level=logging.CRITICAL,  # 设置为最高级别，避免任何日志输出
            format='%(message)s',
            handlers=[]
        )
    
    return logging_handlers

# 调用 setup_logging 函数，传递配置字典
config = {
    'enable_logging': False,
    'console_output': False,
    'log_file_path': 'logfile.log'
}

setup_logging(config)
