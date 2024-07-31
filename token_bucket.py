#token_bucket.py

import threading
import time

class TokenBucket:
    """
    令牌桶算法实现
    """
    def __init__(self, capacity, fill_rate):
        """
        初始化令牌桶
        :param capacity: 桶的容量
        :param fill_rate: 填充速率（每秒）
        """
        self.capacity = float(capacity)
        self._tokens = float(capacity)
        self.fill_rate = fill_rate
        self.lock = threading.Lock()
        self.last_time = time.time()

    def consume(self, tokens=1):
        """
        消耗令牌
        :param tokens: 要消耗的令牌数量
        :return: 如果成功消耗返回True，否则返回False
        """
        with self.lock:
            now = time.time()
            self._tokens += (now - self.last_time) * self.fill_rate
            self._tokens = min(self.capacity, self._tokens)
            self.last_time = now
            
            if self._tokens >= tokens:
                self._tokens -= tokens
                return True
            return False
