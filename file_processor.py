#file_processor.py

import json
import logging
from concurrent.futures import ThreadPoolExecutor, as_completed
from tqdm import tqdm
from utils import append_translation_update, load_progress_from_log
from translate_function import translate_text, contains_japanese
from API_caiyun_translator import CaiyunAPITranslator
from API_tencent_translator import TencentAPITranslator
from caiyun_translator import CaiyunTranslator
import os

translations = {}

def process_translated_texts(translator, texts):
    translated_texts = translator.translate(texts)
    if isinstance(translator, TencentAPITranslator):
        translated_texts = [text.split('\n') for text in translated_texts]
        translated_texts = [item for sublist in translated_texts for item in sublist]
    return translated_texts

# 增强 process_file 函数中的日志记录
def process_file(file_path, token_bucket, progress_path, config, batch_size=1):
    global translations
    with open(file_path, 'r', encoding='utf-8') as file:
        data = json.load(file)
    
    # 增加日志记录
    logging.info(f"加载文件: {file_path}")
    
    progress_translations = load_progress_from_log(progress_path)
    translations.update(progress_translations)
    
    # 确认任务加载正确
    tasks = [(str(i+1), key, value) for i, (key, value) in enumerate(data.items()) if key == value and str(i+1) not in progress_translations and contains_japanese(key)]
    logging.info(f"任务总数：{len(tasks)}")
    
    # 确认是否加载到任务
    if not tasks:
        logging.warning("未能加载到任何任务，请检查任务条件和过滤函数。")
    
    translator = None
    custom_processing_instance = None

    if config['API_translation']:
        api_configs = config.get('API_translation_config', {})
        translators = [
            ('API_caiyun', CaiyunAPITranslator),
            ('API_tencent', TencentAPITranslator)
        ]
        sorted_translators = sorted(translators, key=lambda x: api_configs.get(x[0], {}).get('priority', 100))
        for name, translator_cls in sorted_translators:
            if api_configs.get(name, {}).get('enable', False):
                translator = translator_cls(config)
                logging.info(f"初始化翻译模块: {name}")
                break

    if config['Web_Translation']:
        web_configs = config.get('Web_Translation_config', {})
        translators = [
            ('Web_caiyun', CaiyunTranslator)
        ]
        sorted_translators = sorted(translators, key=lambda x: web_configs.get(x[0], {}).get('priority', 100))
        for name, translator_cls in sorted_translators:
            if web_configs.get(name, {}).get('enable', False):
                translator = translator_cls(config)
                logging.info(f"初始化翻译模块: {name}")
                break

    custom_translation_config = config.get('custom_translation', {})
    if custom_translation_config.get('enable', False):
        from module_loader import load_translator_and_processor
        translator, custom_processing_instance = load_translator_and_processor(config)

    if translator is None:
        logging.error("Translator initialization failed.")
        return

    with ThreadPoolExecutor(max_workers=10) as executor:
        futures = [executor.submit(
            translate_text,
            [f"{line_num}-{key}" for line_num, key, _ in tasks[i:i + batch_size]],
            [value for _, _, value in tasks[i:i + batch_size]],
            token_bucket, config, translator
        ) for i in range(0, len(tasks), batch_size)]

        with tqdm(total=len(futures), desc='翻译中', unit='批次') as progress:
            for future in as_completed(futures):
                try:
                    translation_results = future.result()
                    for id, translated_text in translation_results:
                        try:
                            line_num, key = id.split("-", 1)
                            data[key] = translated_text
                            append_translation_update(progress_path, line_num, translated_text)
                        except ValueError as e:
                            logging.error(f'解析翻译结果时出错：{e}，结果：{id}--{translated_text}')
                except Exception as exc:
                    logging.error(f'翻译失败：{exc}')
                finally:
                    progress.update(1)

    with open(file_path, 'w', encoding='utf-8') as file:
        json.dump(data, file, ensure_ascii=False, indent=4)
    
    logging.info(f"文件已写入: {file_path}")

    # 删除进度文件
    if os.path.exists(progress_path):
        os.remove(progress_path)
        logging.info(f"进度文件已删除: {progress_path}")

    return tasks, data

