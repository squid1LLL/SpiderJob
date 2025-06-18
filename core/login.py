#!/usr/bin/env python
# -*- coding: utf-8 -*-

"""
登录模块 - 智联招聘独立实现
"""

import os
import json
import time
import random
import re
from cryptography.fernet import Fernet
from selenium.webdriver.common.by import By
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
from selenium.common.exceptions import TimeoutException, NoSuchElementException

from utils.logger import logger
from config.settings import URLS, SELECTORS, ENABLE_PASSWORD_ENCRYPTION, SAVE_CREDENTIALS, CREDENTIALS_FILE, MAX_LOGIN_ATTEMPTS, LOGIN_RETRY_DELAY, get_encryption_key

class PasswordValidator:
    """密码验证器"""
    @staticmethod
    def validate_password(password, min_length=6, require_special=False, require_number=False, require_uppercase=False):
        if len(password) < min_length:
            return False, f"密码长度不能少于{min_length}位"
        if require_special and not re.search(r'[!@#$%^&*(),.?":{}|<>]', password):
            return False, "密码必须包含特殊字符"
        if require_number and not re.search(r'\d', password):
            return False, "密码必须包含数字"
        if require_uppercase and not re.search(r'[A-Z]', password):
            return False, "密码必须包含大写字母"
        return True, "密码有效"

class CredentialsManager:
    """登录凭据管理器"""
    def __init__(self):
        self.key = get_encryption_key()
        self.cipher_suite = Fernet(self.key)
    
    def save_credentials(self, site_name, username, password):
        if not ENABLE_PASSWORD_ENCRYPTION:
            logger.warning("密码加密已禁用，凭据将以明文存储")
            encrypted_password = password
        else:
            encrypted_password = self.cipher_suite.encrypt(password.encode()).decode()
        
        credentials = {}
        if os.path.exists(CREDENTIALS_FILE):
            with open(CREDENTIALS_FILE, 'r') as f:
                credentials = json.load(f)
        
        credentials[site_name] = {
            'username': username,
            'password': encrypted_password
        }
        
        with open(CREDENTIALS_FILE, 'w') as f:
            json.dump(credentials, f, indent=4)
        
        logger.info(f"{site_name}凭据已保存")
    
    def load_credentials(self, site_name):
        if not os.path.exists(CREDENTIALS_FILE):
            return None, None
        
        with open(CREDENTIALS_FILE, 'r') as f:
            credentials = json.load(f)
        
        if site_name not in credentials:
            return None, None
        
        creds = credentials[site_name]
        username = creds['username']
        encrypted_password = creds['password']
        
        if ENABLE_PASSWORD_ENCRYPTION:
            try:
                password = self.cipher_suite.decrypt(encrypted_password.encode()).decode()
            except Exception as e:
                logger.error(f"密码解密失败: {str(e)}")
                return None, None
        else:
            password = encrypted_password
        
        return username, password

class BaseLoginHandler:
    """登录处理器基类"""
    def __init__(self, driver):
        self.driver = driver
        self.credentials_manager = CredentialsManager()
        self.password_validator = PasswordValidator()
    
   
    
    def login_with_retry(self, username, password, save_credentials=False):
        """带重试机制的登录（通用实现）"""
        for attempt in range(MAX_LOGIN_ATTEMPTS):
            try:
                logger.info(f"第{attempt + 1}次尝试登录...")
                success = self.login(username, password)
                
                if success:
                    if save_credentials:
                        self.credentials_manager.save_credentials(self.site_name, username, password)
                    return True
                else:
                    if attempt < MAX_LOGIN_ATTEMPTS - 1:
                        logger.warning(f"登录失败，{LOGIN_RETRY_DELAY}秒后重试...")
                        time.sleep(LOGIN_RETRY_DELAY)
                    
            except Exception as e:
                logger.error(f"登录尝试{attempt + 1}失败: {str(e)}")
                if attempt < MAX_LOGIN_ATTEMPTS - 1:
                    time.sleep(LOGIN_RETRY_DELAY)
        
        logger.error(f"登录失败，已尝试{MAX_LOGIN_ATTEMPTS}次")
        return False
    
    def _input_text_with_delay(self, element, text):
        """模拟人工输入文本，带有随机延迟"""
        element.clear()
        time.sleep(0.5)
        for char in text:
            element.send_keys(char)
            time.sleep(random.uniform(0.05, 0.15))
    
    def _wait_for_login_success(self, success_selector):
        """等待登录成功（通用实现）"""
        try:
            logger.info("等待登录成功...")
            
            # 检查错误信息（各平台通用）
            error_selectors = [".error-msg", ".ant-message-error"]
            time.sleep(2)
            
            for selector in error_selectors:
                error_elements = self.driver.find_elements(By.CSS_SELECTOR, selector)
                if error_elements and error_elements[0].is_displayed():
                    error_text = error_elements[0].text
                    if error_text and ("错误" in error_text or "失败" in error_text):
                        logger.error(f"登录失败: {error_text}")
                        return False
            
            # 等待平台特定的成功标志
            WebDriverWait(self.driver, 10).until(
                EC.presence_of_element_located((By.CSS_SELECTOR, success_selector)))
            
            logger.info(f"{self.site_name} 登录成功")
            return True
            
        except Exception as e:
            logger.error(f"等待登录成功失败: {str(e)}")
            return False


