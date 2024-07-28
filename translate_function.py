# translate_function.py

import logging
import re
import time

error_count = 0

def contains_japanese(text):
    """
    判断文本是否包含日文字符
    :param text: 输入文本
    :return: 如果包含日文字符返回True，否则返回False
    """
    return bool(re.search(r'[\u3040-\u30ff\u31f0-\u31ff\uFF00-\uFFEF]', text))

def translate_text(line_num_id, texts, token_bucket, config, translator, source_lang='auto', target_lang='zh', max_retries=20):
    """
    翻译文本
    :param line_num_id: 行号ID列表
    :param texts: 待翻译文本列表
    :param token_bucket: 令牌桶对象
    :param config: 配置字典
    :param translator: 翻译器对象
    :param source_lang: 源语言
    :param target_lang: 目标语言
    :param max_retries: 最大重试次数
    :return: 翻译结果列表
    """
    global error_count
    retries = 0
    results = []
    
    while retries < max_retries:
        if token_bucket.consume():
            try:
                logging.debug(f"请求内容: texts={texts}, source_lang={source_lang}, target_lang={target_lang}")
                translated_texts = translator.translate(texts, source_lang, target_lang)
                if translated_texts:
                    for id, translated in zip(line_num_id, translated_texts):
                        if id and translated:
                            results.append((id, translated))
                        else:
                            logging.error(f"无效的翻译结果: id={id}, translated={translated}")
                    break
                else:
                    logging.error("翻译结果为空，重试中...")
            except Exception as e:
                if 'API rate limit exceeded' in str(e):
                    error_count += 1
                    if error_count >= 5: 
                        logging.warning("达到请求异常次数上限，等待10秒后重试...")
                        time.sleep(10)
                        error_count = 0
                else:
                    logging.error(f"发送翻译请求时出现异常: {e}.")
            retries += 1
            logging.warning(f"重试第 {retries} 次翻译请求.")
        else:
            logging.debug("令牌桶为空，等待下一个令牌.")
            time.sleep(5)

    if retries >= max_retries:
        raise Exception("翻译请求失败次数过多，已放弃翻译。")

    return results
