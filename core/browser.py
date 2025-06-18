#!/usr/bin/env python
# -*- coding: utf-8 -*-

import os
import logging
from selenium import webdriver
from selenium.webdriver.chrome.options import Options as ChromeOptions
from selenium.webdriver.firefox.options import Options as FirefoxOptions
from selenium.webdriver.chrome.service import Service as ChromeService
from selenium.webdriver.firefox.service import Service as FirefoxService
from webdriver_manager.chrome import ChromeDriverManager
from webdriver_manager.firefox import GeckoDriverManager
from fake_useragent import UserAgent
from selenium.common.exceptions import WebDriverException

from utils.logger import logger
from utils.proxys_pool import ProxyPoolManager
from config.settings import (
    HEADLESS, BROWSER_TYPE, WINDOW_SIZE,
    PAGE_LOAD_TIMEOUT, IMPLICIT_WAIT
)

class BrowserManager:
    """多浏览器支持的高级浏览器管理器"""

    def __init__(self, browser_type=None, headless=None, enable_images=False, proxy=None, driver_path=None):
        self.browser_type = (browser_type or BROWSER_TYPE).lower()
        self.headless = HEADLESS if headless is None else headless
        self.enable_images = enable_images
        self.proxy = proxy
        self.driver_path = driver_path
        self.driver = None
        self.ua = UserAgent()
        self._silence_logs()

    def _silence_logs(self):
        """禁用无关日志"""
        os.environ['WDM_LOG_LEVEL'] = '0'
        os.environ['WDM_PRINT_FIRST_LINE'] = 'False'
        logging.getLogger('selenium').setLevel(logging.WARNING)
        logging.getLogger('urllib3').setLevel(logging.WARNING)

    def create_browser(self):
        """创建浏览器实例"""
        try:
            if self.browser_type == "chrome":
                self.driver = self._create_chrome()
            elif self.browser_type == "firefox":
                self.driver = self._create_firefox()
            else:
                raise ValueError(f"❌ 不支持的浏览器类型: {self.browser_type}")

            self._post_configure()
            return self.driver
        except Exception as e:
            logger.error(f"创建浏览器失败: {e}")
            raise

    def _create_chrome(self):
        options = ChromeOptions()
        options.add_argument(f"--window-size={WINDOW_SIZE[0]},{WINDOW_SIZE[1]}")
        options.add_argument("user-agent=Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/115.0.0.0 Safari/537.36")


        if self.headless:
            options.add_argument("--headless=new")
            options.add_argument("--disable-gpu")

        if self.proxy:
            options.add_argument(f"--proxy-server={self.proxy}")

        # 防检测配置
        options.add_argument("--disable-blink-features=AutomationControlled")
        options.add_experimental_option("excludeSwitches", ["enable-automation", "enable-logging"])
        options.add_experimental_option("useAutomationExtension", False)

        # 图片加载控制
        prefs = {
            "profile.default_content_setting_values.images": 1 if self.enable_images else 2
        }
        options.add_experimental_option("prefs", prefs)

        service = ChromeService(
            executable_path=self.driver_path or ChromeDriverManager().install(),
            log_path=os.devnull
        )
        return webdriver.Chrome(service=service, options=options)

    def _create_firefox(self):
        options = FirefoxOptions()
        if self.headless:
            options.add_argument("--headless")
        options.add_argument("user-agent=Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/115.0.0.0 Safari/537.36")


        if not self.enable_images:
            options.set_preference("permissions.default.image", 2)

        if self.proxy:
            ip_port = self.proxy.replace("http://", "").replace("https://", "").replace("socks5://", "")
            options.set_preference("network.proxy.type", 1)
            options.set_preference("network.proxy.http", ip_port.split(":")[0])
            options.set_preference("network.proxy.http_port", int(ip_port.split(":")[1]))
            options.set_preference("network.proxy.ssl", ip_port.split(":")[0])
            options.set_preference("network.proxy.ssl_port", int(ip_port.split(":")[1]))

        service = FirefoxService(
            executable_path=self.driver_path or GeckoDriverManager().install(),
            log_path=os.devnull
        )
        return webdriver.Firefox(service=service, options=options)

    def _post_configure(self):
        """页面加载设置与防检测 JavaScript"""
        if not self.driver:
            raise RuntimeError("浏览器未初始化")

        self.driver.set_page_load_timeout(PAGE_LOAD_TIMEOUT)
        self.driver.implicitly_wait(IMPLICIT_WAIT)
        self.driver.execute_script("Object.defineProperty(navigator, 'webdriver', {get: () => undefined})")

        if not self.headless:
            self.driver.maximize_window()

        logger.info(f"✅ 浏览器已创建: {self.browser_type}, 无头: {self.headless}, 图片: {self.enable_images}, 代理: {self.proxy}")

    def close_browser(self):
        """安全关闭浏览器"""
        if self.driver:
            try:
                self.driver.quit()
                logger.info("🔒 浏览器已关闭")
            except Exception as e:
                logger.warning(f"⚠️ 浏览器关闭异常: {e}")
            finally:
                self.driver = None
    @staticmethod
    def create_with_proxy_retry(max_retries=5, browser_type=None, headless=None, enable_images=False):
        """
        从本地代理池中尝试多次创建浏览器
        """
        proxy_pool = ProxyPoolManager()
        last_error = None

        for attempt in range(max_retries):
            proxy = proxy_pool.get_random_proxy()
            if not proxy:
                logger.warning("⚠️ 没有可用代理")
                break

            logger.info(f"🔁 第 {attempt + 1}/{max_retries} 次尝试，使用代理: {proxy}")
            try:
                bm = BrowserManager(browser_type=browser_type, headless=headless, enable_images=enable_images, proxy=proxy)
                bm.create_browser()
                return bm
            except WebDriverException as e:
                logger.warning(f"❌ 创建失败，移除代理 {proxy}：{e}")
                proxy_pool.remove_proxy(proxy)
                last_error = e

        raise RuntimeError(f"❌ 所有代理均失败，最后错误：{last_error}")
    