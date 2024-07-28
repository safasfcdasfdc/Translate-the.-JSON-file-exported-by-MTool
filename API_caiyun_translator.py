import requests
import logging

class CaiyunAPITranslator:
    """
    彩云API翻译器
    """
    def __init__(self, config):
        """
        初始化彩云API翻译器
        :param config: 配置字典
        """
        self.token = config['API_translation_config']['API_caiyun']['token']

    def translate(self, text, source_lang='auto', target_lang='zh'):
        """
        翻译函数
        :param text: 待翻译内容
        :param source_lang: 源语言
        :param target_lang: 目标语言
        :return: 翻译结果
        """
        url = "http://api.interpreter.caiyunai.com/v1/translator"
        headers = {
            "content-type": "application/json",
            "x-authorization": "token " + self.token,
        }
        payload = {
            "source": text,
            "trans_type": f"{source_lang}2{target_lang}",
            "request_id": "demo",
            "detect": True,
        }
        response = requests.post(url, json=payload, headers=headers)
        if response.status_code == 200:
            result = response.json()
            return result.get("target", [])
        else:
            logging.error(f"彩云API翻译请求失败，HTTP状态码: {response.status_code}")
            return []
