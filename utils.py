# utils.py

import json
import logging
import os
def append_translation_update(translation_updates_path, key, translation):
    with open(translation_updates_path, 'a', encoding='utf-8') as log_file:
        log_file.write(f"{json.dumps({key: translation}, ensure_ascii=False)}\n")
    logging.info("翻译更新已追加到记录文件。")

def load_progress_from_log(translation_updates_path):
    translations = {}
    if os.path.exists(translation_updates_path):
        with open(translation_updates_path, 'r', encoding='utf-8') as log_file:
            for line in log_file:
                try:
                    progress_record = json.loads(line.strip())
                    translations.update(progress_record)
                except json.JSONDecodeError:
                    logging.error(f"读取进度文件时遇到格式错误: {line}")
    return translations
