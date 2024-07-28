import requests
import hashlib
import hmac
import time
from datetime import datetime
import logging
import json
import threading

class TencentAPITranslator:
    """
    腾讯API翻译器
    """
    def __init__(self, config):
        """
        初始化腾讯API翻译器
        :param config: 配置字典
        """
        self.secret_id = config['API_translation_config']['API_tencent']['secret_id']
        self.secret_key = config['API_translation_config']['API_tencent']['secret_key']
        self.region = config['API_translation_config']['API_tencent']['region']
        self.service = "tmt"
        self.host = "tmt.tencentcloudapi.com"
        self.version = "2018-03-21"
        self.action = "TextTranslate"
        self.algorithm = "TC3-HMAC-SHA256"
        self.capacity = config['API_translation_config']['API_tencent']['capacity']
        self.fill_rate = config['API_translation_config']['API_tencent']['fill_rate']
        self.lock = threading.Lock()
        self.tokens = self.capacity
        self.last_fill_time = time.time()

        # 速率限制配置
        self.request_exception_count = config['API_translation_config']['API_tencent']['request_exception_count']
        self.request_exception = config['API_translation_config']['API_tencent']['request_exception']

    def sign(self, key, msg):
        """
        计算签名
        :param key: 密钥
        :param msg: 消息
        :return: 签名
        """
        return hmac.new(key, msg.encode("utf-8"), hashlib.sha256).digest()

    def get_token(self):
        with self.lock:
            now = time.time()
            elapsed = now - self.last_fill_time
            self.tokens = min(self.capacity, self.tokens + elapsed * self.fill_rate)
            self.last_fill_time = now
            if self.tokens >= 1:
                self.tokens -= 1
                return True
            return False

    def parse_response(self, response):
        """
        解析API响应内容，提取翻译文本
        :param response: API响应
        :return: 翻译文本列表
        """
        try:
            data = response.json()
            if 'Response' in data and 'Error' in data['Response']:
                logging.error(f"API错误: {data['Response']['Error']['Message']}")
                return []

            if 'Response' in data and 'TargetText' in data['Response']:
                # 确保返回的每一行翻译文本是独立的
                return data['Response']['TargetText'].split('\n')
            else:
                logging.error("响应格式错误，缺少 'TargetText' 字段。")
                return []

        except json.JSONDecodeError:
            logging.error("无法解析响应内容，非JSON格式。")
            return []

    def translate(self, source_text, source_lang='auto', target_lang='zh'):
        """
        进行文本翻译
        :param source_text: 源文本
        :param source_lang: 源语言
        :param target_lang: 目标语言
        :return: 翻译文本
        """
        if isinstance(source_text, list):
            source_text = "\n".join(source_text)

        timestamp = int(time.time())
        date = datetime.utcfromtimestamp(timestamp).strftime('%Y-%m-%d')
        credential_scope = f"{date}/{self.service}/tc3_request"
        canonical_headers = "content-type:application/json; charset=utf-8\nhost:" + self.host + "\n"
        signed_headers = "content-type;host"
        payload = {
            "SourceText": source_text,
            "Source": source_lang,
            "Target": target_lang,
            "ProjectId": 0
        }
        hashed_request_payload = hashlib.sha256(json.dumps(payload).encode('utf-8')).hexdigest()
        canonical_request = (f"POST\n/\n\n{canonical_headers}\n{signed_headers}\n{hashed_request_payload}")
        hashed_canonical_request = hashlib.sha256(canonical_request.encode('utf-8')).hexdigest()
        string_to_sign = f"{self.algorithm}\n{timestamp}\n{credential_scope}\n{hashed_canonical_request}"

        secret_date = self.sign(("TC3" + self.secret_key).encode('utf-8'), date)
        secret_service = self.sign(secret_date, self.service)
        secret_signing = self.sign(secret_service, "tc3_request")
        signature = hmac.new(secret_signing, string_to_sign.encode('utf-8'), hashlib.sha256).hexdigest()

        authorization = f"{self.algorithm} Credential={self.secret_id}/{credential_scope}, SignedHeaders={signed_headers}, Signature={signature}"
        headers = {
            "Authorization": authorization,
            "Content-Type": "application/json; charset=utf-8",
            "Host": self.host,
            "X-TC-Action": self.action,
            "X-TC-Timestamp": str(timestamp),
            "X-TC-Version": self.version,
            "X-TC-Region": self.region,
            "X-TC-Language": "zh-CN"
        }

        logging.debug(f"Request Headers: {headers}")
        logging.debug(f"Request Payload: {payload}")

        # 请求重试逻辑
        for attempt in range(self.request_exception_count):
            if not self.get_token():
                logging.warning("请求频率超过限制，等待中...")
                time.sleep(self.request_exception)
                continue

            try:
                response = requests.post(f"https://{self.host}", headers=headers, json=payload)
                logging.debug(f"Response Status Code: {response.status_code}")
                logging.debug(f"Response Content: {response.content}")

                if response.status_code == 200:
                    target_texts = self.parse_response(response)
                    if not target_texts:
                        logging.error("翻译结果为空。")
                    else:
                        logging.debug(f"翻译结果: {target_texts}")
                    return target_texts
                else:
                    logging.error(f"请求失败，状态码: {response.status_code}")
            except Exception as e:
                logging.error(f"发送翻译请求时出现异常: {e}.")

        return []
