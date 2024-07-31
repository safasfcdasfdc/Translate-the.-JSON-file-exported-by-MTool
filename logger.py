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
        # 当 console_output 为 False 时，只显示任务进度信息
        logging.basicConfig(
            level=logging.INFO,
            format='%(message)s',  # 仅显示信息，不显示日志格式
            handlers=[logging.StreamHandler(sys.stdout)]
        )
    
    return logging_handlers
