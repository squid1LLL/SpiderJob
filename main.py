#!/usr/bin/env python
# -*- coding: utf-8 -*-

import os
import sys
import getpass
from datetime import datetime
import pandas as pd

from core.browser import BrowserManager
from core.login import ZhilianLoginHandler, PasswordValidator
from core.crawler import ZhilianCrawler
from utils import data_cleaner
from utils.logger import logger
from utils.proxys_pool import ProxyPoolManager 

from config.settings import (
    MAX_RESULTS, OUTPUT_DIR, OUTPUT_FILENAME, 
    DETECTED_LOGIN_MODE as LOGIN_MODE,
    ZHILIAN_USERNAME, ZHILIAN_PASSWORD,
    PASSWORD_MIN_LENGTH,
    PASSWORD_REQUIRE_SPECIAL_CHAR,
    PASSWORD_REQUIRE_NUMBER,
    PASSWORD_REQUIRE_UPPERCASE
)

def clear_screen():
    os.system('cls' if os.name == 'nt' else 'clear')

def print_banner():
    banner = """
    ==============================================
    |                                            |
    |       Python智联招聘数据爬虫工具           |
    |           （精简版，支持智联）            |
    |                                            |
    | 爬取内容：职位名称、公司名称、薪资         |
    ==============================================
    """
    print(banner)

def input_search_keyword():
    while True:
        keyword = input("\n请输入要搜索的职位关键词 (默认: Python): ").strip()
        return keyword if keyword else "Python"

def input_max_results():
    while True:
        try:
            results = input(f"\n请输入要爬取的最大结果数 (默认: {MAX_RESULTS}): ").strip()
            return int(results) if results else MAX_RESULTS
        except ValueError:
            print("请输入有效数字!")

def show_env_setup_guide():
    print("\n📋 环境变量设置指南:")
    print("export ZHILIAN_USERNAME=\"your_username\"")
    print("export ZHILIAN_PASSWORD=\"your_password\"")

def input_login_credentials_interactive():
    print(f"\n📝 请输入智联招聘的登录信息:")
    while True:
        username = input("用户名: ").strip()
        if username:
            break
        print("用户名不能为空，请重新输入!")

    password_validator = PasswordValidator()
    while True:
        password = getpass.getpass("密码: ")
        if not password:
            print("密码不能为空，请重新输入!")
            continue

        is_valid, error_msg = password_validator.validate_password(
            password,
            min_length=PASSWORD_MIN_LENGTH,
            require_special=PASSWORD_REQUIRE_SPECIAL_CHAR,
            require_number=PASSWORD_REQUIRE_NUMBER,
            require_uppercase=PASSWORD_REQUIRE_UPPERCASE
        )

        if is_valid:
            return username, password
        else:
            print(f"密码不符合要求: {error_msg}")

def get_login_credentials():
    print(f"\n🔐 获取智联招聘登录凭据...")
    print(f"当前登录模式: {LOGIN_MODE}")
     
    if LOGIN_MODE == "env":
        if ZHILIAN_USERNAME and ZHILIAN_PASSWORD:
            print("✅ 使用环境变量中的登录信息")
            return ZHILIAN_USERNAME, ZHILIAN_PASSWORD
        else:
            print("❌ 未设置环境变量")
            choice = input("选择操作: [1]手动输入 [2]查看设置指南 [3]退出: ").strip()
            if choice == "2":
                show_env_setup_guide()
                return None, None
            elif choice == "3":
                sys.exit(0)
    return input_login_credentials_interactive()

def main():
    try:
        clear_screen()
        print_banner()

        print(f"\n🔧 当前配置:")
        print(f"   支持网站: 智联招聘")

        keyword = input_search_keyword()
        max_results = input_max_results()
        
        # ✅ 加载代理池并获取一个代理
        proxy_manager = ProxyPoolManager()
        proxy = proxy_manager.get_proxy()
        if proxy:
            print(f"🌐 使用代理: {proxy}")
        else:
            print("⚠️ 未获取到可用代理，使用直连")

        print("\n🌐 初始化浏览器...")
        browser_manager = BrowserManager()
        driver = browser_manager.create_browser()

        login_handler = ZhilianLoginHandler(driver)
        credentials = get_login_credentials()
        if not credentials or not credentials[0]:
            browser_manager.close_browser()
            return

        username, password = credentials

        print("\n🔐 正在登录，请稍候...")
        # 去掉保存登录凭证的相关参数
        login_success = login_handler.login_with_retry(username, password)
        if not login_success:
            print("\n❌ 登录失败，请检查用户名和密码是否正确!")
            browser_manager.close_browser()
            return

        crawler = ZhilianCrawler(driver)
        print(f"\n🕷️ 开始爬取智联招聘的 {keyword} 职位数据...")
        job_data = crawler.search_jobs(keyword, max_results)

        if job_data:
            # 1. 数据清洗
            cleaned = data_cleaner.DataCleaner.clean_job_data(job_data)
            df = pd.DataFrame(cleaned)

            # 2. 分类优先级：实习 > 面议 > 正式
            is_intern = df["职位名称"].str.contains("实习", case=False, na=False)
            is_negotiable = df["薪资"].str.contains("面议", na=False)

            df_intern = df[is_intern]
            df_negotiable = df[~is_intern & is_negotiable]  # 排除实习中的面议
            df_filtered = df[~is_intern & ~is_negotiable]   # 剩下的正式岗位

            # 3. 输出目录准备
            timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
            base_dir = os.path.join(OUTPUT_DIR, f"zhilian_{keyword}_{timestamp}")
            os.makedirs(base_dir, exist_ok=True)

            file_main = os.path.join(base_dir, "正式岗位_已清洗.xlsx")
            file_intern = os.path.join(base_dir, "实习岗位.xlsx")
            file_negotiable = os.path.join(base_dir, "面议岗位.xlsx")

            df_filtered.to_excel(file_main, index=False)
            df_intern.to_excel(file_intern, index=False)
            df_negotiable.to_excel(file_negotiable, index=False)

            # 4. 仅对正式岗位分析
            stats = data_cleaner.DataCleaner.analyze_data(df_filtered)
            print("\n📊 正式岗位数据统计:")
            for k, v in stats.items():
                print(f"{k}: {v}")

            # 5. 总结
            print(f"\n✅ 清洗完成，共 {len(df)} 条数据")
            print(f"📁 正式岗位：{len(df_filtered)} 条，文件：{file_main}")
            print(f"📁 实习岗位：{len(df_intern)} 条，文件：{file_intern}")
            print(f"📁 面议岗位(非实习)：{len(df_negotiable)} 条，文件：{file_negotiable}")

        else:
            print("\n⚠️ 未获取到任何职位数据")
        browser_manager.close_browser()

    except KeyboardInterrupt:
        print("\n⏹️ 用户中断程序")
        sys.exit(0)
    except Exception as e:
        logger.error(f"运行出错: {str(e)}")
        print(f"\n❌ 程序出错: {str(e)}")
        sys.exit(1)

if __name__ == "__main__":
    main()
