#!/usr/bin/env python
# -*- coding: utf-8 -*-

import os
from cryptography.fernet import Fernet

# 加载.env文件中的环境变量
def load_env_file():
    env_file = os.path.join(os.path.dirname(__file__), '..', '.env')
    if os.path.exists(env_file):
        try:
            with open(env_file, 'r', encoding='utf-8') as f:
                for line in f:
                    line = line.strip()
                    if line and not line.startswith('#') and '=' in line:
                        key, value = line.split('=', 1)
                        value = value.strip('"\'')
                        os.environ[key] = value
            print("✅ 已加载.env文件中的环境变量")
        except Exception as e:
            print(f"⚠️ 加载.env文件失败: {e}")

load_env_file()

# 网站与搜索配置
TARGET_SITE = "zhilian"
SEARCH_KEYWORD = "Python"
MAX_PAGES = 5
MAX_RESULTS = 50

# 浏览器配置
HEADLESS = False
BROWSER_TYPE = "chrome"
WINDOW_SIZE = (1366, 768)
PAGE_LOAD_TIMEOUT = 30
IMPLICIT_WAIT = 10

# 登录模式配置
LOGIN_MODE = "auto"

# 环境变量登录信息
ZHILIAN_USERNAME = os.getenv("ZHILIAN_USERNAME", "")
ZHILIAN_PASSWORD = os.getenv("ZHILIAN_PASSWORD", "")

def detect_login_mode():
    if LOGIN_MODE == "auto":
        if ZHILIAN_USERNAME and ZHILIAN_PASSWORD:
            return "env"
        else:
            return "interactive"
    return LOGIN_MODE

DETECTED_LOGIN_MODE = detect_login_mode()

# 安全配置
ENABLE_PASSWORD_ENCRYPTION = True
SAVE_CREDENTIALS = False     # 不保存登录凭据，关闭该功能
CREDENTIALS_FILE = "data/.credentials"
MAX_LOGIN_ATTEMPTS = 3
LOGIN_RETRY_DELAY = 3

# 密码要求
PASSWORD_MIN_LENGTH = 6
PASSWORD_REQUIRE_SPECIAL_CHAR = False
PASSWORD_REQUIRE_NUMBER = False
PASSWORD_REQUIRE_UPPERCASE = False

# 反爬虫与代理
RANDOM_DELAY_MIN = 2
RANDOM_DELAY_MAX = 5
USE_PROXY = False
#代理
USE_PROXY_POOL = True
PROXY_POOL_FROM_FILE = True
PROXY_POOL_FILE_PATH = "./data/proxies.txt"
PROXY_POOL_URL = "http://127.0.0.1:7890/random"

# 重试设置
MAX_RETRIES = 3
RETRY_DELAY = 5

# 输出设置
OUTPUT_DIR = "data/output"
OUTPUT_FILENAME = "python_jobs.xlsx"

# URL配置
URLS = {
    "zhilian": {
        "login": "https://passport.zhaopin.com/additional?appID=8b25de552a844b6c8493333ce98b9caf&redirectURL=https%3A%2F%2Fxiaoyuan.zhaopin.com%2Fredirect%3Furl%3Dhttps%253A%252F%252Fxiaoyuan.zhaopin.com%252F%253Frefcode%253D",
        "search": "https://xiaoyuan.zhaopin.com/search/index?refcode=4404&query={keyword}"
    }
}

# 元素选择器配置
SELECTORS = {
    "zhilian": {
        "login": {
            "qrcode_tab": "div.zppp-panel-qrcode-bar__img",
            "login_tab": "li.zppp-panel-tab[data-bind*='账密登录']",
            "username_input": "input[name='username']",
            "password_input": "input[name='password']",
            "login_button": ".login-submit",
            "captcha_img": ".captcha-img",
            "captcha_input": "input[name='captcha']",
            "password_login_tab": ".login-tab-item:nth-child(2)",
            "error_message": ".error-msg",
            "username_input_backup": [
                "input[name='username']",
                "input[type='text']"
            ],
            "password_input_backup": [
                "input[name='password']",
                "input[type='password']"
            ],
            "login_button_backup": [
                ".login-submit",
                "button[type='submit']",
                ".submit-btn"
            ]
        },
        "search": {
            "job_list": ".position-list",
            "job_item": ".position-list__item",
            "title": ".position-card__job-name",
            "company": ".position-card__company__name",
            "salary": ".position-card__salary",
            "location": ".position-card__city-name",
            "pagination": ".pagination__inner",
            "next_page": ".pagination__arrow-next:not(.disabled)",
            "current_page": ".pagination__number--active"
        }
    }
}

def generate_encryption_key():
    return Fernet.generate_key()

def get_encryption_key():
    key_file = "data/.key"
    if os.path.exists(key_file):
        with open(key_file, 'rb') as f:
            return f.read()
    else:
        key = generate_encryption_key()
        os.makedirs(os.path.dirname(key_file), exist_ok=True)
        with open(key_file, 'wb') as f:
            f.write(key)
        return key

def print_config_status():
    print(f"🔧 配置状态:")
    print(f"   登录模式: {DETECTED_LOGIN_MODE}")
    print(f"   环境变量: {'✅' if ZHILIAN_USERNAME else '❌'} ZHILIAN_USERNAME")
    print(f"   环境变量: {'✅' if ZHILIAN_PASSWORD else '❌'} ZHILIAN_PASSWORD")
    # 不显示保存凭据状态
    # print(f"   保存凭据: {'✅' if SAVE_CREDENTIALS else '❌'}")
    print(f"   密码加密: {'✅' if ENABLE_PASSWORD_ENCRYPTION else '❌'}")

if __name__ == "__main__":
    print_config_status()
