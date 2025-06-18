import random
import os
import requests
from config.settings import PROXY_POOL_FROM_FILE, PROXY_POOL_FILE_PATH, PROXY_POOL_URL

class ProxyPoolManager:
    """代理池管理器，支持从文件或URL获取"""

    def __init__(self):
        self.from_file = PROXY_POOL_FROM_FILE
        self.file_path = PROXY_POOL_FILE_PATH
        self.pool_url = PROXY_POOL_URL
        self.proxies = []

        if self.from_file:
            self._load_proxies_from_file()

    def _load_proxies_from_file(self):
        """加载本地代理池文本"""
        if not os.path.exists(self.file_path):
            print(f"⚠️ 本地代理文件未找到: {self.file_path}")
            return

        with open(self.file_path, 'r', encoding='utf-8') as f:
            self.proxies = [line.strip() for line in f if line.strip()]
        print(f"📄 已加载 {len(self.proxies)} 条代理")

    def get_proxy(self):
        """获取一个代理（从文件或API）"""
        if self.from_file:
            if not self.proxies:
                return None
            return random.choice(self.proxies)
        else:
            try:
                response = requests.get(self.pool_url, timeout=5)
                if response.ok:
                    return response.text.strip()
            except Exception as e:
                print(f"⚠️ 获取远程代理失败: {e}")
        return None