class ZhilianLoginHandler(BaseLoginHandler):
    """优化后的智联招聘登录处理器"""
    
    name_selector = [
        "input[placeholder='用户名/手机号/邮箱']",
        "input#input_958BO",
        "input.zppp-input[type='text']",
    ]

    passwd_selector = [
        "input[placeholder='密码']",
        "input#input_EIWRE",
        "input.zppp-input[type='password']",
    ]

    def __init__(self, driver):
        super().__init__(driver)
        self.site_name = "zhilian"
        self.login_url = URLS[self.site_name]["login"]
        self.selectors = SELECTORS[self.site_name]["login"]
        self.max_retries = 3  # 最大重试次数
    
    def login(self, username, password):
        """执行登录流程"""
        for attempt in range(1, self.max_retries + 1):
            try:
                logger.info(f"第 {attempt} 次尝试登录智联招聘...")
                
                #  访问登录页
                self.driver.get(self.login_url)
                time.sleep(random.uniform(1, 2))  # 随机延迟防检测

                
                #  确保切换到账密登录模式
                if not self._switch_to_password_login():
                    continue
                
                # 输入凭据
                self._input_credentials(username, password)

                #协议处理
                try:
                    # 等待复选框出现
                    accept_checkbox = WebDriverWait(self.driver, 5).until(
                        EC.presence_of_element_located((By.CSS_SELECTOR, "input.zppp-accept__checkbox"))
                    )
                    
                    # 检查是否已经勾选
                    if not accept_checkbox.is_selected():
                        # 使用JavaScript点击，避免元素被遮挡
                        self.driver.execute_script("arguments[0].click();", accept_checkbox)
                        logger.info("已勾选用户协议复选框")
                        time.sleep(0.5)  # 等待状态更新
                except Exception as e:
                    logger.warning(f"勾选用户协议时出错: {str(e)}")
                

                self._submit_login()
                
                # 验证登录结果
                if self._verify_login_success():
                    logger.info("智联招聘登录成功")
                    return True
                
            except Exception as e:
                logger.error(f"登录尝试 {attempt} 失败: {str(e)}")
                if attempt == self.max_retries:
                    logger.error("已达到最大重试次数")
                else:
                    time.sleep(2 ** attempt)  # 指数退避
        
        return False

    def _switch_to_password_login(self):

        password_selectors = [
            "li.zppp-panel-tab[data-bind*='账密登录']",
            "//li[contains(@class, 'zppp-panel-tab') and contains(text(), '账密登录')]",
            "li.zppp-panel-tab--active"
        ]

        qrcode_selectors = [
            "div.zppp-panel-qrcode-bar__img",
            "[data-bind*='loginPanelToggle']"
        ]


        for attempt in range(3):
            logger.info(f"尝试切换到账密登录（第{attempt + 1}次）")
            try:
                # 点击二维码标签以重置状态
                for qr_selector in qrcode_selectors:
                    try:
                        qr_tab = WebDriverWait(self.driver, 3).until(
                            EC.element_to_be_clickable((By.CSS_SELECTOR, qr_selector)))
                        qr_tab.click()
                        time.sleep(1)
                    except:
                        continue

                    # 点击账密登录标签
                    for pwd_selector in password_selectors:
                        try:
                            by_method = By.XPATH if "//" in pwd_selector else By.CSS_SELECTOR
                            pwd_tab = WebDriverWait(self.driver, 3).until(
                                EC.element_to_be_clickable((by_method, pwd_selector)))
                            pwd_tab.click()
                            time.sleep(1)
                            return True  # 直接认为点击完成即可
                        except:
                            continue
            except Exception as e:
                logger.warning(f"第{attempt + 1}次尝试异常: {e}")
                time.sleep(2 ** attempt)

        logger.error("自动切换到账密登录失败")
        return False


    def _input_credentials(self, username, password):
        """最终修正版凭证输入"""
        # 类型安全处理
        def safe_str(s):
            if s is None:
                return ""
            try:
                return str(s)
            except Exception as e:
                logger.warning(f"类型转换失败: {str(e)}")
                return ""
        
        username = safe_str(username)
        password = safe_str(password)
        
        logger.debug(f"输入凭证 - 用户名: {username[:1]}***{username[-1:]}, 密码: {'*'*len(password)}")
        
        try:
            # 获取输入框（带重试）
            def get_input(selectors, name):
                for selector in selectors:
                    try:
                        return WebDriverWait(self.driver, 3).until(
                            EC.element_to_be_clickable((By.CSS_SELECTOR, selector)))
                    except:
                        continue
                raise NoSuchElementException(f"找不到{name}输入框")
            
            # 输入用户名
            username_input = get_input(self.name_selector, "用户名")
            self._input_text_with_delay(username_input, username)
            
            # 输入密码
            password_input = get_input(self.passwd_selector, "密码")
            self._input_text_with_delay(password_input, password)
            
            return True
            
        except Exception as e:
            logger.error(f"输入凭证失败: {str(e)}")
            self._save_screenshot("input_credentials_failed")
            raise
    def _handle_security_checks(self):
        """处理安全验证（验证码/滑块等）"""
        try:
            # 检查图形验证码
            captcha = self.driver.find_elements(
                By.CSS_SELECTOR, self.selectors["captcha"])
            if captcha and captcha[0].is_displayed():
                logger.warning("检测到图形验证码")
                print("\n" + "="*50)
                print("⚠️ 请手动输入验证码")
                print("="*50)
                input("完成后按回车继续...")
                
            # 检查滑块验证
            slider = self.driver.find_elements(
                By.CSS_SELECTOR, ".nc_iconfont.btn_slide")
            if slider and slider[0].is_displayed():
                logger.warning("检测到滑块验证")
                print("\n" + "="*50)
                print("⚠️ 请手动完成滑块验证")
                print("="*50)
                input("完成后按回车继续...")
                
            return True
        except Exception as e:
            logger.error(f"安全验证处理失败: {str(e)}")
            return False

    def _submit_login(self):
        login_selectors = [
            ("css selector", "button.zppp-submit"),
            ("xpath", "//button[@class='zppp-submit' and text()='登录']")
        ]

        for by, selector in login_selectors:
            try:
                login_button = WebDriverWait(self.driver, 10).until(
                    EC.element_to_be_clickable((by, selector))
                )
                login_button.click()
                time.sleep(2)
                print(f"点击成功: {selector}")
                return
            except Exception as e:
                print(f"尝试 {selector} 失败: {e}")
                continue

        raise Exception("未找到可点击的登录按钮")

    def _verify_login_success(self):
        """验证登录是否成功"""
        try:
            # 方式1：检查URL变化
            if "login" not in self.driver.current_url.lower():
                return True
                
            # 方式2：检查用户信息元素
            WebDriverWait(self.driver, 10).until(
                EC.presence_of_element_located(
                    (By.CSS_SELECTOR, self.selectors["success_indicator"])))
            return True
        except:
            # 方式3：检查错误提示
            error_msg = self.driver.find_elements(
                By.CSS_SELECTOR, self.selectors["error_msg"])
            if error_msg and error_msg[0].is_displayed():
                logger.error(f"登录失败: {error_msg[0].text}")
            return False