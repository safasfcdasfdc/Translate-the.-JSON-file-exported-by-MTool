import base64
import logging
import requests
import time

class CaiyunTranslator:
    """
    彩云网页翻译器
    """
    def __init__(self, config):
        """
        初始化彩云网页翻译器
        :param config: 配置字典
        """
        caiyun_config = config['Web_Translation_config']['Web_caiyun']
        self.token = caiyun_config['token']
        self.bid = caiyun_config['bid']
        self.cipher_key = caiyun_config['cipher_key']
        self.normal_key = caiyun_config['normal_key']
        self.proxysession = requests.Session()
        self.jwt = None

    def decrypt(self, cipher_text):
        """
        解密函数
        :param cipher_text: 加密文本
        :return: 解密后的文本
        """
        try:
            decryption_dict = {k: v for k, v in zip(self.cipher_key, self.normal_key)}
            _ciphertext = "".join(list(map(lambda k: decryption_dict[k], cipher_text)))
            return base64.b64decode(_ciphertext).decode()
        except Exception as e:
            logging.error(f"解密失败: {e}")
            return None

    def get_jwt(self):
        """
        获取JWT令牌
        """
        headers = {
            "authority": "api.interpreter.caiyunai.com",
            "accept": "application/json, text/plain, */*",
            "accept-language": "zh-CN,zh;q=0.9,en;q=0.8,en-GB;q=0.7,en-US;q=0.6",
            "app-name": "xy",
            "cache-control": "no-cache",
            "content-type": "application/json;charset=UTF-8",
            "device-id": "",
            "origin": "https://fanyi.caiyunapp.com",
            "os-type": "web",
            "os-version": "",
            "pragma": "no-cache",
            "referer": "https://fanyi.caiyunapp.com/",
            "sec-ch-ua": '"Chromium";v="106", "Microsoft Edge";v="106", "Not;A=Brand";v="99"',
            "sec-ch-ua-mobile": "?0",
            "sec-ch-ua-platform": '"Windows"',
            "sec-fetch-dest": "empty",
            "sec-fetch-mode": "cors",
            "sec-fetch-site": "cross-site",
            "user-agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/106.0.0.0 Safari/537.36 Edg/106.0.1370.52",
            "x-authorization": self.token,
        }

        json_data = {
            "browser_id": self.bid,
        }

        response = self.proxysession.post(
            "https://api.interpreter.caiyunai.com/v1/user/jwt/generate",
            headers=headers,
            json=json_data,
        )

        if response.status_code == 200:
            self.jwt = response.json()["jwt"]
        else:
            logging.error(f"获取JWT失败，HTTP状态码: {response.status_code}")
            raise Exception("获取JWT失败")

    def translate(self, content, srclang="auto", tgtlang="zh"):
        """
        翻译函数
        :param content: 待翻译内容
        :param srclang: 源语言
        :param tgtlang: 目标语言
        :return: 翻译结果
        """
        if not self.jwt:
            self.get_jwt()

        headers = {
            "authority": "api.interpreter.caiyunai.com",
            "accept": "application/json, text/plain, */*",
            "accept-language": "zh-CN,zh;q=0.9,en;q=0.8,en-GB;q=0.7,en-US;q=0.6",
            "app-name": "xy",
            "cache-control": "no-cache",
            "content-type": "application/json;charset=UTF-8",
            "device-id": "",
            "origin": "https://fanyi.caiyunapp.com",
            "os-type": "web",
            "os-version": "",
            "pragma": "no-cache",
            "referer": "https://fanyi.caiyunapp.com/",
            "sec-ch-ua": '"Chromium";v="106", "Microsoft Edge";v="106", "Not;A=Brand";v="99"',
            "sec-ch-ua-mobile": "?0",
            "sec-ch-ua-platform": '"Windows"',
            "sec-fetch-dest": "empty",
            "sec-fetch-mode": "cors",
            "sec-fetch-site": "cross-site",
            "t-authorization": self.jwt,
            "user-agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/106.0.0.0 Safari/537.36 Edg/106.0.1370.52",
            "x-authorization": self.token,
        }

        json_data = {
            "source": content,
            "trans_type": f"{srclang}2{tgtlang}",
            "request_id": "web_fanyi",
            "media": "text",
            "os_type": "web",
            "dict": True,
            "cached": True,
            "replaced": True,
            "detect": True,
            "browser_id": self.bid,
        }

        logging.info(f"发送翻译请求: {json_data}")

        response = self.proxysession.post(
            "https://api.interpreter.caiyunai.com/v1/translator",
            headers=headers,
            json=json_data,
        )

        if response.status_code == 200:
            try:
                encrypted_texts = response.json()["target"]
                logging.info(f"收到的加密翻译结果: {encrypted_texts}")
                decrypted_texts = [self.decrypt(text) for text in encrypted_texts]
                logging.info(f"解密后的翻译结果: {decrypted_texts}")
                return decrypted_texts
            except Exception as e:
                logging.error(f"解密翻译结果时出现异常: {e}")
                raise Exception(response.json())
        else:
            logging.error(f"翻译请求失败，HTTP状态码: {response.status_code}")
            raise Exception("翻译请求失败")
